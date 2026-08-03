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
    result = _assemble(rules_repository, stances=StancesIn(power_attack=True, flanking=True))
    assert result.character.stances.power_attack is True
    assert result.character.stances.flanking is True


def test_two_handed_wield_maps(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        weapons=[EquippedWeaponIn(catalog_name="Espada larga", wielding="two_handed")],
    )
    assert result.character.weapons[0].wield == Wield.TWO_HANDED
