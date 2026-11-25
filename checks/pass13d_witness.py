"""Exhaust the literal rooted Boolean witness and compare symbolic coefficients to HC."""
from collections import Counter
from itertools import permutations
import json
from math import prod


def cycles(n):
    """Independent target: enumerate successor maps, keep the single-orbit permutations."""
    answer = Counter()
    for sigma in permutations(range(n)):
        seen = set()
        v = 0
        while n and v not in seen:
            seen.add(v)
            v = sigma[v]
        if len(seen) == n:
            answer[tuple(enumerate(sigma))] += 1
    return answer


def witness(n):
    if n == 0:
        return Counter({(): 1}), Counter({(): 1}), 1
    clashes = [(i, j) for i in range(n*n) for j in range(n*n)
               if i != j and (i // n == j // n or i % n == j % n)]
    assert len(clashes) == 2*n*n*(n-1)
    anchored, all_orders = Counter(), Counter()
    accepted = 0
    for mask in range(1 << (n*n)):
        bits = [(mask >> k) & 1 for k in range(n*n)]
        if any(bits[i] and bits[j] for i,j in clashes):
            continue
        rows = [bits[i*n:(i+1)*n] for i in range(n)]
        test = prod(sum(row) for row in rows)
        if not test:
            continue
        assert test == 1
        edges = []
        for i in range(n):
            pairs = [(u,v) for u in range(n) for v in range(n)
                     if rows[i][u] and rows[(i+1) % n][v]]
            assert len(pairs) == 1
            edges.extend(pairs)
        monomial = tuple(sorted(edges))
        all_orders[monomial] += test
        if bits[0]:
            accepted += 1
            anchored[monomial] += test
    return anchored, all_orders, accepted


def run_checks():
    sizes = []
    for n in range(5):
        target = cycles(n)
        anchored, unrooted, survivors = witness(n)
        assert anchored == target
        assert unrooted == Counter({key: max(n,1)*v for key,v in target.items()})
        for characteristic in [2,3,5]:
            assert all(anchored[key] % characteristic == target[key] % characteristic for key in target)
        sizes.append(dict(n=n, tables=2**(n*n), rooted_tables=survivors,
                          distinct_target_monomials=len(target), unrooted_per_monomial=max(1,n)))
    # Weakening: modular row and column sums can accept three ones in every row/column.
    all_ones = [[1]*3 for _ in range(3)]
    assert all(sum(row) % 2 == 1 for row in all_ones)
    assert all(sum(col) % 2 == 1 for col in zip(*all_ones))
    assert 1-all_ones[0][0]*all_ones[0][1] == 0
    return sizes


if __name__ == "__main__":
    print(json.dumps(run_checks(), indent=2))
