"""Validate Edition 11 evidence offline with Python 3.9+ (no Git, Lean or network required)."""

import csv
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from pass09_endpoint_replay import REVIEW, SOURCE, dependency_order, source_file
from pass12e_verify_pin import git_object, publisher_tree
from pass13_reader_check import verify_anchors
from pass14_warnings import audit_log, audit_modules


CHECKS = REVIEW / "checks"
PUBLISHER = "11b6c7e3c927df2658f513b6b68ea7f8929c62c5"
TREE = "b076b4b081298c4e909bac3f87f0e4462d1fb2cb"
CHECKER = "0143ba15873eac3d3056ceee0f19471b82987a98"
AXIOM_QUERY = re.compile(r"^'([\w.]+)' depends on axioms:\s*\[([^\]]*)\]", re.MULTILINE)
TYPE_QUERY = re.compile(r"^@?((?:Paper|Solution|Review\.Pass14A)\.[\w.]+?)(?=\.\{|\s*[:(])", re.MULTILINE)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def receipt(filename):
    path = CHECKS / filename
    need(path.is_file(), f"missing receipt {path.relative_to(REVIEW)}")
    return json.loads(path.read_bytes())


def digest_bytes(content):
    return hashlib.sha256(content).hexdigest()


def hashed(path):
    return digest_bytes(path.read_bytes())


def read_axioms(transcript, names, permitted):
    rows = AXIOM_QUERY.findall(transcript)
    sets = {name: sorted(item.strip() for item in words.split(",") if item.strip())
            for name, words in rows}
    need(len(rows) == len(names) and set(sets) == set(names), "missing or duplicate axiom readback")
    need(all(set(found) <= set(permitted) for found in sets.values()), "unexpected axiom in readback")
    return sets


def originals(lock):
    tree, size = publisher_tree(SOURCE)
    need(tree.hex() == lock["git_tree"] == TREE and lock["commit"] == PUBLISHER
         and size == lock["blob_count"] == 333, "publisher tree differs from the pinned release")
    checker = SOURCE.parent / ".github/scripts/comparator-check.sh"
    need(git_object("blob", checker.read_bytes()).hex() == CHECKER, "publisher Comparator driver differs")
    need(hashed(SOURCE / "paper.pdf") == lock["paper_sha256"], "manuscript differs")
    print(f"Verified publisher tree, {size} files, and the separate checker blob.")


def evidence_index(lock):
    replay = lock["local_replay"]
    need(replay["entire_separation_replayed"] is True and replay["comparator_replayed"] is True,
         "source lock does not describe a finished independent replay")
    edition = replay["pass14"]
    need(edition["review_baseline"] == "3754047be3854ef313df17ae5117c6ca5a66b4b8",
         "Edition 10 baseline differs")
    need(edition["full_local_build"]["record"] == "checks/pass14_release.json"
         and edition["review_owned_linux_comparator"]["record"] == "checks/pass14_comparator.json"
         and edition["flat_circuit_strict_bound"]["scalar"] == "checks/pass14a_margin_results.json"
         and edition["flat_circuit_strict_bound"]["circuit"] == "checks/pass14a_circuit_results.json",
         "source lock points to different proof receipts")


def coverage():
    count = verify_anchors()
    with (REVIEW / "report/proof-coverage.csv").open(newline="") as file:
        ledger = {row["claim_id"]: row for row in csv.DictReader(file)}
    ids = ("E.7", "E.8", "E.9", "E.10", "H.1", "H.2 value", "H.2 loads", "K.2", "K.3",
           "Global build", "Comparator")
    for name in ids:
        need(name in ledger, "missing coverage row for " + name)
        row = ledger[name]
        review_text = " ".join(row[field] for field in ("review_anchor", "independent_evidence_scope", "review_finding"))
        updated = re.search(r"passes/14|pass[ /-]?14|\b14[A-E]\b|edition 11", review_text, re.IGNORECASE)
        need(updated, "earlier coverage row for " + name)
    print(f"Verified {count} distinct claim IDs, populated fields and local line anchors.")


def finite():
    previous = receipt("pass14_prior_controls.json")["results"]
    need(len(previous) == len({row["script"] for row in previous}) == 18, "incomplete previous controls receipt")
    for row in previous:
        path = Path(row["script"])
        need(path.parent == Path("checks") and path.suffix == ".py" and row["exit_code"] == 0
             and hashed(REVIEW / path) == row["script_sha256"]
             and re.fullmatch(r"[a-f0-9]{64}", row["stdout_sha256"]), "prior control receipt differs: " + str(path))
    print("Verified the source hashes and recorded outcomes of 18 earlier controls.")
    for stem in ("pass14a_flat", "pass14b_tower", "pass14c_compiler"):
        path = CHECKS / (stem + "_results.json")
        actual = subprocess.check_output([sys.executable, str(CHECKS / (stem + ".py"))], cwd=REVIEW)
        need(actual == path.read_bytes(), f"{stem}: rerun differs from published JSON")
        print(f"Reproduced {stem} byte for byte.")


def scalar(record, revisions, version, config):
    src = CHECKS / "pass14a_margin.lean"
    need(record["file"] == src.relative_to(REVIEW).as_posix() and record["sha256"] == hashed(src)
         and record["exit_code"] == 0 and record["external_checkout_revisions"] == revisions
         and version in record["lean_version"] and record["options"] == ["-j1", "-DautoImplicit=false"],
         "scalar proof receipt differs from source, pinned tools or build options")
    read_axioms(record["output"], {"Review.Pass14A.margin12"}, config["permitted_axioms"])


def bridge(revisions, version, config):
    record = receipt("pass14a_circuit_results.json")
    scalar(record, revisions, version, config)
    src, proof = CHECKS / "pass14a_margin.lean", CHECKS / "pass14a_circuit.lean"
    bodies = ["\n".join(line for line in p.read_text().splitlines() if not line.startswith("import "))
              for p in (src, proof)]
    harness = "import Paper.Rate\n" + "\n".join(bodies) + "\n"
    entry = record["bridge"]
    need(entry["file"] == proof.relative_to(REVIEW).as_posix() and entry["sha256"] == hashed(proof)
         and entry["harness_sha256"] == digest_bytes(harness.encode())
         and entry["rate_source_sha256"] == hashed(SOURCE / "Paper/Rate.lean")
         and re.fullmatch(r"[a-f0-9]{64}", entry["rate_olean_sha256"]) and entry["exit_code"] == 0,
         "circuit proof, harness, publisher source, object digest or exit code differs")
    obj = entry["rate_olean_sha256"]
    full = receipt("pass14_release.json")
    need(obj == full["rate_olean_sha256"], "the circuit proof used a different Paper.Rate object")
    read_axioms(entry["output"], {"Review.Pass14A.margin12", "Review.Pass14A.printed_circuit12"},
                config["permitted_axioms"])
    # The query runs inside the review namespace, so Lean shortens its displayed name.
    need(re.search(r"^@(?:Review\.Pass14A\.)?printed_circuit12\s*:", entry["output"], re.MULTILINE),
         "missing /12 circuit type")
    print("Verified the independent /12 circuit readback and the Paper.Rate object cross-reference.")


def local_build(revisions, version, config):
    rec = receipt("pass14_release.json")
    targets = ["Statement", "Challenge", "Solution", "Paper"]
    modules = set().union(*(dependency_order(name) for name in targets))
    all_modules = {".".join(p.relative_to(SOURCE).with_suffix("").parts) for p in SOURCE.rglob("*.lean")}
    need(rec["publisher_commit"] == PUBLISHER and rec["git_tree"] == TREE and version in rec["toolchain"]
         and rec["external_checkout_revisions"] == revisions and rec["default_targets"] == targets,
         "full-build pins, external revisions, or targets differ")
    need(modules | {"scripts.PrintAxioms"} == all_modules and len(modules) == rec["default_target_modules"]
         and len(all_modules) == rec["modules_requested"], "full build does not cover all publisher source")
    rows = rec["modules"]
    need({r["module"] for r in rows} == all_modules and len(rows) == len(all_modules), "incomplete module ledger")
    for row in rows:
        name = row["module"]
        rel = source_file(name)
        need(rel.as_posix() == row["source"] and row["sha256"] == hashed(SOURCE / rel)
             and row["exit_code"] == 0, "module build or source hash differs for " + name)
    warnings = audit_modules(rows)
    if "build_warning_audit" in rec:
        need(warnings == rec["build_warning_audit"], "native warning summary differs from full diagnostics")
    print("Reviewed all native module diagnostics; only the five expected challenge placeholders appear.")
    need("Challenge" not in dependency_order("Solution") and rec["challenge_in_solution_imports"] is False,
         "trusted challenge entered Solution imports")
    signatures = rec["challenge_and_solution_signatures"]
    text = signatures["Challenge"]
    names = config["theorem_names"]
    need(text == signatures["Solution"] and digest_bytes(text.encode()) == rec["matching_signature_sha256"]
         and TYPE_QUERY.findall(text) == names, "isolated full signatures differ or omit configured declarations")
    q = CHECKS / "pass14_release.lean"
    verification = rec["verification"]
    need(verification["query_file"] == q.relative_to(REVIEW).as_posix() and verification["sha256"] == hashed(q)
         and verification["exit_code"] == 0, "release query receipt differs")
    commands = q.read_text().splitlines()
    axioms = [line.split()[-1] for line in commands if line.startswith("#print axioms ")]
    checks = [line.removeprefix("#check @") for line in commands if line.startswith("#check @")]
    output = verification["output"]
    need(set(names) <= set(axioms), "missing full theorem axiom query")
    need(read_axioms(output, axioms, config["permitted_axioms"]) == verification["axioms"], "axiom table differs")
    need(TYPE_QUERY.findall(output) == checks, "one or more requested type signatures missing")
    print(f"Verified {len(rows)} publisher source hashes and build results, {len(names)} isolated signature pairs,"
          f" {len(checks)} intermediate types, and {len(axioms)} axiom readbacks.")


def hosted(config, lock):
    rec = receipt("pass14_comparator.json")
    edition = lock["local_replay"]["pass14"]
    head = "3524ec471d5e2dee4cd70bd3c60f1dcc94dc43cc"
    repository = "nousentllc/VP-VNP-Review"
    base = f"https://github.com/{repository}"
    run_url = base + "/actions/runs/45691617731"
    hosted_index = edition["review_owned_linux_comparator"]
    need(rec["review_repository"] == repository and rec["review_baseline"] == edition["review_baseline"]
         and rec["review_commit"] == head and rec["publisher_commit"] == PUBLISHER
         and rec["source_tree"] == TREE and rec["checker_blob"] == CHECKER
         and rec["run_id"] == 45691617731 and rec["job_id"] == hosted_index["job_id"] == 139478246305
         and rec["run_url"] == hosted_index["run_url"] == run_url
         and rec["job_url"] == run_url + "/job/139478246305"
         and rec["workflow_file"] == hosted_index["workflow"] == ".github/workflows/pass14-comparator.yml"
         and rec["workflow_as_run"] == f"{base}/blob/{head}/{rec['workflow_file']}",
         "hosted source, review workflow, run or job identifiers differ")
    need(rec["theorem_names"] == config["theorem_names"] and rec["permitted_axioms"] == config["permitted_axioms"]
         and rec["enable_nanoda"] is config["enable_nanoda"] is True, "hosted scope differs from the pinned configuration")
    need(rec["run_conclusion"] == rec["conclusion"] == "success", "hosted run or job did not succeed")
    for phrase in ("Verify the exact source and checker", "build the four default targets",
                   "unmodified publisher Comparator driver", "Retain build and Comparator output"):
        steps = [step for step in rec["steps"] if phrase in step["name"]]
        need(len(steps) == 1 and steps[0]["status"] == "completed" and steps[0]["conclusion"] == "success",
             "hosted step did not complete successfully: " + phrase)

    artifact = rec["artifact"]
    path = CHECKS / "pass14_linux_artifact.zip"
    need(artifact["path"] == path.relative_to(REVIEW).as_posix() and artifact["id"] == 15063516125
         and artifact["name"] == "pass14-lean-comparator" and artifact["size_in_bytes"] == path.stat().st_size
         and artifact["digest"] == "sha256:" + hashed(path)
         == "sha256:51c556d89448e6574e57dc4cceca799fd187d786fb7807516d65bc5629772307",
         "hosted artifact identity, size or GitHub SHA-256 digest differs")
    cfg_member = "pass14-comparator/comparator.json"
    log_member = "pass14-comparator/comparator.log"
    build_member = "pass14-build.log"
    with ZipFile(path) as z:
        names = z.namelist()
        need(len(names) == 3 and set(names) == {cfg_member, log_member, build_member}, "unexpected ZIP directory")
        members = {name: z.read(name) for name in names}
    need({name: digest_bytes(data) for name, data in members.items()} == artifact["members"],
         "one or more ZIP member hashes differ")
    need(json.loads(members[cfg_member]) == config, "archived Comparator configuration differs from publisher")
    build = members[build_member].decode()
    need(audit_log(build) == rec["build_warning_audit"], "complete Linux build log differs from warning audit")
    success = "Build completed successfully (9032 jobs)."
    evidence = rec["evidence_lines"]
    need(success in build.splitlines() and success in evidence, "full Lake build completion missing")

    archived_log = rec["comparator_log"]
    standalone = CHECKS / "pass14_comparator.log"
    need(archived_log["path"] == standalone.relative_to(REVIEW).as_posix()
         and archived_log["archive_member"] == log_member
         and archived_log["sha256"] == artifact["members"][log_member]
         and standalone.read_bytes() == members[log_member], "standalone Comparator log differs from original ZIP member")
    lines = members[log_member].decode().splitlines()
    exports = []
    for line in lines:
        match = re.fullmatch(r"Exporting #\[(.+)\] from (Challenge|Solution)", line)
        if match:
            declarations = match[1].split(", ")
            need([n for n in declarations if n.startswith("Solution.")] == config["theorem_names"]
                 and set(config["permitted_axioms"]) <= set(declarations) and line in evidence,
                 "archived export names or receipt differ for " + match[2])
            exports.append(match[2])
    need(exports == [config["challenge_module"], config["solution_module"]], "missing or duplicate module export")
    markers = ["Running nanoda kernel on solution", "nanoda kernel accepts the solution",
               "Running Lean default kernel on solution.", "Lean default kernel accepts the solution", "Your solution is okay!"]
    need([line for line in lines if line in markers] == markers and all(line in evidence for line in markers),
         "kernel acceptance transcript or summary differs")
    need("PASS comparator.json" in evidence and "All 1 comparator configuration(s) accepted." in evidence,
         "driver acceptance markers absent")
    revisions = rec["tool_revisions"]
    driver = (SOURCE.parent / ".github/scripts/comparator-check.sh").read_text()
    need(set(revisions) == {"comparator", "lean4export", "nanoda_lib", "landrun"}
         and all(re.fullmatch(r"[0-9a-f]{40}", rev) and f"== {tool} @ {rev}" in evidence
                 for tool, rev in revisions.items())
         and all(revisions[name] in driver for name in ("comparator", "nanoda_lib", "landrun")),
         "hosted tool revision evidence differs from driver pins or job summary")
    print("Verified Linux artifact bytes and all three members, the full build warning audit, both theorem exports,"
          " and both kernels' acceptance of the solution.")


def main():
    lock = json.loads((REVIEW / "source-lock.json").read_bytes())
    manifest = json.loads((SOURCE / "lake-manifest.json").read_bytes())
    revisions = {p["name"]: p["rev"] for p in manifest["packages"]}
    version = "version " + (SOURCE / "lean-toolchain").read_text().strip().split(":v")[-1] + ","
    config = json.loads((SOURCE / "comparator.json").read_bytes())
    checks = (
        ("publisher", lambda: originals(lock)),
        ("evidence index", lambda: evidence_index(lock)),
        ("coverage", coverage),
        ("finite controls", finite),
        ("scalar", lambda: scalar(receipt("pass14a_margin_results.json"), revisions, version, config)),
        ("local release", lambda: local_build(revisions, version, config)),
        ("strengthened circuit", lambda: bridge(revisions, version, config)),
        ("hosted Comparator", lambda: hosted(config, lock)),
    )
    errors = []
    for label, check in checks:
        try:
            check()
        except (KeyError, ValueError, OSError, TypeError, BadZipFile, subprocess.CalledProcessError) as err:
            errors.append(f"{label}: {err}")
    if errors:
        raise SystemExit("\n".join(errors))
    print("Edition 11 source, coverage, receipts and finite controls agree. This command did not invoke Lean or Comparator.")


if __name__ == "__main__":
    main()
