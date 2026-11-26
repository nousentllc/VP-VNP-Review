"""Finite checks of K.4's tally predicate and weighted partition. Standard Python 3."""

from collections import Counter
from itertools import product
import json
from math import prod


def count_bits(value, width):
    """Encode one fixed-width leaf counter least significant bit first."""
    return [(value >> bit) & 1 for bit in range(width)]


def consumes(bill, budget, width, leaves):
    """Execute the lookup, binary borrow, and final zero test on one branch."""
    counters = {name: count_bits(value, width) for name, value in zip(leaves, budget)}
    for name in bill:
        if name not in counters:
            return False
        digits = counters[name]
        for position, digit in enumerate(digits):
            if digit:
                digits[position] = 0
                break
            digits[position] = 1
        else:
            return False
    return all(not any(digits) for digits in counters.values())


def check_tallies():
    constants = {"0": 2, "10": -1, "11": 0}
    leaves = tuple(constants)
    alphabet = ("", "0", "1", "10", "11", "101")
    width = 2
    budgets = list(product(range(2**width), repeat=len(leaves)))
    tested = supported = 0
    for length in range(2**width):
        for bill in product(alphabet, repeat=length):
            counts = Counter(bill)
            matches = [e for e in budgets if consumes(bill, e, width, leaves)]
            expected = [tuple(counts[name] for name in leaves)] if counts.keys() <= constants.keys() else []
            assert matches == expected
            matched_weight = sum(prod(constants[n]**k for n, k in zip(leaves, e)) for e in matches)
            assert matched_weight == prod(constants.get(name, 0) for name in bill)
            tested += 1
            supported += bool(matches)

    # Ordered records model separate accepting occurrences; zero-weight occurrences still count.
    runs = [
        (("0", "10"), 2), ((), 7), (("10", "0"), 2), (("0", "10"), -3),
        (("11",), 5), (("10", "0"), 0), (("1",), 11),
    ]
    filtered = {e: [weight for bill, weight in runs if consumes(bill, e, width, leaves)] for e in budgets}
    assert filtered[(1, 1, 0)] == [2, 2, -3, 0]
    assert filtered[(0, 0, 1)] == [5] and filtered[(0, 0, 0)] == [7]
    direct = sum(weight * prod(constants.get(name, 0) for name in bill) for bill, weight in runs)
    postponed = sum(prod(constants[n]**k for n, k in zip(leaves, e)) * sum(row) for e, row in filtered.items())
    assert postponed == direct == 5

    # At the width boundary a single count of four is lost; four total uses can also fit.
    assert not any(consumes(("0",) * 4, e, width, leaves) for e in budgets)
    assert consumes(("0", "10", "0", "10"), (2, 2, 0), width, leaves)
    assert consumes((), (0, 0, 0), 0, leaves)
    assert not consumes(("0",), (0, 0, 0), 0, leaves)
    return {
        "accepting_occurrences_in_example": len(runs), "bill_budget_comparisons": tested * len(budgets),
        "bills": tested, "budgets_per_bill": len(budgets), "direct_weighted_total": direct,
        "filtered_weights_for_1_1_0": filtered[(1, 1, 0)], "postponed_weighted_total": postponed,
        "represented_bills": supported, "unrepresented_zero_lookup_bills": tested - supported,
    }


if __name__ == "__main__":
    print(json.dumps(check_tallies(), indent=2, sort_keys=True))
