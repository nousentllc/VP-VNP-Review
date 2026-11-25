"""Summarize all timed and censored AC trials, with separately labeled publisher data."""
import csv
import json
import re
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARMS = ["full_dc", "full_matched", "all", "low_degree"]


def write_csv(path, rows):
    with path.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def median(rows, field):
    x = [float(row[field]) for row in rows if row[field] != ""]
    return statistics.median(x) if x else None


def summarize(directory):
    rows = list(csv.DictReader((directory / "comparison.csv").open()))
    baselines = {}
    for line in (HERE.parent / "foundation/inputs/ac/BASELINE.md").read_text().splitlines():
        if line.startswith("| pglib_opf_case"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            baselines[cells[0]] = cells[4]
    cases = sorted({r["case"] for r in rows}, key=lambda s: (int(re.search(r"case(\d+)", s)[1]), s))
    cells, effects = [], []
    for case in cases:
        group = [r for r in rows if r["case"] == case]
        for arm in ARMS:
            trials = [r for r in group if r["policy"] == arm]
            hits = [r for r in trials if r["on_time"] == "True"]
            admissible = [r for r in trials if r["admissible"] == "True"]
            u = median(hits, "cost")
            ext = float(baselines[case])
            cells.append(dict(case=case, arm=arm, scheduled=len(trials), hits=len(hits), valid_any_clock=len(admissible),
                    ontime_median_cost=u, published_rounded_ac=ext, rel_to_published=(u-ext)/ext if u is not None else None,
                    ontime_median_s=median(hits, "elapsed"), all_returned_median_s=median(trials, "elapsed"),
                    ontime_median_iters=median(hits,"iterations"), n=median(trials,"n"),m=median(trials,"m"),
                    jac=median(trials,"jac"),hess=median(trials,"hess"),rcm_fill=median(trials,"fill"),
                    cond_proxy=median(trials,"condition"),factor_proxy_s=median(trials,"proxy_factor_s"),
                    rss_bytes_median=median(trials,"rss"),computed_lower=median(trials,"lower")))
            if arm in ("all", "low_degree"):
                for base in ARMS[:2]:
                    paired = []
                    for t in hits:
                        b = next(z for z in group if z["policy"] == base and z["repeat"] == t["repeat"])
                        if b["on_time"] == "True":
                            rel = abs(float(t["cost"])-float(b["cost"]))/max(1,abs(float(b["cost"])))
                            if rel <= 1e-5:
                                paired.append(float(t["elapsed"])/float(b["elapsed"]))
                    ratio=statistics.median(paired) if paired else None
                    effects.append(dict(case=case, arm=arm, comparator=base, jointly_ontime_matched_cost=len(paired),
                                        median_time_ratio=ratio, reduction_ge_ten_percent=None if ratio is None else ratio<=.90))
    write_csv(directory / "case_metrics.csv", cells)
    write_csv(directory / "matched_pairs.csv", effects)


if __name__ == "__main__":
    summarize(Path(sys.argv[1]))
