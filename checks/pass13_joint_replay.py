"""Freshly build the union of the Paper.Flat and Paper.Laws imports and read their statements.

Use --offline to verify the archived evidence with Python alone.
"""
import argparse
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from graphlib import TopologicalSorter
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from tempfile import TemporaryDirectory

from pass09_endpoint_replay import REVIEW, SOURCE, dependency_order, source_file
from pass12e_verify_pin import publisher_tree


TARGETS = ("Paper.Flat", "Paper.Laws")
QUERY = REVIEW / "checks/pass13_joint.lean"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment(mathlib, objects):
    manifest = json.loads((SOURCE / "lake-manifest.json").read_text())
    libs = [objects]
    revisions = {}
    for pkg in manifest["packages"]:
        name = pkg["name"]
        checkout = mathlib if name == "mathlib" else mathlib / ".lake/packages" / name
        rev = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
        if rev != pkg["rev"]:
            raise ValueError(f"Expected {pkg['rev']} for {name}, found {rev}")
        revisions[name] = rev
        lib = checkout / ".lake/build/lib/lean"
        if lib.is_dir():
            libs.append(lib)
    if not (mathlib / ".lake/build/lib/lean/Mathlib.olean").is_file():
        raise ValueError("Build the pinned mathlib dependencies first.")
    return dict(os.environ, LEAN_PATH=os.pathsep.join(map(str, libs))), revisions


def imports(module, universe):
    lines = (SOURCE / source_file(module)).read_text().splitlines()
    deps = set()
    for line in lines:
        match = re.fullmatch(r"(?:public\s+)?import\s+([\w. ]+)", line.strip())
        if match:
            deps.update(name for name in match[1].split() if name in universe)
    return deps


def run(args, work):
    pin = json.loads((REVIEW / "source-lock.json").read_text())
    tree, files = publisher_tree(SOURCE)
    if (tree.hex(), files) != (pin["git_tree"], pin["blob_count"]):
        raise ValueError("Publisher source tree differs from the review pin")
    objects = work / "objects"
    objects.mkdir()
    env, revisions = environment(args.mathlib.resolve(), objects)
    version = subprocess.check_output([args.lean, "--version"], env=env, text=True).strip()
    if f"version {pin['lean_toolchain'].split(':v')[-1]}," not in version:
        raise ValueError(f"Unexpected Lean version {version}")
    cmd = [args.lean, "-j1", "-DautoImplicit=false"]
    closures = {name: dependency_order(name) for name in TARGETS}
    modules = set().union(*closures.values())

    def compile_one(name):
        rel = source_file(name)
        target = objects / rel.with_suffix(".olean")
        target.parent.mkdir(parents=True, exist_ok=True)
        p = subprocess.run([*cmd, "-o", str(target), str(rel)], cwd=SOURCE, env=env,
                           capture_output=True, text=True)
        if p.returncode:
            raise RuntimeError(f"{name}\n{p.stdout}{p.stderr}")
        return dict(module=name, source=rel.as_posix(), sha256=sha(SOURCE / rel), exit_code=0)

    graph = TopologicalSorter({name: imports(name, modules) for name in sorted(modules)})
    graph.prepare()
    rows = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        pending = {}
        while graph.is_active():
            for name in graph.get_ready():
                pending[pool.submit(compile_one, name)] = name
            finished, _ = wait(pending, return_when=FIRST_COMPLETED)
            for task in finished:
                name = pending.pop(task)
                rows[name] = task.result()
                graph.done(name)
                print(f"{len(rows)}/{len(modules)} {name}", flush=True)
    query = subprocess.run([*cmd, str(QUERY)], cwd=SOURCE, env=env, capture_output=True, text=True)
    if query.returncode:
        raise RuntimeError(query.stdout + query.stderr)
    output = (query.stdout + query.stderr).strip()
    axiom_lines = dict(re.findall(r"'([\w.]+)' depends on axioms: \[([^\]]+)\]", output))
    commands = [line for line in QUERY.read_text().splitlines() if line.startswith("#")]
    expected = {line.split()[-1] for line in commands if line.startswith("#print")}
    if axiom_lines.keys() != expected or any(
        set(names.split(", ")) - {"propext", "Classical.choice", "Quot.sound"}
        for names in axiom_lines.values()
    ):
        raise ValueError(f"Unexpected axiom readback: {axiom_lines}")
    return dict(targets=list(TARGETS), closures={k:len(v) for k,v in closures.items()},
                publisher_commit=pin["commit"], git_tree=tree.hex(), lean_version=version,
                external_checkout_revisions=revisions, scope="Fresh project modules compiled once in a shared empty object directory against prebuilt pinned dependencies.",
                modules_requested=len(modules), modules=[rows[k] for k in sorted(rows)],
                verification=dict(query_file=QUERY.relative_to(REVIEW).as_posix(), sha256=sha(QUERY),
                                  queries=commands, output=output, exit_code=0))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mathlib", required=True, type=Path)
    ap.add_argument("--lean", default="lean")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.jobs < 1:
        ap.error("Use at least one job")
    with TemporaryDirectory(prefix="pass13-joint-") as tmp:
        result = run(args, Path(tmp))
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    from offline_replays import run_entrypoint

    run_entrypoint(__file__, main)
