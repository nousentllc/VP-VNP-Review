"""Exact arithmetic checks of the clamped telescope in Theorem C.1, pp. 27–28."""

from fractions import Fraction


def check_profile(lengths, step, diameter, upper_bound):
    size = len(lengths) - 1
    assert 1 <= step <= size
    assert all(0 <= value <= upper_bound for value in lengths)
    assert all(size * abs(a - b) <= diameter for a, b in zip(lengths, lengths[1:]))
    squared = [length * length for length in lengths]
    # The box mean cancels the factor n² = size in the rescaled difference.
    total = sum(squared[min(i + step, size)] - squared[i] for i in range(size))
    boundary = sum(squared[0] - squared[i] for i in range(step))
    target = step * (squared[-1] - squared[0])
    assert total - target == boundary
    assert abs(boundary) <= Fraction(diameter * upper_bound * step * (step - 1), size)
    return boundary


def main():
    cases = 0
    for n in (2, 3, 5, 8, 16):
        size = n * n
        for profile in (
            [1 + Fraction(i, size) for i in range(size + 1)],
            [2 - Fraction(i, size) for i in range(size + 1)],
            [1 + Fraction(min(i, size - i), size) for i in range(size + 1)],
        ):
            for step in range(1, n + 1):
                check_profile(profile, step, 1, 2)
                cases += 1
        # For the increasing profile at S=n, the unnormalized error approaches 1 in magnitude.
        linear = [1 + Fraction(i, size) for i in range(size + 1)]
        expected = Fraction(n - 1, n) + Fraction((n - 1) * n * (2 * n - 1), 6 * size**2)
        assert -check_profile(linear, n, 1, 2) == expected
    print(f"Passed {cases} fixed-step checks and 5 growing-step identities.")


if __name__ == "__main__":
    main()
