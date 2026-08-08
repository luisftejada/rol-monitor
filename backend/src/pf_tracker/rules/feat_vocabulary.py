"""Translation of the feats corpus vocabulary into domain terms.

The corpus speaks two different dialects for the same concepts. ``sistema.
tipos_de_bonificador`` — which :class:`BonusType` mirrors 1:1 — uses accented
Spanish nouns (``potenciador``, ``introspección``, ``armadura natural``). The feats
block added in the 2026-08-06 rewrite uses ASCII slugs, and picks different words
for several of them (``mejora``, ``perspicacia``, ``natural``).

Reconciling the two is an adapter concern, not a domain one: the stacking engine
must not have to know how the feats file happens to spell things. Everything here
maps *into* the domain vocabulary; nothing maps back out.
"""

from __future__ import annotations

from pf_tracker.domain.enums import BonusType

#: Feat-vocabulary bonus types that carry no stacking type of their own.
#:
#: ``sin_tipo`` is untyped. ``penalizador`` is a *type* in the feats file, but the
#: engine reads penalties from the sign of the value — they always stack and are
#: deduplicated by source — so it also resolves to untyped. A data-contract test
#: pins that no ``penalizador`` ever carries a positive value.
UNTYPED_FEAT_BONUSES: frozenset[str] = frozenset({"sin_tipo", "penalizador"})

#: Markers that describe the *shape* of ``valor`` rather than a stacking type.
#:
#: The corpus warns that these values ("x2", "2d6", "1_por_dado_de_golpe") cannot be
#: summed and must be dispatched per target. They are deliberately not bonus types:
#: mapping them to untyped would let a multiplier be added like a flat bonus.
NON_SCALAR_FEAT_BONUSES: frozenset[str] = frozenset({"multiplicador", "formula", "variable"})

#: Feat-vocabulary slug -> domain bonus type.
#:
#: Only the spellings that actually differ are interesting; the rest are here so the
#: table is exhaustive and a corpus addition fails the contract test loudly.
_FEAT_BONUS_TYPES: dict[str, BonusType] = {
    "alquimico": BonusType.ALCHEMICAL,  # vs. "alquimia"
    "circunstancia": BonusType.CIRCUMSTANCE,
    "competencia": BonusType.COMPETENCE,
    "deflexion": BonusType.DEFLECTION,  # vs. "deflexión"
    "escudo": BonusType.SHIELD,
    "esquiva": BonusType.DODGE,
    "mejora": BonusType.ENHANCEMENT,  # vs. "potenciador"
    "moral": BonusType.MORALE,
    "natural": BonusType.NATURAL_ARMOR,  # vs. "armadura natural"
    "perspicacia": BonusType.INSIGHT,  # vs. "introspección"
    "profano": BonusType.PROFANE,
    "resistencia": BonusType.RESISTANCE,
    "sagrado": BonusType.SACRED,
    "suerte": BonusType.LUCK,
    "tamano": BonusType.SIZE,  # vs. "tamaño"
}


class UnknownFeatBonusTypeError(ValueError):
    """Raised when the feats corpus uses a bonus type this adapter cannot map."""


def is_scalar_feat_bonus(raw: str) -> bool:
    """Whether ``raw`` denotes an additive bonus rather than a multiplier or formula."""
    return raw not in NON_SCALAR_FEAT_BONUSES


def parse_feat_bonus_type(raw: str) -> BonusType | None:
    """Translate a feats-vocabulary bonus type into a :class:`BonusType`.

    Returns ``None`` for untyped bonuses and for penalties, which the engine
    distinguishes by sign. Raises for non-scalar markers and unknown values rather
    than guessing: silently treating a multiplier as untyped would add "x2" as a
    flat bonus.
    """
    if raw in UNTYPED_FEAT_BONUSES:
        return None
    if raw in NON_SCALAR_FEAT_BONUSES:
        raise UnknownFeatBonusTypeError(
            f"{raw!r} describes the shape of a value, not a stacking type; "
            "dispatch it by target instead"
        )
    try:
        return _FEAT_BONUS_TYPES[raw]
    except KeyError:
        raise UnknownFeatBonusTypeError(f"unmapped feat bonus type {raw!r}") from None


#: Every feat-vocabulary token this module recognises, scalar or not.
KNOWN_FEAT_BONUSES: frozenset[str] = frozenset(
    set(_FEAT_BONUS_TYPES) | UNTYPED_FEAT_BONUSES | NON_SCALAR_FEAT_BONUSES
)
