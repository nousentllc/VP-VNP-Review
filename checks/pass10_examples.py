"""Exact finite controls for the two quantifier choices in Propositions A.7–A.8."""

from fractions import Fraction
from itertools import product


def rank_two_by_two_f2(entries):
    a, b, c, d = entries
    if (a * d - b * c) % 2:
        return 2
    return int(any(entries))


def check_unit_saturation():
    # On two parties the paper lists rank and the nonzero indicator as spectral points.
    # Zero-padding the scalar unit gives this rank-one representative.
    unit = (1, 0, 0, 0)
    binary_wire = (1, 0, 0, 1)
    for matrix in product((0, 1), repeat=4):
        assert int(any(matrix)) <= rank_two_by_two_f2(matrix)
    assert int(any(unit)) == rank_two_by_two_f2(unit) == 1
    assert int(any(binary_wire)) == 1 and rank_two_by_two_f2(binary_wire) == 2


def check_joint_limits():
    # A new label q is pulled back to 0 in one extension and to 1 in the other.
    profiles = [(abs(old - 0), abs(old - 1)) for old in (0, 1)]
    assert profiles == [(0, 1), (1, 0)]
    assert all(a + b == 1 for a, b in profiles)
    mixed = tuple(min(pair) for pair in zip(*profiles))
    assert sum(mixed) < 1  # Combining limits from different subsequences violates triangle.


def check_joint_law():
    half = Fraction(1, 2)
    same_bit = [(0, 0), (1, 1)]
    swapped_bits = [(0, 1), (1, 0)]
    for placements in (same_bit, swapped_bits):
        for index in (0, 1):
            assert sum(half * q[index] for q in placements) == half
    assert sum(half * abs(a - b) for a, b in same_bit) == 0
    assert sum(half * abs(a - b) for a, b in swapped_bits) == 1


if __name__ == "__main__":
    check_unit_saturation()
    check_joint_limits()
    check_joint_law()
    print("Passed: rank versus indicator on 16 binary matrices, incompatible coordinate limits, and two joint laws with equal marginals.")
