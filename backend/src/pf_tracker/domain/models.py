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
    #: A buckler straps to the forearm, so it is the one shield that survives a
    #: two-handed grip — at -1 to attack while the hand is busy. Every other shield
    #: needs the hand outright and simply stops applying.
    is_buckler: bool = False


@dataclass(frozen=True, slots=True)
class EquippedWeapon:
    """Resolved weapon stats for one weapon the character can attack with."""

    name: str
    wield: Wield
    is_ranged: bool
    threat_range: int
    crit_multiplier: int
    #: What makes this line different from the weapon's base one — the declared or
    #: situational feat(s) behind it (``"Ataque poderoso"``, ``"Disparo a
    #: bocajarro — sólo objetivo a 30 pies (9 m) o menos"``) — already folded into
    #: ``name`` as ``"<name> (<variant_label>)"`` for anything that reads the whole
    #: line as one string. Carried separately too so a renderer can show the two
    #: on their own lines instead of repeating the weapon name inside them.
    variant_label: str | None = None
    #: Unarmed strikes are their own category: some feats only add attacks to them.
    is_unarmed: bool = False
    is_thrown: bool = False
    damage_dice: str | None = None  # size-appropriate dice, e.g. "1d8"
    damage_type: str | None = None
    range_increment: str | None = None
    #: The weapon's enhancement bonus, kept as two numbers because the sheet lets a
    #: GM state them apart. A magic weapon has *one* bonus that applies to both, so
    #: these are normally equal; masterwork is the standard case where they are not
    #: (+1 to attack, nothing to damage). Both are typed `enhancement`, so they
    #: neither stack with each other nor with another enhancement source.
    attack_enhancement: int = 0
    damage_enhancement: int = 0
    is_proficient: bool = True
    #: Extra per-weapon modifiers (weapon-specific feats/stances), applied on top.
    attack_modifiers: tuple[Modifier, ...] = ()
    damage_modifiers: tuple[Modifier, ...] = ()
    #: Modifiers this line puts on the character's CMB. Power Attack buys damage
    #: with a penalty to attacks *and* to combat manoeuvres, and the second half is
    #: only paid when this line is the one being used.
    cmb_modifiers: tuple[Modifier, ...] = ()
    #: How many times the weapon's damage dice are rolled (Vital Strike, Manyshot).
    #: Only the dice multiply; flat damage bonuses are added once.
    damage_dice_multiplier: int = 1
    #: Whether that multiplier applies to the first attack only (Manyshot) rather
    #: than to every attack in the routine.
    dice_multiplier_first_attack_only: bool = False
    #: Extra attacks made at the highest attack bonus (Rapid Shot, Medusa's Wrath).
    #: They are added to the routine rather than following the iterative sequence.
    extra_attacks_at_full_bab: int = 0
    #: Prose shown with this line: what a feat does that is not a number of yours
    #: (a critical feat applies a condition to the *target*, which no sheet field
    #: can hold until there is an opponent to hold it).
    notes: tuple[str, ...] = ()
    #: Whether this line is a single attack rather than a full-attack routine.
    #: Vital Strike trades the iteratives for extra dice on one blow, so showing
    #: "+20/+15/+10/+5" beside its damage would advertise four of them.
    single_attack: bool = False
    #: Whether Weapon Finesse covers this weapon — light, or one of the four the feat
    #: names. It is a *permission*, not a decision: damage still uses Strength, and
    #: the derivation picks whichever ability actually comes out ahead.
    allows_finesse: bool = False
    #: Stable identity of this line among the ways of using one weapon: catalog name,
    #: grip, and the optional feats folded in. The display name would nearly do, but it
    #: carries a translated label and a situational caveat, so a reworded string would
    #: silently un-hide every line a player had hidden.
    variant_key: str | None = None
    #: Whether this weapon can also be held in both hands for 1.5x Strength damage.
    #: True only for the one-handed category: a two-handed weapon has no other grip,
    #: and a light one gains nothing ("no concede ventaja al daño"), so neither earns
    #: a second line.
    allows_two_handed_grip: bool = False


@dataclass(frozen=True, slots=True)
class SkillState:
    """One skill on the sheet, whether or not the character has invested in it."""

    slug: str
    name: str
    ability: Ability
    ranks: int = 0
    is_class_skill: bool = False
    uses_armor_check_penalty: bool = False
    untrained: bool = True
    misc_modifier: int = 0
    #: Whether the character has state of their own here — ranks, a misc modifier, or
    #: a feat naming it — as opposed to being present because every skill is. Only a
    #: tracked skill can be *wrongly* untrained: a barbarian who never took Descifrar
    #: escritura has not made a mistake, they simply cannot roll it.
    is_tracked: bool = True


@dataclass(frozen=True, slots=True)
class Stances:
    """Combat stance toggles. Each emits modifiers; none mutates the character."""

    charge: bool = False
    fighting_defensively: bool = False
    total_defense: bool = False
    flanking: bool = False
    higher_ground: bool = False
    #: Names of declared feats currently active (``Acometer``, ``Hendedura``…). Their
    #: modifiers come from the corpus, so no scaling is recomputed here.
    feat_stances: tuple[str, ...] = ()


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
    #: Hit points contributed by each level, before Constitution. When present it
    #: derives ``max_hp``, so a sheet cannot show a total that disagrees with the
    #: levels behind it.
    hp_per_level: tuple[int, ...] = ()
    current_hp: int = 0
    temporary_hp: int = 0
    nonlethal_damage: int = 0

    skills: tuple[SkillState, ...] = ()

    feats: tuple[str, ...] = ()
    conditions: tuple[str, ...] = ()
    stances: Stances = field(default_factory=Stances)
    two_weapon_fighting: TwoWeaponFighting = field(default_factory=TwoWeaponFighting)

    #: Terms a feat replaces rather than adds to. These are not modifiers — the
    #: stacking engine adds to a total, it cannot swap out one of its terms — so they
    #: arrive as flags the derivation reads. See ``rules/feat_substitutions.py``.
    #: `Maniobras ágiles`: CMB counts Dexterity where it would count Strength.
    cmb_uses_dexterity: bool = False
    #: `Entrenamiento en combate defensivo`: CMD counts total Hit Dice where it would
    #: count base attack bonus. It says explicitly that CMB is unaffected.
    cmd_uses_hit_dice: bool = False
    #: `Sutileza con las armas`: melee attacks may use Dexterity, on weapons that
    #: allow it. Held on the character because the feat is the character's; whether a
    #: given line can take it up is the weapon's ``allows_finesse``.
    has_weapon_finesse: bool = False

    #: External modifiers (feats, race traits, spells, items, manual ad-hoc).
    modifiers: tuple[Modifier, ...] = ()
    #: Armour check penalty contributed by worn magic items. Separate from the
    #: armour's because penalties stack: this adds, it does not compete.
    item_armor_check_penalty: int = 0

    load: CarryingLoad | None = None

    @property
    def total_level(self) -> int:
        return sum(cl.level for cl in self.class_levels)
