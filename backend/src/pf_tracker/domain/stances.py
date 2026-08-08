"""Combat stances as modifier emitters.

Each stance is a toggle that emits modifiers; none mutates the character.

These are the *situational* choices — what the character is doing this round, which
no weapon can know: charging, fighting defensively, flanking, holding high ground.
Power Attack and Combat Expertise used to live here too, but they belong to a weapon:
they are now rendered as alternative attack lines, with their scaling read from the
corpus rather than recomputed (see ``rules/weapon_feats.py``).
"""

from __future__ import annotations

from pf_tracker.domain.enums import BonusType, ModifierTarget, SourceKind
from pf_tracker.domain.models import Stances
from pf_tracker.domain.modifiers import Modifier


def _stance(target: str, value: int, bonus_type: BonusType | None, source: str) -> Modifier:
    return Modifier(
        target=target,
        value=value,
        bonus_type=bonus_type,
        source=source,
        source_kind=SourceKind.STANCE,
    )


def stance_modifiers(stances: Stances, bab: int) -> list[Modifier]:
    """Return the global modifiers emitted by the active stances.

    Only the situational ones live here: what the character is *doing* this round.
    Power Attack and Combat Expertise moved out — they belong to a weapon, and are
    rendered as alternative attack lines (see ``rules/weapon_feats.py``).
    """
    modifiers: list[Modifier] = []

    if stances.charge:
        modifiers.append(_stance(ModifierTarget.ATTACK_MELEE.value, 2, None, "Cargar"))
        modifiers.append(_stance(ModifierTarget.AC.value, -2, None, "Cargar"))

    if stances.fighting_defensively:
        modifiers.append(
            _stance(ModifierTarget.ALL_ATTACKS.value, -4, None, "Luchar a la defensiva")
        )
        modifiers.append(
            _stance(ModifierTarget.AC.value, 2, BonusType.DODGE, "Luchar a la defensiva")
        )

    if stances.total_defense:
        modifiers.append(_stance(ModifierTarget.AC.value, 4, BonusType.DODGE, "Defensa total"))

    if stances.flanking:
        modifiers.append(_stance(ModifierTarget.ATTACK_MELEE.value, 2, None, "Flanqueo"))

    if stances.higher_ground:
        modifiers.append(
            _stance(ModifierTarget.ATTACK_MELEE.value, 1, None, "Superioridad de altura")
        )

    return modifiers
