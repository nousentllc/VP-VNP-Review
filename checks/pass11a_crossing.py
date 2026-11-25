"""Exact small checks for the crossing identity and the common price witness.

Run with Python 3 and SymPy. The determinant is transcribed from Appendix B,
page 23, independently of the Lean implementation.
"""

from collections import Counter
from itertools import combinations, permutations, product
from math import prod

from sympy import GF, Matrix, Poly, Symbol
from sympy.polys.matrices import DomainMatrix


def determinant_polynomial(symbols, x):
    """Each symbol has one row index and one column index, either 0 or 1."""
    y = x**2

    def b_poly(i, j):
        return 1 if j == 0 else i - (i + 1) * y

    def c_poly(i, j):
        return 1 if j == 0 else i * y - (i + 1)

    def entry(row, column):
        i, j = symbols[row][0], symbols[column][1]
        diagonal = int(i == j) * x ** (2 * i + 1)
        forward = x ** (2 * i + 1) * b_poly(i, j)
        reverse = x ** (2 * j + 1) * b_poly(j, i)
        rows = (
            (0, c_poly(i, j), diagonal, (y - 1) * forward),
            (-c_poly(j, i), 0, reverse, -diagonal),
            (-diagonal, -forward, 0, -(y - 1) * c_poly(i, j)),
            (-(y - 1) * reverse, diagonal, (y - 1) * c_poly(j, i), 0),
        )
        return rows[row][column]

    result = 0
    for p in permutations(range(4)):
        inversions = sum(p[i] > p[j] for i, j in combinations(range(4), 2))
        result += (-1) ** inversions * prod(entry(i, p[i]) for i in range(4))
    return Poly(result, x)


def state_counts(max_energy):
    counts = Counter()
    odd_weights = range(1, max_energy + 1, 2)
    for k in range(len(odd_weights) + 1):
        by_weight = Counter(sum(s) for s in combinations(odd_weights, k))
        for a, count_a in by_weight.items():
            for b, count_b in by_weight.items():
                counts[a + b] += count_a * count_b
    return [sum(counts[e] for e in range(n + 1)) for n in range(max_energy + 1)]


def compare_coefficients_and_cuts():
    x = Symbol("X")
    symbols = ((0, 1), (1, 0))  # all size-1, energy-4 symbols
    theta = 16
    count = state_counts(theta)
    arguments = list(product(symbols, repeat=4))
    raw = {(a, b, c, d): determinant_polynomial((a, d, c, b), x)
           for a, b, c, d in arguments}
    for (a, b, c, d), polynomial in raw.items():
        assert polynomial.degree() <= theta
        reflected = raw[a, d, c, b]
        assert all(polynomial.nth(n) == reflected.nth(theta - n)
                   for n in range(theta + 1))
        assert polynomial.eval(1) == int(a == c[::-1] and b == d[::-1])

    # Relabel the index alphabets at c,d as in the paper. In this class the sign is +1.
    tensors = {(a, b, c, d): raw[a, b, c[::-1], d[::-1]] for a, b, c, d in arguments}
    pairs = list(product(symbols, repeat=2))
    ranks = []
    binary_ranks = []
    for n in range(theta + 1):
        ad = Matrix([[tensors[a, b, c, d].nth(n) for b, c in pairs] for a, d in pairs])
        ab = Matrix([[tensors[a, b, c, d].nth(n) for c, d in pairs] for a, b in pairs])
        ranks.append((ad.rank(), ab.rank()))
        assert ranks[-1][0] <= (n + 1) * count[n]
        assert ranks[-1][1] <= (theta - n + 1) * count[theta - n]
        binary_ranks.append(tuple(DomainMatrix.from_Matrix(matrix).convert_to(GF(2)).rank()
                                  for matrix in (ad, ab)))
        assert all(binary <= rational for binary, rational in zip(binary_ranks[-1], ranks[-1]))
    assert all(sum(poly.nth(n) for n in range(theta + 1)) == int(a == c and b == d)
               for (a, b, c, d), poly in tensors.items())
    assert ranks[0] == (1, 4) and ranks[theta] == (4, 1)
    print("Theta = 16. Exact (AD|BC, AB|CD) ranks by degree:", ranks)
    print("Exact ranks over F_2 by degree:", binary_ranks)


def test_separate_cut_witnesses():
    def distance(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

    x, v, y, u = (-1, -1), (1, 1), (-1, 1), (1, -1)
    o, other_o, w, other_w = (-1, 0), (1, 0), (0, -1), (0, 1)
    demand = distance(x, v) + distance(y, u)
    legs_ab = sum((distance(x, o), distance(y, o), distance(v, other_o), distance(u, other_o)))
    legs_ad = sum((distance(x, w), distance(u, w), distance(y, other_w), distance(v, other_w)))
    hub_ab, hub_ad = distance(o, other_o), distance(w, other_w)
    assert (demand, legs_ab, legs_ad, hub_ab, hub_ad) == (8, 4, 4, 2, 2)
    assert legs_ab + 2 * hub_ab == demand and legs_ad + 2 * hub_ad == demand
    assert 2**2 + 2**2 > 4  # Yet each separate choice (2,0), (0,2) fits.
    lhs = 2 * demand
    twice_rhs = 2 * (legs_ab + legs_ad + 2) + hub_ab**2 + hub_ad**2
    assert (2 * lhs, twice_rhs) == (32, 28)  # Display (B.2), p=q=t₀=1.
    print("Manhattan metric control: both cuts force 2; squared cost 8 exceeds 4. Display gives 16 > 14.")


if __name__ == "__main__":
    compare_coefficients_and_cuts()
    test_separate_cut_witnesses()
