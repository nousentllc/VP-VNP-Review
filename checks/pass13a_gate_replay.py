"""Freshly build the coefficient induction, then check the publisher's E.4 excerpt."""

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path

from pass09_endpoint_replay import REVIEW, SOURCE, run_replay

PREFIX = "import Nc.CaseI.Multi\nnamespace Paper\nopen Finset MvPolynomial Nc Nc.CaseI\n"
QUERIES = [
    "#check @lem_balanced",
    "#check @lem_balanced_cf",
    "#print axioms lem_balanced",
    "#print axioms lem_balanced_cf",
]


def run(lean, mathlib, work):
    receipt, code = run_replay(lean, mathlib, work, target_module="Nc.CaseI.Multi",
                               query_file=REVIEW / "checks/pass13a_gate.lean")
    if code:
        raise RuntimeError("The publisher induction did not build")
    flat = SOURCE / "Paper/Flat.lean"
    original = flat.read_text()
    start = original.index("/-- A polynomial that is linear in each block of S")
    end = original.index("/-! ### The tensor of f_{k,ℓ}", start)
    excerpt = original[start:end]
    script = PREFIX + excerpt + "\n".join(QUERIES) + "\nend Paper\n"
    file = work / "FullBalancedDeclaration.lean"
    file.write_text(script)
    manifest = json.loads((SOURCE / "lake-manifest.json").read_bytes())["packages"]
    packages = [mathlib if p["name"] == "mathlib" else mathlib / ".lake/packages" / p["name"]
                for p in manifest]
    libraries = [p / ".lake/build/lib/lean" for p in packages]
    path = os.pathsep.join(map(str, [work / "objects", *libraries]))
    extra = subprocess.run([lean, *receipt["lean_options"], str(file)], cwd=SOURCE,
                           env=dict(os.environ, LEAN_PATH=path), capture_output=True, text=True)
    if extra.returncode:
        raise RuntimeError(extra.stdout + extra.stderr)
    receipt["E4_excerpt"] = {
        "scope": "Unmodified contiguous source excerpt under its own namespace, using freshly built Nc.CaseI.Multi. Other Paper.Flat declarations and downstream E.7 were not built by this test.",
        "source": "Paper/Flat.lean",
        "line_start": 1 + original[:start].count("\n"),
        "line_end": original[:end].count("\n"),
        "source_sha256": hashlib.sha256(flat.read_bytes()).hexdigest(),
        "excerpt_sha256": hashlib.sha256(excerpt.encode()).hexdigest(),
        "harness_sha256": hashlib.sha256(script.encode()).hexdigest(),
        "queries": QUERIES,
        "exit_code": extra.returncode,
        "output": (extra.stdout + extra.stderr).strip(),
    }
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", default="lean")
    parser.add_argument("--mathlib", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="pass13a-induction-") as tmp:
        receipt = run(args.lean, args.mathlib.resolve(), Path(tmp))
    args.output.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
