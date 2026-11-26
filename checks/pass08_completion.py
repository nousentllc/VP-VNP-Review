"""Replay the two C.3 completion lemmas from pinned source, using Lean on PATH.

From a built, pinned vp-vnp project:
    lake env python3 /path/to/VP_VNP_Review/checks/pass08_completion.py

The test reads the reviewed sources, compiles in a temporary directory, and
prints the axioms used. It does not build the publisher's whole module.

Use --offline to verify the archived evidence with Python alone.
"""

import hashlib
from pathlib import Path
import subprocess
import tempfile


SOURCE = Path(__file__).resolve().parents[1] / "primary" / "vp-vnp"
IMPORTS = """import Mathlib.Topology.MetricSpace.Completion
import Mathlib.Topology.Instances.Real.Lemmas
import Mathlib.Topology.Sequences
import Mathlib.Tactic.Linarith
import Mathlib.Tactic.Positivity
import Mathlib.Tactic.FunProp"""


def excerpt(text, start_marker, end_marker):
    start = text.index(start_marker)
    return text[start:text.index(end_marker, start)]


def replay():
    core = (SOURCE / "Nc/Cat/Core.lean").read_text()
    curvature = (SOURCE / "Paper/Curvature.lean").read_text()
    license_header = excerpt(core, "/-", "import Mathlib")
    cn = excerpt(core, "class CN (", "\nvariable {X : Type*}")
    lemmas = excerpt(curvature, "theorem prop_space_cauchy ", '/-- "Its metric is a price as a limit"')
    harness = (
        f"{license_header}{IMPORTS}\n\nopen Filter Topology\nnamespace Cat\n{cn}\nend Cat\n"
        f"namespace Paper\nopen Cat\n{lemmas}\n"
        "#print axioms prop_space_cauchy\n#print axioms prop_space_completion\nend Paper\n"
    )
    print("Extracted CN declaration SHA-256:", hashlib.sha256(cn.encode()).hexdigest(), flush=True)
    print("Extracted completion lemmas SHA-256:", hashlib.sha256(lemmas.encode()).hexdigest(), flush=True)
    with tempfile.TemporaryDirectory(prefix="vp-vnp-pass08-") as directory:
        source_file = Path(directory) / "CompletionReplay.lean"
        source_file.write_text(harness)
        subprocess.run(["lean", "-j1", str(source_file)], check=True)


if __name__ == "__main__":
    from offline_replays import run_entrypoint

    run_entrypoint(__file__, replay)
