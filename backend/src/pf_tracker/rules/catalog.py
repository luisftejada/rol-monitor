"""DTOs for the read-only rules catalog that powers the UI pickers.

Field names are English; values stay in Spanish (opaque canonical identifiers). Each
entry carries an ASCII ``slug`` derived from its canonical name for use as a stable
client key or URL segment.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class _CatalogModel(BaseModel):
    model_config = ConfigDict(frozen=True)


# --------------------------------------------------------------------------- meta
class BonusTypesDTO(_CatalogModel):
    """The stacking classification, verbatim from ``sistema.tipos_de_bonificador``."""

    always_stack: list[str]
    do_not_stack: list[str]
    penalties: str
    note: str | None = None


class AbilityDTO(_CatalogModel):
    name: str
    abbr: str
    uses: str


class SizeDTO(_CatalogModel):
    slug: str
    name: str
    ac_attack_mod: int
    cmb_cmd_mod: int
    stealth_mod: int
    space: str
    reach: str
    load_multiplier: float


class ActionTypeDTO(_CatalogModel):
    type: str
    notes: str | None = None


class MetaDTO(_CatalogModel):
    bonus_types: BonusTypesDTO
    abilities: list[AbilityDTO]
    sizes: list[SizeDTO]
    action_types: list[ActionTypeDTO]
    units: dict[str, str]


# -------------------------------------------------------------------------- races
class RaceDTO(_CatalogModel):
    slug: str
    key: str
    name: str
    size: str
    speed_ft: int
    ability_modifiers: dict[str, int]
    type: str
    vision: str | None = None
    traits: list[str]
    languages: dict[str, list[str]]


# ------------------------------------------------------------------------- classes
class ClassSummaryDTO(_CatalogModel):
    slug: str
    name: str
    hit_die: str
    skill_ranks_per_level: int
    bab_progression: str
    good_saves: list[str]
    proficiencies: str | None = None
    class_skills: list[str]
    is_spellcaster: bool
    is_prestige: bool
    max_level: int


class ClassProgressionRowDTO(_CatalogModel):
    level: int
    bab: str
    bab_iteratives: list[int]
    fort: int
    ref: int
    will: int
    special: str | None = None
    spells_per_day: list[str] | None = None


# -------------------------------------------------------------------------- skills
class SkillDTO(_CatalogModel):
    slug: str
    name: str
    ability: str
    untrained: bool
    armor_check_penalty: bool
    class_for: list[str]


# --------------------------------------------------------------------------- feats
class FeatDTO(_CatalogModel):
    slug: str
    name: str
    types: list[str]
    prerequisites: str | None = None
    benefit: str | None = None
    is_eligible: bool = True


# --------------------------------------------------------------------------- weapons
class CriticalDTO(_CatalogModel):
    threat_range: int
    multiplier: int


class WeaponDTO(_CatalogModel):
    slug: str
    name: str
    proficiency: str
    category: str
    cost: str | None = None
    damage_small: str | None = None
    damage_medium: str | None = None
    critical: list[CriticalDTO]
    range_increment: str | None = None
    weight: str | None = None
    damage_type: str | None = None
    special: str | None = None


# ---------------------------------------------------------------------------- armor
class ArmorDTO(_CatalogModel):
    slug: str
    name: str
    category: str
    price_gp: float
    armor_bonus: int
    max_dex: int | None = None
    armor_check_penalty: int
    arcane_spell_failure_pct: int
    speed_30: str | None = None
    speed_20: str | None = None
    weight: str | None = None


# ----------------------------------------------------------------------- conditions
class ConditionDTO(_CatalogModel):
    slug: str
    name: str
    effect: str


# --------------------------------------------------------------------------- spells
class SpellDTO(_CatalogModel):
    slug: str
    name: str
    school: str | None = None
    levels: dict[str, int]
    descriptors: list[str]
    casting_time: str | None = None
    components: str | None = None
    range: str | None = None
    duration: str | None = None
    saving_throw: str | None = None
    spell_resistance: str | None = None
