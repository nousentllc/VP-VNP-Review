"""Check the pinned inputs and verify a fresh Linux Comparator result."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "checks"))
from pass14_reader_check import originals  # noqa: E402
from tier1 import PROJECT, verify_packages  # noqa: E402


def read(path):
    return json.loads(path.read_bytes())


def verify_inputs():
    lock = read(ROOT / "source-lock.json")
    originals(lock)
    verify_packages(PROJECT / ".lake/packages")
    version = subprocess.check_output(["lean", "--version"], cwd=PROJECT, text=True)
    pin = (PROJECT / "lean-toolchain").read_text().strip()
    if f"version {pin.split(':v')[-1]}," not in version:
        raise ValueError(f"Expected {pin}, got {version.strip()}")
    return lock, pin


def verify_result(directory):
    lock, pin = verify_inputs()
    recorded = read(ROOT / "checks/pass14_comparator.json")
    build = (directory / "build.log").read_text()
    log = (directory / "comparator/comparator.log").read_text()
    driver_lines = (directory / "driver.log").read_text().splitlines()
    config = read(directory / "comparator/comparator.json")
    expected_config = dict(read(PROJECT / "comparator.json"), enable_nanoda=True)
    if config != expected_config or len(config["theorem_names"]) != 5:
        raise ValueError("Comparator configuration differs from the publisher configuration with nanoda enabled")
    if not re.search(r"^Build completed successfully \(\d+ jobs\)\.$", build, re.MULTILINE):
        raise ValueError("Missing full Lake build acceptance")
    tool_names = {"comparator": "comparator", "lean4export": "lean4export", "nanoda_lib": "nanoda_lib", "landrun": "landrun"}
    tools = recorded["tool_revisions"]
    markers = ["nanoda kernel accepts the solution", "Lean default kernel accepts the solution", "Your solution is okay!"]
    for name, revision in tools.items():
        if f"== {tool_names[name]} @ {revision}" not in driver_lines:
            raise ValueError(f"Missing pinned driver tool marker: {name}")
    if not all(marker in log.splitlines() for marker in markers):
        raise ValueError("Missing Lean or nanoda acceptance marker")
    if "All 1 comparator configuration(s) accepted." not in driver_lines:
        raise ValueError("The publisher driver did not accept the configuration")
    evidence = dict(publisher_commit=lock["commit"], publisher_tree=lock["git_tree"], checker_blob=recorded["checker_blob"],
                    toolchain=pin, tool_revisions=tools, config=config, acceptance=markers)
    payload = (json.dumps(evidence, sort_keys=True, separators=(",", ":")) + "\n").encode()
    digest = hashlib.sha256(payload).hexdigest()
    (directory / "tier2-evidence.json").write_bytes(payload)
    expected = read(ROOT / "reproduce/expected.json")["tier2"]["sha256"]
    if digest != expected:
        raise ValueError(f"Tier 2 digest mismatch: {digest}")
    print(f"Tier 2 passed. Evidence SHA-256 {digest}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--inputs-only", action="store_true")
    mode.add_argument("--results", type=Path)
    args = parser.parse_args()
    if args.inputs_only:
        verify_inputs()
    else:
        verify_result(args.results)


if __name__ == "__main__":
    main()
