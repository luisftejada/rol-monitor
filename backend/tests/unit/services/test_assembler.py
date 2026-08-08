"""Unit tests for the persisted-character -> domain assembler."""

from __future__ import annotations

from pf_tracker.domain.enums import Ability, Size, Wield
from pf_tracker.rules.repository import RulesRepository
from pf_tracker.schemas.character import (
    CharacterCreate,
    EquippedArmorIn,
    EquippedWeaponIn,
    ModifierIn,
    StancesIn,
    new_character,
)
from pf_tracker.services.assembler import assemble


def _assemble(repo: RulesRepository, **kwargs: object):
    character = new_character(CharacterCreate(**kwargs))  # type: ignore[arg-type]
    return assemble(character, repo)


def test_resolves_race_defaults_and_flexible_bonus(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        race="mediano",  # Small, Des +2 / Car +2 / Fue -2, speed 20
        racial_bonus_choices={},
        base_scores={"Fue": 12, "Des": 14, "Con": 12, "Int": 10, "Sab": 10, "Car": 10},
    )
    char = result.character
    assert char.size == Size.SMALL
    assert char.base_speed_ft == 20
    assert char.racial_ability_modifiers == {Ability.DEX: 2, Ability.CHA: 2, Ability.STR: -2}


def test_human_flexible_bonus_is_applied(rules_repository: RulesRepository) -> None:
    result = _assemble(rules_repository, race="humano", racial_bonus_choices={"Fue": 2})
    assert result.character.racial_ability_modifiers == {Ability.STR: 2}


def test_unknown_catalog_entries_warn(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        race="dragon",
        class_levels=[{"class_slug": "nope", "level": 1}],
        armor=EquippedArmorIn(catalog_name="Placas de nube"),
        weapons=[EquippedWeaponIn(catalog_name="Rayo", wielding="one_handed")],
        skill_ranks={"volar-alto": 1},
    )
    joined = " ".join(result.warnings)
    assert "Raza desconocida" in joined
    assert "Clase desconocida" in joined
    assert "Armadura" in joined
    assert "Arma desconocida" in joined
    assert "Habilidad desconocida" in joined


def test_incomplete_prestige_saves_warn_but_bab_still_derives(
    rules_repository: RulesRepository,
) -> None:
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "danzarin_sombrio", "level": 10, "is_prestige": True}],
    )
    assert any("progresión incompleta" in w for w in result.warnings)
    # BAB comes from the by-type formula, so it derives even without save rows.
    (level,) = result.character.class_levels
    assert level.base_saves == {}


def test_weapon_crit_size_and_proficiency(rules_repository: RulesRepository) -> None:
    # Small fighter with a short sword -> small damage die; fighter is proficient (marcial).
    result = _assemble(
        rules_repository,
        race="mediano",
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        weapons=[EquippedWeaponIn(catalog_name="Espada corta", wielding="one_handed")],
    )
    (weapon,) = result.character.weapons
    assert weapon.damage_dice == "1d4"  # Small
    assert (weapon.threat_range, weapon.crit_multiplier) == (19, 2)
    assert weapon.is_proficient is True


def test_wizard_not_proficient_with_martial_weapon(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "mago", "level": 1}],
        weapons=[EquippedWeaponIn(catalog_name="Espada larga", wielding="one_handed")],
    )
    (weapon,) = result.character.weapons
    assert weapon.is_proficient is False


def test_exotic_weapon_requires_feat(rules_repository: RulesRepository) -> None:
    without = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        weapons=[EquippedWeaponIn(catalog_name="Hacha de guerra enana", wielding="two_handed")],
    )
    assert without.character.weapons[0].is_proficient is False

    with_feat = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        feats=["Competencia con arma exótica"],
        weapons=[EquippedWeaponIn(catalog_name="Hacha de guerra enana", wielding="two_handed")],
    )
    assert with_feat.character.weapons[0].is_proficient is True


def test_masterwork_weapon_and_armor(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        armor=EquippedArmorIn(catalog_name="Cota de mallas", is_masterwork=True),
        weapons=[EquippedWeaponIn(catalog_name="Espada larga", is_masterwork=True)],
    )
    assert result.character.armor is not None
    assert result.character.armor.armor_check_penalty == -4  # -5 improved by masterwork
    weapon = result.character.weapons[0]
    assert any(m.value == 1 for m in weapon.attack_modifiers)  # masterwork +1 to attack


def test_enhancement_adds_to_armor_bonus(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        armor=EquippedArmorIn(catalog_name="Cota de mallas", enhancement_bonus=2),
    )
    assert result.character.armor is not None
    assert result.character.armor.ac_bonus == 8  # base 6 + 2 enhancement


def test_two_weapon_fighting_detection(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "picaro", "level": 5}],
        feats=["Combate con dos armas"],
        weapons=[
            EquippedWeaponIn(catalog_name="Espada corta", wielding="one_handed"),
            EquippedWeaponIn(catalog_name="Espada corta", wielding="off_hand"),
        ],
    )
    twf = result.character.two_weapon_fighting
    assert twf.enabled is True
    assert twf.has_light_off_hand is True  # short sword is a light weapon
    assert twf.has_twf_feat is True


def test_custom_override_forces_proficiency(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "mago", "level": 1}],
        weapons=[
            EquippedWeaponIn(
                catalog_name="Espada larga",
                wielding="one_handed",
                custom_overrides={"is_proficient": True},
            )
        ],
    )
    assert result.character.weapons[0].is_proficient is True


def test_conditions_map_and_flat_footed_flag(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        active_conditions=["fatigado"],
        is_flat_footed=True,
    )
    assert "Fatigado" in result.character.conditions
    assert "Desprevenido" in result.character.conditions


def test_modifiers_and_active_effects_are_collected(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        modifiers=[
            ModifierIn(
                target="AC", value=1, bonus_type="esquiva", source="Esquiva", source_kind="feat"
            )
        ],
        active_effects=[
            {
                "name": "Bendecir",
                "modifiers": [
                    {
                        "target": "ALL_ATTACKS",
                        "value": 1,
                        "bonus_type": "moral",
                        "source": "Bendecir",
                        "source_kind": "spell",
                    }
                ],
            }
        ],
    )
    sources = {m.source for m in result.character.modifiers}
    assert {"Esquiva", "Bendecir"} <= sources


def test_load_thresholds_from_strength(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        race="humano",
        racial_bonus_choices={"Fue": 2},
        base_scores={"Fue": 13, "Des": 12, "Con": 12, "Int": 10, "Sab": 10, "Car": 10},
        load_carried_lb=120.0,
    )
    load = result.character.load
    assert load is not None
    # Strength 15 -> heavy max 200.
    assert (load.light_max, load.heavy_max) == (66, 200)


def test_stances_pass_through(rules_repository: RulesRepository) -> None:
    result = _assemble(rules_repository, stances=StancesIn(charge=True, flanking=True))
    assert result.character.stances.charge is True
    assert result.character.stances.flanking is True


def test_two_handed_wield_maps(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        weapons=[EquippedWeaponIn(catalog_name="Espada larga", wielding="two_handed")],
    )
    assert result.character.weapons[0].wield == Wield.TWO_HANDED


def test_passive_feats_contribute_modifiers(rules_repository: RulesRepository) -> None:
    """The gap this closes: before the corpus carried machine-readable effects,
    `Esquiva` and `Iniciativa mejorada` were stored but did nothing."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 5}],
        feats=["Esquiva", "Iniciativa mejorada"],
    )
    emitted = {(m.source, m.target, m.value) for m in result.character.modifiers}
    assert ("Esquiva", "AC", 1) in emitted
    assert ("Iniciativa mejorada", "INITIATIVE", 4) in emitted


def test_a_declared_feat_becomes_a_weapon_variant_not_a_global_modifier(
    rules_repository: RulesRepository,
) -> None:
    """A greatsword with Power Attack is a second way of using the same weapon, so
    the sheet lists both lines instead of applying a penalty to everything."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 5}],
        feats=["Ataque poderoso"],
        weapons=[{"catalog_name": "Mandoble", "wielding": "two_handed"}],
    )

    assert all(m.source != "Ataque poderoso" for m in result.character.modifiers)

    lines = {w.name: w for w in result.character.weapons}
    assert set(lines) == {"Mandoble", "Mandoble (Ataque poderoso)"}
    variant = lines["Mandoble (Ataque poderoso)"]
    # BAB 5 lands in the +4..+7 band: -2 to hit, +6 damage two-handed.
    assert [m.value for m in variant.attack_modifiers] == [-2]
    assert [m.value for m in variant.damage_modifiers] == [6]
    # The same -2 applies to combat manoeuvres, and only while this line is in use.
    assert [(m.target, m.value) for m in variant.cmb_modifiers] == [("CMB", -2)]
    assert lines["Mandoble"].attack_modifiers == ()
    assert lines["Mandoble"].cmb_modifiers == ()


def test_weapon_variants_cover_every_combination(rules_repository: RulesRepository) -> None:
    """An archer with both ranged feats gets base, each feat, and both together."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 6}],
        feats=["Puntería mortal", "Disparo rápido"],
        weapons=[{"catalog_name": "Arco largo", "wielding": "two_handed"}],
    )
    # Combination labels follow catalog order, which is stable no matter how the
    # player happened to order their feats.
    names = [w.name for w in result.character.weapons]
    assert names == [
        "Arco largo",
        "Arco largo (Disparo rápido)",
        "Arco largo (Puntería mortal)",
        "Arco largo (Disparo rápido + Puntería mortal)",
    ]


def test_a_chosen_weapon_feat_only_changes_that_weapon(
    rules_repository: RulesRepository,
) -> None:
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 5}],
        feats=["Soltura con un arma"],
        feat_options={"Soltura con un arma": "Mandoble"},
        weapons=[
            {"catalog_name": "Mandoble", "wielding": "two_handed"},
            {"catalog_name": "Espada larga", "wielding": "one_handed"},
        ],
    )
    lines = {w.name: w for w in result.character.weapons}
    assert [m.value for m in lines["Mandoble"].attack_modifiers] == [1]
    assert lines["Espada larga"].attack_modifiers == ()


def test_improved_critical_widens_the_threat_range(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 5}],
        feats=["Crítico mejorado"],
        weapons=[{"catalog_name": "Espada larga", "wielding": "one_handed"}],
    )
    # The longsword threatens on 19-20; doubled, that is 17-20.
    assert result.character.weapons[0].threat_range == 17


def test_a_character_without_feats_gains_nothing(rules_repository: RulesRepository) -> None:
    result = _assemble(rules_repository, race="humano", feats=[])
    assert result.character.modifiers == ()


def test_manyshot_doubles_the_first_arrow_only(rules_repository: RulesRepository) -> None:
    """`1d8` on the first attack becomes `2d8`; the iteratives stay `1d8`."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 6}],
        base_scores={"Fue": 12, "Des": 18, "Con": 12, "Int": 10, "Sab": 10, "Car": 10},
        feats=["Disparos múltiples"],
        weapons=[EquippedWeaponIn(catalog_name="Arco largo", wielding="two_handed")],
    )
    lines = {w.name: w for w in result.character.weapons}
    variant = lines["Arco largo (Disparos múltiples)"]
    assert variant.damage_dice_multiplier == 2
    assert variant.dice_multiplier_first_attack_only is True
    # The plain line is untouched.
    assert lines["Arco largo"].damage_dice_multiplier == 1


def test_vital_strike_family_yields_one_single_attack_line(
    rules_repository: RulesRepository,
) -> None:
    """Prerequisites force a character to hold all three, so without supersession the
    sheet would multiply them into x24 dice across eight lines."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 16}],
        base_scores={"Fue": 18, "Des": 12, "Con": 14, "Int": 10, "Sab": 10, "Car": 8},
        feats=["Golpe vital", "Golpe vital mejorado", "Golpe vital mayor"],
        weapons=[EquippedWeaponIn(catalog_name="Mandoble", wielding="two_handed")],
    )
    lines = {w.name: w for w in result.character.weapons}
    assert set(lines) == {"Mandoble", "Mandoble (Golpe vital mayor)"}

    variant = lines["Mandoble (Golpe vital mayor)"]
    assert variant.damage_dice_multiplier == 4
    # It cannot be used with a full attack, so the iteratives are gone.
    assert variant.single_attack is True
    assert lines["Mandoble"].single_attack is False


def test_medusas_wrath_is_its_own_weapon_line(rules_repository: RulesRepository) -> None:
    """A full attack cannot mix armed and unarmed strikes, so the feat is a line of
    its own built from the unarmed strike rather than a variant of the sword."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "monje", "level": 11}],
        base_scores={"Fue": 16, "Des": 16, "Con": 12, "Int": 10, "Sab": 14, "Car": 8},
        feats=[
            "Impacto sin arma mejorado",
            "Puño del gorgón",
            "Estilo del escorpión",
            "Ira de la medusa",
        ],
        weapons=[EquippedWeaponIn(catalog_name="Espada larga", wielding="one_handed")],
    )
    lines = {w.name.split(" (")[0]: w for w in result.character.weapons}
    assert set(lines) == {"Espada larga", "Impacto sin armas"}

    unarmed = lines["Impacto sin armas"]
    assert unarmed.extra_attacks_at_full_bab == 2
    assert unarmed.is_unarmed is True
    # Improved Unarmed Strike is what makes a monk proficient with their own fists.
    assert unarmed.is_proficient is True
    # The situation it depends on is part of the line's name.
    assert "aturdido" in next(w.name for w in result.character.weapons if w.is_unarmed)

    # The sword keeps its own routine, untouched by an unarmed feat.
    assert lines["Espada larga"].extra_attacks_at_full_bab == 0


def test_rapid_shot_line_gains_the_extra_shot(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 6}],
        feats=["Disparo rápido"],
        weapons=[EquippedWeaponIn(catalog_name="Arco largo", wielding="two_handed")],
    )
    variant = next(w for w in result.character.weapons if "Disparo rápido" in w.name)
    assert variant.extra_attacks_at_full_bab == 1


def test_a_feat_stance_applies_only_when_switched_on(rules_repository: RulesRepository) -> None:
    """`Acometer` costs 2 AC for reach; the -2 comes from the corpus, not a literal."""

    def ac_of(stances: object) -> int:
        result = _assemble(
            rules_repository,
            race="humano",
            class_levels=[{"class_slug": "guerrero", "level": 6}],
            feats=["Acometer"],
            stances=stances,
        )
        return sum(m.value for m in result.character.modifiers if m.target == "AC")

    assert ac_of(StancesIn()) == 0
    assert ac_of(StancesIn(feat_stances=["Acometer"])) == -2


def test_combat_expertise_splits_across_the_stance_and_the_weapon_line(
    rules_repository: RulesRepository,
) -> None:
    """Switching it on must raise AC and lower CMB once, without touching the attack
    penalty that already lives on the weapon variant."""

    def build(stances: object):
        return _assemble(
            rules_repository,
            race="humano",
            class_levels=[{"class_slug": "guerrero", "level": 8}],
            base_scores={"Fue": 16, "Des": 14, "Con": 14, "Int": 13, "Sab": 10, "Car": 8},
            feats=["Pericia en combate"],
            stances=stances,
            weapons=[EquippedWeaponIn(catalog_name="Espada larga", wielding="one_handed")],
        ).character

    off = build(StancesIn())
    on = build(StancesIn(feat_stances=["Pericia en combate"]))

    def total(character: object, target: str) -> int:
        return sum(m.value for m in character.modifiers if m.target == target)  # type: ignore[attr-defined]

    # BAB 8 falls in the +8..+11 band: -3 attack, +3 AC, -3 CMB.
    assert total(off, "AC") == 0 and total(off, "CMB") == 0
    assert total(on, "AC") == 3
    assert total(on, "CMB") == -3
    # The attack penalty is not emitted globally; it stays on the variant.
    assert total(on, "ATTACK_MELEE") == 0
    variant = next(w for w in on.weapons if "Pericia en combate" in w.name)
    assert [m.value for m in variant.attack_modifiers] == [-3]
    # ...and the CMB penalty stays on the stance, or ticking the box and reading the
    # line would take it twice.
    assert variant.cmb_modifiers == ()


def test_a_feat_stance_needs_the_feat(rules_repository: RulesRepository) -> None:
    """Switching on a stance for a feat the character lacks must change nothing."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 6}],
        feats=[],
        stances=StancesIn(feat_stances=["Acometer"]),
    )
    assert result.character.modifiers == ()


def test_critical_feats_annotate_every_line_of_the_weapon(
    rules_repository: RulesRepository,
) -> None:
    """A critical feat fires with whatever you are holding, so the base line and its
    variants all carry it."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 15}],
        base_scores={"Fue": 18, "Des": 14, "Con": 14, "Int": 10, "Sab": 10, "Car": 8},
        feats=["Soltura con los críticos", "Crítico agotador", "Ataque poderoso"],
        weapons=[EquippedWeaponIn(catalog_name="Espada larga", wielding="one_handed")],
    )
    for weapon in result.character.weapons:
        assert any("exhausto" in note for note in weapon.notes), weapon.name

    # It is prose, not a number: nothing on the sheet moved.
    assert all(m.source != "Crítico agotador" for m in result.character.modifiers)


def test_a_bleed_stance_changes_none_of_your_numbers(rules_repository: RulesRepository) -> None:
    """The damage lands on the opponent, so switching it on must not move the sheet."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 11}],
        feats=["Soltura con los críticos", "Crítico sangrante"],
        stances=StancesIn(feat_stances=["Crítico sangrante"]),
        weapons=[EquippedWeaponIn(catalog_name="Espada larga", wielding="one_handed")],
    )
    assert result.character.modifiers == ()
    # It is still announced on the weapon line, where the crit is confirmed.
    assert any("sangrante" in note.lower() for note in result.character.weapons[0].notes)
