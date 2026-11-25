"""Exact controls for the counting and signed-minor arguments of Appendix B.

Run from the review root with Python 3 and SymPy.
"""

from collections import Counter
from itertools import combinations, product
from math import comb
from random import Random

from sympy import Matrix, Poly, Symbol, diag, expand, zeros


def check_counts(cap):
    # Count distinct odd parts by number and weight for each half of a symbol.
    half = Counter({(0, 0): 1})
    for weight in range(1, cap + 1, 2):
        added = {(size + 1, total + weight): ways
                 for (size, total), ways in half.items() if total + weight <= cap}
        half.update(added)
    exact = Counter()
    for (left_size, a), a_count in half.items():
        for (right_size, b), b_count in half.items():
            if left_size == right_size and a + b <= cap:
                exact[a + b] += a_count * b_count
    # Frobenius coordinates of a partition separate its diagonal arms and legs.
    partitions = [1] + [0] * (cap // 2)
    for part in range(1, len(partitions)):
        for size in range(part, len(partitions)):
            partitions[size] += partitions[size - part]
    for e in range(cap + 1):
        assert exact[e] == (0 if e % 2 else partitions[e // 2])
    return sum(exact.values())


def energy(symbol):
    return sum(2 * i + 1 for half in symbol for i in half)


def glue(symbols, reflected=True):
    k = len(symbols)
    left = tuple(sorted(k * i + r for r, (a, _) in enumerate(symbols) for i in a))
    right = tuple(sorted(k * j + (k - 1 - r if reflected else r)
                         for r, (_, b) in enumerate(symbols) for j in b))
    return left, right


def check_interleaving():
    subsets = [s for size in range(4) for s in combinations(range(3), size)]
    states = [(a, b) for a in subsets for b in subsets if len(a) == len(b) and energy((a, b)) <= 6]
    inputs = list(product(states, repeat=3))
    outputs = {glue(family) for family in inputs}
    assert len(outputs) == len(inputs)
    assert all(energy(glue(family)) == 3 * sum(map(energy, family)) for family in inputs)
    example = (((), ()), ((0,), (0,)))
    assert energy(glue(example)) == 4 and energy(glue(example, reflected=False)) == 6
    return len(inputs)


def check_orthogonality(y):
    def coefficient(r, i):
        return sum(comb(r, h) * (-1) ** (i - h) * comb(r + i - h, i - h) * y ** (i - h)
                   for h in range(min(i, r) + 1))

    count = 0
    for cutoff in range(1, 6):
        for i, j in product(range(5), repeat=2):
            value = (1 - y) * sum(y**r * coefficient(r, i) * coefficient(r, j) for r in range(cutoff))
            remainder = Poly(value - int(i == j) * y**i, y).rem(Poly(y**cutoff, y))
            assert remainder.is_zero
            count += 1
    return count


def border(block, columns, rows):
    return block.row_join(columns).col_join(rows.row_join(zeros(rows.rows, columns.cols)))


def check_signed_minors(x):
    random = Random(1204)
    def matrix(nrow, ncol):
        return Matrix(nrow, ncol, lambda _i, _j: random.randint(-2, 2) + random.randint(-1, 1) * x)

    cases = ((1, 1, 0), (1, 2, 1), (2, 1, 2), (2, 2, 3))
    for m, n, cutoff in cases:
        a, b = matrix(m, m), matrix(n, n)
        f, fp = matrix(m, cutoff), matrix(cutoff, m)
        g, gp = matrix(cutoff, n), matrix(n, cutoff)
        d = diag(*(x ** (2*r + 1) for r in range(cutoff)))
        direct = a.row_join(f*d*g).col_join((-gp*d*fp).row_join(b))
        expected = direct.det(method="domain-ge")
        minor_sum = 0
        for size in range(cutoff + 1):
            subsets = list(combinations(range(cutoff), size))
            for first, second in product(subsets, repeat=2):
                left = border(a, f[:, first], fp[second, :])
                right = border(b, gp[:, second], g[first, :])
                minor_sum += x**energy((first, second)) * left.det(method="domain-ge") * right.det(method="domain-ge")
        assert expand(expected - minor_sum) == 0
    assert Matrix([[0, 1], [-1, 0]]).det() == 1
    assert Matrix([[0, 1], [1, 0]]).det() == -1
    return len(cases)


def main():
    print("Symbols up to energy 48:", check_counts(48))
    print("Injective, energy-preserving interleavings checked:", check_interleaving())
    print("Truncated orthogonality identities:", check_orthogonality(Symbol("y")))
    print("Polynomial matrix identities checked coefficientwise:", check_signed_minors(Symbol("X")))


if __name__ == "__main__":
    main()
