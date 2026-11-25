"""Exact controls for the cube, the shared type selector and the E.10 tolerance."""

from fractions import Fraction
from itertools import product
from math import comb


def cube_image(k, j, tail, axis, sign):
    """Double the manuscript's position so the output is an integer vector."""
    if axis < j:
        return tuple(sign * int(x == axis) for x in range(k))
    return (0,) * j + tuple(sign * tail[axis - j] * x for x in tail)


def check_conditional_cube():
    tested = 0
    for k in range(1, 7):
        for j in range(k + 1):
            for tail in product((-1, 1), repeat=k - j):
                for axis, sign in product(range(k), (-1, 1)):
                    expected = cube_image(k, j, tail, axis, sign)
                    # Average the original diagonal position over all hidden signs.
                    total = [0] * k
                    for head in product((-1, 1), repeat=j):
                        original = head + tail
                        for coordinate in range(k):
                            total[coordinate] += sign * original[axis] * original[coordinate]
                    assert tuple(total) == tuple((2 ** j) * x for x in expected)
                    if j:
                        first = cube_image(k, j-1, (1,) + tail, axis, sign)
                        second = cube_image(k, j-1, (-1,) + tail, axis, sign)
                        assert tuple(a+b for a,b in zip(first, second)) == tuple(2*x for x in expected)
                    tested += 1
    return tested


def check_word_selector():
    # Two two-party diagonal basis tensors e_0⊗e_0 and e_1⊗e_1.
    # At tensor power two, type (1,1) contains exactly these two words.
    words = [(0, 1), (1, 0)]
    for row, column in product(words, repeat=2):
        true_entry = sum(int(row == w and column == w) for w in words)
        shared = sum(int(row == w) * int(column == w) for w in words)
        separate = sum(int(row == w) for w in words) * sum(int(column == w) for w in words)
        assert true_entry == shared == int(row == column)
        assert separate == 1
    # n letters and n positions. Each initial binary count vector gives a distinct type.
    for n in range(1, 17):
        count = comb(2*n - 1, n-1)
        assert count >= 2 ** (n-1)


def comparison_slack(delta):
    # The surplus in displayed (E.2) before the hub term at k=64, ell=800.
    k, root, ell = 64, 8, 800
    pairs = k*(k-1)//2
    demand = ell * pairs * (1-delta)
    label = k * (root+delta)
    outer = ell * (pairs - Fraction(4, 81) * k + delta*k*k)
    return demand - label - outer


def main():
    total = check_conditional_cube()
    check_word_selector()
    fixed = comparison_slack(Fraction(1,1000))
    scaled = comparison_slack(Fraction(1,64000))
    assert fixed < 0 < scaled
    print(f"Checked {total} cube images and all available predecessor midpoints in dimensions 1–6.")
    print("Shared type selector gives the two-by-two identity; separate choices give all ones.")
    print("The growing-alphabet type count exceeds or equals 2^(n-1) for n=1,...,16.")
    print(f"E.2 demand minus label and outer cost at k=64: fixed tolerance {fixed}, scaled tolerance {scaled}.")


if __name__ == "__main__":
    main()
