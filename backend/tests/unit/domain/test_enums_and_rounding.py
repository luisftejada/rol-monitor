"""Tests for target matching and the shared rounding helper."""

from __future__ import annotations

from fractions import Fraction

import pytest

from pf_tracker.domain.enums import (
    Ability,
    ModifierTarget,
    ability_target,
    skill_target,
    target_matches,
)
from pf_tracker.domain.rounding import round_down, scaled


def test_exact_and_group_target_matching() -> None:
    assert target_matches(ModifierTarget.AC.value, ModifierTarget.AC.value)
    assert target_matches(ModifierTarget.ALL_SAVES.value, ModifierTarget.SAVE_FORT.value)
    assert not target_matches(ModifierTarget.SAVE_FORT.value, ModifierTarget.SAVE_REF.value)


def test_all_skills_and_all_checks_matching() -> None:
    acro = skill_target("acrobacias")
    assert target_matches(ModifierTarget.ALL_SKILLS.value, acro)
    assert target_matches(ModifierTarget.ALL_CHECKS.value, acro)
    assert target_matches(ModifierTarget.ALL_CHECKS.value, ModifierTarget.SAVE_WILL.value)
    assert not target_matches(ModifierTarget.ALL_CHECKS.value, ModifierTarget.AC.value)
    assert not target_matches(ModifierTarget.ALL_SKILLS.value, ModifierTarget.SAVE_WILL.value)


def test_ability_target_string() -> None:
    assert ability_target(Ability.STR) == "ABILITY:Fue"


@pytest.mark.parametrize(
    ("value", "expected"),
    [(Fraction(-3, 2), -2), (Fraction(3, 2), 1), (Fraction(4, 1), 4), (7, 7), (-7, -7)],
)
def test_round_down(value: Fraction | int, expected: int) -> None:
    assert round_down(value) == expected


def test_scaled() -> None:
    assert scaled(3, Fraction(3, 2)) == 4
    assert scaled(-1, Fraction(3, 2)) == -2
    assert scaled(3, Fraction(1, 2)) == 1
