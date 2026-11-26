"""Run all standalone finite controls and validate archived proof evidence with standard Python."""

import argparse
import gzip
import hashlib
import json
import subprocess
import sys

from offline_replays import archived_suite, read_index, verify_bytes
from pass14_reader_check import CHECKS, REVIEW, hashed, need, receipt


def verify_hosted_transcript():
    archive = REVIEW / "history/actions/pass14-job-139478246305.log.gz"
    raw = gzip.decompress(archive.read_bytes())
    need(hashlib.sha256(raw).hexdigest() == "f4202727be9e16f795a32cf2e4df28be0917001edfb9102c821ba4ed81b57e21",
         "Preserved Actions transcript differs")
    excerpts = json.loads((REVIEW / "reconciliation/edition12-hosted-log-excerpts.json").read_text())
    lines = raw.decode("utf-8-sig").splitlines()
    need(all(lines[row["line"] - 1] == row["text"] for row in excerpts["lines"]),
         "Actions transcript and historical excerpts disagree")
    print("Verified the full archived Actions transcript and all recorded excerpts.")


def finite_suite():
    index = read_index()
    verify_bytes(index, ["checks/pass14_prior_controls.json"])
    expected = {}
    for row in receipt("pass14_prior_controls.json")["results"]:
        script = REVIEW / row["script"]
        need(hashed(script) == row["script_sha256"], f"Historical control changed: {script.name}")
        expected[script] = row["stdout_sha256"]
    for stem in ("pass14a_flat", "pass14b_tower", "pass14c_compiler", "pass15_k4", "pass15_k5", "pass15_k6"):
        record = stem + ("_results.json" if stem.startswith("pass14") else ".json")
        expected[CHECKS / (stem + ".py")] = hashed(CHECKS / record)
    failures = []
    for script, reference in expected.items():
        print(f"Running {script.name}", flush=True)
        try:
            # Ignore PYTHONOPTIMIZE so the assertions in the finite controls really execute.
            output = subprocess.check_output([sys.executable, "-EB", str(script)], cwd=REVIEW)
            need(hashlib.sha256(output).hexdigest() == reference, f"{script.name}: stdout digest differs")
        except (OSError, ValueError, subprocess.CalledProcessError) as error:
            failures.append(str(error))
    need(not failures, "\n".join(failures))
    print(f"All {len(expected)} standalone finite controls reran and matched their recorded outputs.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--finite-only", action="store_true", help="Run only the finite mathematical controls")
    modes.add_argument("--receipts-only", action="store_true", help="Check only stored formal and release evidence")
    args = parser.parse_args()
    if not args.receipts_only:
        finite_suite()
    if not args.finite_only:
        archived_suite()
        verify_hosted_transcript()
        print("Checking the Edition 12 Comparator and margin reconciliation.", flush=True)
        subprocess.run([sys.executable, "-EB", str(REVIEW / "reconciliation/check_edition12_comparator_margin.py")],
                       cwd=REVIEW, check=True)
    print("Offline checks passed. This run did not start Lean or Comparator.")


if __name__ == "__main__":
    main()
