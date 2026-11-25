"""Replay the unmodified publisher dependency closure for Propositions A.7 and A.8.

From the review directory, with the pinned mathlib and dependencies built:
python3 checks/pass10_formal_replay.py --mathlib /path/to/mathlib \
    --lean /path/to/lean --output /path/to/result.json
"""

import argparse
import json
import tempfile
from pathlib import Path

from pass09_endpoint_replay import REVIEW, run_replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mathlib", required=True, type=Path, help="Built pinned mathlib checkout")
    parser.add_argument("--lean", default="lean", help="Pinned Lean executable")
    parser.add_argument("--output", required=True, type=Path, help="Destination JSON")
    parser.add_argument("--build-dir", type=Path, help="Retain new compiled objects in this previously absent directory")
    args = parser.parse_args()
    mathlib = args.mathlib.resolve()
    target = dict(target_module="Paper.Prices", query_file=REVIEW / "checks/pass10_formal.lean")
    if args.build_dir is None:
        with tempfile.TemporaryDirectory(prefix="pass10-prices-") as tmp:
            result, code = run_replay(args.lean, mathlib, Path(tmp), **target)
    else:
        args.build_dir.mkdir(exist_ok=False)
        result, code = run_replay(args.lean, mathlib, args.build_dir.resolve(), **target)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    raise SystemExit(code)


if __name__ == "__main__":
    main()
