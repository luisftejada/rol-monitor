"""Golden-character regression tests: hand-computed values drive the engine."""

from __future__ import annotations

from typing import Any

import pytest

from pf_tracker.domain.derivation import CombatSheet, derive_combat_sheet
from pf_tracker.domain.enums import Ability, SaveKind
from tests.fixtures.loader import build_character, load_fixtures

_FIXTURES = load_fixtures()


@pytest.fixture(params=_FIXTURES, ids=[name for name, _ in _FIXTURES])
def golden(request: pytest.FixtureRequest) -> tuple[dict[str, Any], CombatSheet]:
    _name, document = request.param
    sheet = derive_combat_sheet(build_character(document["input"]))
    return document["expected"], sheet


def test_abilities(golden: tuple[dict[str, Any], CombatSheet]) -> None:
    expected, sheet = golden
    for abbr, values in expected.get("abilities", {}).items():
        result = sheet.abilities[Ability(abbr)]
        assert result.score == values["score"], f"{abbr} score"
        assert result.modifier == values["modifier"], f"{abbr} modifier"


def test_ac(golden: tuple[dict[str, Any], CombatSheet]) -> None:
    expected, sheet = golden
    ac = expected["ac"]
    assert sheet.ac.resolved.total == ac["total"]
    assert sheet.ac.touch == ac["touch"]
    assert sheet.ac.flat_footed == ac["flat_footed"]
    if "cap_binds" in ac:
        assert sheet.ac.cap_binds is ac["cap_binds"]


def test_bab(golden: tuple[dict[str, Any], CombatSheet]) -> None:
    expected, sheet = golden
    assert sheet.bab.total == expected["bab"]["total"]
    assert sheet.bab.iteratives == expected["bab"]["iteratives"]


def test_saves(golden: tuple[dict[str, Any], CombatSheet]) -> None:
    expected, sheet = golden
    for name, value in expected["saves"].items():
        assert sheet.saves[SaveKind(name)].resolved.total == value, f"save {name}"


def test_initiative_cmb_cmd(golden: tuple[dict[str, Any], CombatSheet]) -> None:
    expected, sheet = golden
    assert sheet.initiative.total == expected["initiative"]
    assert sheet.cmb.total == expected["cmb"]
    assert sheet.cmd.total == expected["cmd"]


def test_attacks(golden: tuple[dict[str, Any], CombatSheet]) -> None:
    expected, sheet = golden
    expected_attacks = expected.get("attacks", [])
    assert len(sheet.attacks) == len(expected_attacks)
    for routine, want in zip(sheet.attacks, expected_attacks, strict=True):
        assert routine.weapon_name == want["weapon"]
        assert routine.attack_line == want["line"]
        assert routine.damage_expression == want["damage"]


def test_skills(golden: tuple[dict[str, Any], CombatSheet]) -> None:
    expected, sheet = golden
    by_slug = {s.slug: s for s in sheet.skills}
    for slug, total in expected.get("skills", {}).items():
        assert by_slug[slug].resolved.total == total, f"skill {slug}"


def test_skill_columns_always_sum_to_the_total(
    golden: tuple[dict[str, Any], CombatSheet],
) -> None:
    """The sheet shows ranks, ability and "others" as three columns. If they do not
    add up to the total the GM is reading, the split is worse than not having it."""
    _, sheet = golden
    for skill in sheet.skills:
        parts = skill.ranks + skill.ability_modifier + skill.other_modifiers
        assert parts == skill.resolved.total, f"{skill.name}: {parts} != {skill.resolved.total}"


def test_derived_secondary_values(golden: tuple[dict[str, Any], CombatSheet]) -> None:
    expected, sheet = golden
    assert sheet.armor_check_penalty == expected["armor_check_penalty"]
    assert sheet.arcane_spell_failure == expected["arcane_spell_failure"]
    assert sheet.speed.final_ft == expected["speed"]


def test_warnings_contains(golden: tuple[dict[str, Any], CombatSheet]) -> None:
    expected, sheet = golden
    for needle in expected.get("warnings_contains", []):
        assert any(needle in w for w in sheet.warnings), f"missing warning: {needle}"
