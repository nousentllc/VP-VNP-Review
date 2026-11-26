"""Run all standalone finite controls and validate archived proof evidence with standard Python."""

import argparse
import hashlib
import subprocess
import sys

from offline_replays import archived_suite, read_index, verify_bytes
from pass14_reader_check import CHECKS, REVIEW, hashed, need, receipt


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
        print("Checking the Edition 12 Comparator and margin reconciliation.", flush=True)
        subprocess.run([sys.executable, "-EB", str(REVIEW / "reconciliation/check_edition12_comparator_margin.py")],
                       cwd=REVIEW, check=True)
    print("Offline checks passed. This run did not start Lean or Comparator.")


if __name__ == "__main__":
    main()
