"""Coverage for derivation branches not exercised by the golden fixtures."""

from __future__ import annotations

import pytest

from pf_tracker.domain.derivation import (
    base_bab,
    derive_combat_sheet,
    iterative_bonuses,
    multiply_damage_dice,
    reduced_speed,
)
from pf_tracker.domain.enums import (
    Ability,
    BabProgression,
    ModifierTarget,
    SaveKind,
    Size,
    SourceKind,
    Wield,
)
from pf_tracker.domain.models import (
    CarryingLoad,
    Character,
    ClassLevel,
    EquippedWeapon,
    Stances,
    TwoWeaponFighting,
)
from pf_tracker.domain.modifiers import Modifier

_SAVES = {SaveKind.FORTITUDE: 0, SaveKind.REFLEX: 0, SaveKind.WILL: 0}


def _character(**overrides: object) -> Character:
    defaults: dict[str, object] = {
        "name": "t",
        "size": Size.MEDIUM,
        "base_speed_ft": 30,
        "class_levels": (ClassLevel("guerrero", "Guerrero", 6, BabProgression.FULL, 10, _SAVES),),
        "base_ability_scores": {Ability.STR: 14, Ability.DEX: 16, Ability.CON: 12},
    }
    defaults.update(overrides)
    return Character(**defaults)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("progression", "level", "expected"),
    [
        (BabProgression.FULL, 20, 20),
        (BabProgression.THREE_QUARTER, 7, 5),
        (BabProgression.HALF, 7, 3),
    ],
)
def test_base_bab(progression: BabProgression, level: int, expected: int) -> None:
    assert base_bab(progression, level) == expected


@pytest.mark.parametrize(
    ("total", "expected"),
    [(0, [0]), (1, [1]), (5, [5]), (6, [6, 1]), (11, [11, 6, 1]), (20, [20, 15, 10, 5])],
)
def test_iterative_bonuses(total: int, expected: list[int]) -> None:
    assert iterative_bonuses(total) == expected


@pytest.mark.parametrize(("base", "expected"), [(30, 20), (20, 15), (40, 30), (25, 20), (100, 95)])
def test_reduced_speed(base: int, expected: int) -> None:
    assert reduced_speed(base) == expected


def test_ranged_attack_uses_dex_and_no_strength_damage() -> None:
    bow = EquippedWeapon(
        "Arco corto",
        Wield.TWO_HANDED,
        is_ranged=True,
        threat_range=20,
        crit_multiplier=3,
        damage_dice="1d6",
    )
    sheet = derive_combat_sheet(_character(weapons=(bow,)))
    routine = sheet.attacks[0]
    # BAB 6 + Dex 3 -> +9/+4; no Strength to damage.
    assert routine.attack_line == "+9/+4"
    assert routine.damage_expression == "1d6"


def test_thrown_weapon_uses_dex_to_hit_and_strength_to_damage() -> None:
    javelin = EquippedWeapon(
        "Jabalina",
        Wield.ONE_HANDED,
        is_ranged=True,
        is_thrown=True,
        threat_range=20,
        crit_multiplier=2,
        damage_dice="1d6",
    )
    sheet = derive_combat_sheet(_character(weapons=(javelin,)))
    routine = sheet.attacks[0]
    assert routine.attack_line == "+9/+4"  # Dex to hit
    assert routine.damage_expression == "1d6+2"  # Str to damage


def test_a_line_that_costs_cmb_reports_its_own_cmb() -> None:
    """Power Attack penalises manoeuvres as well as attacks. The character's own CMB
    is untouched — the penalty is only paid while that line is the one in use."""
    penalty = Modifier(ModifierTarget.CMB.value, -2, None, "Ataque poderoso", SourceKind.FEAT)
    greatsword = EquippedWeapon(
        "Mandoble (Ataque poderoso)",
        Wield.TWO_HANDED,
        is_ranged=False,
        threat_range=19,
        crit_multiplier=2,
        damage_dice="2d6",
        cmb_modifiers=(penalty,),
    )
    sheet = derive_combat_sheet(_character(weapons=(greatsword,)))
    line_cmb = sheet.attacks[0].cmb
    assert line_cmb is not None
    # BAB 6 + Str 2 = +8 on the sheet, one worse per point of Power Attack.
    assert sheet.cmb.total == 8
    assert line_cmb.total == 6
    assert ("Ataque poderoso", -2) in [(m.source, m.value) for m in line_cmb.applied]


def test_a_line_that_does_not_touch_cmb_reports_none() -> None:
    """Absent rather than repeated: a line that changes nothing must not look like a
    second CMB the GM has to reconcile with the sheet's own."""
    weapon = EquippedWeapon(
        "Espada larga",
        Wield.ONE_HANDED,
        is_ranged=False,
        threat_range=19,
        crit_multiplier=2,
        damage_dice="1d8",
    )
    sheet = derive_combat_sheet(_character(weapons=(weapon,)))
    assert sheet.attacks[0].cmb is None


def test_offhand_iteratives_scale_with_improved_and_greater_twf() -> None:
    off = EquippedWeapon(
        "Daga",
        Wield.OFF_HAND,
        is_ranged=False,
        threat_range=19,
        crit_multiplier=2,
        damage_dice="1d4",
    )
    twf = TwoWeaponFighting(enabled=True, has_light_off_hand=True, improved=True, greater=True)
    sheet = derive_combat_sheet(_character(weapons=(off,), two_weapon_fighting=twf))
    # Three off-hand attacks (base + improved + greater), each -4 with a light off-hand.
    assert len(sheet.attacks[0].attack_bonuses) == 3


def test_non_proficiency_penalty_and_warning() -> None:
    weapon = EquippedWeapon(
        "Guja",
        Wield.TWO_HANDED,
        is_ranged=False,
        threat_range=20,
        crit_multiplier=3,
        damage_dice="1d10",
        is_proficient=False,
    )
    sheet = derive_combat_sheet(_character(weapons=(weapon,)))
    # BAB 6 + Str 2 - 4 non-proficiency -> +4/-1.
    assert sheet.attacks[0].attack_line == "+4/-1"
    assert any("no competente" in w for w in sheet.warnings)


def test_total_defense_forbids_attacks() -> None:
    weapon = EquippedWeapon(
        "Espada larga",
        Wield.ONE_HANDED,
        is_ranged=False,
        threat_range=19,
        crit_multiplier=2,
        damage_dice="1d8",
    )
    sheet = derive_combat_sheet(_character(weapons=(weapon,), stances=Stances(total_defense=True)))
    assert sheet.attacks == []
    assert any("Defensa total" in w for w in sheet.warnings)


def test_action_preventing_condition_forbids_attacks() -> None:
    weapon = EquippedWeapon(
        "Espada larga",
        Wield.ONE_HANDED,
        is_ranged=False,
        threat_range=19,
        crit_multiplier=2,
        damage_dice="1d8",
    )
    sheet = derive_combat_sheet(_character(weapons=(weapon,), conditions=("Aturdido",)))
    assert sheet.attacks == []
    assert any("No puede actuar" in w for w in sheet.warnings)


def test_carrying_capacity_reported_and_overload_warning() -> None:
    load = CarryingLoad(light_max=66, medium_max=133, heavy_max=200, carried_lb=250)
    sheet = derive_combat_sheet(_character(load=load))
    assert sheet.carrying_capacity == {"light_max": 66, "medium_max": 133, "heavy_max": 200}
    assert any("máximo pesado" in w for w in sheet.warnings)


@pytest.mark.parametrize(
    ("dice", "factor", "expected"),
    [
        ("1d8", 1, "1d8"),
        ("1d8", 2, "2d8"),
        ("2d6", 2, "4d6"),
        ("1d10", 3, "3d10"),
        ("special", 2, "special"),  # unparseable notation is left alone
    ],
)
def test_multiply_damage_dice(dice: str, factor: int, expected: str) -> None:
    assert multiply_damage_dice(dice, factor) == expected
