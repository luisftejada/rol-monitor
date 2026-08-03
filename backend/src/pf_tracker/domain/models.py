"""Frozen input models for the derivation engine.

These carry every rules fact derivation needs as plain data — resolved ability
scores, class facts, equipment stats, skill state — so the engine never reaches
into the rules corpus. The Phase 3 service layer assembles these from persisted
characters plus the rules repository; golden fixtures specify them directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pf_tracker.domain.enums import (
    Ability,
    BabProgression,
    SaveKind,
    Size,
    Wield,
)
from pf_tracker.domain.modifiers import Modifier


@dataclass(frozen=True, slots=True)
class ClassLevel:
    """One class entry in a (possibly multiclass) character."""

    class_slug: str
    class_name: str
    level: int
    bab_type: BabProgression
    hit_die: int
    #: Base save bonus this class contributes at ``level`` (authoritative row values).
    base_saves: dict[SaveKind, int]
    is_prestige: bool = False
    is_favored: bool = False


@dataclass(frozen=True, slots=True)
class EquippedArmor:
    """Resolved armor or shield stats (base bonus already combined with enhancement)."""

    name: str
    is_shield: bool
    ac_bonus: int
    max_dex: int | None
    armor_check_penalty: int  # <= 0
    arcane_spell_failure: int  # percent
    category: str  # ligera | intermedia | pesada | escudo


@dataclass(frozen=True, slots=True)
class EquippedWeapon:
    """Resolved weapon stats for one weapon the character can attack with."""

    name: str
    wield: Wield
    is_ranged: bool
    threat_range: int
    crit_multiplier: int
    is_thrown: bool = False
    damage_dice: str | None = None  # size-appropriate dice, e.g. "1d8"
    damage_type: str | None = None
    range_increment: str | None = None
    enhancement_bonus: int = 0
    is_proficient: bool = True
    #: Extra per-weapon modifiers (weapon-specific feats/stances), applied on top.
    attack_modifiers: tuple[Modifier, ...] = ()
    damage_modifiers: tuple[Modifier, ...] = ()


@dataclass(frozen=True, slots=True)
class SkillState:
    """A skill the character has state for (ranks and/or misc modifiers)."""

    slug: str
    name: str
    ability: Ability
    ranks: int = 0
    is_class_skill: bool = False
    uses_armor_check_penalty: bool = False
    untrained: bool = True
    misc_modifier: int = 0


@dataclass(frozen=True, slots=True)
class Stances:
    """Combat stance toggles. Each emits modifiers; none mutates the character."""

    charge: bool = False
    fighting_defensively: bool = False
    total_defense: bool = False
    power_attack: bool = False
    combat_expertise: bool = False
    flanking: bool = False
    higher_ground: bool = False


@dataclass(frozen=True, slots=True)
class CarryingLoad:
    """Encumbrance thresholds and current load, in pounds."""

    light_max: int
    medium_max: int
    heavy_max: int
    carried_lb: float = 0.0


@dataclass(frozen=True, slots=True)
class TwoWeaponFighting:
    """Two-weapon fighting configuration (feats owned drive the penalties)."""

    enabled: bool = False
    has_light_off_hand: bool = False
    improved: bool = False  # Combate con dos armas mejorado
    greater: bool = False  # Combate con dos armas mayor
    has_twf_feat: bool = False  # Combate con dos armas (base)


@dataclass(frozen=True, slots=True)
class Character:
    """A fully resolved character, ready for pure derivation."""

    name: str
    size: Size
    base_speed_ft: int
    class_levels: tuple[ClassLevel, ...]

    base_ability_scores: dict[Ability, int]
    racial_ability_modifiers: dict[Ability, int] = field(default_factory=dict)
    level_ability_increments: dict[Ability, int] = field(default_factory=dict)
    ability_damage: dict[Ability, int] = field(default_factory=dict)

    armor: EquippedArmor | None = None
    shield: EquippedArmor | None = None
    weapons: tuple[EquippedWeapon, ...] = ()

    natural_armor_bonus: int = 0
    deflection_bonus: int = 0
    other_ac_modifiers: int = 0

    max_hp: int = 0
    current_hp: int = 0
    temporary_hp: int = 0
    nonlethal_damage: int = 0

    skills: tuple[SkillState, ...] = ()

    feats: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()
    stances: Stances = field(default_factory=Stances)
    two_weapon_fighting: TwoWeaponFighting = field(default_factory=TwoWeaponFighting)

    #: External modifiers (feats, race traits, spells, items, manual ad-hoc).
    modifiers: tuple[Modifier, ...] = ()

    load: CarryingLoad | None = None

    @property
    def total_level(self) -> int:
        return sum(cl.level for cl in self.class_levels)
