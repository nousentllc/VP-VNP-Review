"""Exact examples for Proposition C.3. Run with python3 from the review root."""

from fractions import Fraction
from itertools import product
from math import floor


def cn_rhs(d, x, v, z):
    return (d(z, x) ** 2 + d(z, v) ** 2) / 2 - d(x, v) ** 2 / 4


def shared_coin_table():
    # Two equally likely outcomes. The old labels are fixed in both outcomes.
    a, b, forward, reverse = labels = ((0, 0), (2, 2), (0, 2), (2, 0))

    def d(i, j):
        return Fraction(sum(abs(x - y) for x, y in zip(i, j)), 2)

    assert all(d(i, k) <= d(i, j) + d(j, k) for i, j, k in product(labels, repeat=3))
    for m in (forward, reverse):
        assert d(a, m) == d(m, b) == d(a, b) / 2 == 1
    assert d(forward, reverse) ** 2 == 4
    assert cn_rhs(d, a, b, reverse) == 0
    print("Shared coin: 64 triangle inequalities hold, but the midpoint CN test asks for 4 <= 0.")


def misplaced_quantifier():
    points = (0, 1)

    def d(i, j):
        return Fraction(abs(i - j))

    def passes(m, z):
        return d(z, m) ** 2 <= cn_rhs(d, 0, 1, z)

    assert all(any(passes(m, z) for m in points) for z in points)
    assert not any(all(passes(m, z) for z in points) for m in points)
    print("Two-point space: each test point has a witness, but no witness works for both.")


def simultaneous_approximation():
    # Points in the completion of the dyadic interval, including a repeated label.
    labels = (Fraction(0), Fraction(1, 3), Fraction(2, 5), Fraction(1, 3), Fraction(1))
    for n in (1, 4, 8, 12):
        scale = 2 ** n
        rounded = [Fraction(floor(x * scale), scale) for x in labels]
        assert rounded[1] == rounded[3]
        for i, j in product(range(len(labels)), repeat=2):
            error = abs(abs(rounded[i] - rounded[j]) - abs(labels[i] - labels[j]))
            assert error <= abs(rounded[i] - labels[i]) + abs(rounded[j] - labels[j])
            assert error < Fraction(2, scale)
    print("One map per depth controls all 25 ordered pairs and preserves the repeated label.")


if __name__ == "__main__":
    shared_coin_table()
    misplaced_quantifier()
    simultaneous_approximation()
