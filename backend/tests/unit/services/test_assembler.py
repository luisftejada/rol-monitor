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
    # A longsword offers both grips, and neither makes a wizard proficient with it.
    assert all(weapon.is_proficient is False for weapon in result.character.weapons)


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
    # `name` folds the label in for anything reading the line as one string; a
    # renderer wanting the two apart gets the label on its own, unparsed.
    assert lines["Mandoble"].variant_label is None
    assert variant.variant_label == "Ataque poderoso"


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


def test_point_blank_shot_becomes_a_ranged_weapon_variant(
    rules_repository: RulesRepository,
) -> None:
    """Whether the target is within 30 feet is the GM's call, not the sheet's — so
    it is offered as a second line rather than assumed true on every shot, the same
    way a declared feat like `Puntería mortal` is."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        feats=["Disparo a bocajarro"],
        weapons=[{"catalog_name": "Arco largo", "wielding": "two_handed"}],
    )

    lines = {w.name: w for w in result.character.weapons}
    variant_name = "Arco largo (Disparo a bocajarro — sólo objetivo a 30 pies (9 m) o menos)"
    assert set(lines) == {"Arco largo", variant_name}
    variant = lines[variant_name]
    assert [(m.target, m.value) for m in variant.attack_modifiers] == [("ATTACK_RANGED", 1)]
    assert [(m.target, m.value) for m in variant.damage_modifiers] == [("DAMAGE_RANGED", 1)]
    assert lines["Arco largo"].attack_modifiers == ()

    # Its own line already carries the number; a bare warning would say the same
    # thing twice, once without one.
    assert not any("bocajarro" in warning for warning in result.warnings)


def test_point_blank_shot_produces_no_line_for_a_melee_only_character(
    rules_repository: RulesRepository,
) -> None:
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        feats=["Disparo a bocajarro"],
        weapons=[{"catalog_name": "Espada larga", "wielding": "one_handed"}],
    )
    # The grip lines are always there; what must not appear is one naming the feat.
    names = [w.name for w in result.character.weapons]
    assert names == ["Espada larga", "Espada larga (a dos manos)"]
    assert not any("bocajarro" in name for name in names)


def test_point_blank_shot_combines_with_a_declared_ranged_feat(
    rules_repository: RulesRepository,
) -> None:
    """A situational passive feat joins the same combination pool as a declared
    one, so an archer with both sees every line: base, each alone, and together."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 6}],
        feats=["Puntería mortal", "Disparo a bocajarro"],
        weapons=[{"catalog_name": "Arco largo", "wielding": "two_handed"}],
    )
    names = {w.name for w in result.character.weapons}
    condition = "sólo objetivo a 30 pies (9 m) o menos"
    assert names == {
        "Arco largo",
        f"Arco largo (Disparo a bocajarro — {condition})",
        "Arco largo (Puntería mortal)",
        f"Arco largo (Disparo a bocajarro + Puntería mortal — {condition})",
    }
    combined = next(
        w for w in result.character.weapons if "Disparo a bocajarro + Puntería mortal" in w.name
    )
    # Both feats' numbers land on the one line: +1 (bocajarro) and -2 (BAB 6 band).
    assert [m.value for m in combined.attack_modifiers] == [1, -2]
    assert [m.value for m in combined.damage_modifiers] == [1, 4]


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


def _wields(repo: RulesRepository, *, race: str, class_slug: str, weapon: str) -> bool:
    """Whether the character is proficient with ``weapon``."""
    result = _assemble(
        repo,
        race=race,
        class_levels=[{"class_slug": class_slug, "level": 3}],
        weapons=[EquippedWeaponIn(catalog_name=weapon, wielding="two_handed")],
    )
    return result.character.weapons[0].is_proficient


def test_a_racial_weapon_word_makes_an_exotic_weapon_martial(
    rules_repository: RulesRepository,
) -> None:
    """The reported bug: an elf was told they could not use an elven curve blade.
    Nothing consulted the race at all — proficiency was read off class lines only."""
    assert _wields(
        rules_repository, race="elfo", class_slug="guerrero", weapon="Espada curva élfica"
    )


def test_martial_is_not_the_same_as_proficient(rules_repository: RulesRepository) -> None:
    """ "Cuentan como marciales" stops the blade being exotic; it does not hand it
    over. A wizard has no martial weapons to begin with, elf or not."""
    assert not _wields(
        rules_repository, race="elfo", class_slug="mago", weapon="Espada curva élfica"
    )


def test_a_race_names_weapons_its_class_never_grants(rules_repository: RulesRepository) -> None:
    """The other half of familiarity: these are proficiencies outright, which is what
    lets an elf wizard hold a rapier."""
    for weapon in ("Espada ropera", "Espada larga", "Arco largo compuesto"):
        assert _wields(rules_repository, race="elfo", class_slug="mago", weapon=weapon), weapon


def test_the_word_belongs_to_one_race_only(rules_repository: RulesRepository) -> None:
    """A dwarf gets nothing from an elven weapon, and a human gets nothing from any."""
    assert not _wields(
        rules_repository, race="enano", class_slug="guerrero", weapon="Espada curva élfica"
    )
    assert not _wields(
        rules_repository, race="humano", class_slug="guerrero", weapon="Espada curva élfica"
    )


def test_a_dwarf_is_not_simply_given_their_exotic_weapons(
    rules_repository: RulesRepository,
) -> None:
    """The corpus used to list the dwarven waraxe and urgrosh as outright racial
    proficiencies. The manual only makes them martial, so a dwarf wizard cannot
    swing one — see docs/corpus/README.md."""
    assert not _wields(
        rules_repository, race="enano", class_slug="mago", weapon="Hacha de guerra enana"
    )
    assert _wields(
        rules_repository, race="enano", class_slug="guerrero", weapon="Hacha de guerra enana"
    )


def _names(result: object) -> list[str]:
    return [w.name for w in result.character.weapons]  # type: ignore[attr-defined]


def _ring(
    name: str, bonus: int, kind: str = "deflexión", slot: str = "anillo"
) -> dict[str, object]:
    return {"name": name, "slot": slot, "ac_bonus": bonus, "ac_bonus_type": kind}


def test_worn_items_carry_their_bonus_type(rules_repository: RulesRepository) -> None:
    """The type is the whole point: deflection, natural armour and worn armour are
    three different things, so all three add to the same AC."""
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        armor=EquippedArmorIn(catalog_name="Completa"),
        magic_items=[
            _ring("Anillo de protección +2", 2),
            _ring("Amuleto +1", 1, kind="armadura natural", slot="cuello"),
        ],
    )
    emitted = {
        (m.source, m.value, m.bonus_type.value if m.bonus_type else None)
        for m in result.character.modifiers
    }
    assert ("Anillo de protección +2", 2, "deflexión") in emitted
    assert ("Amuleto +1", 1, "armadura natural") in emitted


def test_an_item_in_the_backpack_grants_nothing(rules_repository: RulesRepository) -> None:
    """Which is what the slot is for — the item is owned, just not worn."""
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        magic_items=[_ring("Anillo de protección +2", 2, slot="mochila")],
    )
    assert all(m.source != "Anillo de protección +2" for m in result.character.modifiers)


def test_a_slot_carrying_more_than_it_holds_warns(rules_repository: RulesRepository) -> None:
    """The ring slot takes two, per the corpus' own "anillo (×2)". Going over is a
    house rule or a slip, so it warns rather than refusing the character."""
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        magic_items=[_ring(f"Anillo {n}", 1) for n in (1, 2, 3)],
    )
    assert any("sólo caben 2" in warning for warning in result.warnings)

    within_capacity = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        magic_items=[_ring(f"Anillo {n}", 1) for n in (1, 2)],
    )
    assert not any("caben" in warning for warning in within_capacity.warnings)


def test_stowed_items_do_not_count_against_a_slot(rules_repository: RulesRepository) -> None:
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        magic_items=[
            _ring("Anillo 1", 1),
            _ring("Anillo 2", 1),
            _ring("Anillo 3", 1, slot="mochila"),
        ],
    )
    assert not any("caben" in warning for warning in result.warnings)


def test_an_items_check_penalty_adds_to_the_armours(rules_repository: RulesRepository) -> None:
    """Penalties stack, so this one adds rather than competing with the armour's."""
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        armor=EquippedArmorIn(catalog_name="Cota de mallas"),
        magic_items=[{"name": "Guantes torpes", "slot": "manos", "armor_check_penalty": -2}],
    )
    assert result.character.item_armor_check_penalty == -2


def test_a_weapons_magic_bonus_can_be_stated_per_side(rules_repository: RulesRepository) -> None:
    """A magic weapon has one bonus for both, but the sheet lets a GM split them —
    masterwork is the standard case, and a homebrew item is the GM's business."""
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        weapons=[
            EquippedWeaponIn(catalog_name="Espada larga", attack_bonus=2, damage_bonus=1),
        ],
    )
    weapon = result.character.weapons[0]
    assert (weapon.attack_enhancement, weapon.damage_enhancement) == (2, 1)


def test_a_character_saved_before_the_split_keeps_its_magic(
    rules_repository: RulesRepository,
) -> None:
    """`enhancement_bonus` is what every stored document holds, and it means both."""
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        weapons=[EquippedWeaponIn(catalog_name="Espada larga", enhancement_bonus=3)],
    )
    weapon = result.character.weapons[0]
    assert (weapon.attack_enhancement, weapon.damage_enhancement) == (3, 3)


def test_a_one_handed_weapon_offers_both_grips(rules_repository: RulesRepository) -> None:
    """Holding a one-handed weapon in both hands is a real choice with a real payoff
    (1.5x Strength), so it earns a line of its own like a declared feat does."""
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        weapons=[EquippedWeaponIn(catalog_name="Espada larga", wielding="one_handed")],
    )
    assert _names(result) == ["Espada larga", "Espada larga (a dos manos)"]
    assert [w.wield for w in result.character.weapons] == [Wield.ONE_HANDED, Wield.TWO_HANDED]


def test_a_two_handed_weapon_is_equipped_as_such_whatever_was_stored(
    rules_repository: RulesRepository,
) -> None:
    """The editor wrote `one_handed` for everything, so a greatsword was quietly
    losing its 1.5x Strength damage. There is no second grip to offer either."""
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        weapons=[EquippedWeaponIn(catalog_name="Mandoble", wielding="one_handed")],
    )
    assert _names(result) == ["Mandoble"]
    assert result.character.weapons[0].wield is Wield.TWO_HANDED


def test_a_light_weapon_gains_nothing_from_a_second_grip(
    rules_repository: RulesRepository,
) -> None:
    """ "Usar dos manos para empuñar un arma ligera no concede ventaja al daño", so a
    second line would be an identical row."""
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        weapons=[EquippedWeaponIn(catalog_name="Daga", wielding="one_handed")],
    )
    assert _names(result) == ["Daga"]


def test_the_grip_composes_with_every_feat_variant(rules_repository: RulesRepository) -> None:
    """Two-handed *with* Power Attack is the line a player reaches for, since the
    manual raises the damage bonus by half for "un arma a una mano usando las dos
    manos" — so the grip has to be an axis, not one extra row."""
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 8}],
        base_scores={"Fue": 18, "Des": 14, "Con": 12, "Int": 13, "Sab": 10, "Car": 8},
        feats=["Ataque poderoso"],
        weapons=[EquippedWeaponIn(catalog_name="Espada larga", wielding="one_handed")],
    )
    assert _names(result) == [
        "Espada larga",
        "Espada larga (Ataque poderoso)",
        "Espada larga (a dos manos)",
        "Espada larga (a dos manos + Ataque poderoso)",
    ]


def test_the_buckler_is_the_one_shield_that_survives_a_two_handed_grip(
    rules_repository: RulesRepository,
) -> None:
    for shield, expected in (("Rodela", True), ("Escudo pesado de acero", False)):
        result = _assemble(
            rules_repository,
            class_levels=[{"class_slug": "guerrero", "level": 1}],
            shield=EquippedArmorIn(catalog_name=shield),
            weapons=[EquippedWeaponIn(catalog_name="Espada larga", wielding="one_handed")],
        )
        assert result.character.shield is not None
        assert result.character.shield.is_buckler is expected, shield


def test_weapon_finesse_reaches_the_weapon_it_covers(rules_repository: RulesRepository) -> None:
    """The reported build: an elf who took the feat for an elven curve blade. The
    weapon carries the permission; the character carries the feat."""
    result = _assemble(
        rules_repository,
        race="elfo",
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        base_scores={"Fue": 16, "Des": 18, "Con": 10, "Int": 12, "Sab": 10, "Car": 8},
        feats=["Sutileza con las armas"],
        weapons=[EquippedWeaponIn(catalog_name="Espada curva élfica", wielding="two_handed")],
    )
    assert result.character.has_weapon_finesse
    assert result.character.weapons[0].allows_finesse


def test_a_weapon_outside_the_feats_list_carries_no_permission(
    rules_repository: RulesRepository,
) -> None:
    result = _assemble(
        rules_repository,
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        feats=["Sutileza con las armas"],
        weapons=[
            EquippedWeaponIn(catalog_name="Daga", wielding="one_handed"),
            EquippedWeaponIn(catalog_name="Mandoble", wielding="two_handed"),
        ],
    )
    by_name = {w.name: w for w in result.character.weapons}
    assert by_name["Daga"].allows_finesse  # light
    assert not by_name["Mandoble"].allows_finesse


def test_the_other_two_substitutions_reach_the_character(
    rules_repository: RulesRepository,
) -> None:
    agile = _assemble(rules_repository, feats=["Maniobras ágiles"])
    assert agile.character.cmb_uses_dexterity
    assert not agile.character.cmd_uses_hit_dice

    defensive = _assemble(rules_repository, feats=["Entrenamiento en combate defensivo"])
    assert defensive.character.cmd_uses_hit_dice
    assert not defensive.character.cmb_uses_dexterity


def test_every_catalog_skill_reaches_the_sheet(rules_repository: RulesRepository) -> None:
    """A sheet lists all 35: the GM rolls Percepción at 0 ranks constantly, and the
    editor needs an ability modifier per row that TypeScript is not allowed to
    compute. Only the ones the character touched are flagged as their own."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 3}],
        skill_ranks={"intimidar": 3},
    )
    skills = result.character.skills
    assert len(skills) == len(rules_repository.skills)

    by_slug = {s.slug: s for s in skills}
    assert by_slug["intimidar"].is_tracked
    assert by_slug["intimidar"].ranks == 3
    assert not by_slug["percepcion"].is_tracked
    assert by_slug["percepcion"].ranks == 0


def test_an_unknown_skill_still_warns(rules_repository: RulesRepository) -> None:
    """Listing every catalog skill must not swallow a slug that matches none."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 1}],
        skill_ranks={"volar-alto": 1},
    )
    assert any("Habilidad desconocida: volar-alto" in w for w in result.warnings)


def test_class_armour_proficiencies_close_the_prerequisite_chain(
    rules_repository: RulesRepository,
) -> None:
    """The reason these became feats at all. A fighter is proficient with shields by
    class, but the eligibility filter matches prerequisites against *feat names*, so
    until the class handed the feat over every shield feat read as out of reach."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 6}],
        base_scores={"Fue": 16, "Des": 14, "Con": 14, "Int": 10, "Sab": 10, "Car": 8},
    )
    granted = set(result.feats.granted)
    assert "Competencia con escudo" in granted
    assert "Competencia con escudo pavés" in granted

    feats = rules_repository.feats(bab=6, abilities={"Fue": 16}, owned=list(granted))
    by_name = {f.name: f for f in feats}
    assert by_name["Golpear con el escudo mejorado"].is_eligible
    assert by_name["Soltura con el escudo"].is_eligible


def test_granted_proficiencies_cost_no_choice(rules_repository: RulesRepository) -> None:
    """A fighter is handed five feats and still picks the same number they always did;
    charging for them would have halved a level-6 fighter's budget."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "guerrero", "level": 6}],
    )
    budget = result.feats
    assert len(budget.granted) == 5
    # Base at 1/3/5, fighter at 1/2/4/6, human at 1.
    assert budget.available == 8
    assert budget.spent == 0
    assert not budget.is_over_budget


def test_a_wizard_is_granted_no_armour_proficiency(rules_repository: RulesRepository) -> None:
    """The exclusions are the half of the rule that is easy to lose: the manual grants
    light armour to everyone *except* monks, sorcerers and wizards."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[{"class_slug": "mago", "level": 6}],
    )
    assert not [f for f in result.feats.granted if f.startswith("Competencia con armadura")]


def test_a_prestige_class_contributes_its_bonus_feat_slots(
    rules_repository: RulesRepository,
) -> None:
    """The arcane knight grants a combat feat at 1, 5 and 9. Class slots are gated on
    the level *in that class*, so a wizard 5 / knight 5 has two of the three."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[
            {"class_slug": "mago", "level": 5},
            {"class_slug": "caballero_arcano", "level": 5},
        ],
    )
    budget = result.feats
    knight = [s for s in budget.slots if s.source == "Caballero arcano"]
    assert [s.level for s in knight] == [1, 5]
    assert all(s.slot.types == ["Combate"] for s in knight)


def test_a_pinned_list_stays_distinct_from_the_wider_one_it_branches_from(
    rules_repository: RulesRepository,
) -> None:
    """A sorcerer 7 / dragon disciple 2 draws from both: the union across bloodlines
    for their own slot, and the draconic branch for the disciple's. Filing both under
    the bare corpus key would let one overwrite the other."""
    result = _assemble(
        rules_repository,
        race="humano",
        class_levels=[
            {"class_slug": "hechicero", "level": 7},
            {"class_slug": "discipulo_del_dragon", "level": 2},
        ],
    )
    lists = result.feats.lists
    assert "dotes_de_linaje_hechicero" in lists
    assert "dotes_de_linaje_hechicero/draconico" in lists
    draconic = set(lists["dotes_de_linaje_hechicero/draconico"])
    assert draconic and draconic < set(lists["dotes_de_linaje_hechicero"])

    # Each slot points at the list it actually draws from.
    refs = {s.source: s.slot.list_ref for s in result.feats.slots if s.slot.list_key}
    assert refs["Hechicero"] == "dotes_de_linaje_hechicero"
    assert refs["Discípulo del dragón"] == "dotes_de_linaje_hechicero/draconico"


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
