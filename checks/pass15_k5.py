"""Finite arithmetic and list-semantics controls for the Pass 15 K.5 reconstruction."""

import itertools
import json
import math


def check_schedule(h, alpha, base_bits, power=4, cut_constant=1):
    """Use v = 2**base_bits and integer shifts to evaluate large monomials exactly.

    This checks the numerical inequalities conditional on the cut hypothesis and
    availability of the fixed programs. It does not construct a cut or accelerator.
    The test uses the maximum allowed program/trie quantities as arithmetic envelopes.
    """
    v = 1 << base_bits

    def term(exponent, coefficient=1):
        assert exponent >= 0 and coefficient >= 0
        return coefficient << (base_bits * exponent)

    H = 16 * h
    bit_length = v.bit_length()
    C = 2 * cut_constant + 6 * (power + 3) + 4
    assert alpha >= 5 and h >= 17 and bit_length >= 1001 + 100 * h
    assert bit_length ** (C * alpha) <= v
    assert bit_length ** (2 * cut_constant * alpha) <= v
    original_bound = (alpha * bit_length) ** power
    trie_height = original_bound
    J = (H * alpha + 1) * bit_length
    # Taking binary logs on these exact powers of two avoids allocating 2**J.
    assert base_bits * (H * alpha + 1) < J
    X = original_bound + (3 * alpha + 1) * (J + 1) + trie_height + 10
    assert 1000 * X**3 <= v
    input_exponent = alpha * (H - 32)
    input_limit = term(input_exponent)
    rows = []

    for n in range(1, 3 * alpha + 1):
        old_bound = original_bound + (n - 1) * J
        f = H * alpha + 1 - 8 * n
        m = trie_height + old_bound + J + 1
        # Expanded nodes <= v**(h*alpha) * node_multiplier.
        node_multiplier = 2 * old_bound + 1
        assert 10 <= m <= X and f >= input_exponent + 40
        assert H <= f + 9 <= 2 * H * alpha
        cut_time = term(f + 9)
        cut_size = term(input_exponent + 1)
        assert term(input_exponent + 1 + 48) <= cut_time
        stored_nodes_times_width = term(h * alpha, node_multiplier * (J + 1))
        interpreter_cost = term(f + 8, 1000 + 100 * m) + 40 * stored_nodes_times_width + 40
        assert interpreter_cost <= cut_time
        # |W|+3 <= v follows from the theorem's fixed-code threshold.
        code_growth = term(h * alpha + 2) + term(H + 1)
        previous_code = v + (n - 1) * code_growth
        assert v + previous_code + input_limit + 4 * stored_nodes_times_width <= cut_size
        guess_cost = term(h * alpha, (8 * J + 10) * node_multiplier)
        listing = term(f - 15)
        leading_piece_term = term(f - 5)
        traversal = term(f + 11 - H, 30)
        assert guess_cost + listing + leading_piece_term + traversal + 30 <= term(f)
        assert previous_code + code_growth <= term(4 * h * alpha)
        # The guess code bound is from Guess.size_gt with prefix [] and N=B_p+J.
        guess_size = stored_nodes_times_width * (4 * (trie_height + old_bound + J) + 100)
        assert guess_size <= term(h * alpha + 1, 2)
        assert 2 * term(h * alpha) + term(H) + guess_size + v <= code_growth
        assert max(old_bound + J, original_bound) == original_bound + n * J
        rows.append(f)

    assert rows[-1] <= alpha * (H - 17)
    assert 3 * alpha * J <= 51 * h * alpha**2 * bit_length
    return {
        "h": h,
        "alpha": alpha,
        "log2_v": base_bits,
        "rounds": len(rows),
        "initial_exponent": H * alpha + 1,
        "last_exponent": rows[-1],
        "last_cut_minimum": input_exponent + 40,
        "target": alpha * (H - 17),
    }


def check_lists():
    weights = {"y": (2, -3), "w": (4,), "reject": ()}

    def path_values(pieces):
        return [math.prod(path) for path in itertools.product(*(weights[y] for y in pieces))]

    checked = 0
    for length in range(5):
        for pieces in itertools.product(weights, repeat=length):
            assert sum(path_values(pieces)) == math.prod(sum(weights[y]) for y in pieces)
            checked += 1
    example = ("y", "y", "w")
    assert path_values(example) == [16, -24, -24, 36]
    assert sum(path_values(tuple(dict.fromkeys(example)))) == -4
    weighted_cut = -2 * sum(path_values(example)) + 5 * sum(path_values(()))
    assert weighted_cut == -3
    return {"lists_checked": checked, "repeated_piece_paths": path_values(example),
            "two_cut_runs_value": weighted_cut}


def main():
    results = {
        "scope": "finite arithmetic on conditional bounds and independent synthetic list controls",
        "schedules": [check_schedule(17, 5, 4096), check_schedule(19, 7, 8192)],
        "list_products": check_lists(),
    }
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
