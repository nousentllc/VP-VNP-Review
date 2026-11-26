"""Compile the review's Lean modules and hash their portable evidence."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CHECKS = ROOT / "checks"
PROJECT = ROOT / "primary/vp-vnp"
AXIOMS = re.compile(r"^'([^']+)' depends on axioms: \[([^\]]*)\]$", re.MULTILINE)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def axiom_sets(transcript):
    return {name: sorted(filter(None, values.split(", "))) for name, values in AXIOMS.findall(transcript)}


def files():
    # The bridge imports the review's arithmetic module. Build that module first.
    return sorted(CHECKS.glob("*.lean"), key=lambda path: (path.stem != "pass14a_margin", path.name))


def targets():
    local = set()
    for path in files():
        for line in path.read_text().splitlines():
            if line.startswith("import "):
                for module in line.split()[1:]:
                    if (PROJECT / Path(*module.split(".")).with_suffix(".lean")).is_file():
                        local.add("+" + module)
    return sorted(local)


def verify_packages(packages, split_mathlib=False):
    manifest = json.loads((PROJECT / "lake-manifest.json").read_text())["packages"]
    paths = []
    for item in manifest:
        name = item["name"]
        if split_mathlib:
            checkout = packages if name == "mathlib" else packages / ".lake/packages" / name
        else:
            checkout = packages / name
        revision = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
        if revision != item["rev"]:
            raise ValueError(f"{name}: expected {item['rev']}, got {revision}")
        lib = checkout / ".lake/build/lib/lean"
        if name == "mathlib" and not (lib / "Mathlib.olean").is_file():
            raise ValueError(f"Missing compiled Mathlib: {lib}")
        if lib.is_dir():
            paths.append(lib)
    return paths


def verify(args):
    lean_pin = (PROJECT / "lean-toolchain").read_text().strip()
    version = subprocess.check_output([args.lean, "--version"], text=True, cwd=PROJECT).strip()
    if f"version {lean_pin.split(':v')[-1]}," not in version:
        raise ValueError(f"Expected {lean_pin}, got {version}")
    paths = verify_packages(args.mathlib or args.packages, split_mathlib=bool(args.mathlib))
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    objects = output / "objects"
    objects.mkdir()
    env = dict(os.environ, LEAN_PATH=os.pathsep.join(map(str, [objects, args.objects.resolve(), *paths])))
    for module in files():
        run = subprocess.run([args.lean, "-j1", "-DautoImplicit=false", "-o", str(objects / module.with_suffix('.olean').name),
                              module.name], cwd=CHECKS, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (output / module.with_suffix(".log").name).write_bytes(run.stdout)
        if run.returncode:
            raise RuntimeError(f"{module.name}:\n{run.stdout.decode(errors='replace')}")
        print(f"Compiled {module.name}", flush=True)

    spec = json.loads((ROOT / "reproduce/expected.json").read_text())["tier1"]
    proof_checks = {}
    for stem, expected in spec["proof_checks"].items():
        actual = axiom_sets((output / f"{stem}.log").read_text())
        found = {name: actual.get(name) for name in expected}
        if found != expected:
            raise ValueError(f"{stem}: axiom readbacks differ from recorded evidence: {found}")
        proof_checks[stem] = found
    evidence = dict(toolchain=lean_pin, modules={p.name: sha(p.read_bytes()) for p in files()}, proof_checks=proof_checks)
    payload = (json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n").encode()
    digest = sha(payload)
    (output / "tier1-evidence.json").write_bytes(payload)
    if digest != spec["sha256"]:
        raise ValueError(f"Tier 1 digest mismatch: {digest}")
    print(f"Tier 1 passed. Evidence SHA-256 {digest}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--targets", action="store_true")
    parser.add_argument("--lean", default="lean")
    providers = parser.add_mutually_exclusive_group()
    providers.add_argument("--packages", type=Path, default=PROJECT / ".lake/packages")
    providers.add_argument("--mathlib", type=Path, help="Standalone pinned Mathlib checkout with its built dependencies")
    parser.add_argument("--objects", type=Path, default=PROJECT / ".lake/build/lib/lean")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.targets:
        print("\n".join(targets()))
        return
    if not args.output:
        parser.error("--output is required")
    verify(args)


if __name__ == "__main__":
    main()
