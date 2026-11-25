"""Recompute the lift and the scope of both repair bounds using exact rationals."""
import argparse
import gzip
import json
from fractions import Fraction
from pathlib import Path

import numpy as np


def exact(value):
    return np.vectorize(Fraction, otypes=[object])(np.asarray(value, dtype=object))


def require(condition, claim):
    if not np.all(condition):
        raise ValueError(claim)


def check_row(rec):
    z = rec["model"]
    A, b, E, d, c, u, anchor, S, G = (
        exact(z[k]) for k in ("A", "b", "E", "d", "c", "cap", "x0", "S", "G")
    )
    groups = G.shape[0]
    require((G >= 0) & (G <= 1), "weights")
    require(G.sum(axis=1) == 1, "row stochastic averaging")
    require((S == 0) | (S == 1), "binary lifting")
    require(S.sum(axis=1) == 1, "one group per coordinate")
    require(G @ S == np.eye(groups, dtype=int), "right inverse")
    require(S @ G @ u == u, "box upper endpoint")
    require(E @ S @ G == E, "terminal equality under projection")

    y = exact(rec["reduced"]["x"])
    raw = S @ y
    require(raw == exact(rec["raw"]), "raw must lift archived reduced primal")
    for point in (raw, anchor):
        require((point >= 0) & (point <= u), "point in nameplate box")
        require(E @ point == d, "point satisfies required equalities")
    slack = b - A @ anchor
    require(slack >= 0, "anchor inside each physical row")

    distortion = A @ S @ G - A
    box_support = np.maximum(distortion, 0) @ u
    require(box_support == exact(rec["h"]), "row support")
    v = np.maximum(A @ raw - b, 0)
    require(v <= box_support, "lift in reduced row budget")
    def ratio(violation, margin):
        return violation / (violation + margin) if violation > 0 else Fraction(0)
    candidate = max(ratio(x, s) for x, s in zip(v, slack, strict=True))
    worst = max(ratio(h, s) for h, s in zip(box_support, slack, strict=True))
    require(0 <= candidate <= worst <= 1, "candidate and uniform weights")
    require(worst == Fraction(rec["lambda_uniform"]), "uniform weight")
    require(candidate == Fraction(rec["lambda_min"]), "candidate weight")
    repaired = (1 - candidate) * raw + candidate * anchor
    require(repaired == exact(rec["mix"]), "repair identity")
    require(A @ repaired <= b, "repaired inequalities")
    require(E @ repaired == d, "repaired equalities")
    require((0 <= repaired) & (repaired <= u), "repaired box")

    alpha = np.maximum(c @ S @ G - c, 0) @ u
    cost = c @ repaired
    raw_cost = c @ raw
    require(c @ S @ y == raw_cost, "surrogate/raw cost correspondence")
    positive_change = max(0, cost - raw_cost)
    box_lower = np.minimum(c, 0) @ u
    uniform = worst * max(0, c @ anchor - box_lower)
    lipschitz = max(abs(c)) * sum(abs(raw - anchor)) * candidate
    require(alpha == Fraction(rec["alpha"]), "projection cost support")
    require(cost == Fraction(rec["cost"]), "repaired cost")
    require(raw_cost == Fraction(rec["raw_cost"]), "surrogate cost")
    require(positive_change == Fraction(rec["beta"]), "candidate beta")
    require(uniform == Fraction(rec["uniform_beta"]), "uniform beta")
    require(lipschitz == Fraction(rec["lipschitz_beta"]), "Lipschitz beta")
    require(positive_change <= min(uniform, lipschitz), "both applicable upper bounds")

    eps = raw_cost - Fraction(rec["reduced"]["L"])
    require(eps >= 0, "reduced witness gap")
    require(alpha + positive_change + eps == Fraction(rec["alpha_beta_eps"]), "composed bound")
    lo = max(0, cost - Fraction(rec["full"]["U"]))
    hi = cost - Fraction(rec["full"]["L"])
    require(lo == Fraction(rec["full_regret_lower"]), "regret lower")
    require(hi == Fraction(rec["full_regret_upper"]), "regret upper")
    require(lo <= min(hi, alpha + positive_change + eps), "nonempty certified regret interval")


def audit(primary_path, retry_path):
    with gzip.open(primary_path, "rt") as file:
        main = [json.loads(line) for line in file]
    with gzip.open(retry_path, "rt") as file:
        retries = [json.loads(line) for line in file]
    primary = [r for r in main if "failed" not in r]
    failed = {(r["seed"], r["regime"]) for r in main if "failed" in r}
    retry_ids = [(r["seed"], r["regime"]) for r in retries]
    require(len(main) == len({(r["seed"], r["regime"]) for r in main}) == 32, "unique primary case IDs")
    require(set(retry_ids) == failed and len(retry_ids) == len(failed), "retry coverage")
    secondary = [r["retry"] for r in retries]
    for rec in primary + secondary:
        check_row(rec)
    control = {**primary[0], "uniform_beta": str(Fraction(primary[0]["uniform_beta"]) + 1)}
    try:
        check_row(control)
    except ValueError as err:
        require(err.args == ("uniform beta",), "mutation failed on unexpected check")
    else:
        raise AssertionError("increasing stored uniform bound by one escaped equality check")
    return {
        "arithmetic": "fractions.Fraction",
        "primary_rows": len(main),
        "primary_passed": len(primary),
        "primary_failures_retained": len(failed),
        "secondary_passed": len(secondary),
        "positive_cases": "all raw/repaired points, supports, uniform/candidate weights, cost bounds and regret intervals passed",
        "negative_control": "inflated stored uniform beta rejected",
        "scope": "fixed-mode engineering records only; full LP primal/dual auditing is provided by engineering/check.py",
    }


def main():
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary", type=Path, default=here / "engineering/holdout.jsonl.gz")
    parser.add_argument("--retry", type=Path, default=here / "engineering/anchor_retry.jsonl.gz")
    parser.add_argument("--out", type=Path)
    options = parser.parse_args()
    result = json.dumps(audit(options.primary, options.retry), indent=2) + "\n"
    if options.out:
        with options.out.open("x") as file:
            file.write(result)
    else:
        print(result, end="")


if __name__ == "__main__":
    main()
