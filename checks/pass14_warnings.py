"""Audit a fresh build log of the pinned publisher release. Run as python3 checks/pass14_warnings.py LOGFILE."""

import argparse
import json
from pathlib import Path
import re

from pass09_endpoint_replay import SOURCE


# Lean's terminal renderer and Lake may style or quote the same diagnostic differently.
ANSI_COLOR = re.compile(r"\x1b\[[0-9;:]*m")
USES_SORRY = re.compile(r"\bdeclaration\s+uses\s+[`'\"‘’“”]*sorry\b", re.IGNORECASE)
CHALLENGE_PATH = re.compile(r"(?:^|\s)(?:(?:\./)*|[^\s:]+/vp-vnp/)Challenge\.lean:(\d+):\d+(?:[:\s]|$)")


def sorry_lines(log):
    return [line for line in log.splitlines() if USES_SORRY.search(ANSI_COLOR.sub("", line))]


def challenge_location(line):
    found = CHALLENGE_PATH.search(ANSI_COLOR.sub("", line))
    return int(found[1]) if found else None


def check_warning_audit(audit):
    """Require one warning at each of the five original challenge declaration sites."""
    lines = audit["challenge_lines"]
    outside = audit["outside_challenge_lines"]
    if not isinstance(lines, list) or not isinstance(outside, list):
        raise ValueError("Expected lists of raw warning lines")
    if outside:
        raise ValueError("Unexpected sorry outside the challenge:\n" + "\n".join(outside))
    expected = [index for index, line in enumerate((SOURCE / "Challenge.lean").read_text().splitlines(), 1)
                if line.startswith("theorem ")]
    if len(expected) != 5:
        raise ValueError("Expected five pinned challenge declarations")
    sites = []
    for line in lines:
        location = challenge_location(line)
        if location is None or sorry_lines(line) != [line]:
            raise ValueError("Unrecognized challenge diagnostic: " + line)
        sites.append(location)
    if sorted(sites) != expected:
        raise ValueError(f"Expected challenge warning lines {expected}, found {sorted(sites)}")
    return audit


def audit_modules(rows):
    audit = {"challenge_lines": [], "outside_challenge_lines": []}
    for row in rows:
        for line in sorry_lines(row.get("output", "")):
            key = "challenge_lines" if row["module"] == "Challenge" and challenge_location(line) else "outside_challenge_lines"
            audit[key].append(line)
    return check_warning_audit(audit)


def audit_log(log):
    audit = {"challenge_lines": [], "outside_challenge_lines": []}
    for line in sorry_lines(log):
        key = "challenge_lines" if challenge_location(line) else "outside_challenge_lines"
        audit[key].append(line)
    return check_warning_audit(audit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit_log(args.log.read_text(errors="replace")), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
