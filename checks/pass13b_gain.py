"""Exact finite controls for the F.6–A.6–G.2 interface. Python 3, standard library."""
from fractions import Fraction
from itertools import combinations, product
from math import isqrt


def ceil_sqrt(rational):
    lower = isqrt(rational.numerator // rational.denominator)
    return lower + int(lower * lower < rational)


def cayley_cycle():
    # (x,y,z) are matrix entries (12,23,13) of UT_3(F_2).
    def multiply(left, right):
        x, y, z = left
        X, Y, Z = right
        return x ^ X, y ^ Y, z ^ Z ^ (x * Y)

    points = list(product(range(2), repeat=3))
    generators = [(1, 0, 0), (0, 1, 0)]
    edges = {tuple(sorted((g, multiply(s, g)))) for g in points for s in generators}
    cycle = [points[0]]
    while len(cycle) < len(points):
        adjacent = {b if a == cycle[-1] else a for a, b in edges if cycle[-1] in (a, b)}
        cycle.append(min(adjacent - set(cycle)))
    assert len(edges) == 8 and tuple(sorted((cycle[-1], cycle[0]))) in edges
    return points, sorted(edges), cycle


def cut_price(cut, pairs):
    return tuple(int((a in cut) != (b in cut)) for a, b in pairs)


def check_support():
    points, edges, cycle = cayley_cycle()
    pairs = list(combinations(points, 2))
    # A cut and its complement have identical prices. Anchor the first point outside.
    prices = []
    for bits in product((0, 1), repeat=7):
        cut = {p for p, bit in zip(points[1:], bits) if bit}
        prices.append((cut_price(cut, pairs), cut_price(cut, edges)))
    ratio = max(Fraction(sum(w), 28) / Fraction(sum(v), 4)
                for w, v in prices if sum(v))
    assert ratio == Fraction(8, 7)
    checks = 0
    for w, v in prices:
        loads = [tuple(int(i == j) for i in range(28)) for j in range(28)]
        loads.extend([(0,) * 28, (1,) * 28, w])
        for load in loads:
            norm_squared = 28 * sum(n * n for n in load)
            # y is constant on crossing near edges. Its square is C R² /(4 #crossing).
            crossings = sum(v)
            y_squared = ratio * norm_squared / (4 * crossings) if crossings else Fraction(0)
            rounded = ceil_sqrt(y_squared)
            charge = sum(n * length for n, length in zip(load, w))
            assert charge <= crossings * rounded
            checks += 1
    half = set(cycle[:4])
    w, v = cut_price(half, pairs), cut_price(half, edges)
    chosen = list(w)
    chosen[chosen.index(1)] = 0
    charge = sum(n * length for n, length in zip(chosen, w))
    crossings = sum(v)
    ideal_squared = ratio * 28 * sum(n * n for n in chosen) / (4 * crossings)
    assert (charge, crossings, ideal_squared) == (15, 2, 60)
    assert 2 * isqrt(60) == 14 < charge <= 2 * ceil_sqrt(ideal_squared) == 16
    return len(prices), checks, ratio


def check_gain():
    # For any nonnegative support functional w, w1+w2 <= max(2w1,2w2).
    # The coordinate functionals already rule out either fixed single winner.
    corners = [(2, 0), (0, 2)]
    samples = list(product(range(9), repeat=2))
    def dot(a, b):
        return sum(x * y for x, y in zip(a, b))
    assert all(sum(w) <= max(dot(beta, w) for beta in corners) for w in samples)
    assert all(any(dot(beta, w) < sum(w) for w in samples) for beta in corners)
    examples = 0
    for z1, z2, c in product(range(9), range(9), [1, Fraction(3, 2), 3]):
        a = 4 * (z1 + z2) + 1
        epsilon = Fraction(a, 4 * (z2 + 1))
        for q in [1, 2, 7, 129]:
            x = epsilon * q
            lam = -(-x.numerator // x.denominator) + 1
            assert lam * z2 + q * (c * (a + z1) + z2) <= 2 * c * a * q
            examples += 1
    # The integer threshold is tight for the sufficient scalar test itself.
    C1, u = 8, 4
    threshold = 4 * (1 + 8 * C1)
    assert threshold == 260 and threshold % u == 0 and threshold >= 2 * u
    assert 1 + 8 * C1 > Fraction(threshold - u, 4)
    return examples


if __name__ == "__main__":
    prices, support_checks, best_ratio = check_support()
    print(f"{prices} cut prices, {support_checks} price/load checks, maximum ratio {best_ratio}.")
    print("Rounding downward sends required cost 15 to 14. Rounding upward gives 16.")
    print(f"{check_gain()} budget checks. With C1=8 and u=4 the first admissible h is 260.")
