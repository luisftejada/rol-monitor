"""Tests for combat stances."""

from __future__ import annotations

from pf_tracker.domain.enums import BonusType, ModifierTarget
from pf_tracker.domain.models import Stances
from pf_tracker.domain.stances import stance_modifiers


def test_no_stances_no_modifiers() -> None:
    assert stance_modifiers(Stances(), bab=5) == []


def test_charge_grants_attack_and_ac_penalty() -> None:
    mods = stance_modifiers(Stances(charge=True), bab=1)
    values = {(m.target, m.value) for m in mods}
    assert (ModifierTarget.ATTACK_MELEE.value, 2) in values
    assert (ModifierTarget.AC.value, -2) in values


def test_fighting_defensively_and_total_defense_are_dodge() -> None:
    fd = stance_modifiers(Stances(fighting_defensively=True), bab=1)
    assert any(m.value == -4 and m.target == ModifierTarget.ALL_ATTACKS.value for m in fd)
    assert any(m.value == 2 and m.bonus_type == BonusType.DODGE for m in fd)

    td = stance_modifiers(Stances(total_defense=True), bab=1)
    assert any(m.value == 4 and m.bonus_type == BonusType.DODGE for m in td)


def test_flanking_and_higher_ground() -> None:
    mods = stance_modifiers(Stances(flanking=True, higher_ground=True), bab=1)
    values = {m.value for m in mods if m.target == ModifierTarget.ATTACK_MELEE.value}
    assert values == {2, 1}


def test_power_attack_and_combat_expertise_are_not_stances() -> None:
    """They belong to a weapon, not to the round: the sheet renders them as
    alternative attack lines, so a toggle here would count them twice."""
    assert not hasattr(Stances(), "power_attack")
    assert not hasattr(Stances(), "combat_expertise")
