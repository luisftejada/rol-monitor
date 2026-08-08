"""The feats corpus and the stacking engine spell bonus types differently; these
tests pin the translation and fail loudly if the corpus grows a token we cannot map.
"""

from __future__ import annotations

from typing import Any

import pytest

from pf_tracker.domain.enums import ALWAYS_STACKING, BonusType
from pf_tracker.rules.feat_vocabulary import (
    KNOWN_FEAT_BONUSES,
    NON_SCALAR_FEAT_BONUSES,
    UnknownFeatBonusTypeError,
    is_scalar_feat_bonus,
    parse_feat_bonus_type,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        # The five that differ between the two vocabularies.
        ("mejora", BonusType.ENHANCEMENT),
        ("perspicacia", BonusType.INSIGHT),
        ("natural", BonusType.NATURAL_ARMOR),
        ("alquimico", BonusType.ALCHEMICAL),
        ("tamano", BonusType.SIZE),
        # And a couple that happen to agree.
        ("esquiva", BonusType.DODGE),
        ("escudo", BonusType.SHIELD),
    ],
)
def test_maps_feat_vocabulary_onto_domain_bonus_types(raw: str, expected: BonusType) -> None:
    assert parse_feat_bonus_type(raw) is expected


@pytest.mark.parametrize("raw", ["sin_tipo", "penalizador"])
def test_untyped_and_penalties_carry_no_bonus_type(raw: str) -> None:
    """Penalties stack and are deduplicated by source; the engine reads their sign."""
    assert parse_feat_bonus_type(raw) is None


@pytest.mark.parametrize("raw", sorted(NON_SCALAR_FEAT_BONUSES))
def test_non_scalar_markers_are_rejected_rather_than_treated_as_untyped(raw: str) -> None:
    """Mapping "x2" to untyped would add a multiplier as if it were a flat bonus."""
    assert not is_scalar_feat_bonus(raw)
    with pytest.raises(UnknownFeatBonusTypeError):
        parse_feat_bonus_type(raw)


def test_unknown_token_raises() -> None:
    with pytest.raises(UnknownFeatBonusTypeError):
        parse_feat_bonus_type("no_existe")


def test_every_declared_feat_bonus_type_is_mapped(nucleo_raw: dict[str, Any]) -> None:
    """Covers the corpus' own declaration in ``esquema_efectos.tipos_bonificador``."""
    declared = nucleo_raw["dotes"]["esquema_efectos"]["tipos_bonificador"]
    tokens = set(declared["apilan_siempre"]) | set(declared["no_apilan_consigo_mismos"])
    assert tokens <= KNOWN_FEAT_BONUSES, f"unmapped: {sorted(tokens - KNOWN_FEAT_BONUSES)}"


def test_every_bonus_type_used_by_a_feat_is_mapped(nucleo_raw: dict[str, Any]) -> None:
    """The declaration omits ``multiplicador``/``formula``/``variable``, which feats
    do use, so the mapping is checked against actual usage as well."""
    used = {
        modifier["tipo"]
        for feat in nucleo_raw["dotes"]["lista"]
        for effect in feat["efectos"]
        for modifier in effect.get("modificadores") or []
    }
    assert used <= KNOWN_FEAT_BONUSES, f"unmapped: {sorted(used - KNOWN_FEAT_BONUSES)}"


def test_stacking_classification_agrees_with_the_engine(nucleo_raw: dict[str, Any]) -> None:
    """The feats block states which types stack with themselves. That must agree with
    the engine, or a translated modifier would stack differently than the data says.
    """
    declared = nucleo_raw["dotes"]["esquema_efectos"]["tipos_bonificador"]

    for raw in declared["apilan_siempre"]:
        bonus_type = parse_feat_bonus_type(raw)
        assert bonus_type is None or bonus_type in ALWAYS_STACKING, (
            f"{raw!r} is declared always-stacking but maps to {bonus_type}"
        )

    for raw in declared["no_apilan_consigo_mismos"]:
        bonus_type = parse_feat_bonus_type(raw)
        assert bonus_type is not None, f"{raw!r} must carry a type to be suppressed"
        # Circumstance is the documented exception: distinct sources do stack, the
        # same source does not, which is exactly how the engine resolves it.
        if bonus_type is not BonusType.CIRCUMSTANCE:
            assert bonus_type not in ALWAYS_STACKING, (
                f"{raw!r} is declared non-stacking but the engine always stacks it"
            )
