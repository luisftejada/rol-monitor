"""Tests for combat stances."""

from __future__ import annotations

import pytest

from pf_tracker.domain.enums import BonusType, ModifierTarget, Wield
from pf_tracker.domain.models import Stances
from pf_tracker.domain.stances import power_attack_damage_bonus, scale_step, stance_modifiers


@pytest.mark.parametrize(("bab", "step"), [(0, 1), (3, 1), (4, 2), (8, 3), (16, 5)])
def test_scale_step(bab: int, step: int) -> None:
    assert scale_step(bab) == step


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


def test_power_attack_and_combat_expertise_scale() -> None:
    mods = stance_modifiers(Stances(power_attack=True, combat_expertise=True), bab=8)
    # Each scales to -3 at BAB 8.
    penalties = [m.value for m in mods if m.target == ModifierTarget.ATTACK_MELEE.value]
    assert penalties.count(-3) == 2
    assert any(m.value == 3 and m.bonus_type == BonusType.DODGE for m in mods)


def test_flanking_and_higher_ground() -> None:
    mods = stance_modifiers(Stances(flanking=True, higher_ground=True), bab=1)
    values = {m.value for m in mods if m.target == ModifierTarget.ATTACK_MELEE.value}
    assert values == {2, 1}


@pytest.mark.parametrize(
    ("bab", "wield", "expected"),
    [
        (0, Wield.ONE_HANDED, 2),
        (0, Wield.TWO_HANDED, 3),
        (0, Wield.OFF_HAND, 1),
        (8, Wield.ONE_HANDED, 6),
        (8, Wield.TWO_HANDED, 9),
        (8, Wield.OFF_HAND, 3),
        (0, Wield.NATURAL, 2),
    ],
)
def test_power_attack_damage_bonus(bab: int, wield: Wield, expected: int) -> None:
    assert power_attack_damage_bonus(bab, wield) == expected
