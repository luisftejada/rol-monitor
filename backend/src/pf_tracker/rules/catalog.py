"""DTOs for the read-only rules catalog that powers the UI pickers.

Field names are English; values stay in Spanish (opaque canonical identifiers). Each
entry carries an ASCII ``slug`` derived from its canonical name for use as a stable
client key or URL segment.
"""

from __future__ import annotations

import hashlib
import json
from functools import cache

from pydantic import BaseModel, ConfigDict


class _CatalogModel(BaseModel):
    model_config = ConfigDict(frozen=True)


@cache
def catalog_schema_fingerprint() -> str:
    """Fingerprint the shape of every catalog DTO.

    Cache validators are built from the corpus bytes, which do not change when a
    field is added to a DTO. Without this, clients keep serving a cached response
    that is missing the new field until their freshness window expires. Hashing the
    JSON schemas means any added, removed, or renamed field invalidates the cache.
    """
    models = sorted(
        (name, obj)
        for name, obj in globals().items()
        if isinstance(obj, type) and issubclass(obj, _CatalogModel) and obj is not _CatalogModel
    )
    digest = hashlib.sha256()
    for name, model in models:
        digest.update(name.encode())
        digest.update(json.dumps(model.model_json_schema(), sort_keys=True).encode())
    return digest.hexdigest()[:16]


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


class ItemSlotDTO(_CatalogModel):
    """One place on the body a magic item can occupy.

    ``capacity`` is how many items may be worn there at once: the corpus writes it
    into the name (``"anillo (×2)"``), so it is parsed out rather than hardcoded.
    """

    #: The corpus' own name, kept whole for display: ``"anillo (×2)"``.
    name: str
    #: The name without its capacity suffix, which is what an item stores.
    slug: str
    capacity: int


class MetaDTO(_CatalogModel):
    bonus_types: BonusTypesDTO
    abilities: list[AbilityDTO]
    sizes: list[SizeDTO]
    action_types: list[ActionTypeDTO]
    units: dict[str, str]
    #: Point-buy cost per ability score (from ``caracteristicas.coste_compra_puntos``).
    point_buy_costs: dict[int, int]
    #: Character levels at which every character gains a feat (``niveles_con_dote``).
    feat_levels: list[int]
    #: Canonical feat categories, verbatim from ``dotes.reglas.tipos``. Drives the
    #: two-level feat picker; taken from the corpus rather than inferred from the
    #: feats themselves, so the ordering and wording stay authoritative.
    feat_types: list[str]
    #: Character levels granting +1 to an ability (``niveles_con_incremento_de_caracteristica``).
    ability_increment_levels: list[int]
    #: The corpus' own wording for what a favored class buys, shown verbatim rather
    #: than reworded: it is a choice the player makes, not a number to apply.
    favored_class_note: str
    #: Magic-item vocabulary, verbatim from ``objetos_magicos``. The body slots carry
    #: their capacity in the corpus' own notation (``"anillo (×2)"``), which is why
    #: they arrive as objects rather than plain strings.
    item_slots: list[ItemSlotDTO]
    item_categories: list[str]
    item_activations: list[str]
    #: Highest enhancement bonus an item may carry (``bonificadores_arma``). The
    #: corpus states the same 5 for weapons and armour.
    max_item_enhancement: int


# --------------------------------------------------------------------- alignments
class AlignmentDTO(_CatalogModel):
    """One entry of ``alineamiento.valores`` with its display name from ``nombres``.

    ``code`` (``LB``, ``NB``, …) is the corpus' own ASCII identifier, so it is used
    verbatim as the stable key instead of slugging the Spanish name.
    """

    code: str
    name: str


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
    #: Feats this race grants (the human's free one, the half-elf's fixed one).
    bonus_feats: list[FeatSlotDTO] = []
    #: Weapons this race is simply proficient with, whatever its class allows. An
    #: elf wizard can use a rapier; wizards as a class cannot.
    weapon_proficiencies: list[str] = []
    #: Words that make a weapon *martial* for this race — "cualquier arma con la
    #: palabra 'élfico' en su nombre". Martial is not the same as proficient: it
    #: still takes a class that grants martial weapons to pick one up safely.
    weapon_words: list[str] = []


# ------------------------------------------------------------------------- classes
class ClassSummaryDTO(_CatalogModel):
    slug: str
    name: str
    hit_die: str
    #: The die as a number, and the floor under a "never roll badly" hit-point roll
    #: (half the die plus one). Both are rules figures, so they are computed here
    #: rather than in the browser, which may then roll and take the better of the two.
    hit_die_faces: int
    hit_points_floor: int
    skill_ranks_per_level: int
    bab_progression: str
    good_saves: list[str]
    proficiencies: str | None = None
    class_skills: list[str]
    is_spellcaster: bool
    is_prestige: bool
    max_level: int
    #: Feats this class grants on top of the ones every character gets.
    bonus_feats: list[FeatSlotDTO] = []


class ClassProgressionRowDTO(_CatalogModel):
    level: int
    bab: str
    bab_iteratives: list[int]
    fort: int
    ref: int
    will: int
    special: str | None = None
    spells_per_day: list[str] | None = None


def list_ref(key: str, option: str | None) -> str:
    """The handle a resolved restricted list is filed under.

    Two slots sharing a corpus key but pinning different branches are two different
    lists — a sorcerer 7 / dragon disciple 2 has both — so the branch is part of the
    handle rather than something every caller has to re-derive.
    """
    return key if option is None else f"{key}/{option}"


class FeatSlotDTO(_CatalogModel):
    """One feat a class or race grants, and what may fill it.

    ``choice`` is the corpus' own ``eleccion``: ``libre`` (any feat), ``tipos``
    (any of the listed categories), ``lista`` (a named restricted list), or ``fija``
    (already decided — it costs the character no choice).
    """

    level: int
    choice: str
    types: list[str] = []
    #: Key into ``dotes.listas_restringidas`` when ``choice`` is ``lista``.
    list_key: str | None = None
    #: One branch of that list, when the slot pins the choice the list is keyed by.
    #: A dragon disciple draws from the *draconic* bloodline, not from every one, so
    #: its list is exact where the sorcerer's own slots resolve to a wider union.
    list_option: str | None = None
    #: The feat itself when ``choice`` is ``fija``.
    feat: str | None = None
    note: str | None = None
    #: Manual page the entry was taken from, for auditing.
    page: str | None = None

    @property
    def list_ref(self) -> str | None:
        """This slot's handle into the resolved lists, if it points at one."""
        if self.list_key is None:
            return None
        return list_ref(self.list_key, self.list_option)


# -------------------------------------------------------------------------- skills
class SkillDTO(_CatalogModel):
    slug: str
    name: str
    ability: str
    untrained: bool
    armor_check_penalty: bool
    class_for: list[str]


# --------------------------------------------------------------------------- feats
class FeatModifierDTO(_CatalogModel):
    """One numeric contribution of a feat, in the feats file's own vocabulary.

    ``value`` is an ``int`` for additive bonuses, or a string for the non-scalar
    forms the corpus warns about ("x2", "2d6", "1_por_dado_de_golpe").
    """

    target: str
    bonus_type: str
    value: int | str


class FeatSubstitutionDTO(_CatalogModel):
    """One term a feat swaps for another in a derived value.

    Not a bonus: `Sutileza con las armas` does not *add* Dexterity to an attack, it
    puts Dexterity where Strength would have gone. The stacking engine has no way to
    say that, so these are read separately (see ``rules/feat_substitutions.py``).
    """

    #: The derived value being changed (``ataque_cuerpo_a_cuerpo``, ``bmc``, ``dmc``).
    target: str
    #: The term that takes over, and the one it displaces.
    use: str
    instead_of: str


class FeatEffectDTO(_CatalogModel):
    """A feat's mechanical decomposition, gated by an optional condition."""

    condition: str | None = None
    #: Machine-readable predicate (``ataque_base``, ``rangos_habilidad``, …).
    when: dict[str, object] = {}
    modifiers: list[FeatModifierDTO] = []
    #: Terms this effect replaces rather than adds to.
    substitutions: list[FeatSubstitutionDTO] = []
    #: Prose for what is not expressible as a modifier.
    rules: list[str] = []


class FeatDTO(_CatalogModel):
    slug: str
    name: str
    types: list[str]
    prerequisites: str | None = None
    benefit: str | None = None
    is_eligible: bool = True
    #: How the feat is used; only ``pasiva`` effects apply without being declared.
    activation: str | None = None
    #: Whether it is a round-long choice the GM toggles (``Acometer``) rather than a
    #: passive bonus or a way of attacking.
    is_stance: bool = False
    #: What the player must pick when taking it (``weapon``, ``skill``, ``school``),
    #: stored in the character's ``feat_options``. ``None`` when it takes no option.
    choice_kind: str | None = None
    effects: list[FeatEffectDTO] = []


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
