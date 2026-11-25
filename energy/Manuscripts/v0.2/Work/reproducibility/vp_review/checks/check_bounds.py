"""Small exact checks from the November 24 audit. Run with Python 3."""

from fractions import Fraction
import json


def mixed_cut_minor(q):
    """Rows index a; columns index selected b,c pairs of the two-term example."""
    columns = [(2, 2)] + [(1, j) for j in range(2, q + 1)]
    return [
        [int(a == 1 and b == c) + int(b == 1 and a == c) for b, c in columns]
        for a in range(1, q + 1)
    ]


def audit_checks():
    margin = Fraction(4, 81) - Fraction(15, 1000) - Fraction(15, 10000)
    hub_bound = Fraction(446, 1000)
    assert margin > Fraction(1, 31)
    assert 31 * hub_bound < 14
    assert margin / hub_bound > Fraction(1, 14)

    q = 3
    minor = mixed_cut_minor(q)
    assert minor == [[int(i == j) for j in range(q)] for i in range(q)]

    strata = [1, 2, 1]  # constant, linear and quadratic coefficients of (x+1)^2
    field_checks = []
    for modulus in (2, 3, 5):
        reduced = [a % modulus for a in strata]
        for x in range(modulus):
            assert sum(a * x**i for i, a in enumerate(reduced)) % modulus == (x + 1)**2 % modulus
        field_checks.append({"characteristic": modulus, "coefficients": reduced})
    # In K.5, tau' is X times v^(f+8) up to a constant.
    piece_offset = 8 + 2 - 16
    listing_offset = 8 - 24
    assert (piece_offset, listing_offset) == (-6, -16)
    return {
        "scope": "Exact algebra and small examples only. No Lean or runtime verification.",
        "E10_lower_margin": str(margin),
        "E10_upper_scaled_hub_distance": str(hub_bound),
        "E10_lower_ratio": str(margin / hub_bound),
        "mixed_cut_example_q": q,
        "mixed_cut_identity_minor": minor,
        "shared_gate_square": field_checks,
        "K5_exponent_offsets_relative_to_f": {"piece_evaluation": piece_offset, "listing": listing_offset},
    }


if __name__ == "__main__":
    print(json.dumps(audit_checks(), indent=2))
