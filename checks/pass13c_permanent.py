"""Exact controls for E.1, using only Python's standard library.

Run from the review root with python3 checks/pass13c_permanent.py.
The determinant observation and the general squarefree proof are in pass 13C.
"""

from fractions import Fraction
from itertools import combinations_with_replacement, permutations, product
from math import comb, prod


def fibre_successors(labels):
    """Choose a forward cyclic order on each nonempty fibre."""
    successor = list(range(len(labels)))
    for label in sorted(set(labels)):
        fibre = [i for i, value in enumerate(labels) if value == label]
        for source, target in zip(fibre, fibre[1:] + fibre[:1]):
            successor[source] = target
    return successor


def grid_sum(v, w, weights):
    values = (0, 1)
    return sum(
        prod(weights[n][2 * x[a] + r[b]] for n, (a, b) in enumerate(zip(v, w)))
        for x in product(values, repeat=max(v, default=-1) + 1)
        for r in product(values, repeat=max(w, default=-1) + 1)
    )


def gadget(v, w, weights, half=Fraction(1, 2), misplaced_weight=False):
    """Write the three coefficient rows. Column order at each site is A, B, C."""
    sigma = fibre_successors(v)
    rho = fibre_successors(w)
    size = 3 * len(v)
    matrix = [[0 for _ in range(size)] for _ in range(size)]
    for n, (sigma_n, rho_n) in enumerate(zip(sigma, rho)):
        a, b, c = 3 * n, 3 * n + 1, 3 * n + 2
        adjacent_a = 3 * sigma_n
        first_row = [(a, half), (b, half), (adjacent_a, half), (c, -half)]
        second_row = [(a, 1), (b, 1), (adjacent_a, -1), (c, 1)]
        shifted = n if misplaced_weight else rho_n
        third_row = [
            (c, weights[n][3]), (b, weights[n][1]),
            (3 * rho_n + 2, weights[shifted][2]),
            (3 * rho_n + 1, weights[shifted][0]),
        ]
        for index, entries in zip((a, b, c), (first_row, second_row, third_row)):
            for column, coefficient in entries:
                matrix[index][column] += coefficient
    return matrix


def permanent(matrix):
    """Subset dynamic program: each state is the set of columns already used."""
    states = {0: 1}
    for row in matrix:
        next_states = {}
        for used, value in states.items():
            for col, weight in enumerate(row):
                bit = 1 << col
                if weight and not used & bit:
                    key = used | bit
                    next_states[key] = next_states.get(key, 0) + weight * value
        states = next_states
    return states.get((1 << len(matrix)) - 1, 0)


def padding(matrix):
    return [row + [0] for row in matrix] + [[0] * len(matrix) + [1]]


def symbolic_coefficient_check(v, w):
    """Recover degree-n coefficients by finite differences at integer table entries.

    Both polynomials are homogeneous of degree n in 4*n formal table entries.
    Delta^alpha at 0 therefore gives the requested coefficient times prod(alpha!).
    """
    n = len(v)
    variables = 4 * n
    differences = {}
    top = []
    for degree in range(n + 1):
        for indices in combinations_with_replacement(range(variables), degree):
            beta = tuple(indices.count(i) for i in range(variables))
            tables = [beta[i:i + 4] for i in range(0, variables, 4)]
            differences[beta] = permanent(gadget(v, w, tables)) - grid_sum(v, w, tables)
            if degree == n:
                top.append(beta)
    for alpha in top:
        numerator = sum(
            (-1) ** (n - sum(beta)) * prod(comb(a, b) for a, b in zip(alpha, beta)) * differences[beta]
            for beta in product(*(range(a + 1) for a in alpha))
        )
        assert numerator == 0, (v, w, alpha, numerator)
    return len(top)


def check_controls():
    empty = gadget((), (), ())
    assert grid_sum((), (), ()) == permanent(empty) == permanent(padding(empty)) == 1
    unit = [(1, 0, 0, 0)]
    assert grid_sum((0,), (0,), unit) == 1
    assert permanent(gadget((0,), (0,), unit)) == 1
    assert permanent(gadget((0,), (0,), unit, half=1)) == 2
    for h in (0, 1):
        assert permanent(gadget((0,), (0,), unit, half=h)) % 2 == 0
    for p in (3, 5, 7):
        assert permanent(gadget((0,), (0,), unit, half=pow(2, -1, p))) % p == 1
    print("One incidence: target 1; h=1 over Q gives 2; both h over F2 give 0.")

    numeric_weights = [(1, 2, 3, 4), (5, 6, 7, 8)]
    shared = (0, 0)
    grid_matrix = gadget(shared, shared, numeric_weights)
    value = permanent(grid_matrix)
    terms = [prod(row[j] for row, j in zip(grid_matrix, perm))
             for perm in permutations(range(6))]
    positive = sum(t for t in terms if t > 0)
    negative = sum(t for t in terms if t < 0)
    assert positive + negative == value == grid_sum(shared, shared, numeric_weights) == 70
    assert negative < 0 and permanent(padding(grid_matrix)) == value
    print(f"Two shared bits: 6! permutation terms total {positive} + ({negative}) = {value}; padding gives {value}.")
    assert grid_sum((0, 1), (0, 1), numeric_weights) == 260

    basis = [tuple(int(i == j) for j in range(4)) for i in range(4)]
    patterns = {1: [(0,)], 2: [(0, 0), (0, 1)]}
    total = 0
    for size, partitions in patterns.items():
        for v, w in product(partitions, repeat=2):
            for weights in product(basis, repeat=size):
                assert permanent(gadget(v, w, weights)) == grid_sum(v, w, weights)
                total += 1
    print(f"All {total} labelled one-hot cases with one or two incidences matched.")

    for y in range(-3, 4):
        weights = [(y, 0, 1, y + 1), (1, 2, y, y - 1)]
        expected = y * y + 2 * y - 1
        assert grid_sum(shared, shared, weights) == permanent(gadget(shared, shared, weights)) == expected
    print("Repeated affine variable: y^2 + 2y - 1 at all seven integers from -3 through 3.")

    v, w = (0, 0, 1), (0, 1, 0)
    weights = numeric_weights + [(9, 10, 11, 12)]
    good = grid_sum(v, w, weights)
    misplaced = permanent(gadget(v, w, weights, misplaced_weight=True))
    assert good == permanent(gadget(v, w, weights)) and misplaced != good
    print(f"Overlapping fibres: shifted table gives {good}; keeping the source table gives {misplaced}.")

    coefficients = symbolic_coefficient_check((0,), (0,))
    for v2, w2 in product(patterns[2], repeat=2):
        coefficients += symbolic_coefficient_check(v2, w2)
    coefficients += symbolic_coefficient_check(v, w)
    assert coefficients == 512
    print(f"All {coefficients} formal coefficients matched across six specified rational grid topologies.")


if __name__ == "__main__":
    check_controls()
