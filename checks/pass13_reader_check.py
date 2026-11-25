"""Check Edition 10 evidence offline. Run from a checkout or extracted review packet."""
import csv
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

from pass09_endpoint_replay import REVIEW, SOURCE, dependency_order
from pass12e_verify_pin import publisher_tree
from pass13a_gate_replay import PREFIX, QUERIES


def read_json(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_receipt(path, targets, revisions):
    record = read_json(path)
    expected = set().union(*(dependency_order(name) for name in targets))
    rows = record["modules"]
    require({row["module"] for row in rows} == expected and len(rows) == len(expected),
            f"Incomplete dependency closure in {path.name}")
    require(record["external_checkout_revisions"] == revisions, path.name + ": dependency mismatch")
    for row in rows:
        src = Path(*row["module"].split(".")).with_suffix(".lean")
        require(row["exit_code"] == 0 and row["source"] == src.as_posix()
                and row["sha256"] == digest(SOURCE / src), f"Source mismatch: {src}")
    report = record["verification"]
    query = REVIEW / report["query_file"]
    commands = [line for line in query.read_text().splitlines() if line.startswith("#")]
    require(digest(query) == report["sha256"] and commands == report["queries"] and report["exit_code"] == 0,
            path.name + ": query mismatch")
    required = {cmd.split()[-1] for cmd in commands if cmd.startswith("#print axioms ")}
    found = dict(re.findall(r"'([\w.]+)' depends on axioms: \[([^\]]+)\]", report["output"]))
    require(found.keys() == required, path.name + ": missing axiom readback")
    for name, axioms in found.items():
        require(set(axioms.split(", ")) <= {"Classical.choice", "Quot.sound", "propext"}, name + ": unexpected axioms")
    print(f"{path.name}: {len(rows)} publisher modules, {len(commands)} queries", flush=True)


def verify_additional_proofs(checks, revisions):
    scalar = read_json(checks / "pass13b_budget_results.json")
    require(scalar["sha256"] == digest(REVIEW / scalar["file"])
            and scalar["external_checkout_revisions"] == revisions and scalar["exit_code"] == 0,
            "Independent budget proof mismatch")
    excerpt = read_json(checks / "pass13a_gate_replay.json")["E4_excerpt"]
    source = SOURCE / excerpt["source"]
    original = source.read_text()
    start = original.index("/-- A polynomial that is linear in each block of S")
    end = original.index("/-! ### The tensor of f_{k,ℓ}", start)
    block = original[start:end]
    harness = PREFIX + block + "\n".join(QUERIES) + "\nend Paper\n"
    require(excerpt["source_sha256"] == digest(source)
            and excerpt["excerpt_sha256"] == hashlib.sha256(block.encode()).hexdigest()
            and excerpt["harness_sha256"] == hashlib.sha256(harness.encode()).hexdigest()
            and excerpt["exit_code"] == 0 and excerpt["queries"] == QUERIES, "E.4 excerpt mismatch")
    print("Checked the independent budget proof and E.4 excerpt against their archived receipts.", flush=True)


def verify_anchors():
    with (REVIEW / "report/proof-coverage.csv").open(newline="") as f:
        rows = list(csv.DictReader(f))
    require(len(rows) == len({r["claim_id"] for r in rows}), "Duplicate claim ID")
    for row in rows:
        require(all(row.values()), "Incomplete ledger row: " + row["claim_id"])
        for key in ["source_anchor", "review_anchor"]:
            file, fragment = row[key].split("#", 1)
            match = re.fullmatch(r"L(\d+)(?:-L(\d+))?", fragment)
            require(match and 0 < int(match[1]) <= int(match[2] or match[1]) <=
                    len((REVIEW / file).read_text().splitlines()), row[key])
    return len(rows)


def main():
    pin = read_json(REVIEW / "source-lock.json")
    tree, files = publisher_tree(SOURCE)
    require((tree.hex(), files) == (pin["git_tree"], pin["blob_count"]), "Publisher tree mismatch")
    require(digest(SOURCE / "paper.pdf") == pin["paper_sha256"], "Manuscript checksum mismatch")
    print(f"Publisher tree verified: {files} files. Coverage anchors verified: {verify_anchors()} rows.", flush=True)
    revisions = {p["name"]: p["rev"] for p in read_json(SOURCE / "lake-manifest.json")["packages"]}
    checks = REVIEW / "checks"
    for path, targets in [
        ("pass13a_gate_replay.json", ["Nc.CaseI.Multi"]),
        ("pass13c_permanent_replay.json", ["Paper.Grids"]),
        ("pass13d_membership_replay.json", ["Nc.Hc.Vnp"]),
        ("pass13_joint_replay.json", ["Paper.Flat", "Paper.Laws"]),
    ]:
        verify_receipt(checks / path, targets, revisions)
    verify_additional_proofs(checks, revisions)
    for name in ["pass13a_gate_reuse.py", "pass13b_gain.py", "pass13c_permanent.py", "pass13d_witness.py"]:
        subprocess.run([sys.executable, str(checks / name)], cwd=REVIEW, check=True, stdout=subprocess.DEVNULL)
        print("Reran " + name, flush=True)
    print("The source and receipts match. The four finite controls passed. This command does not invoke Lean.")


if __name__ == "__main__":
    main()
