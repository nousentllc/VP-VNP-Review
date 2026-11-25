"""Exact finite controls for E.4. Run from the repository root with Python 3."""

from collections import Counter
from functools import lru_cache
from itertools import product
import json


def polynomial_oracle(gates):
    """Ordinary sparse polynomials, including powers and off-target monomials."""
    polynomials = []
    for op, left, right in gates:
        if op == "variable":
            value = Counter({((left, right),): 1})
        elif op == "constant":
            value = Counter({(): left})
        elif op == "add":
            value = polynomials[left].copy()
            value.update(polynomials[right])
        elif op == "multiply":
            value = Counter()
            for a, v in polynomials[left].items():
                for b, w in polynomials[right].items():
                    value[tuple(sorted(a + b))] += v * w
        else:
            raise ValueError(op)
        polynomials.append(value)
    return polynomials


def subsets(bits):
    index = bits
    while True:
        yield index
        if index == 0:
            break
        index = (index - 1) & bits


def gate_decomposition(gates, k, x):
    """For one table x, compute coefficients and aggregate by original gate and cut."""
    def add_scaled(out, terms, scale):
        for key, value in terms.items():
            out[key] += scale * value

    @lru_cache(None)
    def cf(i, s):
        op, left, right = gates[i]
        if op == "variable":
            return int(s == 1 << left and x[left] == right)
        if op == "constant":
            return left if s == 0 else 0
        if op == "add":
            return cf(left, s) + cf(right, s)
        return sum(cf(left, a) * cf(right, s ^ a) for a in subsets(s))

    @lru_cache(None)
    def cofactor(i, s):
        assert 3 * s.bit_count() > 2 * k
        op, left, right = gates[i]
        out = Counter()
        if op == "add":
            add_scaled(out, cofactor(left, s), 1)
            add_scaled(out, cofactor(right, s), 1)
        elif op == "multiply":
            for a in subsets(s):
                b = s ^ a
                # Prefer the left side as soon as it meets the lower threshold.
                if 3 * a.bit_count() >= k:
                    active, cut, outside = left, a, cf(right, b)
                else:
                    active, cut, outside = right, b, cf(left, a)
                if 3 * cut.bit_count() > 2 * k:
                    add_scaled(out, cofactor(active, cut), outside)
                else:
                    assert k <= 3 * cut.bit_count() <= 2 * k
                    out[active, cut] += outside
        return {key: value for key, value in out.items() if value}
    return cf, cofactor


def shared_examples():
    # Gate 2 produces A0 B0. Gates 9 and 10 both use it.
    joined = [("variable", 0, 0), ("variable", 1, 0), ("multiply", 0, 1),
              ("variable", 2, 0), ("variable", 3, 0), ("multiply", 3, 4),
              ("variable", 2, 1), ("variable", 3, 1), ("multiply", 6, 7),
              ("multiply", 2, 5), ("multiply", 2, 8), ("add", 9, 10)]
    # u = A0 B0 + C0 D0, with identical input wires to the last gate.
    squared = joined[:6] + [("add", 2, 5), ("multiply", 6, 6)]
    return joined, squared


def signed_chain(k, reflect):
    gates = []
    for block in range(k):
        start = len(gates)
        gates.extend([("variable", block, 0), ("variable", block, 1),
                      ("constant", -1, 0), ("multiply", start + 1, start + 2),
                      ("add", start, start + 3)])
        if block:
            a, b = accumulated, start + 4
            gates.append(("multiply", b, a) if reflect else ("multiply", a, b))
        accumulated = len(gates) - 1
    # Repeat seven same-input additions without duplicating the upstream subgraph.
    for _ in range(7):
        i = len(gates) - 1
        gates.append(("add", i, i))
    return gates


def audit_case(gates, k):
    direct = polynomial_oracle(gates)
    big = [s for s in range(1 << k) if 3 * s.bit_count() > 2 * k]
    seen = {}
    coefficient_checks = 0
    decompositions = 0
    for x in product(range(2), repeat=k):
        cf, cof = gate_decomposition(gates, k, x)
        for i in range(len(gates)):
            for s in range(1 << k):
                monomial = tuple((a, x[a]) for a in range(k) if s & (1 << a))
                assert cf(i, s) == direct[i][monomial]
                coefficient_checks += 1
            for s in big:
                table = cof(i, s)
                assert sum(cf(delta, a) * v for (delta, a), v in table.items()) == cf(i, s)
                # Include zero entries: a sparse support change can violate locality too.
                for a in subsets(s):
                    if k <= 3 * a.bit_count() <= 2 * k:
                        outside = tuple(x[j] for j in range(k) if (s ^ a) & (1 << j))
                        row = tuple(table.get((d, a), 0) for d in range(len(gates)))
                        key = i, s, a, outside
                        assert seen.setdefault(key, row) == row
                decompositions += 1
    return coefficient_checks, decompositions


def main():
    joined, squared = shared_examples()
    z = (0, 0, 0, 0)
    cf, cofactor = gate_decomposition(joined, 4, z)
    assert cf(11, 15) == 1 and cofactor(11, 15)[2, 3] == 1
    cf, cofactor = gate_decomposition(joined, 4, (0, 0, 1, 1))
    assert cf(11, 15) == 1 and cofactor(11, 15)[2, 3] == 1
    cf, cofactor = gate_decomposition(joined, 4, (0, 0, 1, 0))
    assert cf(11, 15) == 0
    cf, cofactor = gate_decomposition(squared, 4, z)
    assert cf(7, 15) == 2
    assert sum(cf(i, a) * v for (i, a), v in cofactor(7, 15).items() if a == 3) == 1
    assert sum(cf(i, a) * v for (i, a), v in cofactor(7, 15).items() if a == 12) == 1
    assert cf(7, 15) % 2 == 0 and (cf(7, 15) // 2) % 2 == 1
    cases = [(4, joined), (4, squared)]
    cases.extend((k, signed_chain(k, reflect)) for k in range(2, 7) for reflect in (False, True))
    checks = [audit_case(gates, k) for k, gates in cases]
    print(json.dumps({
        "circuits": len(cases), "blocks": [2, 3, 4, 5, 6],
        "coefficients_compared_with_full_polynomials": sum(c for c, _ in checks),
        "large_gate_set_assignment_decompositions": sum(d for _, d in checks),
        "outside_locality": "all gate and cut entries, including zero, checked across all binary assignments",
        "shared_cofactor_suffix_values_00_11_10": [1, 1, 0],
        "square_over_integers": 2, "same_coefficient_mod_2": 0, "unordered_split_mod_2": 1,
    }, indent=2))


if __name__ == "__main__":
    main()
