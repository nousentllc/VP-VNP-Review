"""Check the packet-index and history distinctions in the J.2 regrouping."""

from itertools import product


WORDS = (None, 0, 1)
LIVE = tuple(product(WORDS, repeat=2))
LEFT = {(0, 1): 2, (1, 0): -1}
RIGHT = {(0, 1): 3, (1, 0): 5}


def left(pair, spent_copy, self_loop):
    return LEFT.get(pair, 0) if spent_copy == 0 and self_loop == 0 else 0


def right(pair, spent_copy):
    return RIGHT.get(pair, 0) if spent_copy == 1 else 0


def global_value(*, merge_parallel=False, equate_spent=False):
    total = 0
    for p, q in product(LIVE, repeat=2):
        if p != q or (merge_parallel and p[0] != p[1]):
            continue
        for a, b, loop in product(WORDS, repeat=3):
            if equate_spent and a != b:
                continue
            total += left(p, a, loop) * right(q, b)
    return total


def group_values():
    left_sums = {p: sum(left(p, a, loop) for a, loop in product(WORDS, repeat=2)) for p in LIVE}
    right_sums = {p: sum(right(p, b) for b in WORDS) for p in LIVE}
    common = sum(left_sums[p] * right_sums[p] for p in LIVE)
    independent = sum(left_sums.values()) * sum(right_sums.values())
    return common, independent


def main():
    total = global_value()
    grouped, independent = group_values()
    assert total == grouped == 1
    assert global_value(merge_parallel=True) == global_value(equate_spent=True) == 0
    assert independent == 8
    assert total % 2 == 1 and independent % 2 == 0
    print("Global and grouped values 1; merged parallel labels 0; tied spent copies 0; independent guesses 8.")


if __name__ == "__main__":
    main()
