"""Rebuild the regrouping and heavy-piece modules with the pinned dependencies."""

import argparse
import json
import tempfile
from pathlib import Path

from pass09_endpoint_replay import REVIEW, run_replay


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mathlib", required=True, type=Path)
    parser.add_argument("--lean", default="lean")
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    for name, target in (("groups", "Nc.Cut.Groups"), ("heavy", "Paper.Heavy")):
        query = REVIEW / "checks" / f"pass11c_{name}.lean"
        with tempfile.TemporaryDirectory(prefix=f"pass11c-{name}-") as directory:
            result, code = run_replay(
                args.lean, args.mathlib.resolve(), Path(directory), target_module=target, query_file=query
            )
        output = args.output_dir / f"pass11c_{name}_replay.json"
        output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        if code:
            raise SystemExit(code)


if __name__ == "__main__":
    main()
