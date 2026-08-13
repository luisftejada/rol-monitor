"""Coverage for derivation branches not exercised by the golden fixtures."""

from __future__ import annotations

from dataclasses import replace

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
    skill_target,
)
from pf_tracker.domain.models import (
    CarryingLoad,
    Character,
    ClassLevel,
    EquippedArmor,
    EquippedWeapon,
    SkillState,
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


def _finesse_weapon(name: str = "Espada ropera") -> EquippedWeapon:
    return EquippedWeapon(
        name,
        Wield.ONE_HANDED,
        is_ranged=False,
        threat_range=18,
        crit_multiplier=2,
        damage_dice="1d6",
        allows_finesse=True,
    )


def test_weapon_finesse_attacks_with_dexterity_and_still_damages_with_strength() -> None:
    """The reported gap: melee always used Strength, so the feat did nothing at all.
    Dex 16 (+3) beats Str 14 (+2) to hit; damage is untouched, as the corpus says."""
    character = _character(weapons=(_finesse_weapon(),), has_weapon_finesse=True)
    routine = derive_combat_sheet(character).attacks[0]

    assert ("Destreza", 3) in [(m.source, m.value) for m in routine.attack_breakdown.applied]
    assert "Fuerza" not in [m.source for m in routine.attack_breakdown.applied]
    # BAB 6 + Dex 3 -> +9/+4, where Strength would have given +8/+3.
    assert routine.attack_line == "+9/+4"
    assert ("Fuerza", 2) in [(m.source, m.value) for m in routine.damage_breakdown.applied]


def test_weapon_finesse_never_makes_an_attack_worse() -> None:
    """The feat says you *may* use Dexterity. A Strength build who took it for one
    weapon must not find their good attacks downgraded."""
    character = _character(
        weapons=(_finesse_weapon(),),
        has_weapon_finesse=True,
        base_ability_scores={Ability.STR: 20, Ability.DEX: 12, Ability.CON: 12},
    )
    routine = derive_combat_sheet(character).attacks[0]
    assert ("Fuerza", 5) in [(m.source, m.value) for m in routine.attack_breakdown.applied]


def test_weapon_finesse_leaves_weapons_it_does_not_cover_alone() -> None:
    greatsword = EquippedWeapon(
        "Mandoble", Wield.TWO_HANDED, is_ranged=False, threat_range=19, crit_multiplier=2
    )
    character = _character(weapons=(greatsword,), has_weapon_finesse=True)
    routine = derive_combat_sheet(character).attacks[0]
    assert "Fuerza" in [m.source for m in routine.attack_breakdown.applied]


def test_a_shield_is_the_price_of_finessing() -> None:
    """ "Si llevas escudo, su penalizador por armadura se aplica a tus tiradas de
    ataque." With a big enough penalty that makes Strength the better line again."""
    light = EquippedArmor(
        name="Escudo ligero de acero",
        is_shield=True,
        ac_bonus=1,
        max_dex=None,
        armor_check_penalty=-1,
        arcane_spell_failure=5,
        category="escudo",
    )
    # Dex 3 - 1 = 2 still beats Str 2? No: the tie goes to Strength, which costs
    # nothing. Drop Dexterity by one more and the shield decides it outright.
    character = _character(weapons=(_finesse_weapon(),), has_weapon_finesse=True, shield=light)
    applied = derive_combat_sheet(character).attacks[0].attack_breakdown.applied
    assert ("Fuerza", 2) in [(m.source, m.value) for m in applied]

    # With a shield light enough to keep Dexterity ahead, the penalty is charged and
    # shown rather than quietly folded into the total.
    heavy_dex = _character(
        weapons=(_finesse_weapon(),),
        has_weapon_finesse=True,
        shield=light,
        base_ability_scores={Ability.STR: 10, Ability.DEX: 18, Ability.CON: 12},
    )
    applied = derive_combat_sheet(heavy_dex).attacks[0].attack_breakdown.applied
    assert ("Destreza", 4) in [(m.source, m.value) for m in applied]
    assert ("Escudo (Sutileza con las armas)", -1) in [(m.source, m.value) for m in applied]


def test_agile_maneuvers_swaps_the_ability_behind_cmb_only() -> None:
    """Unlike Weapon Finesse there is no weapon to qualify and no shield clause, so
    it applies as stated rather than as the better of the two."""
    plain = derive_combat_sheet(_character())
    agile = derive_combat_sheet(_character(cmb_uses_dexterity=True))

    assert ("Fuerza", 2) in [(m.source, m.value) for m in plain.cmb.applied]
    assert ("Destreza", 3) in [(m.source, m.value) for m in agile.cmb.applied]
    # "No afecta a tu DMC": CMD still counts Strength *and* Dexterity as it always did.
    assert agile.cmd.total == plain.cmd.total


def test_defensive_combat_training_counts_hit_dice_for_cmd_only() -> None:
    """Worth taking precisely when base attack lags behind level, so the test uses a
    half-progression class where the two differ."""
    wizard = ClassLevel("mago", "Mago", 8, BabProgression.HALF, 6, _SAVES)
    plain = derive_combat_sheet(_character(class_levels=(wizard,)))
    trained = derive_combat_sheet(_character(class_levels=(wizard,), cmd_uses_hit_dice=True))

    # BAB 4 at level 8, so the swap is worth four points.
    assert ("Ataque base", 4) in [(m.source, m.value) for m in plain.cmd.applied]
    assert ("Dados de Golpe", 8) in [(m.source, m.value) for m in trained.cmd.applied]
    assert trained.cmd.total == plain.cmd.total + 4
    # "No afecta a tu BMC ni a tus tiradas de ataque."
    assert trained.cmb.total == plain.cmb.total


def _shield(name: str, *, is_buckler: bool, ac_bonus: int = 2, acp: int = -2) -> EquippedArmor:
    return EquippedArmor(
        name=name,
        is_shield=True,
        ac_bonus=ac_bonus,
        max_dex=None,
        armor_check_penalty=acp,
        arcane_spell_failure=15,
        category="escudo",
        is_buckler=is_buckler,
    )


def _greatsword() -> EquippedWeapon:
    return EquippedWeapon(
        "Mandoble",
        Wield.TWO_HANDED,
        is_ranged=False,
        threat_range=19,
        crit_multiplier=2,
        damage_dice="2d6",
    )


def test_a_two_handed_line_gives_up_the_shield_it_cannot_hold() -> None:
    """The sheet's own AC assumes you are holding the shield. On a line that needs
    both hands you are not, so the line carries the AC you actually have."""
    character = _character(
        weapons=(_greatsword(),), shield=_shield("Escudo pesado", is_buckler=False)
    )
    sheet = derive_combat_sheet(character)
    line = sheet.attacks[0]

    assert line.ac is not None
    assert sheet.ac.resolved.total == line.ac.resolved.total + 2
    # Re-derived rather than subtracted, so flat-footed loses the shield too.
    assert sheet.ac.flat_footed == line.ac.flat_footed + 2
    assert "Escudo pesado" not in [m.source for m in line.ac.resolved.applied]


def test_a_buckler_stays_on_and_charges_one_instead() -> None:
    """It straps to the forearm, so it is the one shield a two-handed grip keeps —
    at -1 to attack for the arm it occupies."""
    character = _character(weapons=(_greatsword(),), shield=_shield("Rodela", is_buckler=True))
    line = derive_combat_sheet(character).attacks[0]

    assert line.ac is None  # the shield is still yours
    assert ("Rodela (mano ocupada)", -1) in [
        (m.source, m.value) for m in line.attack_breakdown.applied
    ]


def test_a_one_handed_line_keeps_the_shield_and_pays_nothing() -> None:
    sword = EquippedWeapon(
        "Espada larga", Wield.ONE_HANDED, is_ranged=False, threat_range=19, crit_multiplier=2
    )
    for shield in (_shield("Escudo pesado", is_buckler=False), _shield("Rodela", is_buckler=True)):
        line = derive_combat_sheet(_character(weapons=(sword,), shield=shield)).attacks[0]
        assert line.ac is None, shield.name
        assert not any("Rodela" in m.source for m in line.attack_breakdown.applied)


def test_a_bow_is_held_in_two_hands_but_keeps_the_shield() -> None:
    """No rule ties a shield to a ranged weapon's grip, and stripping it would cost
    an archer two AC the manual never charges."""
    bow = EquippedWeapon(
        "Arco largo",
        Wield.TWO_HANDED,
        is_ranged=True,
        threat_range=20,
        crit_multiplier=3,
        damage_dice="1d8",
    )
    character = _character(weapons=(bow,), shield=_shield("Escudo pesado", is_buckler=False))
    assert derive_combat_sheet(character).attacks[0].ac is None


def test_a_skill_splits_into_ranks_ability_and_everything_else() -> None:
    """The three columns the sheet shows. "Others" is a residue by construction —
    total minus the two named parts — so nothing can fall between the columns."""
    bonus = Modifier(skill_target("intimidar"), 2, None, "Persuasivo", SourceKind.FEAT)
    skill = SkillState(
        slug="intimidar",
        name="Intimidar",
        ability=Ability.CHA,
        ranks=3,
        is_class_skill=True,
    )
    # Cha 8 -> -1; class skill with ranks -> +3; the feat -> +2.
    character = _character(
        skills=(skill,),
        base_ability_scores={Ability.STR: 14, Ability.DEX: 16, Ability.CON: 12, Ability.CHA: 8},
        modifiers=(bonus,),
    )
    line = derive_combat_sheet(character).skills[0]

    assert line.ranks == 3
    assert line.ability_modifier == -1
    assert line.other_modifiers == 5  # class skill 3 + Persuasivo 2
    assert line.resolved.total == 7
    # The itemised breakdown behind "others" excludes ranks and the ability
    # modifier: they already have their own columns, so repeating them here would
    # just restate numbers the GM can already see.
    assert {(m.source, m.value) for m in line.other_applied} == {
        ("Habilidad de clase", 3),
        ("Persuasivo", 2),
    }


def test_an_ability_names_itself_in_spanish_in_a_breakdown() -> None:
    """Breakdown labels are shown to the GM beside corpus strings like "Cota de
    escamas", so an English enum name reads as a bug."""
    skill = SkillState(slug="trepar", name="Trepar", ability=Ability.STR)
    line = derive_combat_sheet(_character(skills=(skill,))).skills[0]
    assert "Fuerza" in [m.source for m in line.resolved.applied]


def test_an_untrained_skill_only_warns_when_the_character_invested_in_it() -> None:
    """Every skill is on the sheet now, so warning on bare absence would fire two
    dozen times for a character who has simply not trained everything."""
    untouched = SkillState(
        slug="descifrar-escritura",
        name="Descifrar escritura",
        ability=Ability.INT,
        untrained=False,
        is_tracked=False,
    )
    invested = replace(untouched, misc_modifier=2, is_tracked=True)

    quiet = derive_combat_sheet(_character(skills=(untouched,)))
    assert quiet.warnings == []
    assert quiet.skills[0].untrained_violation is True  # still flagged on the line

    loud = derive_combat_sheet(_character(skills=(invested,)))
    assert any("sin entrenamiento" in w for w in loud.warnings)


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
