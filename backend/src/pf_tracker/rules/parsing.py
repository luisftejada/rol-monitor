"""Pure parsers for the compact Spanish notation used in the corpus.

These translate corpus strings into structured data for the catalog DTOs. They are
pure and deterministic; the domain derivation engine (phase 2) reuses the same
notation, and ``rules`` may depend on ``domain`` later without breaking layering.
"""

from __future__ import annotations

import re
from typing import NamedTuple

_BAB_TOKEN = re.compile(r"[+-]?\d+")
# A multiplier token like "×2" / "x3"; the threat range low end like "19–20" (en dash).
_MULTIPLIER = re.compile(r"[×xX]\s*(\d+)")
_RANGE_LOW = re.compile(r"(\d+)")

# Corpus placeholders that mean "not applicable".
_DASHES = {"—", "–", "-", ""}


class CriticalSpec(NamedTuple):
    """A single critical profile: crit on a natural roll of ``threat_range``..20."""

    threat_range: int
    multiplier: int


def parse_bab(bab: str) -> list[int]:
    """Parse a BAB progression string into its iterative bonuses.

    ``"+11/+6/+1"`` -> ``[11, 6, 1]``; ``"+0"`` -> ``[0]``.
    """
    tokens = _BAB_TOKEN.findall(bab)
    if not tokens:
        raise ValueError(f"unparseable BAB string: {bab!r}")
    return [int(token) for token in tokens]


def parse_critical(critical: str | None) -> list[CriticalSpec]:
    """Parse a critical string into one spec per weapon head.

    ``"×2"`` -> ``[(20, 2)]``; ``"19–20/×2"`` -> ``[(19, 2)]``;
    ``"×3/×4"`` (double weapon) -> ``[(20, 3), (20, 4)]``; ``"—"`` -> ``[]``.
    """
    if critical is None or critical.strip() in _DASHES:
        return []

    specs: list[CriticalSpec] = []
    pending_range = 20
    for raw in critical.split("/"):
        token = raw.strip()
        multiplier = _MULTIPLIER.search(token)
        if multiplier is not None:
            specs.append(
                CriticalSpec(threat_range=pending_range, multiplier=int(multiplier.group(1)))
            )
            pending_range = 20
        else:
            low = _RANGE_LOW.search(token)
            if low is None:
                raise ValueError(f"unparseable critical string: {critical!r}")
            pending_range = int(low.group(1))

    if not specs:
        raise ValueError(f"unparseable critical string: {critical!r}")
    return specs
