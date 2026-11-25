"""Run in the pinned mathlib environment with Lean on PATH. Print the replay receipt as JSON."""

import hashlib
import json
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "primary" / "vp-vnp"
EXCERPTS = (
    ("Nc/Price/BorderFew.lean", "le_of_pow_le_poly", "/-- The N-th power"),
    ("Paper/Rate.lean", "rate_numbers14", "/-- What Lemma"),
    ("Paper/Rate.lean", "rate_pow", "/-- A finite numbering"),
    ("Paper/Rate.lean", "exists_cube_root", "/-- The proof of Theorem"),
    ("Paper/Rate.lean", "rate_of_projection", "/-- **Paper: Theorem thm:flat-rate."),
)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def replay():
    version = subprocess.check_output(["lean", "--version"], text=True).strip()
    pin = (SOURCE / "lean-toolchain").read_text().strip()
    if f"version {pin.split(':v')[-1]}," not in version:
        raise RuntimeError(f"Expected {pin} and found {version}")
    headers = (SOURCE / "Paper/Rate.lean").read_text().split("import Paper.Scales")[0]
    cube_file = ROOT / "checks/pass12c_budget.lean"
    chunks = [headers, cube_file.read_text(), "\nnamespace ExcerptReplay\n"]
    spans = []
    for filename, theorem, stop in EXCERPTS:
        p = SOURCE / filename
        full = p.read_text()
        start = full.index(f"theorem {theorem} ")
        end = full.index(stop, start)
        excerpt = full[start:end]
        spans.append({"source": filename, "line": 1 + full[:start].count("\n"),
                      "declaration": theorem, "source_sha256": digest(p.read_bytes()),
                      "excerpt_sha256": digest(excerpt.encode())})
        chunks.extend([excerpt, f"#print axioms {theorem}\n"])
    chunks.append("end ExcerptReplay\n")
    with tempfile.TemporaryDirectory() as tmp:
        filename = Path(tmp) / "Pass12c.lean"
        code = "".join(chunks)
        filename.write_text(code)
        run = subprocess.run(["lean", "-j1", "-DautoImplicit=false", str(filename)],
                             text=True, capture_output=True)
        if run.returncode:
            raise RuntimeError(run.stdout + run.stderr)
    return {
        "publisher_commit": json.loads((ROOT / "source-lock.json").read_text())["commit"],
        "scope": "Independent induction and five verbatim arithmetic excerpts in isolation, imported with Mathlib. Neither Paper.Convex nor Paper.Rate was rebuilt.",
        "lean_version": version, "lean_options": ["-j1", "-DautoImplicit=false"],
        "independent_source": "checks/pass12c_budget.lean",
        "independent_source_sha256": digest(cube_file.read_bytes()),
        "harness_sha256": digest(code.encode()), "excerpts": spans, "exit_code": run.returncode,
        "output": (run.stdout + run.stderr).strip(),
    }


if __name__ == "__main__":
    print(json.dumps(replay(), ensure_ascii=False, indent=2))
