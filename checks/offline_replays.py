"""Verify recorded evidence offline, or dispatch to an entry point's fresh Lean run."""

import argparse
import json
import sys
from pathlib import Path

from pass14_reader_check import (REVIEW, SOURCE, bridge, digest_bytes, hashed, hosted,
                                 local_build, need, originals, receipt, scalar)


def read_index():
    return receipt("offline-evidence.json")


def verify_bytes(index, paths):
    for name in paths:
        expected = index["sha256"][name]
        active = REVIEW / name
        if name == "checks/pass14_comparator.json":
            old = REVIEW / "reconciliation/edition11-comparator-receipt.json"
            need(hashed(old) == expected, "preserved comparator receipt digest differs")
            if hashed(active) != expected:
                record = json.loads(active.read_bytes())
                need("evidence_lines_provenance" in record, "expected additive provenance field")
                del record["evidence_lines_provenance"]
                need(json.dumps(record, sort_keys=True) == json.dumps(json.loads(old.read_bytes()), sort_keys=True),
                     "original comparator receipt fields changed")
        else:
            need(hashed(active) == expected, f"Edition 11 evidence differs: {name}")


def verify_sources():
    lock = json.loads((REVIEW / "source-lock.json").read_bytes())
    originals(lock)
    return lock


def release_config():
    packages = json.loads((SOURCE / "lake-manifest.json").read_bytes())["packages"]
    revisions = {p["name"]: p["rev"] for p in packages}
    version = "version " + (SOURCE / "lean-toolchain").read_text().strip().split(":v")[-1] + ","
    config = json.loads((SOURCE / "comparator.json").read_bytes())
    return revisions, version, config


def check_completion_excerpt():
    from pass08_completion import excerpt

    source = (SOURCE / "Paper/Curvature.lean").read_text()
    lemmas = excerpt(source, "theorem prop_space_cauchy ", '/-- "Its metric is a price as a limit"')
    note = (REVIEW / "passes/08-price-space-completion.md").read_text()
    need(digest_bytes(lemmas.encode()) in note, "completion excerpt differs from its written record")
    print("Pass 8 retained a written account of the two Lean checks and an excerpt hash.")


def selected(stem, target=None):
    lock = verify_sources()
    index = read_index()
    if target == "Paper.NoAcc":
        from pass15_reader_check import check_target

        check_target(lock)
        return
    paths = index["generic_targets"][target] if target else index["entrypoints"][stem]
    verify_bytes(index, paths)
    print("Matched " + ", ".join(paths) + " to the preserved Edition 11 snapshot.")
    if stem == "pass08_completion":
        check_completion_excerpt()
    if stem == "pass14_release":
        local_build(*release_config())
    elif stem == "pass14a_margin_replay":
        revisions, version, config = release_config()
        scalar(receipt("pass14a_margin_results.json"), revisions, version, config)
        bridge(revisions, version, config)


def archived_suite():
    from pass12e_verify_pin import main as verify_alternative
    from pass14_reader_check import coverage, evidence_index
    from pass15_reader_check import check_report, check_target

    index = read_index()
    lock = verify_sources()
    verify_bytes(index, index["sha256"])
    print(f"Matched {len(index['sha256'])} historical proof sources, receipts and records.")
    evidence_index(lock)
    coverage()
    check_completion_excerpt()
    verify_alternative()
    revisions, version, config = release_config()
    scalar(receipt("pass14a_margin_results.json"), revisions, version, config)
    local_build(revisions, version, config)
    bridge(revisions, version, config)
    hosted(config, lock)
    check_target(lock)
    check_report()


def run_entrypoint(filename, fresh):
    stem = Path(filename).stem
    if "--offline" not in sys.argv[1:]:
        if stem in {"pass08_completion", "pass12c_replay"}:
            # The original tools take no parameters; expose their help without launching Lean.
            parser = argparse.ArgumentParser(description=sys.modules["__main__"].__doc__)
            parser.add_argument("--offline", action="store_true", help="Verify previously recorded evidence")
            parser.parse_args()
        return fresh()
    parser = argparse.ArgumentParser(description="Check recorded evidence with Python alone.")
    parser.add_argument("--offline", required=True, action="store_true")
    if stem == "pass09_endpoint_replay":
        parser.add_argument("--target-module", choices=sorted([*read_index()["generic_targets"], "Paper.NoAcc"]))
    args = parser.parse_args()
    selected(stem, getattr(args, "target_module", None))
    print("Offline receipt check passed. No Lean process was run.")
