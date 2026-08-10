"""Feats that swap one input of a derived value for another.

Three feats in the corpus carry a ``sustituciones`` block, and none of them is a
bonus: they change *which* number feeds a formula. Weapon Finesse puts Dexterity
where Strength would go on a melee attack, Agile Maneuvers does the same for CMB,
and Defensive Combat Training feeds CMD your Hit Dice instead of your base attack.

The stacking engine cannot express any of that — a modifier adds to a total, it does
not replace a term — so these resolve to flags the derivation reads, the same way
``single_attack`` is a flag rather than a modifier.

The vocabulary is listed exhaustively so a substitution added to the corpus fails a
contract test instead of being silently ignored, which is how the whole block came to
sit unread until someone noticed their Dexterity build attacking with Strength.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from pf_tracker.rules.catalog import FeatDTO

#: `en`: the derived value whose input is replaced.
MELEE_ATTACK = "ataque_cuerpo_a_cuerpo"
CMB = "bmc"
CMD = "dmc"
SUBSTITUTION_TARGETS: frozenset[str] = frozenset({MELEE_ATTACK, CMB, CMD})

#: `usar` / `en_lugar_de`: the terms swapped in and out.
DEX_MODIFIER = "modificador_destreza"
STR_MODIFIER = "modificador_fuerza"
BASE_ATTACK = "ataque_base"
TOTAL_HIT_DICE = "dados_de_golpe_totales"
SUBSTITUTION_TERMS: frozenset[str] = frozenset(
    {DEX_MODIFIER, STR_MODIFIER, BASE_ATTACK, TOTAL_HIT_DICE}
)

#: Weapons Weapon Finesse names one by one, because none of them is light. Everything
#: else it covers is identified by category instead.
FINESSE_WEAPONS: frozenset[str] = frozenset(
    {"Espada ropera", "Látigo", "Espada curva élfica", "Cadena armada"}
)

#: The corpus category for light melee weapons, and for unarmed strikes — "las armas
#: naturales se consideran armas ligeras a estos efectos".
LIGHT_MELEE_CATEGORY = "Armas cuerpo a cuerpo ligeras"
UNARMED_CATEGORY = "Ataques sin armas"


@dataclass(frozen=True, slots=True)
class Substitutions:
    """Which terms the character's feats replace, ready for the derivation."""

    #: Melee attack rolls may use Dexterity, on weapons that qualify.
    melee_attack_uses_dexterity: bool = False
    #: CMB uses Dexterity instead of Strength.
    cmb_uses_dexterity: bool = False
    #: CMD counts total Hit Dice where it would count base attack bonus.
    cmd_uses_hit_dice: bool = False


def resolve_substitutions(feats: Sequence[FeatDTO]) -> Substitutions:
    """Collapse every ``sustituciones`` entry the character's feats carry.

    A substitution the vocabulary does not cover is ignored here and caught by the
    contract test, which is the honest split: this function must not guess, and the
    corpus must not grow a term nobody implemented without somebody noticing.
    """
    melee = cmb = cmd = False
    for feat in feats:
        for effect in feat.effects:
            for swap in effect.substitutions:
                if swap.target == MELEE_ATTACK and swap.use == DEX_MODIFIER:
                    melee = True
                elif swap.target == CMB and swap.use == DEX_MODIFIER:
                    cmb = True
                elif swap.target == CMD and swap.use == TOTAL_HIT_DICE:
                    cmd = True
    return Substitutions(
        melee_attack_uses_dexterity=melee,
        cmb_uses_dexterity=cmb,
        cmd_uses_hit_dice=cmd,
    )


def allows_finesse(*, category: str, name: str) -> bool:
    """Whether Weapon Finesse covers this weapon.

    "…de tu categoría de tamaño" is not checked: the sheet only ever equips weapons
    sized for their wielder, so the clause is satisfied by construction rather than
    by a test that could never fail.
    """
    if category in {LIGHT_MELEE_CATEGORY, UNARMED_CATEGORY}:
        return True
    return name in FINESSE_WEAPONS
