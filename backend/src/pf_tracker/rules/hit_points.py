"""The one rules figure behind a hit-point roll.

The roll itself is randomness and belongs to whoever presses the button; this is the
part that is a rule, so it is computed once, here, and shipped as a number.
"""

from __future__ import annotations


def hit_points_floor(die_faces: int) -> int:
    """Half the die plus one: the "never roll badly" option, 6 on a d10, 4 on a d6.

    Integer division deliberately — the corpus rounds down unless it says otherwise,
    so a d6 floors at 4 rather than at 4.5.
    """
    return die_faces // 2 + 1 if die_faces else 0
