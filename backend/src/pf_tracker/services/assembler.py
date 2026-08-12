"""Assemble a persisted character into a resolved domain :class:`Character`.

This is the seam between the rules corpus (Spanish catalog) and the pure domain
engine (English, numeric). It resolves catalog references to concrete stats, applies
masterwork/enhancement, derives proficiency and two-weapon configuration, and maps
conditions and modifiers. Anything it cannot resolve becomes a warning, never a
silent failure. An NPC variant can reuse this unchanged (see the ``kind`` field).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace
from itertools import combinations

from pf_tracker.domain.derivation import base_bab
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
from pf_tracker.rules.catalog import FeatDTO, list_ref
from pf_tracker.rules.feat_effects import apply_feats, effect_holds
from pf_tracker.rules.feat_slots import ClassLevelRef, FeatBudget, build_budget
from pf_tracker.rules.feat_substitutions import allows_finesse, resolve_substitutions
from pf_tracker.rules.feat_targets import parse_feat_target
from pf_tracker.rules.feat_vocabulary import is_scalar_feat_bonus, parse_feat_bonus_type
from pf_tracker.rules.repository import RuleNotFoundError, RulesRepository
from pf_tracker.rules.weapon_feats import (
    FEAT_WEAPONS,
    WeaponFeatContext,
    WeaponProfile,
    critical_notes,
    drop_superseded,
    has_situational_weapon_effect,
    is_feat_stance,
    is_global_feat_target,
    is_optional,
    is_single_attack,
    is_weapon_scoped,
    resolve_for_weapon,
    widen_threat_range,
)
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
_UNARMED_CATEGORY = "Ataques sin armas"


class AssembledCharacter:
    """A domain character plus the warnings raised while assembling it."""

    def __init__(
        self,
        character: DomainCharacter,
        warnings: list[str],
        feats: FeatBudget | None = None,
    ) -> None:
        self.character = character
        self.warnings = warnings
        #: What the character may pick and what was handed to them.
        self.feats = feats or FeatBudget()


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
    feat_context = _feat_context(character, class_levels)
    # Feats a class hands over are the character's whether or not anyone typed them
    # in: a monk *has* Improved Unarmed Strike, and without it took -4 with their
    # own fists.
    budget = _feat_budget(character, class_levels, repo, warnings)
    owned_names = list(dict.fromkeys([*character.feats, *budget.granted]))
    owned_feats = _owned_feats(owned_names, repo)
    weapons = tuple(
        [
            line
            for raw in character.weapons
            if (weapon := _weapon(raw, character, owned_names, repo, size, warnings)) is not None
            for line in _weapon_lines(weapon, owned_feats, feat_context)
        ]
        + _feat_weapons(character, owned_feats, repo, size, feat_context, warnings)
    )

    conditions = _conditions(character, repo)
    modifiers = _modifiers(character) + _feat_modifiers(
        owned_feats, feat_context, character.stances.feat_stances, warnings
    )
    skills = _skills(character, repo, class_levels, warnings)
    load = _load(character, base_scores, racial, increments, ability_damage, repo)
    # Feats that replace a term rather than add to one. They cannot travel as
    # modifiers, so they reach the derivation as flags on the character.
    swaps = resolve_substitutions(owned_feats)

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
        feats=tuple(owned_names),
        conditions=conditions,
        stances=_stances(character.stances),
        two_weapon_fighting=_twf(character, repo),
        cmb_uses_dexterity=swaps.cmb_uses_dexterity,
        cmd_uses_hit_dice=swaps.cmd_uses_hit_dice,
        has_weapon_finesse=swaps.melee_attack_uses_dexterity,
        modifiers=modifiers,
        load=load,
    )
    return AssembledCharacter(domain, warnings, budget)


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
    feat_names: Sequence[str],
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
    is_unarmed = item.category == _UNARMED_CATEGORY
    proficient = _is_proficient(item, character, feat_names, repo)

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
        "is_unarmed": is_unarmed,
        "threat_range": crit.threat_range if crit else 20,
        "crit_multiplier": crit.multiplier if crit else 2,
        "is_thrown": bool((raw.custom_overrides or {}).get("is_thrown", False)),
        "damage_dice": _damage_dice(item, size),
        "damage_type": item.damage_type,
        "range_increment": item.range_increment,
        "enhancement_bonus": raw.enhancement_bonus,
        "is_proficient": proficient,
        "allows_finesse": allows_finesse(category=item.category, name=item.name),
        "attack_modifiers": tuple(attack_modifiers),
    }
    if raw.custom_overrides:
        fields.update({k: v for k, v in raw.custom_overrides.items() if k in fields})
    return EquippedWeapon(**fields)  # type: ignore[arg-type]


def _damage_dice(item: object, size: Size) -> str | None:
    small = getattr(item, "damage_small", None)
    medium = getattr(item, "damage_medium", None)
    return small if size in _SMALL_OR_LESS else medium


def _is_proficient(
    item: object, character: CharacterRead, feat_names: Sequence[str], repo: RulesRepository
) -> bool:
    """Whether the character can use this weapon without the -4.

    ``feat_names`` is the *effective* list, including feats a class hands over: a
    monk never types Improved Unarmed Strike, but they have it.
    """
    proficiency = _norm(getattr(item, "proficiency", ""))
    weapon_name = _norm(getattr(item, "name", ""))
    text = " ".join(
        _norm(summary.proficiencies or "")
        for entry in character.class_levels
        if (summary := repo.class_summary(entry.class_slug)) is not None
    )
    feats = " ".join(_norm(f) for f in feat_names)

    # Racial weapon familiarity, which no class proficiency line mentions. Two halves:
    # a short list the race simply *has* — an elf wizard can use a rapier — and a word
    # that makes any weapon carrying it martial. The second is not proficiency: the
    # elven curve blade stops being exotic for an elf, and it still takes a class with
    # martial weapons to wield it without the -4.
    race = repo.race(character.race)
    if race is not None:
        if weapon_name in {_norm(name) for name in race.weapon_proficiencies}:
            return True
        if any(_norm(word) in weapon_name for word in race.weapon_words):
            proficiency = "marcial"

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
    # Improved Unarmed Strike is what makes an unarmed strike a real weapon, and the
    # monk's proficiency line reads "armas de monje seleccionadas" — it never says
    # "sencilla", so without this a monk took -4 with their own fists.
    if getattr(item, "category", "") == _UNARMED_CATEGORY and "impacto sin arma mejorado" in feats:
        return True
    # A weapon named outright in a class proficiency line or a feat (the wizard's
    # five, a cleric's favoured weapon) counts.
    return weapon_name in text or weapon_name in feats


def _conditions(character: CharacterRead, repo: RulesRepository) -> tuple[str, ...]:
    names: list[str] = []
    for slug in character.active_conditions:
        name = repo.condition_name(slug)
        names.append(name if name is not None else slug)
    if (character.is_flat_footed or character.dexterity_denied) and "Desprevenido" not in names:
        names.append("Desprevenido")
    return tuple(names)


#: Safety valve on the variant explosion. In practice only two optional feats ever
#: apply to one weapon (melee: Power Attack + Combat Expertise; ranged: Deadly Aim +
#: Rapid Shot), so this is never reached; it exists so a future corpus cannot turn
#: one weapon into dozens of lines.
_MAX_OPTIONAL_FEATS_PER_WEAPON = 3


def _owned_feats(names: Sequence[str], repo: RulesRepository) -> tuple[FeatDTO, ...]:
    """The catalog entries for the feats this character has."""
    owned = {_norm(name) for name in names}
    if not owned:
        return ()
    return tuple(feat for feat in repo.feats() if _norm(feat.name) in owned)


def _feat_budget(
    character: CharacterRead,
    class_levels: tuple[ClassLevel, ...],
    repo: RulesRepository,
    warnings: list[str],
) -> FeatBudget:
    """Slots from level, class and race, with an over-budget warning that does not
    block: house rules are real, so the sheet reports rather than refuses."""
    race = repo.race(character.race)
    budget = build_budget(
        feat_levels=repo.meta.feat_levels,
        class_levels=[ClassLevelRef(cl.class_name, cl.level) for cl in class_levels],
        class_slots={
            cl.class_name: summary.bonus_feats
            for cl in class_levels
            if (summary := repo.class_summary(cl.class_slug)) is not None
        },
        race_name=race.name if race else None,
        race_slots=race.bonus_feats if race else [],
        chosen=character.feats,
    )
    # Resolve every restricted list the character's slots point at, once each, at the
    # highest level that references it. A slot pinning a branch of a list is a list of
    # its own, so the branch is part of what makes two references distinct.
    highest: dict[tuple[str, str | None], int] = {}
    for entry in budget.slots:
        if entry.slot.list_key is None:
            continue
        ref = (entry.slot.list_key, entry.slot.list_option)
        highest[ref] = max(highest.get(ref, entry.level), entry.level)

    if highest:
        budget = replace(
            budget,
            lists={
                list_ref(key, option): tuple(repo.restricted_feat_list(key, level, option))
                for (key, option), level in highest.items()
            },
            list_notes={
                list_ref(key, option): note
                for key, option in highest
                if (note := repo.restricted_list_note(key, option)) is not None
            },
        )

    if budget.is_over_budget:
        warnings.append(f"Dotes: has elegido {budget.spent} y te corresponden {budget.available}")
    return budget


def _feat_context(
    character: CharacterRead, class_levels: tuple[ClassLevel, ...]
) -> WeaponFeatContext:
    return WeaponFeatContext(
        base_attack_bonus=sum(base_bab(cl.bab_type, cl.level) for cl in class_levels),
        hit_dice=sum(cl.level for cl in class_levels),
        skill_ranks=dict(character.skill_ranks),
        feat_options=dict(character.feat_options),
    )


def _feat_modifiers(
    feats: tuple[FeatDTO, ...],
    context: WeaponFeatContext,
    active: Sequence[str],
    warnings: list[str],
) -> tuple[Modifier, ...]:
    """Modifiers contributed passively by feats that apply to the whole character.

    Weapon-scoped feats are excluded: they are resolved per weapon instead, where
    the grip and the chosen weapon are known. So are passive feats with a
    situational weapon effect (``Disparo a bocajarro``) — `_weapon_lines` turns
    those into a line of their own, and a warning here as well would say the same
    thing twice, once without any numbers.

    Effects the producer cannot turn into a number — declared feats, situational
    conditions, multipliers — come back as notes and are surfaced as warnings, so
    the GM sees what the sheet is *not* accounting for rather than assuming it is.
    """
    global_feats = [
        feat
        for feat in feats
        if not is_weapon_scoped(feat)
        and not is_feat_stance(feat)
        and not has_situational_weapon_effect(feat, context)
    ]
    applied = apply_feats(global_feats, context)
    warnings.extend(applied.notes)
    return applied.modifiers + _active_feat_stances(feats, active, context)


def _active_feat_stances(
    feats: tuple[FeatDTO, ...], active: Sequence[str], context: WeaponFeatContext
) -> tuple[Modifier, ...]:
    """Modifiers from the declared feats the GM has switched on this round.

    They are skipped by the passive producer precisely because they are declared, so
    toggling one here is what makes it apply. The numbers come from the corpus, so
    ``Acometer`` costs the 2 AC the data says and nothing is recomputed.
    """
    switched_on = {_norm(name) for name in active}
    chosen = [f for f in feats if is_feat_stance(f) and _norm(f.name) in switched_on]
    if not chosen:
        return ()

    modifiers: list[Modifier] = []
    for feat in chosen:
        for effect in feat.effects:
            # Combat Expertise states one block per BAB band; without this the stance
            # summed all six at once, giving +21 AC at level 8.
            if not effect_holds(effect, context):
                continue
            for raw in effect.modifiers:
                # The weapon half of a feat like `Pericia en combate` is already on
                # its attack line; emitting it here as well would apply it twice.
                if not is_global_feat_target(raw.target):
                    continue
                target = parse_feat_target(raw.target)
                if target is None or not isinstance(raw.value, int):
                    continue
                if not is_scalar_feat_bonus(raw.bonus_type):
                    continue
                modifiers.append(
                    Modifier(
                        target=target,
                        value=raw.value,
                        bonus_type=parse_feat_bonus_type(raw.bonus_type),
                        source=feat.name,
                        source_kind=SourceKind.STANCE,
                    )
                )
    return tuple(modifiers)


def _weapon_lines(
    weapon: EquippedWeapon, feats: tuple[FeatDTO, ...], context: WeaponFeatContext
) -> list[EquippedWeapon]:
    """The weapon's own attack line, plus one per combination of optional feats.

    A feat the GM declares before attacking does not change the weapon; it describes
    a different way of using it. Modelling each as its own weapon means the sheet
    shows "Mandoble" and "Mandoble (Ataque poderoso)" side by side, and the GM picks
    at the table instead of toggling and re-reading.

    A passive feat with a situational weapon effect (``Disparo a bocajarro``) joins
    the same pool: whether it applies is also a per-attack judgment call, just the
    GM's rather than the player's, so it gets a line alongside the declared feats'
    rather than a warning with no numbers on it.
    """
    profile = _profile_of(weapon)

    # A superseded feat has no effect at all, so it is dropped before anything else:
    # it must not fold into the base line nor spawn a variant of its own.
    effective = drop_superseded(feats)

    # Excludes a passive-but-situational feat too: `is_optional` alone would miss
    # it (it is not declared), and it must never fold into the unconditional base
    # line the way an *unconditional* passive feat does.
    always = [
        f
        for f in effective
        if not is_optional(f)
        and is_weapon_scoped(f)
        and not has_situational_weapon_effect(f, context)
    ]
    # Critical feats fire with whatever you are holding, so they annotate the base
    # line and every variant inherits them.
    annotated = replace(weapon, notes=weapon.notes + critical_notes(effective))
    base = _with_feats(annotated, always, profile, context, suffix=None)

    optional = [
        f
        for f in effective
        if (is_optional(f) or has_situational_weapon_effect(f, context))
        and _affects(f, profile, context)
    ]
    lines = [base]
    for combination in _combinations(optional[:_MAX_OPTIONAL_FEATS_PER_WEAPON]):
        label = " + ".join(feat.name for feat in combination)
        lines.append(_with_feats(base, list(combination), profile, context, suffix=label))
    return lines


def _feat_weapons(
    character: CharacterRead,
    feats: tuple[FeatDTO, ...],
    repo: RulesRepository,
    size: Size,
    context: WeaponFeatContext,
    warnings: list[str],
) -> list[EquippedWeapon]:
    """Lines for feats that are a way of attacking rather than a weapon modifier.

    ``Ira de la medusa`` is a full attack of unarmed strikes with two extra attacks:
    it is built from the weapon it is based on and stands on its own, because a full
    attack cannot mix armed and unarmed strikes. It therefore never combines with the
    variants of a carried weapon.
    """
    lines: list[EquippedWeapon] = []
    for feat in feats:
        base_name = FEAT_WEAPONS.get(feat.name)
        if base_name is None:
            continue
        base = _weapon(
            EquippedWeaponIn(catalog_name=base_name, wielding=Wield.ONE_HANDED.value),
            character,
            [f.name for f in feats],
            repo,
            size,
            warnings,
        )
        if base is None:
            continue
        lines.append(_with_feats(base, [feat], _profile_of(base), context, suffix=feat.name))
    return lines


def _profile_of(weapon: EquippedWeapon) -> WeaponProfile:
    return WeaponProfile(
        name=weapon.name,
        wield=weapon.wield,
        is_ranged=weapon.is_ranged,
        is_unarmed=weapon.is_unarmed,
    )


def _affects(feat: FeatDTO, profile: WeaponProfile, context: WeaponFeatContext) -> bool:
    """Whether a feat changes any number for this weapon; if not, it is no variant."""
    resolved = resolve_for_weapon(feat, profile, context)
    return bool(
        resolved.attack
        or resolved.damage
        or resolved.threat_range_factor > 1
        or resolved.damage_dice_multiplier > 1
    )


def _combinations(feats: list[FeatDTO]) -> list[tuple[FeatDTO, ...]]:
    """Every non-empty combination, shortest first, so single feats read first."""
    result: list[tuple[FeatDTO, ...]] = []
    for size in range(1, len(feats) + 1):
        result.extend(combinations(feats, size))
    return result


def _with_feats(
    weapon: EquippedWeapon,
    feats: list[FeatDTO],
    profile: WeaponProfile,
    context: WeaponFeatContext,
    *,
    suffix: str | None,
) -> EquippedWeapon:
    """Fold a set of feats into a copy of ``weapon``."""
    attack = list(weapon.attack_modifiers)
    damage = list(weapon.damage_modifiers)
    cmb = list(weapon.cmb_modifiers)
    threat_range = weapon.threat_range
    dice_multiplier = weapon.damage_dice_multiplier
    first_only = weapon.dice_multiplier_first_attack_only
    single = weapon.single_attack or any(is_single_attack(feat) for feat in feats)
    extra_attacks = weapon.extra_attacks_at_full_bab
    conditions: list[str] = []

    for feat in feats:
        resolved = resolve_for_weapon(feat, profile, context)
        attack.extend(resolved.attack)
        damage.extend(resolved.damage)
        cmb.extend(resolved.cmb)
        threat_range = widen_threat_range(threat_range, resolved.threat_range_factor)
        extra_attacks += resolved.extra_attacks_at_full_bab
        if resolved.condition:
            conditions.append(resolved.condition)
        if resolved.damage_dice_multiplier > 1:
            dice_multiplier *= resolved.damage_dice_multiplier
            first_only = first_only or resolved.dice_multiplier_first_attack_only

    # The situation a line only applies in is part of its name, so the GM reads the
    # numbers and the caveat together instead of applying it unaware.
    label = suffix
    if label is not None and conditions:
        label = f"{label} — sólo {'; '.join(conditions)}"

    return replace(
        weapon,
        name=weapon.name if label is None else f"{weapon.name} ({label})",
        threat_range=threat_range,
        attack_modifiers=tuple(attack),
        damage_modifiers=tuple(damage),
        cmb_modifiers=tuple(cmb),
        damage_dice_multiplier=dice_multiplier,
        dice_multiplier_first_attack_only=first_only,
        extra_attacks_at_full_bab=extra_attacks,
        single_attack=single,
    )


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
    """Every skill in the catalog, whether or not the character has touched it.

    A sheet lists all of them because a GM rolls Percepción at 0 ranks constantly,
    and because the editor shows a line per skill: deriving the ability modifier for
    the untouched ones in the frontend would put game arithmetic in TypeScript.
    Skills the character *has* state for are flagged, since only those can be wrong.
    """
    class_slugs = {cl.class_slug for cl in class_levels}
    tracked = set(character.skill_ranks) | set(character.skill_misc_modifiers)
    tracked |= {
        m.target.split(":", 1)[1] for m in character.modifiers if m.target.startswith("SKILL:")
    }

    known = {dto.slug for dto in repo.skills}
    for slug in sorted(tracked - known):
        warnings.append(f"Habilidad desconocida: {slug}")

    states: list[SkillState] = []
    for dto in sorted(repo.skills, key=lambda s: s.slug):
        states.append(
            SkillState(
                slug=dto.slug,
                name=dto.name,
                ability=Ability(dto.ability),
                ranks=character.skill_ranks.get(dto.slug, 0),
                is_class_skill=any(cslug in dto.class_for for cslug in class_slugs),
                uses_armor_check_penalty=dto.armor_check_penalty,
                untrained=dto.untrained,
                misc_modifier=character.skill_misc_modifiers.get(dto.slug, 0),
                is_tracked=dto.slug in tracked,
            )
        )
    return tuple(states)


def _stances(raw: StancesIn) -> Stances:
    return Stances(
        charge=raw.charge,
        fighting_defensively=raw.fighting_defensively,
        total_defense=raw.total_defense,
        flanking=raw.flanking,
        higher_ground=raw.higher_ground,
        feat_stances=tuple(raw.feat_stances),
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
