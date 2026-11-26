"""Finite arithmetic controls for the K.6 audit. Run with standard Python 3."""

import json


def power_orbit(modulus):
    """Compute successive unary functions by pointwise squaring until repetition."""
    current = tuple(range(modulus))
    first = {}
    while current not in first:
        first[current] = len(first)
        current = tuple((value * value) % modulus for value in current)
    return tuple(first), first[current]


def check_power_names():
    fields = [2, 3, 5, 7, 11, 13, 17]
    names_checked = 0
    products_checked = 0
    orbits = {}
    for p in fields:
        orbit, start = power_orbit(p)
        period = len(orbit) - start
        orbits[str(p)] = {"first_repeat_at": len(orbit), "cycle_begins": start}
        for index in range(32):
            r = index if index < start else start + (index - start) % period
            for c in range(p):
                assert orbit[r][c] == pow(c, 2**index, p)
                names_checked += 1
        # Pick one expanded leaf indexed by i and independently evaluate its
        # 4-bit tally exponent. Each set tally bit j names the reduced i+j.
        for i in range(len(orbit) + 1):
            for c in range(p):
                for tally in range(16):
                    product = 1
                    for j in range(4):
                        if tally & (1 << j):
                            index = i + j
                            r = index if index < start else start + (index - start) % period
                            product = (product * pow(c, 2**r, p)) % p
                    assert product == pow(pow(c, 2**i, p), tally, p)
                    products_checked += 1
    assert orbits["5"] == {"first_repeat_at": 3, "cycle_begins": 2}
    assert pow(2, 2**2, 5) == 1 and pow(2, 2**(2 % 2), 5) == 2
    return orbits, names_checked, products_checked


def check_cost_envelopes():
    """Exercise bounds with saturated upper bounds, without assuming an accelerator."""
    rows = []
    for h in [17, 21]:
        for k in [96, 128, 192]:
            u = 2**k
            H = 16*h
            J = H * u.bit_length()
            trie_height, B, M = 4, 2, 3
            b = max(B, M)
            X = trie_height + b + J + 10
            n = u * (2*b + 1)  # upper bound for expanded nodes at Q = u
            t = u**(H-16)
            T = u**(H-15)
            W = u-500            # upper envelope for size(WF.code) + 500 <= u
            guess_size = n*(J+1)*(4*(trie_height+M)+100)
            prog_size = u**(4*h) + guess_size + W + 500
            query_size = W + 2*prog_size + 4*n*(J+1) + 3
            guess_cost = (8*J+10)*n
            postponed_cost = (1000+100*(trie_height+b+J+1))*T + 40*n*(J+1)+40
            assert X >= 10 and 1000*X**3 <= u
            assert T < 2**J and guess_size <= 2*u**2
            assert prog_size <= u**(4*h+1) and query_size <= u**(H-32)
            assert guess_cost <= 2*u**2 and guess_cost + t + 30 <= T
            assert 40*n*(J+1)+40 <= T and postponed_cost <= u*T <= u**H
            rows.append([h, k])
    return rows


def main():
    orbits, names, products = check_power_names()
    print(json.dumps({
        "purpose": "Finite power-table and arithmetic controls, with no accelerator assumed",
        "orbits": orbits,
        "power_name_comparisons": names,
        "bit_product_comparisons": products,
        "cost_envelopes_h_log2u": check_cost_envelopes()
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
