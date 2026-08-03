"""Assemble a persisted character into a resolved domain :class:`Character`.

This is the seam between the rules corpus (Spanish catalog) and the pure domain
engine (English, numeric). It resolves catalog references to concrete stats, applies
masterwork/enhancement, derives proficiency and two-weapon configuration, and maps
conditions and modifiers. Anything it cannot resolve becomes a warning, never a
silent failure. An NPC variant can reuse this unchanged (see the ``kind`` field).
"""

from __future__ import annotations

from pf_tracker.domain.enums import (
    Ability,
    BabProgression,
    BonusType,
    SaveKind,
    Size,
    SourceKind,
    Wield,
)
from pf_tracker.domain.models import (
    CarryingLoad,
    ClassLevel,
    EquippedArmor,
    EquippedWeapon,
    SkillState,
    Stances,
    TwoWeaponFighting,
)
from pf_tracker.domain.models import (
    Character as DomainCharacter,
)
from pf_tracker.domain.modifiers import Modifier
from pf_tracker.rules.repository import RuleNotFoundError, RulesRepository
from pf_tracker.schemas.character import (
    CharacterRead,
    EquippedArmorIn,
    EquippedWeaponIn,
    ModifierIn,
    StancesIn,
)

_ABILITIES = {a.value for a in Ability}
_SAVE_BY_ROW = {SaveKind.FORTITUDE: "fort", SaveKind.REFLEX: "ref", SaveKind.WILL: "will"}
_SMALL_OR_LESS = {Size.FINE, Size.DIMINUTIVE, Size.TINY, Size.SMALL}
_LIGHT_MELEE_CATEGORY = "Armas cuerpo a cuerpo ligeras"
_RANGED_CATEGORY = "Armas a distancia"


class AssembledCharacter:
    """A domain character plus the warnings raised while assembling it."""

    def __init__(self, character: DomainCharacter, warnings: list[str]) -> None:
        self.character = character
        self.warnings = warnings


def assemble(character: CharacterRead, repo: RulesRepository) -> AssembledCharacter:
    warnings: list[str] = []

    race = repo.race(character.race)
    if race is None and character.race:
        warnings.append(f"Raza desconocida: {character.race}")

    size = _resolve_size(character, race, warnings)
    speed = (
        character.speed_ft if character.speed_ft is not None else (race.speed_ft if race else 30)
    )
    racial = _racial_modifiers(character, race)

    class_levels = _class_levels(character, repo, warnings)
    base_scores = _abilities(character.base_scores)
    increments = _abilities(character.level_ability_increments)
    ability_damage = _abilities(character.ability_damage)

    armor = _armor_slot(character.armor, repo, is_shield=False, warnings=warnings)
    shield = _armor_slot(character.shield, repo, is_shield=True, warnings=warnings)
    weapons = tuple(
        weapon
        for raw in character.weapons
        if (weapon := _weapon(raw, character, repo, size, warnings)) is not None
    )

    conditions = _conditions(character, repo)
    modifiers = _modifiers(character)
    skills = _skills(character, repo, class_levels, warnings)
    load = _load(character, base_scores, racial, increments, ability_damage, repo)

    domain = DomainCharacter(
        name=character.name,
        size=size,
        base_speed_ft=speed,
        class_levels=class_levels,
        base_ability_scores=base_scores,
        racial_ability_modifiers=racial,
        level_ability_increments=increments,
        ability_damage=ability_damage,
        armor=armor,
        shield=shield,
        weapons=weapons,
        natural_armor_bonus=character.natural_armor_bonus,
        deflection_bonus=character.deflection_bonus,
        other_ac_modifiers=character.other_ac_modifiers,
        max_hp=character.max_hp,
        current_hp=character.current_hp,
        temporary_hp=character.temporary_hp,
        nonlethal_damage=character.nonlethal_damage,
        skills=skills,
        feats=tuple(character.feats),
        conditions=conditions,
        stances=_stances(character.stances),
        two_weapon_fighting=_twf(character, repo),
        modifiers=modifiers,
        load=load,
    )
    return AssembledCharacter(domain, warnings)


def _resolve_size(character: CharacterRead, race: object, warnings: list[str]) -> Size:
    name = character.size or (getattr(race, "size", None) if race else None) or Size.MEDIUM.value
    try:
        return Size(name)
    except ValueError:
        warnings.append(f"Tamaño desconocido: {name}; se usa Mediano")
        return Size.MEDIUM


def _racial_modifiers(character: CharacterRead, race: object) -> dict[Ability, int]:
    modifiers: dict[Ability, int] = {}
    raw = getattr(race, "ability_modifiers", {}) if race else {}
    for key, value in raw.items():
        if key in _ABILITIES:  # skips "cualquiera" (flexible bonus, chosen below)
            modifiers[Ability(key)] = modifiers.get(Ability(key), 0) + value
    for key, value in character.racial_bonus_choices.items():
        if key in _ABILITIES:
            modifiers[Ability(key)] = modifiers.get(Ability(key), 0) + value
    return modifiers


def _abilities(raw: dict[str, int]) -> dict[Ability, int]:
    return {Ability(key): value for key, value in raw.items() if key in _ABILITIES}


def _class_levels(
    character: CharacterRead, repo: RulesRepository, warnings: list[str]
) -> tuple[ClassLevel, ...]:
    levels: list[ClassLevel] = []
    for entry in character.class_levels:
        summary = repo.class_summary(entry.class_slug)
        if summary is None:
            warnings.append(f"Clase desconocida: {entry.class_slug}")
            continue
        base_saves = _base_saves(entry.class_slug, entry.level, summary.name, repo, warnings)
        levels.append(
            ClassLevel(
                class_slug=summary.slug,
                class_name=summary.name,
                level=entry.level,
                bab_type=BabProgression(summary.bab_progression),
                hit_die=int(summary.hit_die.lstrip("dD")),
                base_saves=base_saves,
                is_prestige=entry.is_prestige or summary.is_prestige,
                is_favored=entry.is_favored,
            )
        )
    return tuple(levels)


def _base_saves(
    slug: str, level: int, class_name: str, repo: RulesRepository, warnings: list[str]
) -> dict[SaveKind, int]:
    try:
        row = repo.class_progression(slug, level)
    except RuleNotFoundError:
        warnings.append(
            f"{class_name}: sin datos de salvación a nivel {level} "
            "(progresión incompleta); se usa 0"
        )
        return {}
    return {kind: getattr(row, field) for kind, field in _SAVE_BY_ROW.items()}


def _armor_slot(
    raw: EquippedArmorIn | None,
    repo: RulesRepository,
    *,
    is_shield: bool,
    warnings: list[str],
) -> EquippedArmor | None:
    if raw is None:
        return None
    item = repo.armor_item(raw.catalog_name)
    if item is None:
        warnings.append(f"Armadura/escudo desconocido: {raw.catalog_name}")
        return None
    check_penalty = item.armor_check_penalty
    if raw.is_masterwork:
        check_penalty = min(0, check_penalty + 1)
    fields: dict[str, object] = {
        "name": item.name,
        "is_shield": is_shield,
        "ac_bonus": item.armor_bonus + raw.enhancement_bonus,
        "max_dex": item.max_dex,
        "armor_check_penalty": check_penalty,
        "arcane_spell_failure": item.arcane_spell_failure_pct,
        "category": item.category,
    }
    if raw.custom_overrides:
        fields.update({k: v for k, v in raw.custom_overrides.items() if k in fields})
    return EquippedArmor(**fields)  # type: ignore[arg-type]


def _weapon(
    raw: EquippedWeaponIn,
    character: CharacterRead,
    repo: RulesRepository,
    size: Size,
    warnings: list[str],
) -> EquippedWeapon | None:
    item = repo.weapon(raw.catalog_name)
    if item is None:
        warnings.append(f"Arma desconocida: {raw.catalog_name}")
        return None

    crit = item.critical[0] if item.critical else None
    is_ranged = item.category == _RANGED_CATEGORY
    proficient = _is_proficient(item, character, repo)

    attack_modifiers: list[Modifier] = []
    if raw.is_masterwork and raw.enhancement_bonus == 0:
        # Masterwork grants +1 to attack only; a magic bonus supersedes it.
        attack_modifiers.append(
            Modifier(
                target="ATTACK_MELEE" if not is_ranged else "ATTACK_RANGED",
                value=1,
                bonus_type=BonusType.ENHANCEMENT,
                source=f"{item.name} (obra maestra)",
                source_kind=SourceKind.ITEM,
            )
        )

    fields: dict[str, object] = {
        "name": item.name,
        "wield": Wield(raw.wielding),
        "is_ranged": is_ranged,
        "threat_range": crit.threat_range if crit else 20,
        "crit_multiplier": crit.multiplier if crit else 2,
        "is_thrown": bool((raw.custom_overrides or {}).get("is_thrown", False)),
        "damage_dice": _damage_dice(item, size),
        "damage_type": item.damage_type,
        "range_increment": item.range_increment,
        "enhancement_bonus": raw.enhancement_bonus,
        "is_proficient": proficient,
        "attack_modifiers": tuple(attack_modifiers),
    }
    if raw.custom_overrides:
        fields.update({k: v for k, v in raw.custom_overrides.items() if k in fields})
    return EquippedWeapon(**fields)  # type: ignore[arg-type]


def _damage_dice(item: object, size: Size) -> str | None:
    small = getattr(item, "damage_small", None)
    medium = getattr(item, "damage_medium", None)
    return small if size in _SMALL_OR_LESS else medium


def _is_proficient(item: object, character: CharacterRead, repo: RulesRepository) -> bool:
    proficiency = _norm(getattr(item, "proficiency", ""))
    text = " ".join(
        _norm(summary.proficiencies or "")
        for entry in character.class_levels
        if (summary := repo.class_summary(entry.class_slug)) is not None
    )
    feats = " ".join(_norm(f) for f in character.feats)

    if proficiency == "sencilla" and (
        "sencilla" in text or "competencia con armas sencillas" in feats
    ):
        return True
    if proficiency == "marcial" and (
        "marcial" in text or "competencia con armas marciales" in feats
    ):
        return True
    if proficiency == "exotica" and "competencia con arma exotica" in feats:
        return True
    # A weapon named in a proficiency/feat (e.g. racial familiarity) counts.
    weapon_name = _norm(getattr(item, "name", ""))
    return weapon_name in text or weapon_name in feats


def _conditions(character: CharacterRead, repo: RulesRepository) -> tuple[str, ...]:
    names: list[str] = []
    for slug in character.active_conditions:
        name = repo.condition_name(slug)
        names.append(name if name is not None else slug)
    if (character.is_flat_footed or character.dexterity_denied) and "Desprevenido" not in names:
        names.append("Desprevenido")
    return tuple(names)


def _modifiers(character: CharacterRead) -> tuple[Modifier, ...]:
    modifiers = [_modifier(m) for m in character.modifiers]
    for effect in character.active_effects:
        modifiers.extend(_modifier(m) for m in effect.modifiers)
    return tuple(modifiers)


def _modifier(raw: ModifierIn) -> Modifier:
    return Modifier(
        target=raw.target,
        value=raw.value,
        bonus_type=BonusType(raw.bonus_type) if raw.bonus_type else None,
        source=raw.source,
        source_kind=_source_kind(raw.source_kind),
        condition=raw.condition,
        is_active=raw.is_active,
        expires_in_rounds=raw.expires_in_rounds,
    )


def _source_kind(value: str) -> SourceKind:
    try:
        return SourceKind(value)
    except ValueError:
        return SourceKind.MANUAL


def _skills(
    character: CharacterRead,
    repo: RulesRepository,
    class_levels: tuple[ClassLevel, ...],
    warnings: list[str],
) -> tuple[SkillState, ...]:
    class_slugs = {cl.class_slug for cl in class_levels}
    slugs = set(character.skill_ranks) | set(character.skill_misc_modifiers)
    slugs |= {
        m.target.split(":", 1)[1] for m in character.modifiers if m.target.startswith("SKILL:")
    }

    states: list[SkillState] = []
    for slug in sorted(slugs):
        dto = repo.skill(slug)
        if dto is None:
            warnings.append(f"Habilidad desconocida: {slug}")
            continue
        states.append(
            SkillState(
                slug=dto.slug,
                name=dto.name,
                ability=Ability(dto.ability),
                ranks=character.skill_ranks.get(slug, 0),
                is_class_skill=any(cslug in dto.class_for for cslug in class_slugs),
                uses_armor_check_penalty=dto.armor_check_penalty,
                untrained=dto.untrained,
                misc_modifier=character.skill_misc_modifiers.get(slug, 0),
            )
        )
    return tuple(states)


def _stances(raw: StancesIn) -> Stances:
    return Stances(
        charge=raw.charge,
        fighting_defensively=raw.fighting_defensively,
        total_defense=raw.total_defense,
        power_attack=raw.power_attack,
        combat_expertise=raw.combat_expertise,
        flanking=raw.flanking,
        higher_ground=raw.higher_ground,
    )


def _twf(character: CharacterRead, repo: RulesRepository) -> TwoWeaponFighting:
    off_hands = [w for w in character.weapons if w.wielding == "off_hand"]
    if not off_hands:
        return TwoWeaponFighting()
    light = False
    for weapon in off_hands:
        item = repo.weapon(weapon.catalog_name)
        if item is not None and item.category == _LIGHT_MELEE_CATEGORY:
            light = True
    feats = {_norm(f) for f in character.feats}
    return TwoWeaponFighting(
        enabled=True,
        has_light_off_hand=light,
        has_twf_feat="combate con dos armas" in feats,
        improved="combate con dos armas mejorado" in feats,
        greater="combate con dos armas mayor" in feats,
    )


def _load(
    character: CharacterRead,
    base: dict[Ability, int],
    racial: dict[Ability, int],
    increments: dict[Ability, int],
    damage: dict[Ability, int],
    repo: RulesRepository,
) -> CarryingLoad | None:
    if character.load_carried_lb is None:
        return None
    strength = (
        base.get(Ability.STR, 10)
        + racial.get(Ability.STR, 0)
        + increments.get(Ability.STR, 0)
        - damage.get(Ability.STR, 0)
    )
    light, medium, heavy = repo.carrying_capacity(max(1, strength))
    return CarryingLoad(
        light_max=light,
        medium_max=medium,
        heavy_max=heavy,
        carried_lb=character.load_carried_lb,
    )


def _norm(value: str) -> str:
    from pf_tracker.rules.vendor.pathfinder_reglas import _norm as vendor_norm

    return vendor_norm(value)
