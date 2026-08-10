"""Feats that replace a term of a formula rather than adding to it."""

from __future__ import annotations

import pytest

from pf_tracker.rules.feat_substitutions import (
    SUBSTITUTION_TARGETS,
    SUBSTITUTION_TERMS,
    allows_finesse,
    resolve_substitutions,
)
from pf_tracker.rules.repository import RulesRepository


@pytest.fixture
def catalog(rules_repository: RulesRepository) -> dict[str, object]:
    return {feat.name: feat for feat in rules_repository.feats()}


def test_each_feat_resolves_to_the_term_it_swaps(catalog) -> None:  # type: ignore[no-untyped-def]
    finesse = resolve_substitutions([catalog["Sutileza con las armas"]])  # type: ignore[list-item]
    assert finesse.melee_attack_uses_dexterity
    assert not finesse.cmb_uses_dexterity and not finesse.cmd_uses_hit_dice

    agile = resolve_substitutions([catalog["Maniobras ágiles"]])  # type: ignore[list-item]
    assert agile.cmb_uses_dexterity
    # The corpus says so in as many words: "No afecta a tu DMC."
    assert not agile.cmd_uses_hit_dice and not agile.melee_attack_uses_dexterity

    defensive = resolve_substitutions([catalog["Entrenamiento en combate defensivo"]])  # type: ignore[list-item]
    assert defensive.cmd_uses_hit_dice
    # "No afecta a tu BMC ni a tus tiradas de ataque."
    assert not defensive.cmb_uses_dexterity and not defensive.melee_attack_uses_dexterity


def test_a_character_with_no_such_feat_swaps_nothing(catalog) -> None:  # type: ignore[no-untyped-def]
    resolved = resolve_substitutions([catalog["Esquiva"], catalog["Ataque poderoso"]])  # type: ignore[list-item]
    assert resolved == resolve_substitutions([])


@pytest.mark.parametrize(
    ("category", "name", "expected"),
    [
        ("Armas cuerpo a cuerpo ligeras", "Daga", True),
        # Natural weapons count as light "a estos efectos".
        ("Ataques sin armas", "Impacto sin armas", True),
        # The four the feat names, none of which is light.
        ("Armas cuerpo a cuerpo a una mano", "Espada ropera", True),
        ("Armas cuerpo a cuerpo a una mano", "Látigo", True),
        ("Armas cuerpo a cuerpo a dos manos", "Espada curva élfica", True),
        ("Armas cuerpo a cuerpo a dos manos", "Cadena armada", True),
        # A one-handed weapon it does not name, and a two-handed one.
        ("Armas cuerpo a cuerpo a una mano", "Espada larga", False),
        ("Armas cuerpo a cuerpo a dos manos", "Mandoble", False),
    ],
)
def test_which_weapons_weapon_finesse_covers(category: str, name: str, expected: bool) -> None:
    assert allows_finesse(category=category, name=name) is expected


def test_the_declared_vocabulary_covers_the_whole_corpus(
    rules_repository: RulesRepository,
) -> None:
    """A substitution added to the corpus with an unknown term would resolve to
    nothing at all — which is exactly how this block sat unread until a player
    noticed their Dexterity build attacking with Strength."""
    for feat in rules_repository.feats():
        for effect in feat.effects:
            for swap in effect.substitutions:
                assert swap.target in SUBSTITUTION_TARGETS, f"{feat.name}: {swap.target}"
                assert swap.use in SUBSTITUTION_TERMS, f"{feat.name}: {swap.use}"
                assert swap.instead_of in SUBSTITUTION_TERMS, f"{feat.name}: {swap.instead_of}"


def test_the_three_feats_that_carry_a_substitution_are_the_ones_we_think(
    rules_repository: RulesRepository,
) -> None:
    """Pins the set: a fourth would silently do nothing until someone wired it."""
    carriers = {
        feat.name
        for feat in rules_repository.feats()
        for effect in feat.effects
        if effect.substitutions
    }
    assert carriers == {
        "Sutileza con las armas",
        "Maniobras ágiles",
        "Entrenamiento en combate defensivo",
    }
