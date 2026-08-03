"""Combat stances as modifier emitters.

Each stance is a toggle that emits modifiers; none mutates the character. Stances
that scale with BAB (power attack, combat expertise) do so at one step per +4 BAB.
Power attack's damage bonus depends on how the weapon is wielded, so it is computed
per weapon in the attack routine via :func:`power_attack_damage_bonus`.
"""

from __future__ import annotations

from pf_tracker.domain.enums import BonusType, ModifierTarget, SourceKind, Wield
from pf_tracker.domain.models import Stances
from pf_tracker.domain.modifiers import Modifier
from pf_tracker.domain.rounding import round_down


def scale_step(bab: int) -> int:
    """Scaling step for power attack / combat expertise: one per +4 BAB (min 1)."""
    return 1 + max(bab, 0) // 4


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

    Power attack's per-weapon damage bonus is not included here (see
    :func:`power_attack_damage_bonus`).
    """
    step = scale_step(bab)
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

    if stances.combat_expertise:
        modifiers.append(
            _stance(ModifierTarget.ATTACK_MELEE.value, -step, None, "Pericia en combate")
        )
        modifiers.append(
            _stance(ModifierTarget.AC.value, step, BonusType.DODGE, "Pericia en combate")
        )

    if stances.power_attack:
        modifiers.append(_stance(ModifierTarget.ATTACK_MELEE.value, -step, None, "Ataque poderoso"))

    if stances.flanking:
        modifiers.append(_stance(ModifierTarget.ATTACK_MELEE.value, 2, None, "Flanqueo"))

    if stances.higher_ground:
        modifiers.append(
            _stance(ModifierTarget.ATTACK_MELEE.value, 1, None, "Superioridad de altura")
        )

    return modifiers


def power_attack_damage_bonus(bab: int, wield: Wield) -> int:
    """Power attack damage bonus for a weapon, by wield.

    Base is +2 per step; two-handed multiplies by 3/2 (rounded down), off-hand by
    1/2. Natural attacks are treated as one-handed here.
    """
    from fractions import Fraction

    base = 2 * scale_step(bab)
    if wield == Wield.TWO_HANDED:
        return round_down(base * Fraction(3, 2))
    if wield == Wield.OFF_HAND:
        return round_down(base * Fraction(1, 2))
    return base
