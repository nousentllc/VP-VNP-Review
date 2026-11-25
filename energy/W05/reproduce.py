"""Audit saved W05 evidence or execute a new frozen campaign outside the packet.

Use 'audit --out DIR' to replay archived witnesses without new policy solves.
The small-cell A diagnostic re-solves fixed-mode LPs off the clock.
Use 'rerun --out DIR --lean EXE --packages DIR' to generate and check fresh
results. The --lean and --packages options also enable a fresh proof check in
audit mode. Set W05_LEAN and W05_LEAN_PACKAGES instead if preferred. Select
tracks using --tracks B E A C. The original clocks and logs remain intact.
"""
import argparse
import datetime as dt
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
W04 = ROOT.parent / "W04"
TRACKS = ("B", "E", "A", "C")
THREADS = ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS",
           "VECLIB_MAXIMUM_THREADS", "NUMEXPR_NUM_THREADS", "BLIS_NUM_THREADS")


def sha(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


def load(path):
    return json.loads(path.read_text())


def check_locks(tracks):
    specs = {
        "B": [("B/proof_lock.json", "sha256", ROOT / "B"),
              ("B/engineering/freeze.json", "sha256", ROOT / "B/engineering")],
        "E": [("E/protocol/freeze.json", "sha256", ROOT / "E"),
              ("E/protocol/freeze.json", "w04_sha256", W04)],
        "A": [("A/protocol/freeze.json", "sha256", ROOT / "A"),
              ("A/protocol/freeze.json", "assets_sha256", ROOT / "A/protocol")],
        "C": [("C/freeze.json", "hashes", ROOT.parent)],
    }
    verified = {}
    for track in tracks:
        for lock, key, base in specs[track]:
            files = load(ROOT / lock)[key]
            for name, expected in files.items():
                if sha(base / name) != expected:
                    raise ValueError(f"Frozen input digest mismatch: {lock}: {name}")
            verified[f"{lock} / {key}"] = len(files)
    return verified


class Campaign:
    def __init__(self, args):
        self.args = args
        self.fresh = args.mode == "rerun"
        self.out = args.out.resolve()
        self.out.mkdir(parents=True, exist_ok=False)
        self.env = dict(os.environ, **{k: "1" for k in THREADS}, PYTHONDONTWRITEBYTECODE="1",
                        PYTHONOPTIMIZE="0", W03_RESULTS=str(self.out / "scratch"),
                        W05_W04_ROOT=str(W04))
        self.record = {"mode": args.mode, "tracks": args.tracks, "steps": [],
                       "archived_outputs_checked": [], "thread_env": {k: self.env[k] for k in THREADS},
                       "started_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
        (self.out / "logs").mkdir()

    def run(self, name, script, *args, capture=None):
        dest = capture or (self.out / "logs" / (name + ".log"))
        argv = [sys.executable, str(ROOT / script), *map(str, args)]
        print(name, flush=True)
        tick = time.monotonic()
        with dest.open("w") as log:
            proc = subprocess.run(argv, cwd=self.out, env=self.env, stdout=log,
                                  stderr=None if capture else subprocess.STDOUT)
        self.record["steps"].append({"step": name, "script": script, "log": str(dest.relative_to(self.out)),
                                     "exit": proc.returncode, "elapsed_s": time.monotonic() - tick})
        if proc.returncode:
            raise RuntimeError(f"{name} exited {proc.returncode}; see {dest}")

    def compare(self, result, archived):
        if self.fresh:
            return
        if result.name.endswith(".json.gz"):
            with gzip.open(result, "rt") as left, gzip.open(archived, "rt") as right:
                equal = json.load(left) == json.load(right)
        elif result.suffix == ".json":
            equal = load(result) == load(archived)
        else:
            equal = sha(result) == sha(archived)
        if not equal:
            raise ValueError(f"Recomputed output differs from archive: {archived.relative_to(ROOT)}")
        self.record["archived_outputs_checked"].append(str(archived.relative_to(ROOT)))

    def tables(self, new, archive, files):
        for name in files.split():
            self.compare(new / name, archive / name)

    def b(self, out):
        base = ROOT / "B/engineering"
        self.run("B-exact", "B/exact_controls.py", capture=out / "exact_controls.json")
        self.compare(out / "exact_controls.json", ROOT / "B/results/exact_controls.json")
        if self.args.lean:
            self.run("B-lean", "B/verify.py", "--lean", self.args.lean.resolve(),
                     "--packages", self.args.packages.resolve(), "--out", out / "lean")
        self.record["lean_recompiled"] = bool(self.args.lean)
        source = out if self.fresh else base
        primary, retry = source / "holdout.jsonl.gz", source / "anchor_retry.jsonl.gz"
        support = out / "support.jsonl.gz"
        if self.fresh:
            self.run("B-primary", "B/engineering/campaign.py", "run", primary)
            self.run("B-retry", "B/engineering/diagnose.py", primary, retry)
            self.run("B-support", "B/engineering/tighten.py", primary, support)
        else:
            shutil.copyfile(base / support.name, support)
        self.run("B-certificates", "B/engineering/check.py", primary, retry, out / "analysis")
        self.run("B-independent-bound-check", "B/audit_engineering.py", "--primary", primary,
                 "--retry", retry, "--out", out / "engineering_crosscheck.json")
        self.run("B-support-check", "B/engineering/tighten.py", primary, support, "--check")
        self.tables(out / "analysis", base / "analysis", "certificates.csv slots.csv primary_failures.csv summary.json")
        self.compare(out / "support_analysis.csv", base / "support_analysis.csv")
        self.compare(out / "engineering_crosscheck.json", ROOT / "B/results/engineering_crosscheck.json")

    def e(self, out):
        base = ROOT / "E/results"
        source = out if self.fresh else base
        primary = source / "primary.jsonl.gz"
        repeat = source / "controlled_replay.jsonl.gz"
        analysis = out / "analysis"
        if self.fresh:
            self.run("E-primary", "E/run.py", "--out", primary)
            self.run("E-controlled-replay", "E/run.py", "--out", repeat, "--signals-from", primary)
        self.run("E-audit", "E/audit.py", "--primary", primary, "--repeat", repeat, "--out", analysis)
        self.run("E-diagnostics", "E/diagnostics.py", "--out", analysis)
        cert = source / "analysis/opportunity_certificates.json.gz"
        if self.fresh:
            self.run("E-opportunity", "E/opportunity.py", "--primary", primary, "--out", analysis)
        self.run("E-opportunity-check", "E/verify_bounds.py", "--certificates", cert,
                 "--out", analysis / "opportunity_verification.json")
        self.run("E-baseline-check", "E/baseline_alignment.py", "--raw", primary,
                 "--certificates", cert, "--out", analysis / "baseline_alignment.json")
        self.tables(analysis,base / "analysis","validation.json arm_summary.csv effects.csv economics.csv "
                    "forecast_errors.csv paired_days.csv scenario_metrics.csv pareto.csv nested_checks.csv "
                    "opportunity_verification.json baseline_alignment.json")

    def a(self, out):
        base = ROOT / "A/results"
        if self.fresh:
            self.run("A-primary", "A/campaign.py", "run", "--out", out)
        raw = (out if self.fresh else base) / "trials.jsonl.gz"
        for name in ["analyze", "mechanism", "rational_primal"]:
            self.run("A-" + name, f"A/{name}.py", "--raw", raw, "--out", out)
        self.tables(out,base,"verification.json mechanisms.json small_exact_summary.json small_exact_primal.json.gz summary.csv stages.csv "
                    "case_medians.csv contrasts.csv paired_cases.csv trials.csv mutation_controls.csv")

    def c(self, out):
        base = ROOT / "C"
        source = out if self.fresh else base
        raw, profile = source / "raw", source / "profile_raw"
        if self.fresh:
            self.run("C-primary", "C/opf.py", "run", raw)
            self.run("C-profile", "C/profile_panel.py", profile)
        self.run("C-analyze", "C/analyze.py", raw, out / "analysis", "--profile", profile)
        self.run("C-initials", "C/check_initials.py", "--raw", raw, "--out", out / "initial_review.json")
        self.run("C-angle-bounds", "C/angle_bounds.py", "--out", out / "angle_bounds.json")
        self.tables(out, base, "initial_review.json angle_bounds.json")
        self.tables(out / "analysis", base / "analysis", "trials.csv cases.csv matched.csv verification.json native_profile.csv")

    def execute(self):
        try:
            self.record["frozen_hash_checks"] = check_locks(self.args.tracks)
            self.run("manuscript-source", "manuscript/check_source.py", capture=self.out / "source_audit.json")
            self.compare(self.out / "source_audit.json", ROOT / "manuscript/reference_audit.json")
            for track in self.args.tracks:
                out = self.out / track
                out.mkdir()
                getattr(self, track.lower())(out)
            self.record["status"] = "passed"
        except BaseException as exc:
            self.record.update(status="failed", error=str(exc))
            raise
        finally:
            self.record["finished_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
            (self.out / "audit_record.json").write_text(json.dumps(self.record, indent=2) + "\n")
        print(f"Completed. Evidence and logs: {self.out}", flush=True)


def main():
    cli = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    cli.add_argument("mode", choices=["audit", "rerun"])
    cli.add_argument("--out", type=Path, required=True, help="new directory outside W04 and W05")
    cli.add_argument("--tracks", nargs="+", choices=TRACKS, default=list(TRACKS))
    cli.add_argument("--lean", type=Path, default=os.getenv("W05_LEAN"))
    cli.add_argument("--packages", type=Path, default=os.getenv("W05_LEAN_PACKAGES"))
    cli.add_argument("--skip-lean", action="store_true", help="explicitly omit the Lean rebuild in a numerical rerun")
    args = cli.parse_args()
    if sys.flags.optimize:
        cli.error("Run with Python assertions enabled")
    if any(args.out.resolve().is_relative_to(p) for p in (ROOT, W04)):
        cli.error("Output must be outside the input W05 and W04 directories")
    if not W04.is_dir():
        cli.error("Extract the bundled W04 directory alongside W05")
    if len(set(args.tracks)) != len(args.tracks):
        cli.error("Each track may appear only once")
    if args.skip_lean:
        args.lean = args.packages = None
    if bool(args.lean) != bool(args.packages):
        cli.error("Supply --lean and --packages together")
    if args.mode == "rerun" and "B" in args.tracks and not (args.lean or args.skip_lean):
        cli.error("Supply --lean and --packages or use --skip-lean explicitly")
    Campaign(args).execute()


if __name__ == "__main__":
    main()
