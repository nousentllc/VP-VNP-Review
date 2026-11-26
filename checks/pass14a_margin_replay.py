"""Recheck the review's sharpened numerical E.10 bound with the publisher's pinned libraries.

Use --offline to verify the archived evidence with Python alone.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile

from pass09_endpoint_replay import REVIEW, SOURCE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mathlib", required=True, type=Path)
    parser.add_argument("--lean", default="lean")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--objects", type=Path,
                        help="Also check the printed-circuit bridge using this previously built publisher object directory")
    args = parser.parse_args()
    libs = []
    revisions = {}
    manifest = json.loads((SOURCE / "lake-manifest.json").read_text())
    mathlib = args.mathlib.resolve()
    for pkg in manifest["packages"]:
        name = pkg["name"]
        checkout = mathlib if name == "mathlib" else mathlib / ".lake/packages" / name
        actual = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
        if actual != pkg["rev"]:
            raise ValueError(f"Unexpected revision for {name}: {actual}")
        revisions[name] = actual
        lib = checkout / ".lake/build/lib/lean"
        if lib.exists():
            libs.append(str(lib))
    version = subprocess.check_output([args.lean, "--version"], text=True).strip()
    version_pin = (SOURCE / "lean-toolchain").read_text().strip().split(":v")[-1]
    if f"version {version_pin}," not in version:
        raise ValueError(f"Expected Lean {version_pin}, received {version}")
    src = REVIEW / "checks/pass14a_margin.lean"
    opts = ["-j1", "-DautoImplicit=false"]
    env = dict(os.environ, LEAN_PATH=os.pathsep.join(libs))
    proc = subprocess.run([args.lean, *opts, str(src)], cwd=SOURCE, env=env, capture_output=True, text=True)
    output = (proc.stdout + proc.stderr).strip()
    if proc.returncode:
        raise RuntimeError(output)
    if output != "'Review.Pass14A.margin12' depends on axioms: [propext, Classical.choice, Quot.sound]":
        raise ValueError(output)
    receipt = dict(scope="Independent strict /12 arithmetic implication on the explicit E.10 wire, hub, selector and cut hypotheses. Imports Mathlib only.",
                   file=src.relative_to(REVIEW).as_posix(), sha256=hashlib.sha256(src.read_bytes()).hexdigest(),
                   lean_version=version, external_checkout_revisions=revisions, options=opts, exit_code=proc.returncode, output=output)
    if args.objects:
        obj = args.objects.resolve()
        rate = obj / "Paper/Rate.olean"
        if not rate.is_file():
            raise ValueError("Paper.Rate must first be built from the pinned publisher source.")
        bridge = REVIEW / "checks/pass14a_circuit.lean"
        def body(path):
            return "\n".join(line for line in path.read_text().splitlines() if not line.startswith("import "))
        program = "import Paper.Rate\n" + body(src) + "\n" + body(bridge) + "\n"
        with tempfile.TemporaryDirectory(prefix="pass14a-bridge-") as work:
            query = Path(work) / "Verify.lean"
            query.write_text(program)
            env["LEAN_PATH"] = os.pathsep.join([str(obj), *libs])
            run = subprocess.run([args.lean, *opts, str(query)], cwd=SOURCE, env=env,
                                 capture_output=True, text=True)
        transcript = (run.stdout + run.stderr).strip()
        expected = "'Review.Pass14A.printed_circuit12' depends on axioms: [propext, Classical.choice, Quot.sound]"
        if run.returncode or expected not in transcript:
            raise RuntimeError(transcript)
        receipt["bridge"] = dict(scope="Readback on existing original Paper.Rate objects, whose build provenance must be checked separately.",
                                 file=bridge.relative_to(REVIEW).as_posix(), sha256=hashlib.sha256(bridge.read_bytes()).hexdigest(),
                                 harness_sha256=hashlib.sha256(program.encode()).hexdigest(),
                                 rate_olean_sha256=hashlib.sha256(rate.read_bytes()).hexdigest(),
                                 rate_source_sha256=hashlib.sha256((SOURCE / "Paper/Rate.lean").read_bytes()).hexdigest(),
                                 exit_code=run.returncode, output=transcript)
        print(transcript)
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")
    print(output)


if __name__ == "__main__":
    from offline_replays import run_entrypoint

    run_entrypoint(__file__, main)
