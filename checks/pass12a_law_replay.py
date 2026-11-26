"""Replay unchanged law-power and code-gluing proof bodies with Mathlib alone.

Run in a Lean 4.33.1 environment with the publisher's built mathlib available on
LEAN_PATH. Pass --lean to choose the executable and --output to save the receipt.

Use --offline to verify the archived evidence with Python alone.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "primary" / "vp-vnp"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lean", default="lean")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    lock = json.loads((ROOT / "source-lock.json").read_text())
    version = subprocess.check_output([args.lean, "--version"], text=True).strip()
    if "version 4.33.1," not in version:
        parser.error(f"unexpected Lean version {version}")

    declarations = (SOURCE / "Nc/G/Defs.lean").read_bytes()
    contract = (SOURCE / "Nc/G/Contract.lean").read_bytes()
    law_start = declarations.index(b"set_option linter.unusedSectionVars false")
    law_end = declarations.index(b"namespace Law\n")
    law = declarations[law_start:law_end]
    proofs = contract[contract.index(b"set_option linter.unusedSectionVars false"):]
    queries = ["Nc.G.contract", "Nc.G.Law.pow", "Nc.G.Law.conn_pow"]
    lines = [f"#print axioms {decl}" for decl in queries]
    harness = (contract[:contract.index(b"import Nc.G.Defs")] + b"import Mathlib\n\n"
               + law + b"end Nc.G\n\n" + proofs + ("\n"+"\n".join(lines)+"\n").encode())
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "LawContraction.lean"
        path.write_bytes(harness)
        result = subprocess.run([args.lean, "-j1", "-DautoImplicit=false", str(path)],
                                capture_output=True, text=True)
    report = {
        "publisher_commit": lock["commit"], "lean_version": version,
        "scope": "Publisher law structure/instances and unchanged declaration bodies from Nc.G.Contract. Isolated Mathlib import. No full Nc.G.Defs or Nc.G.Contract project-module rebuild.",
        "sources_sha256": {"Nc/G/Defs.lean": digest(declarations), "Nc/G/Contract.lean": digest(contract)},
        "excerpts_sha256": {"Law_and_instances": digest(law), "Contract_declarations": digest(proofs)},
        "harness_sha256": digest(harness), "queries": lines, "exit_code": result.returncode,
        "output": (result.stdout + result.stderr).replace(str(path), "<harness>").strip(),
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
    print(report["output"])
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    from offline_replays import run_entrypoint

    run_entrypoint(__file__, main)
