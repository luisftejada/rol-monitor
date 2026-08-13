"""Character DTOs.

These are the persisted/edited shape of a character (what a combat round needs).
Spanish canonical names and slugs come straight from the corpus; validation is
deliberately lenient (house rules and edge cases are real), so problems surface as
warnings on the combat sheet rather than as 422s.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

Wielding = Literal["one_handed", "two_handed", "off_hand", "natural"]
HpRollMode = Literal["manual", "average", "max_first_then_average"]


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(UTC)


class ClassLevelIn(BaseModel):
    class_slug: str
    level: int = Field(ge=1, le=40)
    is_prestige: bool = False
    is_favored: bool = False


class EquippedArmorIn(BaseModel):
    catalog_name: str
    enhancement_bonus: int = 0
    is_masterwork: bool = False
    material: str | None = None
    custom_overrides: dict[str, Any] | None = None


class EquippedWeaponIn(BaseModel):
    id: str = Field(default_factory=_uuid)
    catalog_name: str
    #: The magic bonus as a single number, which is what a magic weapon actually has.
    #: Kept because every character saved before the split stores it here.
    enhancement_bonus: int = 0
    #: The same bonus stated per side, which is what the editor edits. A +1 weapon is
    #: 1 and 1; masterwork is the standard case where they differ. Left at zero they
    #: fall back to ``enhancement_bonus``, so an older document keeps its magic.
    attack_bonus: int = 0
    damage_bonus: int = 0
    is_masterwork: bool = False
    material: str | None = None
    wielding: Wielding = "one_handed"
    size_category: str | None = None
    ammo: str | None = None
    notes: str | None = None
    custom_overrides: dict[str, Any] | None = None


class ModifierIn(BaseModel):
    id: str = Field(default_factory=_uuid)
    target: str
    value: int
    bonus_type: str | None = None  # Spanish canonical (e.g. "moral"); None == untyped
    source: str
    source_kind: str = "manual"
    condition: str | None = None
    is_active: bool = True
    expires_in_rounds: int | None = None


class ActiveEffectIn(BaseModel):
    id: str = Field(default_factory=_uuid)
    name: str
    modifiers: list[ModifierIn] = Field(default_factory=list)
    remaining_rounds: int | None = None


class StancesIn(BaseModel):
    charge: bool = False
    fighting_defensively: bool = False
    total_defense: bool = False
    flanking: bool = False
    higher_ground: bool = False
    #: Declared feats active this round, by canonical name.
    feat_stances: list[str] = Field(default_factory=list)


def _standard_array() -> dict[str, int]:
    # Standard array assigned to a default fighter (Str-forward).
    return {"Fue": 15, "Des": 14, "Con": 13, "Int": 12, "Sab": 10, "Car": 8}


def _default_class_levels() -> list[ClassLevelIn]:
    return [ClassLevelIn(class_slug="guerrero", level=1)]


class CharacterData(BaseModel):
    """The editable content of a character. New characters default to a level-1
    human fighter with the standard array, so the live combat card is never empty."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["pc", "npc"] = "pc"
    name: str = "Nuevo personaje"
    player_name: str | None = None
    race: str = "humano"
    alignment: str | None = None
    size: str | None = None  # None -> default from race
    speed_ft: int | None = None  # None -> default from race
    notes: str | None = None
    portrait_url: str | None = None

    class_levels: list[ClassLevelIn] = Field(default_factory=_default_class_levels)

    base_scores: dict[str, int] = Field(default_factory=_standard_array)
    #: Flexible racial bonuses the player assigns (e.g. human's +2 to any ability).
    racial_bonus_choices: dict[str, int] = Field(default_factory=dict)
    ability_damage: dict[str, int] = Field(default_factory=dict)
    level_ability_increments: dict[str, int] = Field(default_factory=dict)

    max_hp: int = 0
    current_hp: int = 0
    temporary_hp: int = 0
    nonlethal_damage: int = 0
    hp_roll_mode: HpRollMode = "manual"

    skill_ranks: dict[str, int] = Field(default_factory=dict)
    skill_misc_modifiers: dict[str, int] = Field(default_factory=dict)

    feats: list[str] = Field(default_factory=list)
    feat_options: dict[str, str] = Field(default_factory=dict)

    armor: EquippedArmorIn | None = None
    shield: EquippedArmorIn | None = None
    weapons: list[EquippedWeaponIn] = Field(default_factory=list)
    natural_armor_bonus: int = 0
    deflection_bonus: int = 0
    other_ac_modifiers: int = 0
    load_carried_lb: float | None = None

    #: ``variant_key`` of the attack lines the player has chosen not to see. Stored as
    #: what to *hide* rather than what to show, so a line that appears later — a new
    #: feat, a new weapon — shows up by default instead of being invisible until
    #: someone thinks to look for it.
    hidden_attack_lines: list[str] = Field(default_factory=list)

    active_conditions: list[str] = Field(default_factory=list)
    active_effects: list[ActiveEffectIn] = Field(default_factory=list)
    modifiers: list[ModifierIn] = Field(default_factory=list)
    stances: StancesIn = Field(default_factory=StancesIn)
    initiative_misc: int = 0
    is_flat_footed: bool = False
    dexterity_denied: bool = False


class CharacterCreate(CharacterData):
    """Body for ``POST /characters``."""


class CharacterImport(CharacterData):
    """Body for ``POST /characters/import``: an exported document, whose
    server-managed fields (id, timestamps) are ignored so a raw export re-imports."""

    model_config = ConfigDict(extra="ignore")


class CharacterRead(CharacterData):
    """A stored character, with server-managed identity and timestamps."""

    id: str
    created_at: datetime
    updated_at: datetime


class CharacterPatch(BaseModel):
    """Partial update: only provided fields change (``exclude_unset`` semantics)."""

    model_config = ConfigDict(extra="forbid")

    kind: Literal["pc", "npc"] | None = None
    name: str | None = None
    player_name: str | None = None
    race: str | None = None
    alignment: str | None = None
    size: str | None = None
    speed_ft: int | None = None
    notes: str | None = None
    portrait_url: str | None = None
    class_levels: list[ClassLevelIn] | None = None
    base_scores: dict[str, int] | None = None
    racial_bonus_choices: dict[str, int] | None = None
    ability_damage: dict[str, int] | None = None
    level_ability_increments: dict[str, int] | None = None
    max_hp: int | None = None
    current_hp: int | None = None
    temporary_hp: int | None = None
    nonlethal_damage: int | None = None
    hp_roll_mode: HpRollMode | None = None
    skill_ranks: dict[str, int] | None = None
    skill_misc_modifiers: dict[str, int] | None = None
    feats: list[str] | None = None
    feat_options: dict[str, str] | None = None
    armor: EquippedArmorIn | None = None
    shield: EquippedArmorIn | None = None
    weapons: list[EquippedWeaponIn] | None = None
    natural_armor_bonus: int | None = None
    deflection_bonus: int | None = None
    other_ac_modifiers: int | None = None
    load_carried_lb: float | None = None
    hidden_attack_lines: list[str] | None = None
    active_conditions: list[str] | None = None
    active_effects: list[ActiveEffectIn] | None = None
    modifiers: list[ModifierIn] | None = None
    stances: StancesIn | None = None
    initiative_misc: int | None = None
    is_flat_footed: bool | None = None
    dexterity_denied: bool | None = None


class CharacterSummary(BaseModel):
    """A dense row for the character list, with a few derived numbers."""

    id: str
    name: str
    player_name: str | None
    kind: str
    classes: str  # e.g. "Guerrero 8 / Pícaro 4"
    total_level: int
    max_hp: int
    current_hp: int
    armor_class: int
    touch_ac: int
    flat_footed_ac: int
    initiative: int
    fortitude: int
    reflex: int
    will: int
    updated_at: datetime


class CharacterListResponse(BaseModel):
    items: list[CharacterSummary]
    total: int
    limit: int
    offset: int


def new_character(data: CharacterCreate) -> CharacterRead:
    """Promote create-input into a stored character with identity and timestamps."""
    now = _now()
    return CharacterRead(id=_uuid(), created_at=now, updated_at=now, **data.model_dump())
