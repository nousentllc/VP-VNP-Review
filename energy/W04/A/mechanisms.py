"""Descriptive decomposition of recorded trial time, incumbents, and presolve."""
import argparse
import csv
import gzip
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def analyze(out):
    with gzip.open(out / "trials.jsonl.gz", "rt") as f:
        rows = [json.loads(line) for line in f]
    labels = defaultdict(list)
    for r in rows:
        labels[r["arm"], r["cohort"]].append(r)
    summaries = []
    for (arm, cohort), runs in sorted(labels.items()):
        durations = defaultdict(list)
        source = Counter()
        skip = Counter()
        presolve = []
        vectors = 0
        for r in runs:
            stages = r["stages"]
            source[r["snapshots"]["2.0"]["source"]] += 1
            first = next((e["at"] for e in r["events"] if "U" in e and e["stage"] != "fallback"), None)
            if first is not None:
                durations["first_strict_improvement"].append(first)
            durations["fallback_validation"].append(r["events"][0]["at"])
            for key in ["build_seconds", "validation_seconds", "start_check_transfer_seconds", "solve_with_callbacks_seconds"]:
                durations[key].append(sum(s.get(key, 0) for s in stages))
            restricted = [s for s in stages if s["label"].startswith(("shared_", "sign_fix", "partial_sign_repair"))]
            if restricted:
                durations["restricted_pipeline"].append(restricted[-1].get("end",r["wall"]) - stages[0].get("end",0))
            for s in stages:
                if s.get("start_set_status") == "incompatible_with_stage":
                    skip[s["label"]] += 1
                if s.get("start_matrix_residual") is not None:
                    vectors += 1
                if s["full_model"]:
                    for line in s.get("solver_evidence", []):
                        m = re.search(r"reductions: rows (\d+).*columns (\d+).*nonzeros (\d+)", line)
                        if m:
                            presolve.append(list(map(int, m.groups())))
            if r["target"] is not None:
                durations["observed_target"].append(r["target"])
            durations["capped_target"].append(r["target"] or 2.)
        summaries.append(dict(arm=arm, cohort=cohort, trajectories=len(runs), final_sources=source,
                              count_timed={k:len(v) for k,v in durations.items()},
                              median_seconds={k:statistics.median(v) for k,v in durations.items()},
                              restricted_candidate_start_incompatible=skip, start_vectors_tested=vectors,
                              full_presolve_reduction_lines=len(presolve),
                              distinct_full_presolved_rows_columns_nnz=sorted(set(tuple(p) for p in presolve))))
    (out/"mechanisms.json").write_text(json.dumps(summaries,indent=2)+"\n")


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    analyze(parser.parse_args().out)
