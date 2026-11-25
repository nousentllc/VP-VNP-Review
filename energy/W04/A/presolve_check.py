"""Post-run, isolated presolve diagnostics on original matrices with no MIP start."""
import argparse
import csv
import json
import time
from pathlib import Path

from campaign import HERE, arrays, model


def check(out):
    instances = json.loads((HERE / "protocol/instances.json").read_text())
    records = []
    for instance in instances:
        a = arrays(instance)
        units = [[i] for i in range(a["n"])]
        for label, groups, kind in [("full_lp", units, "lp"),
                                    ("full_milp", units, "mixed"),
                                    ("group_root", [list(range(a["n"]))], "mixed")]:
            m, _, _ = model(a, groups, kind)
            solver = m.solver("on", 1e-6)
            start = time.perf_counter()
            solver.presolve()
            elapsed = time.perf_counter() - start
            reduced = solver.getPresolvedLp()
            records.append(dict(case=a["id"], form=label, seconds=elapsed,
                                status=str(solver.getModelPresolveStatus()),
                                original_rows=solver.getNumRow(), original_columns=solver.getNumCol(),
                                original_nonzeros=solver.getNumNz(), reduced_rows=reduced.num_row_,
                                reduced_columns=reduced.num_col_, reduced_nonzeros=len(reduced.a_matrix_.value_)))
    with (out / "isolated_presolve.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True, type=Path)
    check(parser.parse_args().out)
