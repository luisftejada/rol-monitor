"""The single shared rounding helper.

The corpus rounds down everywhere unless stated otherwise. All derivation goes
through this module rather than scattering ``int()`` / ``//`` across the codebase.
"""

from __future__ import annotations

from fractions import Fraction


def round_down(value: Fraction | int) -> int:
    """Round toward negative infinity (floor), negative-safe.

    ``round_down(Fraction(-3, 2)) == -2`` (i.e. -1.5 floors to -2), matching how
    Pathfinder treats fractional results.
    """
    if isinstance(value, int):
        return value
    return value.numerator // value.denominator


def scaled(modifier: int, factor: Fraction) -> int:
    """Multiply an integer modifier by a factor and round down.

    Used for the Strength-to-damage multipliers: two-handed melee uses ``×3/2`` and
    off-hand uses ``×1/2``.
    """
    return round_down(modifier * factor)
