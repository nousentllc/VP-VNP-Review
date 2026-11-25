"""Enumerate Hamiltonian cycles of explicit small M.2 graphs without imposing the XOR rules in search.

Run with Python 3 from any directory. Edge labels (incidence, left bit, right bit)
represent independent weight indeterminates. None denotes multiplicative identity.
"""

from collections import Counter, defaultdict
from itertools import product

BITS = (0, 1)
PAIRS = tuple(product(BITS, repeat=2))


def grid_graph(left, right, left_count, right_count, size, reverse_slots=False):
    """Choose one cyclic segment order and one order for the gadgets on each option."""
    if len(left) != len(right):
        raise ValueError("Each incidence needs two endpoints")
    count = len(left)
    pad = size - (left_count + right_count + 37 * count)
    if pad < 0:
        raise ValueError("Requested size is smaller than the unpadded construction")
    options = {}
    for i in range(left_count):
        options["x", i] = BITS
    for j in range(right_count):
        options["r", j] = BITS
    for n in range(count):
        options["selector", n] = PAIRS
        options["left", n] = (None, 0, 1)
        options["right", n] = (None, 0, 1)
        for t in PAIRS:
            options["flag", n, t] = BITS
    for k in range(pad):
        options["pad", k] = (None,)

    slots = defaultdict(list)
    gadgets = []

    def join(port_one, port_zero):
        g = len(gadgets)
        gadgets.append(g)
        slots[port_one].append((g, 1))
        slots[port_zero].append((g, 0))

    for n, (i, j) in enumerate(zip(left, right)):
        for t in PAIRS:
            join((("selector", n), t), (("flag", n, t), 0))
        for b in BITS:
            join((("left", n), b), (("flag", n, (1, b)), 0))
            join((("right", n), b), (("flag", n, (b, 1)), 0))
        join((("left", n), None), (("x", i), 1))
        join((("right", n), None), (("r", j), 1))

    heads = list(options)
    vertices = heads + [(part, g) for g in gadgets for part in ("tip0", "middle", "tip1")]
    index = {vertex: i for i, vertex in enumerate(vertices)}
    assert len(index) == size
    edges = [{} for _ in vertices]
    for pos, head in enumerate(heads):
        first_destinations = set()
        for option in options[head]:
            route = [head]
            ports = slots[head, option]
            for g, side in (reversed(ports) if reverse_slots else ports):
                route.extend(((f"tip{side}", g), ("middle", g), (f"tip{1-side}", g)))
            route.append(heads[(pos + 1) % len(heads)])
            if route[1] in first_destinations:
                raise ValueError("Two options at a head have the same first edge")
            first_destinations.add(route[1])
            for step, (u, v) in enumerate(zip(route, route[1:])):
                label = (head[1], *option) if step == 0 and head[0] == "selector" else None
                adjacency = edges[index[u]]
                assert index[v] not in adjacency or adjacency[index[v]] == label
                adjacency[index[v]] = label
    return edges


def enumerate_cycles(edges):
    """Fix vertex 0 as the origin. Search simple directed paths using only graph adjacency."""
    size = len(edges)
    monomials = Counter()
    if size == 0:
        return Counter({(): 1})
    all_vertices = (1 << size) - 1
    incoming = [0] * size
    for u, row in enumerate(edges):
        for v in row:
            incoming[v] |= 1 << u
    path = [0]

    def visit(current, remaining):
        if not remaining:
            if 0 in edges[current]:
                labels = (edges[u][v] for u, v in zip(path, path[1:] + [0]))
                monomials[tuple(sorted(label for label in labels if label is not None))] += 1
            return
        for next_vertex in edges[current]:
            bit = 1 << next_vertex
            if not remaining & bit:
                continue
            # Only remaining vertices can supply a predecessor after this departure.
            # Prune if taking this edge would strand an unvisited vertex or the origin.
            if any((v == 0 or (v != next_vertex and remaining & (1 << v))) and not incoming[v] & remaining
                   for v in edges[current]):
                continue
            path.append(next_vertex)
            visit(next_vertex, remaining ^ bit)
            path.pop()

    visit(0, all_vertices ^ 1)
    return monomials


def grid_assignments(left, right, left_count, right_count):
    result = Counter()
    for x in product(BITS, repeat=left_count):
        for r in product(BITS, repeat=right_count):
            result[tuple((n, x[i], r[j]) for n, (i, j) in enumerate(zip(left, right)))] += 1
    return result


def coefficient_sum(terms, weights):
    """Substitute 1 or one shared variable z for each weight, recording coefficients by degree."""
    by_degree = Counter()
    for term, multiplicity in terms.items():
        degree = sum(weights[label] for label in term)
        by_degree[degree] += multiplicity
    return by_degree


def main():
    cases = (
        ("empty", (), (), 0, 0, 0),
        ("singleton padding", (), (), 0, 0, 1),
        ("four padding segments", (), (), 0, 0, 4),
        ("one incidence", (0,), (0,), 1, 1, 40),
        ("one incidence, more padding", (0,), (0,), 1, 1, 43),
        ("both endpoints repeated", (0, 0), (0, 0), 1, 1, 80),
        ("one endpoint repeated", (0, 0), (0, 1), 1, 2, 80),
    )
    evaluated = {}
    for name, left, right, lcount, rcount, size in cases:
        expected = grid_assignments(left, right, lcount, rcount)
        for reverse in (False, True):
            graph = grid_graph(left, right, lcount, rcount, size, reverse_slots=reverse)
            actual = enumerate_cycles(graph)
            assert actual == expected, (name, reverse, actual, expected)
            assert all(k == 1 for k in actual.values())
        evaluated[name] = actual
        print(f"{name}: {size} vertices, {sum(expected.values())} cycles, both slot orders")

    # The matrix entry (1,1) is z at both incidences. Every other entry is 1.
    # A shared bit pair gives 3 + z^2; independent copies give (3+z)^2.
    actual = evaluated["both endpoints repeated"]
    split = grid_assignments((0, 1), (0, 1), 2, 2)
    labels = {(n, a, b): int(a == b == 1) for n in range(2) for a, b in PAIRS}
    polynomial = coefficient_sum(actual, labels)
    weakened = coefficient_sum(split, labels)
    assert polynomial == {0: 3, 2: 1} and weakened == {0: 9, 1: 6, 2: 1}
    assert {i: c % 2 for i, c in polynomial.items() if c % 2} == {0: 1, 2: 1}
    print("Shared variables: 3 + z^2 over Z, 1 + z^2 over F_2. Independent copies give 9 + 6z + z^2 over Z.")

    # Distinct trigger pairs expose the coupling even after reducing coefficients modulo two.
    labels[1, 1, 1], labels[1, 1, 0] = 0, 1
    shared_poly, split_poly = coefficient_sum(actual, labels), coefficient_sum(split, labels)
    assert shared_poly == {0: 2, 1: 2} and split_poly == weakened
    assert all(c % 2 == 0 for c in shared_poly.values())
    assert {i: c % 2 for i, c in split_poly.items() if c % 2} == {0: 1, 2: 1}
    print("Different trigger pairs in F_2[z]: shared bits give zero, split copies give 1 + z^2.")

    # With one unused x bit, its two options both run directly to the next head.
    try:
        grid_graph((0,), (0,), 2, 1, 40)
    except ValueError as error:
        assert "same first edge" in str(error)
    else:
        raise AssertionError("Expected a parallel edge at the unused variable")
    print("Unused bit: distinct options collide on the first edge when surjectivity is dropped.")


if __name__ == "__main__":
    main()
