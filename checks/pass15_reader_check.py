"""Check Edition 12's archived evidence and rerun the three finite diagnostics offline."""
import csv
import json
import re
import subprocess
import sys

from pass09_endpoint_replay import REVIEW, SOURCE, dependency_order
from pass13_reader_check import verify_receipt
from pass14_reader_check import hashed, main as verify_edition11, need, read_axioms

CHECKS = REVIEW / "checks"
EDITION11 = "a6868a523e92ddf262de29af8bcba07580f6c0bb"
PUBLISHER_NAMES = {
    "Paper.lem_postpone", "Paper.prop_next_round", "Paper.prop_next", "Paper.thm_noacc_finite_field",
    "Paper.thm_noacc_periodic", "Paper.thm_noacc_all_scales", "Paper.thm_noacc_diagonal", "Paper.thm_noacc",
}
REVIEW_NAMES = {"Review.Pass15." + name for name in (
    "bill_lt_cost", "postpone_endpoint", "postponed_accelerator_sum", "fast_named_input", "requestEmpty_ev",
)}


def check_target(lock):
    entry = lock["local_replay"]["pass15"]
    need(entry["review_baseline"] == EDITION11 and entry["target"] == "Paper.NoAcc", "unexpected baseline or target")
    record = json.loads((REVIEW / entry["record"]).read_bytes())
    revisions = {p["name"]: p["rev"] for p in json.loads((SOURCE / "lake-manifest.json").read_bytes())["packages"]}
    verify_receipt(REVIEW / entry["record"], [entry["target"]], revisions)
    need(record["publisher_commit"] == lock["commit"] and record["lean_toolchain"] == lock["lean_toolchain"]
         and "version 4.33.1," in record["lean_version"], "targeted build pin mismatch")
    modules = record["modules"]
    need([r["module"] for r in modules] == dependency_order(entry["target"]) and len(modules) == 16
         and not any(r.get("output", "").strip() for r in modules), "source order or compiler diagnostics differ")
    verify = record["verification"]
    need(verify["query_file"] == entry["review_proofs"], "unexpected review proof file")
    names = PUBLISHER_NAMES | REVIEW_NAMES
    read_axioms(verify["output"], names, json.loads((SOURCE / "comparator.json").read_bytes())["permitted_axioms"])
    types = re.findall(r"^@?((?:Paper|Review\.Pass15)\.\w+)(?=\.\{|\s*[:(])", verify["output"], re.MULTILINE)
    need(set(types) == names and len(types) == len(names), "type readbacks missing or duplicated")
    need("warning:" not in verify["output"] and "error:" not in verify["output"], "query diagnostics present")
    print("Verified 16 freshly compiled publisher modules and the type and axiom records for 13 declarations.")


def check_controls(lock):
    paths = [REVIEW / name for name in lock["local_replay"]["pass15"]["finite_controls"]]
    need([p.name for p in paths] == [f"pass15_k{i}.json" for i in range(4, 7)], "wrong finite controls")
    for path in paths:
        actual = subprocess.check_output([sys.executable, "-E", str(path.with_suffix(".py"))], cwd=REVIEW)
        need(actual == path.read_bytes(), "finite check differs: " + path.name)
        print("Reproduced", path.name)
    with (REVIEW / "report/proof-coverage.csv").open(newline="") as file:
        rows = {r["claim_id"]: r for r in csv.DictReader(file)}
    for name in ("K.4", "K.5", "K.6", "K.4 filter", "K.5 cut costs", "K.6 scale choice",
                 "K.6 plainness before value", "K.4 review endpoint"):
        need(rows[name]["review_anchor"].startswith("passes/15-diagonal.md#L"), "missing Pass 15 row: " + name)


def check_report():
    report = REVIEW / "report"
    receipt = json.loads((report / "edition12-build.json").read_bytes())
    need(receipt["edition"] == 12 and receipt["baseline"] == EDITION11, "wrong PDF edition")
    inputs = {str(p.relative_to(REVIEW)): hashed(p) for p in [*report.glob("*.tex"), report / "nous-black.png"]}
    need(receipt["inputs_sha256"] == inputs, "TeX sources or logo changed")
    need(hashed(REVIEW / receipt["pdf"]) == receipt["pdf_sha256"], "release PDF differs from build receipt")
    need(inputs["report/nous-black.png"] == "bdfff8716596a351b480896d4bc21a7786470d6283c050b4ee801e3a88d061b6",
         "original Nous logo differs")
    print(f"Verified the {receipt['pages']}-page PDF and its complete TeX/PNG source set.")


def main():
    verify_edition11()
    lock = json.loads((REVIEW / "source-lock.json").read_bytes())
    check_target(lock)
    check_controls(lock)
    check_report()
    print("Edition 12 packet checks passed. The recorded formal runs can be repeated with the commands in README.md.")


if __name__ == "__main__":
    main()
