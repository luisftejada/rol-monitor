"""How many feats a character is entitled to, and what may fill each one.

Three sources add up: the feats every character gets by level
(``avance.niveles_con_dote``), the ones a class grants, and the ones a race grants.

A ``fija`` slot is not a choice — the monk simply *has* Improved Unarmed Strike — so
it never counts towards the budget and is granted outright. Counting it would tell a
level-1 monk they had three feats to pick when they have one.

Class slots are gated on the level *in that class*, not the character's total: a
cleric 8 / fighter 4 has the fighter's level-4 feat, a cleric 4 / fighter 8 does not.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

from pf_tracker.rules.catalog import FeatSlotDTO

#: Source label for the feats every character gets, regardless of class or race.
BASE_SOURCE = "base"


@dataclass(frozen=True, slots=True)
class FeatSlot:
    """One feat the character is entitled to, and where it came from."""

    level: int
    source: str
    slot: FeatSlotDTO

    @property
    def is_granted(self) -> bool:
        """Whether it is already decided, and so costs the character no choice."""
        return self.slot.choice == "fija"


@dataclass(frozen=True, slots=True)
class FeatBudget:
    """What the character may pick, what is handed to them, and what they spent."""

    slots: tuple[FeatSlot, ...] = ()
    #: Feats granted outright by a ``fija`` slot, in corpus order.
    granted: tuple[str, ...] = ()
    #: Slots the character chooses for themselves.
    available: int = 0
    spent: int = 0
    #: Restricted lists referenced by the slots, already resolved to feat names,
    #: so nothing has to walk the corpus structure downstream.
    lists: dict[str, tuple[str, ...]] = field(default_factory=dict)
    #: The corpus' own caveat per list, where it has one.
    list_notes: dict[str, str] = field(default_factory=dict)

    @property
    def is_over_budget(self) -> bool:
        return self.spent > self.available


@dataclass(frozen=True, slots=True)
class ClassLevelRef:
    """A class the character has levels in, for gating class slots."""

    name: str
    level: int


def build_budget(
    *,
    feat_levels: Sequence[int],
    class_levels: Sequence[ClassLevelRef],
    class_slots: dict[str, Sequence[FeatSlotDTO]],
    race_name: str | None,
    race_slots: Sequence[FeatSlotDTO],
    chosen: Sequence[str],
) -> FeatBudget:
    """Work out the character's feat budget.

    ``chosen`` is what the character has taken. Granted feats are excluded from the
    spend even when they appear there, so a monk who also lists Improved Unarmed
    Strike explicitly is not charged for it twice.
    """
    total_level = sum(entry.level for entry in class_levels)

    slots: list[FeatSlot] = [
        FeatSlot(level=level, source=BASE_SOURCE, slot=FeatSlotDTO(level=level, choice="libre"))
        for level in sorted(feat_levels)
        if level <= total_level
    ]

    for entry in class_levels:
        slots.extend(
            FeatSlot(level=slot.level, source=entry.name, slot=slot)
            for slot in class_slots.get(entry.name, ())
            if slot.level <= entry.level
        )

    if race_name and total_level >= 1:
        slots.extend(
            FeatSlot(level=slot.level, source=race_name, slot=slot)
            for slot in race_slots
            if slot.level <= total_level
        )

    granted = tuple(s.slot.feat for s in slots if s.is_granted and s.slot.feat)
    available = sum(1 for s in slots if not s.is_granted)
    spent = sum(1 for name in chosen if name not in set(granted))

    return FeatBudget(
        slots=tuple(slots),
        granted=granted,
        available=available,
        spent=spent,
    )
