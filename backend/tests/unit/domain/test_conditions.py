"""Tests for condition -> modifier mapping."""

from __future__ import annotations

from pf_tracker.domain.conditions import (
    condition_modifiers,
    denies_dexterity,
    prevents_actions,
)
from pf_tracker.domain.enums import Ability, ModifierTarget, ability_target


def test_frightened_applies_penalties_to_attacks_saves_skills() -> None:
    mods = condition_modifiers(("Asustado",))
    targets = {m.target for m in mods}
    assert ModifierTarget.ALL_ATTACKS.value in targets
    assert ModifierTarget.ALL_SAVES.value in targets
    assert ModifierTarget.ALL_SKILLS.value in targets
    assert all(m.value == -2 for m in mods)


def test_fatigued_penalises_str_and_dex() -> None:
    mods = condition_modifiers(("Fatigado",))
    by_target = {m.target: m.value for m in mods}
    assert by_target[ability_target(Ability.STR)] == -2
    assert by_target[ability_target(Ability.DEX)] == -2


def test_unknown_condition_is_ignored() -> None:
    assert condition_modifiers(("Confuso", "Muerto")) == []


def test_denies_dexterity() -> None:
    assert denies_dexterity(("Desprevenido",)) is True
    assert denies_dexterity(("Fatigado",)) is False


def test_prevents_actions() -> None:
    assert prevents_actions(("Aturdido", "Fatigado")) == ["Aturdido"]
    assert prevents_actions(("Fatigado",)) == []
