"""Check the two J.4 follow-up declarations against the pinned Lean project."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
PUBLISHER = "11b6c7e3c927df2658f513b6b68ea7f8929c62c5"
SOURCE_HASHES = {
    "Paper/Cuts.lean": "80fed8d478bc9b6c9e9265942a1d5e910f531ed34a9c2bf63bdbe4f77aa608b6",
    "Paper/Next.lean": "bfe9a9a6ca66911ba9fc8beae195e8101e5e0283fd3c732fee61c8f6c9768a5c",
    "NS1/OneCut.lean": "161c6a46c1851e8ad58356cfc5c2fdf7fd9606aaa333d851c65ca6dc42a03f17",
}
EXPECTED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def environment(mathlib, objects, project):
    revisions = {}
    libraries = [objects]
    lock = json.loads((project / "lake-manifest.json").read_text())
    for entry in lock["packages"]:
        name = entry["name"]
        package = mathlib if name == "mathlib" else mathlib / ".lake/packages" / name
        revision = subprocess.check_output(["git", "-C", str(package), "rev-parse", "HEAD"],
                                           text=True).strip()
        if revision != entry["rev"]:
            raise ValueError(f"{name} is at {revision}, expected {entry['rev']}")
        revisions[name] = revision
        lib = package / ".lake/build/lib/lean"
        if name == "mathlib" and not (lib / "Mathlib.olean").is_file():
            raise ValueError("Build the pinned Mathlib checkout first.")
        if lib.is_dir():
            libraries.append(lib)
    return dict(os.environ, LEAN_PATH=os.pathsep.join(map(str, libraries))), revisions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True, type=Path, help="Pinned publisher vp-vnp source tree")
    parser.add_argument("--mathlib", required=True, type=Path, help="Pinned, built standalone Mathlib checkout")
    parser.add_argument("--objects", required=True, type=Path, help="Compiled objects for the pinned publisher")
    parser.add_argument("--lean", default="lean")
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    project = args.project.resolve()
    objects = args.objects.resolve()
    for rel, expected in SOURCE_HASHES.items():
        if sha(project / rel) != expected:
            raise ValueError(f"Publisher input differs: {rel}")
    version = subprocess.check_output([args.lean, "--version"], cwd=project, text=True).strip()
    if "version 4.33.1," not in version:
        raise ValueError(f"Expected Lean 4.33.1, received {version}")
    env, revisions = environment(args.mathlib.resolve(), objects, project)
    options = ["-j1", "-DautoImplicit=false"]
    proof = HERE / "J4_Followup.lean"
    started = time.monotonic()
    run = subprocess.run([args.lean, *options, str(proof)], cwd=project, env=env,
                         capture_output=True, text=True)
    transcript = run.stdout + run.stderr
    print(transcript, end="")
    if run.returncode:
        sys.exit(run.returncode)
    rows = re.findall(r"^'([^']+)' depends on axioms: \[([^]]+)\]$", transcript, re.MULTILINE)
    axioms = {name: set(items.split(", ")) for name, items in rows}
    expected = {f"Review.J4.{name}": EXPECTED_AXIOMS for name in
                ("j4_iterate_bounds", "k5_listing_and_traversal")}
    if axioms != expected or len(rows) != 2 or len(transcript.splitlines()) != 2:
        raise ValueError("Unexpected declaration, axiom dependency or diagnostic")
    receipt = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "publisher_commit": PUBLISHER,
        "publisher_source_sha256": SOURCE_HASHES,
        "imported_cuts_olean_sha256": sha(objects / "Paper/Cuts.olean"),
        "mathlib_and_dependencies": revisions,
        "lean_version": version,
        "lean_options": options,
        "proof_sha256": sha(proof),
        "scope": "New review declarations checked using retained publisher objects. The check does not rebuild publisher or external libraries.",
        "axioms": {name: sorted(items) for name, items in axioms.items()},
        "runtime_seconds": round(time.monotonic() - started, 3),
        "exit_code": run.returncode,
        "stdout": run.stdout.splitlines(),
        "stderr": run.stderr.splitlines(),
    }
    if args.receipt:
        args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")


if __name__ == "__main__":
    main()
