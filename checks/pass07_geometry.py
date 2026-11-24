"""Exact finite checks for the distinctions used in Theorem D.2."""

from itertools import product


def binary_rank(matrix, dimension):
    """Rows occupy consecutive blocks of bits. Eliminate over F_2."""
    mask = (1 << dimension) - 1
    pivots = {}
    for i in range(dimension):
        row = (matrix >> (dimension * i)) & mask
        while row:
            lead = row.bit_length() - 1
            if lead not in pivots:
                pivots[lead] = row
                break
            row ^= pivots[lead]
    return len(pivots)


def rank_means_without_curvature():
    ranks = [binary_rank(m, 3) for m in range(512)]
    first, second, third = 1, 1 << 4, 1 << 8

    def scaled_square(a, b):
        # Eight times the squared distance. Move 1/8 between two rank-one pairs.
        low, high = sorted((a, b))
        tweak = int(low == 0 and high == third) - int(low == 0 and high == first)
        return 8 * ranks[a ^ b] + tweak

    totals = [0] * 4
    counts = [0] * 4
    for a, b in product(range(512), repeat=2):
        rank = ranks[a ^ b]
        totals[rank] += scaled_square(a, b)
        counts[rank] += 1
    assert counts == [512, 25088, 150528, 86016]
    assert totals == [8 * r * count for r, count in enumerate(counts)]
    # d_max <= sqrt(3) < 2*sqrt(7/8) <= sum of any two nonzero sides.
    assert 8 * 3 < 4 * 7
    square = [0, first, first ^ second, second]
    sides = sum(scaled_square(x, square[(i + 1) % 4]) for i, x in enumerate(square))
    diagonals = scaled_square(square[0], square[2]) + scaled_square(square[1], square[3])
    assert (sides, diagonals) == (31, 32)
    print("All 262144 ordered pairs have the required rank-class totals. One square has defect -1/8.")


def pairwise_transversality():
    # E11, E22 and (e1+e2)(e1+e2)^T in a 3-by-3 matrix.
    u, v, w = 1, 1 << 4, 1 | (1 << 1) | (1 << 3) | (1 << 4)
    rank = lambda m: binary_rank(m, 3)
    assert all(rank(m) == 1 for m in (u, v, w))
    assert all(rank(m) == 2 for m in (u ^ v, u ^ w, v ^ w, u ^ v ^ w))

    def twice_cross(x, y):
        return rank(x ^ y) - rank(x) - rank(y)

    assert twice_cross(u, v ^ w) == -1
    assert twice_cross(u, v) + twice_cross(u, w) == 0
    print("Pairwise transversal directions give -1/2 versus 0 in the weakened additivity claim.")


def euclidean_obstruction():
    matrices = range(16)
    signs = [(-1) ** ((m & 1) ^ ((m >> 3) & 1)) for m in matrices]
    assert sum(signs) == 0
    total = sum(signs[a] * signs[b] * binary_rank(a ^ b, 2)
                for a, b in product(matrices, repeat=2))
    assert total == 16
    print("The 16-matrix signed squared-distance sum is +16. A Euclidean realization requires <= 0.")


if __name__ == "__main__":
    rank_means_without_curvature()
    pairwise_transversality()
    euclidean_obstruction()
