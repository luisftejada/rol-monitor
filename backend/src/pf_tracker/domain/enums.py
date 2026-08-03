"""Domain enumerations.

Enum *values* are the Spanish canonical strings from the corpus where one exists
(bonus types, abilities, saves, sizes), so they round-trip against the data without
translation. Enum *names* are English, per the code convention.
"""

from __future__ import annotations

from enum import Enum


class Ability(str, Enum):
    """The six ability scores, valued by their Spanish abbreviation."""

    STR = "Fue"
    DEX = "Des"
    CON = "Con"
    INT = "Int"
    WIS = "Sab"
    CHA = "Car"


class SaveKind(str, Enum):
    """The three saving throws."""

    FORTITUDE = "Fortaleza"
    REFLEX = "Reflejos"
    WILL = "Voluntad"


class Size(str, Enum):
    """Creature sizes (Spanish canonical names from ``tamanos``)."""

    FINE = "Menudo"
    DIMINUTIVE = "Diminuto"
    TINY = "Minúsculo"
    SMALL = "Pequeño"
    MEDIUM = "Mediano"
    LARGE = "Grande"
    HUGE = "Enorme"
    GARGANTUAN = "Gigantesco"
    COLOSSAL = "Colosal"


class BabProgression(str, Enum):
    """Base attack bonus progression type (``clases[].bab``)."""

    FULL = "completo"
    THREE_QUARTER = "3/4"
    HALF = "1/2"


class BonusType(str, Enum):
    """Bonus types, mapped 1:1 to ``sistema.tipos_de_bonificador`` Spanish strings.

    ``None`` (untyped) is represented by the absence of a bonus type on a modifier,
    not by a member here.

    ``DEFLECTION`` ("deflexión") is not listed in ``sistema.tipos_de_bonificador`` but
    is a standard non-stacking type used by the AC formula and the combat-sheet
    breakdown; see docs/assumptions.md. The exhaustiveness test asserts the corpus
    types are a subset of this enum, so extra standard types are allowed.
    """

    ALCHEMICAL = "alquimia"
    ARMOR = "armadura"
    NATURAL_ARMOR = "armadura natural"
    COMPETENCE = "competencia"
    DEFLECTION = "deflexión"
    DODGE = "esquiva"
    SHIELD = "escudo"
    INHERENT = "inherente"
    INSIGHT = "introspección"
    CIRCUMSTANCE = "circunstancia"
    MORALE = "moral"
    ENHANCEMENT = "potenciador"
    PROFANE = "profano"
    RACIAL = "racial"
    RESISTANCE = "resistencia"
    SACRED = "sagrado"
    LUCK = "suerte"
    SIZE = "tamaño"


#: Bonus types that always stack with everything, including with themselves.
#: Untyped (``None``) also always stacks; it is handled separately in the engine.
ALWAYS_STACKING: frozenset[BonusType] = frozenset({BonusType.DODGE, BonusType.CIRCUMSTANCE})


class SourceKind(str, Enum):
    """Where a modifier comes from, for grouping and display."""

    BASE = "base"
    ABILITY = "ability"
    ARMOR = "armor"
    SHIELD = "shield"
    FEAT = "feat"
    RACE = "race"
    CLASS = "class"
    SPELL = "spell"
    ITEM = "item"
    CONDITION = "condition"
    STANCE = "stance"
    SIZE = "size"
    MANUAL = "manual"


class Wield(str, Enum):
    """How a weapon is wielded, which drives the Str-to-damage multiplier."""

    ONE_HANDED = "one_handed"
    TWO_HANDED = "two_handed"
    OFF_HAND = "off_hand"
    NATURAL = "natural"


class ModifierTarget(str, Enum):
    """What a modifier applies to.

    Concrete targets are members here; per-skill and per-ability targets use the
    string forms ``SKILL:<slug>`` and ``ABILITY:<abbr>``. Group targets (``ALL_*``)
    apply to every concrete target they cover; see :func:`target_matches`.
    """

    AC = "AC"
    ATTACK_MELEE = "ATTACK_MELEE"
    ATTACK_RANGED = "ATTACK_RANGED"
    ALL_ATTACKS = "ALL_ATTACKS"
    DAMAGE_MELEE = "DAMAGE_MELEE"
    DAMAGE_RANGED = "DAMAGE_RANGED"
    ALL_DAMAGE = "ALL_DAMAGE"
    SAVE_FORT = "SAVE_FORT"
    SAVE_REF = "SAVE_REF"
    SAVE_WILL = "SAVE_WILL"
    ALL_SAVES = "ALL_SAVES"
    INITIATIVE = "INITIATIVE"
    CMB = "CMB"
    CMD = "CMD"
    SPEED = "SPEED"
    ALL_SKILLS = "ALL_SKILLS"
    ALL_CHECKS = "ALL_CHECKS"


#: Prefixes for the dynamic, name-parameterised targets.
SKILL_TARGET_PREFIX = "SKILL:"
ABILITY_TARGET_PREFIX = "ABILITY:"

# Which concrete targets each group expands to. ALL_SKILLS / ALL_CHECKS are handled
# by prefix in target_matches rather than enumerated here.
_GROUPS: dict[ModifierTarget, frozenset[ModifierTarget]] = {
    ModifierTarget.ALL_ATTACKS: frozenset(
        {ModifierTarget.ATTACK_MELEE, ModifierTarget.ATTACK_RANGED}
    ),
    ModifierTarget.ALL_DAMAGE: frozenset(
        {ModifierTarget.DAMAGE_MELEE, ModifierTarget.DAMAGE_RANGED}
    ),
    ModifierTarget.ALL_SAVES: frozenset(
        {ModifierTarget.SAVE_FORT, ModifierTarget.SAVE_REF, ModifierTarget.SAVE_WILL}
    ),
}


def skill_target(slug: str) -> str:
    """Return the modifier target string for a skill by slug."""
    return f"{SKILL_TARGET_PREFIX}{slug}"


def ability_target(ability: Ability) -> str:
    """Return the modifier target string for an ability score."""
    return f"{ABILITY_TARGET_PREFIX}{ability.value}"


def target_matches(applied_target: str, query: str) -> bool:
    """Whether a modifier declared for ``applied_target`` applies to ``query``.

    Exact matches apply. Group targets apply to their members. ``ALL_SKILLS``
    applies to any ``SKILL:*`` query; ``ALL_CHECKS`` applies to skills and saves
    (ability/skill checks and saving throws), matching how fear-type penalties are
    described in the corpus.
    """
    if applied_target == query:
        return True

    applied = _as_target(applied_target)
    if applied is not None:
        group = _GROUPS.get(applied)
        if group is not None and _as_target(query) in group:
            return True

    if applied_target == ModifierTarget.ALL_SKILLS.value:
        return query.startswith(SKILL_TARGET_PREFIX)

    if applied_target == ModifierTarget.ALL_CHECKS.value:
        return query.startswith(SKILL_TARGET_PREFIX) or query in {
            ModifierTarget.SAVE_FORT.value,
            ModifierTarget.SAVE_REF.value,
            ModifierTarget.SAVE_WILL.value,
        }

    return False


def _as_target(value: str) -> ModifierTarget | None:
    try:
        return ModifierTarget(value)
    except ValueError:
        return None
