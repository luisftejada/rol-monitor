"""Feats resolved against a specific weapon rather than the character."""

from __future__ import annotations

import pytest

from pf_tracker.domain.enums import Wield
from pf_tracker.rules.repository import RulesRepository
from pf_tracker.rules.weapon_feats import (
    FEAT_WEAPONS,
    SUPERSEDED_FEATS,
    WeaponFeatContext,
    WeaponProfile,
    critical_notes,
    drop_superseded,
    has_ongoing_target_effect,
    is_feat_stance,
    is_global_feat_target,
    is_optional,
    is_single_attack,
    is_weapon_scoped,
    resolve_for_weapon,
    widen_threat_range,
)

GREATSWORD = WeaponProfile(name="Mandoble", wield=Wield.TWO_HANDED, is_ranged=False)
LONGSWORD = WeaponProfile(name="Espada larga", wield=Wield.ONE_HANDED, is_ranged=False)
LONGBOW = WeaponProfile(name="Arco largo", wield=Wield.TWO_HANDED, is_ranged=True)


@pytest.fixture
def catalog(rules_repository: RulesRepository) -> dict[str, object]:
    return {feat.name: feat for feat in rules_repository.feats()}


# --------------------------------------------------------------- grip-aware damage
def test_power_attack_uses_the_two_handed_row_for_a_greatsword(catalog) -> None:  # type: ignore[no-untyped-def]
    """The case that motivated this: at BAB 5 the greatsword variant is -2 / +6."""
    resolved = resolve_for_weapon(
        catalog["Ataque poderoso"], GREATSWORD, WeaponFeatContext(base_attack_bonus=5)
    )
    assert [(m.target, m.value) for m in resolved.attack] == [("ATTACK_MELEE", -2)]
    assert [(m.target, m.value) for m in resolved.damage] == [("DAMAGE_MELEE", 6)]


def test_power_attack_uses_the_one_handed_row_for_a_longsword(catalog) -> None:  # type: ignore[no-untyped-def]
    resolved = resolve_for_weapon(
        catalog["Ataque poderoso"], LONGSWORD, WeaponFeatContext(base_attack_bonus=5)
    )
    assert [m.value for m in resolved.damage] == [4]


def test_power_attack_scales_with_base_attack(catalog) -> None:  # type: ignore[no-untyped-def]
    low = resolve_for_weapon(
        catalog["Ataque poderoso"], GREATSWORD, WeaponFeatContext(base_attack_bonus=1)
    )
    high = resolve_for_weapon(
        catalog["Ataque poderoso"], GREATSWORD, WeaponFeatContext(base_attack_bonus=12)
    )
    assert [m.value for m in low.attack] == [-1]
    assert [m.value for m in low.damage] == [3]
    assert [m.value for m in high.attack] == [-4]
    assert [m.value for m in high.damage] == [12]


def test_a_melee_feat_does_nothing_to_a_bow(catalog) -> None:  # type: ignore[no-untyped-def]
    resolved = resolve_for_weapon(
        catalog["Ataque poderoso"], LONGBOW, WeaponFeatContext(base_attack_bonus=5)
    )
    assert resolved.attack == () and resolved.damage == ()


# ----------------------------------------------------------- manoeuvres on the line
def test_power_attack_charges_its_penalty_to_combat_manoeuvres(catalog) -> None:  # type: ignore[no-untyped-def]
    """The corpus penalises attacks *and* manoeuvres; only the first half was applied.

    Power Attack is weapon-scoped, so it is never offered as a stance and nothing else
    could have carried the CMB half.
    """
    resolved = resolve_for_weapon(
        catalog["Ataque poderoso"], GREATSWORD, WeaponFeatContext(base_attack_bonus=5)
    )
    assert [(m.target, m.value) for m in resolved.cmb] == [("CMB", -2)]
    assert all(m.source == "Ataque poderoso" for m in resolved.cmb)


def test_the_manoeuvre_penalty_scales_with_base_attack(catalog) -> None:  # type: ignore[no-untyped-def]
    context = WeaponFeatContext(base_attack_bonus=12)
    resolved = resolve_for_weapon(catalog["Ataque poderoso"], GREATSWORD, context)
    assert [m.value for m in resolved.cmb] == [-4]


def test_combat_expertise_leaves_its_manoeuvre_penalty_to_the_stance(catalog) -> None:  # type: ignore[no-untyped-def]
    """It is offered as a stance, which already charges the CMB — charging it here
    as well would take it twice from a GM who uses both halves of the feat."""
    feat = catalog["Pericia en combate"]
    assert is_feat_stance(feat)
    resolved = resolve_for_weapon(feat, GREATSWORD, WeaponFeatContext(base_attack_bonus=5))
    assert resolved.cmb == ()
    assert [m.value for m in resolved.attack] == [-2]


def test_deadly_aim_applies_to_a_bow_only(catalog) -> None:  # type: ignore[no-untyped-def]
    context = WeaponFeatContext(base_attack_bonus=5)
    bow = resolve_for_weapon(catalog["Puntería mortal"], LONGBOW, context)
    assert [(m.target, m.value) for m in bow.attack] == [("ATTACK_RANGED", -2)]
    assert [(m.target, m.value) for m in bow.damage] == [("DAMAGE_RANGED", 4)]

    assert resolve_for_weapon(catalog["Puntería mortal"], GREATSWORD, context).attack == ()


# ------------------------------------------------------------- chosen-weapon feats
def test_weapon_focus_applies_only_to_the_chosen_weapon(catalog) -> None:  # type: ignore[no-untyped-def]
    context = WeaponFeatContext(feat_options={"Soltura con un arma": "Mandoble"})
    chosen = resolve_for_weapon(catalog["Soltura con un arma"], GREATSWORD, context)
    assert [(m.target, m.value) for m in chosen.attack] == [("ATTACK_MELEE", 1)]

    other = resolve_for_weapon(catalog["Soltura con un arma"], LONGSWORD, context)
    assert other.attack == ()


def test_weapon_focus_without_a_choice_applies_to_nothing(catalog) -> None:  # type: ignore[no-untyped-def]
    """Guessing the weapon would silently inflate whichever one happened to be first."""
    resolved = resolve_for_weapon(catalog["Soltura con un arma"], GREATSWORD, WeaponFeatContext())
    assert resolved.attack == ()


def test_weapon_specialization_adds_damage_to_the_chosen_weapon(catalog) -> None:  # type: ignore[no-untyped-def]
    context = WeaponFeatContext(feat_options={"Especialización con un arma": "Mandoble"})
    resolved = resolve_for_weapon(catalog["Especialización con un arma"], GREATSWORD, context)
    assert [(m.target, m.value) for m in resolved.damage] == [("DAMAGE_MELEE", 2)]


# ------------------------------------------------------------------- threat range
@pytest.mark.parametrize(
    ("threat_range", "factor", "expected"),
    [
        (20, 1, 20),  # untouched
        (20, 2, 19),  # 1 face -> 2
        (19, 2, 17),  # 19-20 -> 17-20
        (18, 2, 15),  # 18-20 -> 15-20
        (19, 3, 15),  # tripled, for completeness
    ],
)
def test_threat_range_doubles_its_width(threat_range: int, factor: int, expected: int) -> None:
    assert widen_threat_range(threat_range, factor) == expected


def test_improved_critical_doubles_the_weapons_threat_range(catalog) -> None:  # type: ignore[no-untyped-def]
    resolved = resolve_for_weapon(catalog["Crítico mejorado"], LONGSWORD, WeaponFeatContext())
    assert resolved.threat_range_factor == 2
    assert widen_threat_range(19, resolved.threat_range_factor) == 17


# ------------------------------------------------------------------ classification
def test_classifies_weapon_scoped_and_optional_feats(catalog) -> None:  # type: ignore[no-untyped-def]
    assert is_weapon_scoped(catalog["Ataque poderoso"])
    assert is_weapon_scoped(catalog["Soltura con un arma"])
    assert not is_weapon_scoped(catalog["Esquiva"])

    # Declared feats describe an alternative line; passive ones change the base one.
    assert is_optional(catalog["Ataque poderoso"])
    assert not is_optional(catalog["Soltura con un arma"])


def test_prose_only_feats_surface_their_rules(catalog) -> None:  # type: ignore[no-untyped-def]
    """`Disparos múltiples` carries no modifier at all, only rules text."""
    resolved = resolve_for_weapon(catalog["Disparos múltiples"], LONGBOW, WeaponFeatContext())
    assert resolved.attack == () and resolved.damage == ()
    assert any("2 flechas" in note for note in resolved.notes)


# --------------------------------------------------------------- damage dice rolls
def test_manyshot_doubles_the_first_attacks_dice_only(catalog) -> None:  # type: ignore[no-untyped-def]
    """The corpus states Manyshot only in prose, so the mechanic is keyed by name."""
    resolved = resolve_for_weapon(catalog["Disparos múltiples"], LONGBOW, WeaponFeatContext())
    assert resolved.damage_dice_multiplier == 2
    assert resolved.dice_multiplier_first_attack_only is True


def test_vital_strike_multiplies_every_attack_in_its_line(catalog) -> None:  # type: ignore[no-untyped-def]
    """`Golpe vital` is a standard action, so its line *is* the single attack."""
    resolved = resolve_for_weapon(catalog["Golpe vital"], GREATSWORD, WeaponFeatContext())
    assert resolved.damage_dice_multiplier == 2
    assert resolved.dice_multiplier_first_attack_only is False

    greater = resolve_for_weapon(catalog["Golpe vital mayor"], GREATSWORD, WeaponFeatContext())
    assert greater.damage_dice_multiplier == 4


# ------------------------------------------------------------------- supersession
def test_a_higher_feat_leaves_the_lower_one_with_no_effect(catalog) -> None:  # type: ignore[no-untyped-def]
    """Holding Vital Strike and its improved version is, in play, holding only the
    improved one. Their prerequisites force a character to hold both."""
    held = [catalog["Golpe vital"], catalog["Golpe vital mejorado"]]
    assert [f.name for f in drop_superseded(held)] == ["Golpe vital mejorado"]

    all_three = [
        catalog["Golpe vital"],
        catalog["Golpe vital mejorado"],
        catalog["Golpe vital mayor"],
    ]
    assert [f.name for f in drop_superseded(all_three)] == ["Golpe vital mayor"]


def test_supersession_leaves_unrelated_feats_alone(catalog) -> None:  # type: ignore[no-untyped-def]
    held = [catalog["Golpe vital mayor"], catalog["Ataque poderoso"], catalog["Esquiva"]]
    assert {f.name for f in drop_superseded(held)} == {
        "Golpe vital mayor",
        "Ataque poderoso",
        "Esquiva",
    }


def test_two_weapon_fighting_chain_is_not_supersession(catalog) -> None:
    """Improved TWF also requires its base feat, but adds an attack instead of
    replacing it — prerequisites alone are not the signal."""
    held = [catalog["Combate con dos armas"], catalog["Combate con dos armas mejorado"]]
    assert len(drop_superseded(held)) == 2


def test_every_declared_supersession_is_backed_by_the_corpus(
    rules_repository: RulesRepository,
) -> None:
    """The table is hand-written, so it is checked against the prose that states it."""
    catalog = {feat.name: feat for feat in rules_repository.feats()}
    for superseding, replaced in SUPERSEDED_FEATS.items():
        feat = catalog[superseding]
        prose = " ".join(rule for effect in feat.effects for rule in effect.rules).lower()
        assert "sustituye" in prose, f"{superseding} claims to supersede without saying so"
        for name in replaced:
            assert name.lower() in prose, f"{superseding} does not name {name}"


# ------------------------------------------------------------------ single attack
def test_vital_strike_is_a_single_attack(catalog) -> None:  # type: ignore[no-untyped-def]
    """It cannot be used with a full attack, so its line keeps only the top bonus."""
    assert is_single_attack(catalog["Golpe vital"])
    assert is_single_attack(catalog["Golpe vital mayor"])


def test_a_full_attack_feat_is_not_a_single_attack(catalog) -> None:  # type: ignore[no-untyped-def]
    assert not is_single_attack(catalog["Ataque poderoso"])
    assert not is_single_attack(catalog["Disparos múltiples"])


# ------------------------------------------------------------------ extra attacks
UNARMED = WeaponProfile(
    name="Impacto sin armas", wield=Wield.ONE_HANDED, is_ranged=False, is_unarmed=True
)


def test_medusas_wrath_adds_two_unarmed_attacks(catalog) -> None:  # type: ignore[no-untyped-def]
    resolved = resolve_for_weapon(
        catalog["Ira de la medusa"], UNARMED, WeaponFeatContext(base_attack_bonus=11)
    )
    assert resolved.extra_attacks_at_full_bab == 2
    # The situation cannot be checked from the sheet, so it is carried as a label.
    assert resolved.condition is not None
    assert "aturdido" in resolved.condition


def test_medusas_wrath_adds_nothing_to_a_carried_weapon(catalog) -> None:  # type: ignore[no-untyped-def]
    """Its attacks are unarmed ones; a greatsword line must not gain them."""
    resolved = resolve_for_weapon(
        catalog["Ira de la medusa"], GREATSWORD, WeaponFeatContext(base_attack_bonus=11)
    )
    assert resolved.extra_attacks_at_full_bab == 0


def test_rapid_shot_adds_its_extra_attack_as_well_as_its_penalty(catalog) -> None:  # type: ignore[no-untyped-def]
    """It used to show the -2 without the extra shot that pays for it."""
    resolved = resolve_for_weapon(
        catalog["Disparo rápido"], LONGBOW, WeaponFeatContext(base_attack_bonus=6)
    )
    assert [m.value for m in resolved.attack] == [-2]
    assert resolved.extra_attacks_at_full_bab == 1


def test_rapid_shot_adds_nothing_to_a_melee_weapon(catalog) -> None:  # type: ignore[no-untyped-def]
    resolved = resolve_for_weapon(
        catalog["Disparo rápido"], GREATSWORD, WeaponFeatContext(base_attack_bonus=6)
    )
    assert resolved.extra_attacks_at_full_bab == 0


def test_feat_weapons_name_a_real_catalog_weapon(rules_repository: RulesRepository) -> None:
    """A typo here would silently drop the line the feat is supposed to create."""
    for base in FEAT_WEAPONS.values():
        assert rules_repository.weapon(base) is not None, base


# ------------------------------------------------------------------ feat stances
def test_lunge_is_a_stance_not_an_attack_variant(catalog) -> None:  # type: ignore[no-untyped-def]
    """It changes no attack or damage number, so there is no weapon line for it —
    but the GM declares it, so it is not passive either."""
    assert is_feat_stance(catalog["Acometer"])
    resolved = resolve_for_weapon(catalog["Acometer"], GREATSWORD, WeaponFeatContext())
    assert resolved.attack == () and resolved.damage == ()


def test_a_purely_weapon_feat_is_never_also_a_stance(catalog) -> None:  # type: ignore[no-untyped-def]
    """Their whole effect lands on an attack line, so a toggle would double it."""
    for name in ("Ataque poderoso", "Puntería mortal", "Disparo rápido"):
        assert not is_feat_stance(catalog[name]), name


def test_combat_expertise_is_both_a_stance_and_a_variant(catalog) -> None:  # type: ignore[no-untyped-def]
    """Its attack penalty is per weapon and its AC bonus is not, so the two halves
    are rendered in different places — and neither is applied twice."""
    feat = catalog["Pericia en combate"]
    assert is_feat_stance(feat)

    # The weapon line carries only the attack penalty.
    resolved = resolve_for_weapon(feat, LONGSWORD, WeaponFeatContext(base_attack_bonus=8))
    assert [(m.target, m.value) for m in resolved.attack] == [("ATTACK_MELEE", -3)]

    # AC and CMB are the character's, never a weapon's.
    assert is_global_feat_target("ca")
    assert is_global_feat_target("bmc")
    assert not is_global_feat_target("ataque_cuerpo_a_cuerpo")


def test_passive_feats_are_not_stances(catalog) -> None:  # type: ignore[no-untyped-def]
    assert not is_feat_stance(catalog["Esquiva"])


# ---------------------------------------------------------------- critical feats
def test_critical_feats_become_notes(catalog) -> None:  # type: ignore[no-untyped-def]
    """They apply a condition to the target, so there is no number of yours to
    change — the line carries what happens instead."""
    notes = critical_notes([catalog["Crítico agotador"]])
    assert len(notes) == 1
    assert notes[0].startswith("Crítico agotador:")
    assert "exhausto" in notes[0]


def test_the_one_per_critical_limit_is_shown_only_when_it_bites(catalog) -> None:  # type: ignore[no-untyped-def]
    two = critical_notes([catalog["Crítico agotador"], catalog["Crítico fatigante"]])
    assert any("una dote de crítico" in note for note in two)

    # Mastery lifts the limit, so repeating it would be noise.
    with_mastery = critical_notes(
        [
            catalog["Crítico agotador"],
            catalog["Crítico fatigante"],
            catalog["Maestría con los críticos"],
        ]
    )
    assert not any("Sólo puedes aplicar" in note for note in with_mastery)

    # One feat cannot collide with itself.
    assert not any("una dote de crítico" in n for n in critical_notes([catalog["Crítico cegador"]]))


def test_a_character_without_critical_feats_gets_no_notes(catalog) -> None:  # type: ignore[no-untyped-def]
    assert critical_notes([catalog["Esquiva"], catalog["Ataque poderoso"]]) == ()


def test_a_bleed_feat_is_a_stance_even_without_a_number_of_yours(catalog) -> None:  # type: ignore[no-untyped-def]
    """`Crítico sangrante` leaves 2d6 running on the target each round. Nothing on
    your sheet changes, but the GM has to keep applying it — the toggle is the
    reminder."""
    feat = catalog["Crítico sangrante"]
    assert has_ongoing_target_effect(feat)
    assert is_feat_stance(feat)


def test_other_critical_feats_are_notes_not_stances(catalog) -> None:  # type: ignore[no-untyped-def]
    """They resolve on the hit itself; there is nothing to carry between rounds."""
    for name in ("Crítico agotador", "Crítico cegador", "Crítico aturdidor"):
        assert not is_feat_stance(catalog[name]), name


# ------------------------------------------------------------------------ mounted
# Mounted combat is deliberately out of scope for this milestone: it needs a mount
# with its own speed and charge rules, which no sheet models yet. The set is pinned
# so that making them stances (the provisional plan) forces this note to be updated.
MOUNTED_ACTIVATION = "accion_de_carga_montado"
DEFERRED_MOUNTED_FEATS = {"Ataque al galope", "Carga impetuosa", "Desmontar jinete"}


def test_mounted_feats_are_the_known_deferred_set(rules_repository: RulesRepository) -> None:
    mounted = {f.name for f in rules_repository.feats() if f.activation == MOUNTED_ACTIVATION}
    assert mounted == DEFERRED_MOUNTED_FEATS


def test_mounted_feats_are_not_yet_modelled(catalog) -> None:  # type: ignore[no-untyped-def]
    """They contribute nothing today. When they become stances, this test fails and
    whoever changes it updates docs/assumptions.md with what was decided."""
    for name in sorted(DEFERRED_MOUNTED_FEATS):
        feat = catalog[name]
        assert not is_feat_stance(feat), name
        resolved = resolve_for_weapon(feat, GREATSWORD, WeaponFeatContext(base_attack_bonus=6))
        assert resolved.attack == () and resolved.damage == (), name
