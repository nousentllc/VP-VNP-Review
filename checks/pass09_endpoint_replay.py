"""Replay an unmodified publisher dependency closure. The default checks Paper.thm_cn.

From the review directory, with the pinned mathlib and dependencies built:
python3 checks/pass09_endpoint_replay.py --mathlib /path/to/mathlib \
    --lean /path/to/lean --output /path/to/result.json

Use --offline to verify the archived evidence with Python alone.
"""

import argparse
import hashlib
import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path


REVIEW = Path(__file__).resolve().parents[1]
SOURCE = REVIEW / "primary/vp-vnp"
TARGET = "Paper.Fan"


def source_file(module):
    return Path(*module.split(".")).with_suffix(".lean")


def dependency_order(target_module=TARGET):
    order = []
    seen = set()

    def visit(module):
        if module in seen:
            return
        seen.add(module)
        for line in (SOURCE / source_file(module)).read_text().splitlines():
            directive = re.fullmatch(r"(?:public\s+)?import\s+([\w. ]+)", line.strip())
            if directive:
                for dep in directive.group(1).split():
                    if (SOURCE / source_file(dep)).is_file():
                        visit(dep)
                    elif dep != "Mathlib":
                        raise ValueError(f"Unexpected external import {dep} in {module}")
        order.append(module)

    visit(target_module)
    return order


def run_replay(lean, mathlib, work, *, target_module=TARGET, query_file=None):
    if target_module != TARGET and query_file is None:
        raise ValueError("A different proof target requires its own Lean query file")
    note = json.loads((REVIEW / "source-lock.json").read_text())
    packages = json.loads((SOURCE / "lake-manifest.json").read_text())["packages"]
    objects = work / "objects"
    objects.mkdir()
    libs = [objects]
    revisions = {}
    for package in packages:
        name = package["name"]
        checkout = mathlib if name == "mathlib" else mathlib / ".lake/packages" / name
        head = subprocess.check_output(
            ["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True
        ).strip()
        if head != package["rev"]:
            raise ValueError(f"Dependency {name} is at {head}, expected {package['rev']}")
        revisions[name] = head
        lib = checkout / ".lake/build/lib/lean"
        if lib.is_dir():
            libs.append(lib)
    if (libs[1] / "Mathlib.olean").is_file() is False:
        raise ValueError("The mathlib checkout requires prebuilt Mathlib objects")
    env = dict(os.environ, LEAN_PATH=os.pathsep.join(map(str, libs)))
    version = subprocess.check_output([lean, "--version"], env=env, cwd=SOURCE, text=True).strip()
    pin = (SOURCE / "lean-toolchain").read_text().strip()
    if f"version {pin.split(':v')[-1]}," not in version:
        raise ValueError(f"Expected Lean {pin}, got {version}")
    options = ["-j1", "-DautoImplicit=false"]
    modules = dependency_order(target_module)
    result = {
        "target": target_module,
        "publisher_commit": note["commit"],
        "lean_version": version,
        "lean_toolchain": pin,
        "external_checkout_revisions": revisions,
        "prebuilt_imports": "Pinned Lean, mathlib and its dependencies. All project modules are rebuilt in dependency order into an empty directory.",
        "lean_options": options,
        "modules_requested": len(modules),
        "modules": [],
        "verification": None,
    }
    for index, module in enumerate(modules, start=1):
        relative = source_file(module)
        target = objects / relative.with_suffix(".olean")
        target.parent.mkdir(parents=True, exist_ok=True)
        start = time.monotonic()
        build = subprocess.run(
            [lean, *options, "-o", str(target), str(relative)], cwd=SOURCE,
            env=env, capture_output=True, text=True,
        )
        row = {
            "module": module, "source": relative.as_posix(),
            "sha256": hashlib.sha256((SOURCE / relative).read_bytes()).hexdigest(),
            "exit_code": build.returncode, "seconds": round(time.monotonic() - start, 2),
        }
        if build.stdout or build.stderr:
            row["output"] = (build.stdout + build.stderr).replace(str(work), "<build>")
        result["modules"].append(row)
        print(f"{index}/{len(modules)} {module} exit {build.returncode} ({row['seconds']} s)", flush=True)
        if build.returncode:
            print(row.get("output", ""), flush=True)
            return result, build.returncode
    if query_file is None:
        queries = [
            "#check @Paper.thm_cn", "#print axioms Paper.lem_means",
            "#print axioms Paper.thm_cn_end", "#print axioms Paper.thm_cn",
        ]
        query = work / "Verify.lean"
        query.write_text("import Paper.Fan\n" + "\n".join(queries) + "\n")
    else:
        query = query_file
        queries = [line for line in query.read_text().splitlines() if line.startswith("#")]
    verify = subprocess.run(
        [lean, *options, str(query)], cwd=SOURCE, env=env, capture_output=True, text=True
    )
    result["verification"] = {
        "queries": queries, "exit_code": verify.returncode,
        "output": (verify.stdout + verify.stderr).replace(str(work), "<build>").strip(),
    }
    if query_file is not None:
        result["verification"]["query_file"] = query.relative_to(REVIEW).as_posix()
        result["verification"]["sha256"] = hashlib.sha256(query.read_bytes()).hexdigest()
    print(result["verification"]["output"], flush=True)
    return result, verify.returncode


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mathlib", required=True, type=Path, help="Built pinned mathlib checkout")
    parser.add_argument("--lean", default="lean", help="Pinned Lean executable")
    parser.add_argument("--output", required=True, type=Path, help="Destination JSON")
    parser.add_argument("--target-module", default=TARGET, help="Publisher module to rebuild")
    parser.add_argument("--query-file", type=Path, help="Lean declarations to check after rebuilding, inside the review repository")
    args = parser.parse_args()
    query = args.query_file.resolve() if args.query_file else None
    if query is not None and (not query.is_file() or REVIEW not in query.parents):
        parser.error("--query-file must name an existing file inside the review repository")
    if args.target_module != TARGET and query is None:
        parser.error("--target-module needs --query-file when checking another theorem")
    with tempfile.TemporaryDirectory(prefix="pass09-fan-") as tmp:
        result, code = run_replay(
            args.lean, args.mathlib.resolve(), Path(tmp),
            target_module=args.target_module, query_file=query,
        )
        args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    raise SystemExit(code)


if __name__ == "__main__":
    from offline_replays import run_entrypoint

    run_entrypoint(__file__, main)
