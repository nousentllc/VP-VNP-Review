"""Exact regression and adversarial examples, using only Python's standard library."""
from fractions import Fraction as Q
from itertools import product
import json


def support(lower, upper, residual):
    if residual == 0:
        return Q(0)
    endpoint = lower if residual > 0 else upper
    return None if endpoint is None else residual * endpoint


def boxed_suite():
    # Enumerate feasible points from two-dimensional rational grids. Equality and
    # inequality right-hand sides below depend on x; each trial is a different
    # feasible LP witness, not an independent randomly sampled instance.
    grid = tuple(Q(x, 2) for x in range(-2, 3))
    equality = (Q(3, 4), Q(-2, 3))
    inequality = (Q(-1, 2), Q(7, 8))
    costs = ((Q(-7, 5), Q(3, 2)), (Q(1, 4), Q(-1, 3)), (Q(0), Q(0)))
    accepted = 0
    exact = 0
    widest = Q(0)
    for point, cost, y, z, slack in product(product(grid, repeat=2), costs, grid, grid[:3], (0, Q(7, 9))):
        d = sum(a*x for a, x in zip(equality, point))
        b = slack + sum(a*x for a, x in zip(inequality, point))
        residual = [c - e*y - a*z for c, e, a in zip(cost, equality, inequality)]
        lower = d*y + b*z + sum(support(-1, 1, r) for r in residual)
        value = sum(c*x for c, x in zip(cost, point))
        assert lower <= value
        exact += int(lower == value)
        widest = max(widest, value-lower)
        accepted += 1
    intervals = [(None, None), (Q(-1), None), (None, Q(1)), (Q(-1), Q(1))]
    signed = []
    for (lo, hi), r in product(intervals, (-2, 0, 3)):
        value = support(lo, hi, r)
        if value is None:
            # Produce a real feasible ray point violating *any proposed zero floor*.
            witness = Q(-1000) if r > 0 else Q(1000)
            assert (lo is None or witness >= lo) and (hi is None or witness <= hi)
            assert r*witness < 0
        else:
            for x in grid:
                if (lo is None or lo <= x) and (hi is None or x <= hi):
                    assert value <= r*x
        signed.append({"bounds": [lo, hi], "reduced_cost": r, "finite_floor": value})
    return {"exact_feasible_trials": accepted, "tight_at_checked_witness": exact,
            "max_slack_in_test_grid": widest, "endpoint_cases": signed}


def scenario_suite():
    # Twenty-one admissible actions, fifty-one Bernoulli distributions. The exact
    # linear optimum is an endpoint; the grid is for independent checks only.
    checks = 0
    for p in (Q(i, 50) for i in range(51)):
        optimum = min(p, 1-p)
        for x in (Q(i, 20) for i in range(21)):
            j = (x, 1-x)
            mean = p*j[0] + (1-p)*j[1]
            penalty = (mean-j[0], mean-j[1])
            assert p*penalty[0] + (1-p)*penalty[1] == 0
            assert min(j[i] + penalty[i] for i in (0, 1)) >= optimum
            checks += 1
        assert min(p, 1-p) == min(p*0 + (1-p)*1, p*1+(1-p)*0)
    return {"distributions": 51, "common_actions_per_distribution": 21, "checks": checks,
            "example_equal_weights": {"baseline_expected_cost": Q(1, 2), "PF_floor": 0,
                "unpenalized_ceiling": Q(1, 2), "centered_floor": Q(1, 2), "centered_ceiling": 0},
            "scope": "Penalties use knowledge of this explicit example's costs. No generic fast penalty generator."}


def falsifiers():
    # Each assertion checks actual numbers for a false proposed strengthening.
    strong_target = Q(1)
    assert 10-9 == strong_target
    assert min([1]) > min([0, 1])
    assert 1*1 + min((0-1)*0, (0-1)*0) > 0
    assert Q(0)-min([1]) < 0 and 0 not in [1]
    assert (0+4)/Q(2) > 1 and Q(0) < 1
    assert Q(-1)*1 > Q(-1)*2
    assert Q(0+80, 2) < 50 and max(0,80) > max(50,50)
    assert Q(7, 1000) < 1 and 7 > 1  # ratio changes under an unconverted numerical threshold
    assert Q(7, 1000)*1000 == 7
    close = Q(1, 10**12)
    assert abs(close) <= Q(1, 10**9) and close != 0
    assert Q(1) <= Q(0)+1 and Q(1) > 0
    assert Q(1, 10) != Q.from_float(0.1)
    return {
        "equality": "U=10, L=9, feasible J=9 achieves target 1 exactly.",
        "restriction": "True costs {0,1}, restricted costs {1}: claimed lower floor 1 exceeds true optimum 0.",
        "positive_upper_row_multiplier": "x=0 fixed, x≤1, c=0, z=+1 gives fabricated lower bound 1.",
        "invalid_baseline": "True allowed costs {1}, infeasible incumbent 0 gives apparent negative ceiling.",
        "missing_scenario": "Equal weights, ceilings (0,4); deleting the second case understates full-panel mean 2.",
        "negative_weight": "Weights of either sign do not preserve order. With w=-1, 1≤2 reverses.",
        "different_measure": "Baseline losses (50,50), candidate (0,80): mean 50→40; upper-half CVaR 50→80.",
        "unit_error": "7 kWh = 0.007 MWh; comparing 0.007 with an unconverted 1 kWh threshold falsely excludes.",
        "rounded_witness": "x=10^-12 violates x=0 exactly despite a 10^-9 residual acceptance tolerance.",
        "invalid_penalty": "J=0, penalty=1 yields L=1 for augmented cost; the unadjusted floor fails.",
        "binary64": {"display": "0.1", "encoded": str(Q.from_float(0.1)), "decimal": "1/10"}
    }


if __name__ == "__main__":
    print(json.dumps({"arithmetic": "fractions.Fraction", "boxed": boxed_suite(),
                      "information": scenario_suite(), "counterexamples": falsifiers()},
                     indent=2, default=str))
