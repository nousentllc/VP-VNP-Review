"""Check archive integrity, recompute results, or rerun the W04 frozen numerical workers."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def integrity():
    listed = set()
    for line in (ROOT / "SHA256SUMS.txt").read_text().splitlines():
        expected, name = line.split("  ", 1)
        if digest(ROOT / name) != expected:
            raise ValueError(f"File digest mismatch for {name}")
        if name in listed:
            raise ValueError(f"Repeated manifest entry for {name}")
        listed.add(name)
    print(f"Verified {len(listed)} release files.", flush=True)


def execute(args):
    integrity()
    if args.mode == "integrity":
        return
    if args.output is None:
        raise ValueError("Supply a new output directory with --output.")
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError("Choose a replay destination outside the evidence archive.")
    selected = [s.strip().upper() for s in args.tracks.split(",")]
    if set(selected) - set("ABCDE"):
        raise ValueError("Use comma-separated track letters A,B,C,D,E.")
    if "B" in selected and not args.exact_only and not (args.lean and args.packages):
        raise ValueError("Supply --lean and --packages, or --exact-only to run only rational B controls.")
    output.mkdir(parents=True,exist_ok=False)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", OPENBLAS_NUM_THREADS="1",
               OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", VECLIB_MAXIMUM_THREADS="1")
    fresh = args.mode == "rerun"

    def run(script, *argv, capture=None):
        command = [sys.executable, str(ROOT / script), *map(str,argv)]
        print("Running", script, *argv, flush=True)
        if capture is None:
            subprocess.run(command, cwd=ROOT, env=env, check=True)
        else:
            with capture.open("w") as stream:
                subprocess.run(command, cwd=ROOT, env=env, stdout=stream, check=True)

    if "A" in selected:
        dest = output / "A"
        dest.mkdir()
        if fresh:
            run("A/campaign.py","run","--out",dest)
        else:
            shutil.copyfile(ROOT / "A/results/trials.jsonl.gz",dest / "trials.jsonl.gz")
        for script in ["analysis","start_audit","supplement","presolve_check"]:
            run(f"A/{script}.py","--out",dest)
        run("A/mutation_checks.py","--out",dest / "mutations.json")
    if "B" in selected:
        dest = output / "B"
        dest.mkdir()
        run("B/exact_controls.py",capture=dest / "exact_controls.json")
        if json.loads((dest / "exact_controls.json").read_text()) != json.loads((ROOT / "B/results/exact_controls.json").read_text()):
            raise ValueError("B rational control mismatch")
        if not args.exact_only:
            run("B/verify.py","--lean",args.lean.resolve(),"--packages",args.packages.resolve(),"--out",dest)
    if "E" in selected:
        dest = output / "E"
        dest.mkdir()
        if fresh:
            primary, repeat = dest / "holdout.jsonl.gz", dest / "repeat.jsonl.gz"
            plans = dest / "projected_plans.jsonl.gz"
            run("E/campaign.py","run","--out",primary)
            run("E/capture_replay.py","--out",repeat,"--plans",plans)
        else:
            primary = ROOT / "E/results/holdout.jsonl.gz"
            repeat = ROOT / "E/results/repeat.jsonl.gz"
            plans = ROOT / "E/results/projected_plans.jsonl.gz"
        run("E/analyze.py","--raw",primary,"--repeat",repeat,"--out",dest / "analysis")
        run("E/supplemental_audit.py","--primary",primary,"--repeat",repeat,"--plans",plans,"--out",dest / "supplemental")
    if "C" in selected:
        dest = output / "C"
        raw = dest / "raw" if fresh else ROOT / "C/raw"
        if fresh:
            run("C/opf.py","run",raw)
        run("C/check.py",raw,dest / "analysis")
        run("C/analyze.py",dest / "analysis")
        run("C/review_check.py","--raw",raw,"--out",dest / "independent_review.json")
    if "D" in selected:
        for name,script in [("raw","panel"),("serial_raw","serial_replay")]:
            dest = output / "D" / name
            raw = dest / "raw" if fresh else ROOT / "D" / name
            if fresh:
                run(f"D/{script}.py",raw)
            run("D/check.py",raw,dest / "analysis")
            run("D/analyze.py",raw,dest / "analysis")
        primary = output / "D/raw/raw" if fresh else ROOT / "D/raw"
        serial = output / "D/serial_raw/raw" if fresh else ROOT / "D/serial_raw"
        run("D/transfer_review.py","--primary",primary,"--serial",serial,"--out",output / "D/transfer_review")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode",choices=["integrity","audit","rerun"])
    parser.add_argument("--output",type=Path)
    parser.add_argument("--tracks",default="A,B,E,C,D")
    parser.add_argument("--lean",type=Path)
    parser.add_argument("--packages",type=Path)
    parser.add_argument("--exact-only",action="store_true",help="B rational controls only; skips Lean.")
    execute(parser.parse_args())
