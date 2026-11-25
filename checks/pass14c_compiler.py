"""Finite exact controls for K.2 and K.3. Run from any directory with Python 3.9+."""
from collections import Counter
from functools import lru_cache
from itertools import combinations, product
import json


def word_code(word, n):
    """True cells as (zero-based position, symbol), with symbol 2 for the end mark."""
    assert len(word) < n
    return frozenset(enumerate((*word, 2)))


def valid(bits, n):
    """Nc.RunMn.VOk. An earlier end may supply later empty rows."""
    return all(sum((p, a) in bits for a in range(3)) <= 1 and
               (any((p, a) in bits for a in range(3)) or
                any((q, 2) in bits for q in range(p)))
               for p in range(n))


def clause_polynomial():
    n = 3
    cells = list(product(range(n), range(3)))
    coeff = Counter()
    patterns = []
    for degree in range(len(cells) + 1):
        for subset in combinations(cells, degree):
            bits = frozenset(subset)
            if not valid(bits, n):
                continue
            patterns.append(bits)
            # One state, no auxiliary tapes, one input channel and one step.
            # Hidden input counter starts at zero; the end counter is forced by the letter.
            for letter, weight in [(None, 0), (0, 1), (1, 0)]:
                final_counter = int(letter is not None)
                if (final_counter, 2) in bits and (letter is None or (0, letter) in bits):
                    coeff[bits] += weight
    coeff = +coeff
    short = word_code((0,), n)
    expected = Counter({short: 1})
    for symbol in range(3):
        expected[short | {(2, symbol)}] = 1
    assert coeff == expected
    codes = [word_code(w, n) for k in range(n) for w in product(range(2), repeat=k)]
    for code in codes:
        assert [b for b in patterns if b <= code] == [code]
        assert sum(weight for b, weight in coeff.items() if b <= code) == int(code == short)
    assert max(map(len, coeff)) == n
    both_ends = short | {(2, 2)}
    assert sum(weight for b, weight in coeff.items() if b <= both_ends) == 2
    assert int(short <= both_ends) == 1
    return codes, len(patterns), len(coeff)


def trailing_factor_checks():
    """Compare the single-input clause support to the trailing-factor expansion with signed paths."""
    n = 3
    cells = list(product(range(n), range(3)))
    matrices = {None: ((1, -1), (0, 2)), 0: ((0, 3), (-1, 1)), 1: ((1, 0), (1, -1))}
    words = [w for k in range(n) for w in product(range(2), repeat=k)]
    patterns = [frozenset(comb) for k in range(len(cells) + 1) for comb in combinations(cells, k)]
    checks = 0
    guarded_checks = 0
    for t in range(4):
        word_values = Counter()
        paths = []
        for letters in product(matrices, repeat=t):
            emitted = tuple(a for a in letters if a is not None)
            for states in product(range(2), repeat=t+1):
                if states[0] != 0 or states[-1] != 1:
                    continue
                weight = 1
                for j, letter in enumerate(letters):
                    weight *= matrices[letter][states[j]][states[j+1]]
                paths.append((letters, weight))
                word_values[emitted] += weight
        expanded = Counter()
        for word in words:
            prefix = word_code(word, n)
            for extension in product((None, 0, 1, 2), repeat=n-len(word)-1):
                extra = {(p,a) for p,a in enumerate(extension, start=len(word)+1) if a is not None}
                expanded[prefix | extra] += word_values[word]
        for pattern in patterns:
            value = 0
            if valid(pattern, n):
                for letters, weight in paths:
                    position = 0
                    for letter in letters:
                        if letter is not None:
                            if (position, letter) not in pattern:
                                break
                            position += 1
                    else:
                        if (position, 2) in pattern:
                            value += weight
            assert expanded[pattern] == value
            # Optional independent stronger variant: every row after an end must be empty.
            end_guard = all(not any(q > p for q, _ in pattern) for p, a in pattern if a == 2)
            exact_word_sum = sum(word_values[w] for w in words if pattern == word_code(w, n))
            assert (value if end_guard else 0) == exact_word_sum
            checks += 1
            guarded_checks += 1
    return checks, guarded_checks


def worked_circuit():
    """Straight-line circuit for Φ' using a shared intermediate and cancellation."""
    return [('v', (0, 0)), ('v', (1, 2)), ('*', 0, 1),
            ('c', 1), ('v', (2, 0)), ('v', (2, 1)), ('v', (2, 2)),
            ('+', 3, 4), ('+', 7, 5), ('+', 8, 6), ('*', 2, 9),
            ('+', 10, 10), ('c', -1), ('*', 12, 10), ('+', 11, 13)]


def combine(left, right, a, b):
    """Linear combination of coefficient dictionaries with integer multiplicities."""
    return {k: a * left.get(k, 0) + b * right.get(k, 0) for k in left.keys() | right.keys()}


def compile_advice(circuit):
    const, lam, kappa = [], [], []
    for gate in circuit:
        op, x, *tail = gate
        if op == 'v':
            c, linear, pairs = 0, {x: 1}, {}
        elif op == 'c':
            c, linear, pairs = x, {}, {}
        else:
            y = tail[0]
            if op == '+':
                c = const[x] + const[y]
                linear = combine(lam[x], lam[y], 1, 1)
                pairs = combine(kappa[x], kappa[y], 1, 1)
            else:
                c = const[x] * const[y]
                linear = combine(lam[x], lam[y], const[y], const[x])
                pairs = combine(kappa[x], kappa[y], const[y], const[x])
                pairs[x, y] = pairs.get((x, y), 0) + 1
        const.append(c)
        lam.append(linear)
        kappa.append(pairs)
    return const, lam, kappa


def direct_line(circuit, active, d):
    gates = []
    for gate in circuit:
        op, x, *tail = gate
        out = [0] * (d + 1)
        if op == 'c':
            out[0] = x
        elif op == 'v':
            if d:
                out[1] = int(x in active)
        else:
            y = tail[0]
            for j in range(d + 1):
                if op == '+':
                    out[j] = gates[x][j] + gates[y][j]
                else:
                    out[j] = sum(gates[x][i] * gates[y][j-i] for i in range(j+1))
        gates.append(out)
    return gates


def compiled_value(advice, active, out, degree, modulus):
    const, lam, kappa = advice
    project = (lambda value: value % modulus) if modulus else (lambda value: value)
    linear = [sum(c for x, c in row.items() if x in active) for row in lam]

    @lru_cache(None)
    def forest(budget, stack):
        if not stack:
            return 1
        g, *tail = stack
        tail = tuple(tail)
        value = linear[g] * forest(budget, tail)
        if budget:
            for (left, right), c in kappa[g].items():
                if c:
                    value += c * forest(budget - 1, (left, right) + tail)
        return project(value)

    if degree == 0:
        return project(const[out])
    return project(const[out] + forest(degree-1, (out,)))


def run():
    codes, admissible, monomials = clause_polynomial()
    # Multiple ring tests use the identical circuit topology; every reference gate is checked.
    circuits = [worked_circuit(),
                [('v', (0, 0)), ('c', -1), ('+', 0, 1), ('*', 2, 2), ('+', 3, 3)],
                [('v', (0, 0)), ('c', 1), ('+', 0, 1), ('*', 2, 2), ('*', 3, 3)],
                [('c', -3)]]
    total = 0
    for circuit in circuits:
        advice = compile_advice(circuit)
        for active in codes:
            for degree in range(5):
                reference = direct_line(circuit, active, degree)
                for out, parts in enumerate(reference):
                    for modulus in (0, 2, 3, 6):
                        value = sum(parts)
                        assert compiled_value(advice, active, out, degree, modulus) == (
                            value % modulus if modulus else value)
                        total += 1
    shared = worked_circuit()
    a = compile_advice(shared)
    active = word_code((0,), 3)
    assert [compiled_value(a, active, len(shared)-1, d, 0) for d in range(5)] == [0, 0, 1, 1, 1]
    assert [compiled_value(a, active, g, 3, 2) for g in (10, 11, 13, 14)] == [1, 0, 1, 1]
    malformed = active | {(2, 2)}
    assert direct_line(shared, malformed, 3)[-1] == [0, 0, 1, 1]
    trial = [('v', (0, 0)), ('c', 1), ('+', 0, 1), ('*', 2, 2)]
    assert direct_line(trial, active, 2)[-1] == [1, 2, 1]
    # Dropping the end marker loses incomparability between a word and a proper extension.
    assert frozenset(enumerate((0,))) < frozenset(enumerate((0, 1)))
    signed_checks, guarded_checks = trailing_factor_checks()
    return dict(boolean_patterns_examined=512, admitted_by_VOk=admissible, canonical_codes=len(codes),
                printed_word_sum_monomials=1, formal_construction_monomials=monomials,
                signed_path_coefficient_checks=signed_checks, guarded_word_sum_coefficient_checks=guarded_checks,
                gate_code_degree_ring_checks=total, characteristic_controls=[0, 2, 3, 6],
                canonical_evaluation_mod_2=1, extra_end_evaluations_over_integers=[1, 2],
                scope="Finite symbolic and semantic controls. No runtime estimate here is a measurement of the publisher interpreter.")


if __name__ == '__main__':
    print(json.dumps(run(), indent=2))
