"""Verify the Alternative replay and its source pins from the offline handoff packet."""

import hashlib
import json
import re
from pathlib import Path

from pass09_endpoint_replay import REVIEW, SOURCE, dependency_order


def git_object(kind, payload):
    header = f"{kind} {len(payload)}".encode() + b"\0"
    return hashlib.sha1(header + payload).digest()


def publisher_tree(directory):
    """Recompute the Git tree ID, including entry modes and recursive tree order."""
    entries = []
    files = 0
    for child in directory.iterdir():
        name = child.name.encode()
        if child.is_symlink():
            raise ValueError(f"Unexpected symlink in this publisher snapshot: {child}")
        if child.is_dir():
            digest, descendants = publisher_tree(child)
            key, mode = name + b"/", b"40000"
            files += descendants
        else:
            digest = git_object("blob", child.read_bytes())
            key = name
            mode = b"100755" if child.stat().st_mode & 0o111 else b"100644"
            files += 1
        entries.append((key, mode + b" " + name + b"\0" + digest))
    payload = b"".join(entry for _, entry in sorted(entries))
    return git_object("tree", payload), files


def main():
    lock = json.loads((REVIEW / "source-lock.json").read_bytes())
    result = json.loads((REVIEW / "checks/pass12e_alternative_replay.json").read_bytes())
    pin, files = publisher_tree(SOURCE)
    assert pin.hex() == lock["git_tree"] and files == lock["blob_count"]
    assert result["publisher_commit"] == lock["commit"]
    assert result["lean_toolchain"] == (SOURCE / "lean-toolchain").read_text().strip()
    dependencies = json.loads((SOURCE / "lake-manifest.json").read_bytes())["packages"]
    assert result["external_checkout_revisions"] == {p["name"]: p["rev"] for p in dependencies}
    target = "Paper.Alternative"
    assert result["target"] == target
    order = dependency_order(target)
    assert set(("Paper.Fan", "Paper.Curvature", "Paper.Alternative")) <= set(order)
    assert result["modules_requested"] == len(order) == 54
    assert [r["module"] for r in result["modules"]] == order
    for row in result["modules"]:
        expected_path = Path(*row["module"].split(".")).with_suffix(".lean")
        assert row["source"] == expected_path.as_posix()
        assert row["exit_code"] == 0
        assert hashlib.sha256((SOURCE / expected_path).read_bytes()).hexdigest() == row["sha256"]
    verification = result["verification"]
    query = REVIEW / "checks/pass12e_alternative.lean"
    assert verification["query_file"] == query.relative_to(REVIEW).as_posix()
    assert verification["sha256"] == hashlib.sha256(query.read_bytes()).hexdigest()
    commands = [line for line in query.read_text().splitlines() if line.startswith("#")]
    assert verification["queries"] == commands and verification["exit_code"] == 0
    reports = dict(re.findall(r"'([\w.]+)' depends on axioms: \[([^]]+)\]", verification["output"]))
    names = {line.removeprefix("#print axioms ") for line in commands if line.startswith("#print axioms ")}
    assert reports.keys() == names
    assert all(set(items.split(", ")) == {"propext", "Classical.choice", "Quot.sound"} for items in reports.values())
    report = {
        "publisher_tree_id": pin.hex(),
        "tree_files": files,
        "matched_module_hashes": len(order),
        "pinned_dependency_revisions": len(dependencies),
        "successful_readback_commands": len(commands),
        "axiom_sets_checked": len(reports),
    }
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
