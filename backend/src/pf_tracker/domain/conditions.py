"""Conditions (`estados`) mapped to modifier sets, where mechanically expressible.

Keyed by the Spanish canonical condition name. Conditions whose effect is not a
clean numeric modifier (e.g. Confuso, Fascinado, Muerto) are absent here; the
service layer still surfaces them on the sheet as informational flags using the
corpus text. Effects that cannot be a single modifier — losing Dexterity to AC,
being unable to act — are expressed as flags on :class:`ConditionEffect`.
"""

from __future__ import annotations

from dataclasses import dataclass

from pf_tracker.domain.enums import (
    Ability,
    ModifierTarget,
    SourceKind,
    ability_target,
)
from pf_tracker.domain.modifiers import Modifier


@dataclass(frozen=True, slots=True)
class ConditionEffect:
    """The mechanical effect of a condition."""

    modifiers: tuple[Modifier, ...] = ()
    denies_dex: bool = False  # loses the Dexterity bonus to AC
    prevents_actions: bool = False  # cannot take actions this round


def _cond(target: str, value: int, source: str) -> Modifier:
    return Modifier(
        target=target,
        value=value,
        bonus_type=None,
        source=source,
        source_kind=SourceKind.CONDITION,
    )


def _ability_penalty(ability: Ability, value: int, source: str) -> Modifier:
    return _cond(ability_target(ability), value, source)


# Only mechanically unambiguous conditions are encoded. Values follow the corpus text.
CONDITION_EFFECTS: dict[str, ConditionEffect] = {
    "Apresado": ConditionEffect(
        modifiers=(
            _ability_penalty(Ability.DEX, -4, "Apresado"),
            _cond(ModifierTarget.ALL_ATTACKS.value, -2, "Apresado"),
            _cond(ModifierTarget.CMB.value, -2, "Apresado"),
        ),
    ),
    "Asustado": ConditionEffect(
        modifiers=(
            _cond(ModifierTarget.ALL_ATTACKS.value, -2, "Asustado"),
            _cond(ModifierTarget.ALL_SAVES.value, -2, "Asustado"),
            _cond(ModifierTarget.ALL_SKILLS.value, -2, "Asustado"),
        ),
    ),
    "Aterrado": ConditionEffect(
        modifiers=(_cond(ModifierTarget.AC.value, -2, "Aterrado"),),
        denies_dex=True,
        prevents_actions=True,
    ),
    "Aturdido": ConditionEffect(
        modifiers=(_cond(ModifierTarget.AC.value, -2, "Aturdido"),),
        denies_dex=True,
        prevents_actions=True,
    ),
    "Cegado": ConditionEffect(
        modifiers=(_cond(ModifierTarget.AC.value, -2, "Cegado"),),
        denies_dex=True,
    ),
    "Deslumbrado": ConditionEffect(
        modifiers=(_cond(ModifierTarget.ALL_ATTACKS.value, -1, "Deslumbrado"),),
    ),
    "Desprevenido": ConditionEffect(denies_dex=True),
    "Enmarañado": ConditionEffect(
        modifiers=(
            _cond(ModifierTarget.ALL_ATTACKS.value, -2, "Enmarañado"),
            _ability_penalty(Ability.DEX, -4, "Enmarañado"),
        ),
    ),
    "Ensordecido": ConditionEffect(
        modifiers=(_cond(ModifierTarget.INITIATIVE.value, -4, "Ensordecido"),),
    ),
    "Estremecido": ConditionEffect(
        modifiers=(
            _cond(ModifierTarget.ALL_ATTACKS.value, -2, "Estremecido"),
            _cond(ModifierTarget.ALL_SAVES.value, -2, "Estremecido"),
            _cond(ModifierTarget.ALL_SKILLS.value, -2, "Estremecido"),
        ),
    ),
    "Exhausto": ConditionEffect(
        modifiers=(
            _ability_penalty(Ability.STR, -6, "Exhausto"),
            _ability_penalty(Ability.DEX, -6, "Exhausto"),
        ),
    ),
    "Fatigado": ConditionEffect(
        modifiers=(
            _ability_penalty(Ability.STR, -2, "Fatigado"),
            _ability_penalty(Ability.DEX, -2, "Fatigado"),
        ),
    ),
    "Indispuesto": ConditionEffect(
        modifiers=(
            _cond(ModifierTarget.ALL_ATTACKS.value, -2, "Indispuesto"),
            _cond(ModifierTarget.ALL_DAMAGE.value, -2, "Indispuesto"),
            _cond(ModifierTarget.ALL_SAVES.value, -2, "Indispuesto"),
            _cond(ModifierTarget.ALL_SKILLS.value, -2, "Indispuesto"),
        ),
    ),
    "Despavorido": ConditionEffect(
        modifiers=(
            _cond(ModifierTarget.ALL_SAVES.value, -2, "Despavorido"),
            _cond(ModifierTarget.ALL_SKILLS.value, -2, "Despavorido"),
        ),
    ),
    "Sujeto": ConditionEffect(
        modifiers=(
            _ability_penalty(Ability.DEX, -4, "Sujeto"),
            _cond(ModifierTarget.ALL_ATTACKS.value, -4, "Sujeto"),
        ),
        denies_dex=True,
    ),
    "Tumbado": ConditionEffect(
        modifiers=(_cond(ModifierTarget.ATTACK_MELEE.value, -4, "Tumbado"),),
    ),
    "Paralizado": ConditionEffect(denies_dex=True, prevents_actions=True),
    "Inconsciente": ConditionEffect(denies_dex=True, prevents_actions=True),
    "Indefenso": ConditionEffect(denies_dex=True, prevents_actions=True),
}


def condition_modifiers(condition_names: tuple[str, ...]) -> list[Modifier]:
    """Collect the modifiers emitted by the given conditions (unknown ones ignored)."""
    modifiers: list[Modifier] = []
    for name in condition_names:
        effect = CONDITION_EFFECTS.get(name)
        if effect is not None:
            modifiers.extend(effect.modifiers)
    return modifiers


def denies_dexterity(condition_names: tuple[str, ...]) -> bool:
    """Whether any active condition denies the Dexterity bonus to AC."""
    return any(
        (effect := CONDITION_EFFECTS.get(name)) is not None and effect.denies_dex
        for name in condition_names
    )


def prevents_actions(condition_names: tuple[str, ...]) -> list[str]:
    """Names of active conditions that prevent taking actions."""
    return [
        name
        for name in condition_names
        if (effect := CONDITION_EFFECTS.get(name)) is not None and effect.prevents_actions
    ]
