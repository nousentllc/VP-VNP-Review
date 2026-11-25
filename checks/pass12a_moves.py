"""Exact two-layer law and packet-count controls for pass 12A.

Run with Python 3. The toy law is independent of the publisher's tower construction.
"""
from collections import Counter
from fractions import Fraction
from itertools import product


# The two matrices multiply to the identity over Z. For local index 1 one payload
# bit exists. The left factor vanishes on nonzero payload, the right need not.
LEFT = ((1, 1), (0, 1))
RIGHT = ((1, -1), (0, 1))


def packetize(bits, width):
    padded = bits + (1,) + (0,) * ((-len(bits) - 1) % width)
    return tuple(padded[k:k + width] for k in range(0, len(padded), width))


def local_table(input_bits, side, width, *, omit_labels=False, drop_end=False):
    table = Counter()
    for indices in product(range(2), repeat=len(input_bits)):
        for data in product(*(tuple(product(range(2), repeat=i)) for i in indices)):
            encoded = ()
            weight = 1
            for x, i, payload in zip(input_bits, indices, data):
                encoded += (() if omit_labels else (i,)) + payload
                if side == "left":
                    weight *= LEFT[x][i] * int(all(bit == 0 for bit in payload))
                else:
                    weight *= RIGHT[i][x]
            packets = packetize(encoded, width)
            outcome = len(encoded) // width
            assert len(packets) == outcome + 1
            key = (outcome, packets[:-1] if drop_end else packets)
            table[key] += weight
    return table


def contracted(left, right):
    return sum(w * right.get(z, 0) for z, w in left.items())


def check_layered_law():
    width = 2
    words = tuple(product(range(2), repeat=width))
    for x, y in product(words, repeat=2):
        value = contracted(local_table(x, "left", width), local_table(y, "right", width))
        assert value == int(x == y)
        assert value % 2 == int(x == y)
    assert sum(LEFT[0][i] * RIGHT[i][1] for i in range(2)) == 0
    assert [LEFT[0][i] * RIGHT[i][1] for i in range(2)] == [-1, 1]
    examples = {}
    for flag in ("omit_labels", "drop_end"):
        for x, y in product(words, repeat=2):
            options = {flag: True}
            v = contracted(local_table(x, "left", width, **options),
                           local_table(y, "right", width, **options))
            if v != int(x == y):
                examples[flag] = (x, y, int(x == y), v)
                break
    assert len(examples) == 2
    assert packetize((), width) == ((1, 0),)
    assert len({(1 + 0 + 1 + 1) // width, (1 + 1 + 1 + 0) // width}) == 1
    return examples


def check_stage_error():
    # Realize equality in the scalar recurrence. X_0 = b^3 and X_j = X_0/b^j.
    for b in (4, 8):
        q = Fraction(0)
        vertices = b**3
        envelope = q + vertices
        for depth in range(1, 4):
            vertices //= b
            prev = q
            q = q / 2 + vertices
            assert q > prev / 2
            assert q + vertices <= envelope / 2**depth
    # Without shrinkage, repeated unit errors tend to 2 rather than decaying.
    q = Fraction(0)
    for j in range(5):
        q = q / 2 + 1
    assert q == Fraction(31, 16) and q + 1 > Fraction(1, 32)


def main():
    examples = check_layered_law()
    check_stage_error()
    print("All 16 pairs of two-bit input strings recover equality over Z and F2.")
    for name, (x, y, original, altered) in examples.items():
        print(f"{name}: inputs {x}, {y}, target {original}, altered contraction {altered}.")
    print("At zero layers the channel still contains the single end packet (1, 0).")
    print("Shrinking and constant-size stage controls passed.")


if __name__ == "__main__":
    main()
