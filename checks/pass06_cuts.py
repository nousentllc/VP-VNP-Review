"""Independent finite diagnostics for the weighted identity and the J.4 budgets."""

from itertools import product
from math import prod


def check_weights():
    # Two identical alternatives for x must retain their multiplicity.
    options = {"x": [3, 3, -4], "y": [1, -2], "fail": []}
    outer = [(1, ["x", "y"]), (2, []), (5, ["fail"]), (-1, ["x", "x"])]
    grouped = sum(w * prod(sum(options[y]) for y in ys) for w, ys in outer)
    expanded = [
        w * prod(choice)
        for w, ys in outer
        for choice in product(*(options[y] for y in ys))
    ]
    assert grouped == sum(expanded) == -4
    assert len(expanded) == 16
    assert sum(term % 2 for term in expanded) % 2 == grouped % 2 == 0


def check_resource_cases():
    # Inputs exercise the parameter recurrence. No actual tower or scale threshold
    # of the publisher's existential theorem is instantiated here.
    v = 2**127
    lam = 128
    target = v**272
    switch = target * v**64 // lam
    assert switch * lam == target * v**64
    cases = [
        ("at target", target, 0),
        ("below switch", switch - 1, 0),
        ("at switch", switch, 1),
        ("above switch", switch + 1, 1),
        ("multiple regular cuts", target * v**143 + 37, 2),
    ]
    for name, initial_time, expected_regular in cases:
        for initial_size in (0, 1, initial_time // v**48):
            tau, size = initial_time, initial_size
            stages = []
            while True:
                regular = tau * lam >= target * v**64
                k = v**63 if regular else tau * lam // target + 1
                assert 2 <= k <= v**64
                assert size <= tau
                child_time = tau * lam // k
                child_size = (size // k + tau // v**256) * lam
                cutter_time = (size + tau * k // v**256) * lam
                stages.append((k * lam, cutter_time))
                if regular:
                    assert target <= child_time <= tau // v**62
                    assert child_size * v**48 <= 4**len(stages) * child_time
                    if name == "at switch" and len(stages) == 1:
                        assert child_time == target * v
                    tau, size = child_time, child_size
                else:
                    assert child_time < target
                    break
            cuts = len(stages)
            assert cuts == expected_regular + 1
            # The formal program composes the first cut with the remaining cuts.
            pieces, time = stages[-1]
            for first_pieces, first_time in reversed(stages[:-1]):
                time = first_time + first_pieces * (time + 62 * pieces + 110) + 100
                pieces *= first_pieces
            assert pieces * target <= initial_time * (4 * lam**2)**cuts
            assert time * v**48 <= initial_time * (100 * lam**3)**cuts
            assert child_size * v**48 <= target * (8 * lam)**cuts
            assert (100 * lam**3)**cuts <= v
            assert pieces * target <= initial_time * v**2
            assert time * v**24 <= initial_time
            assert child_size <= v**(272 - 32)
        print(f"{name}: {expected_regular} regular + 1 terminal cut, 3 input sizes")


if __name__ == "__main__":
    check_weights()
    print("16 expanded terms: value -4 over the integers and 0 modulo 2")
    check_resource_cases()
