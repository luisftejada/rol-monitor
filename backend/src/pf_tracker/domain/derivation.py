"""The derivation engine: turns a resolved :class:`Character` into a combat sheet.

Every derived number is produced by the stacking engine over a list of modifiers,
so each carries its full breakdown (applied and suppressed). Structural
contributions (the base 10 of AC, ability modifiers, BAB, size) are emitted as
untyped modifiers so they appear in the breakdown and always stack.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from fractions import Fraction

from pf_tracker.domain.conditions import condition_modifiers, denies_dexterity, prevents_actions
from pf_tracker.domain.enums import (
    Ability,
    BabProgression,
    BonusType,
    ModifierTarget,
    SaveKind,
    SourceKind,
    Wield,
    ability_target,
    skill_target,
)
from pf_tracker.domain.models import CarryingLoad, Character, EquippedWeapon
from pf_tracker.domain.modifiers import Modifier, ResolvedValue, resolve
from pf_tracker.domain.rounding import round_down, scaled
from pf_tracker.domain.sizes import SIZE_AC_ATTACK_MOD, SIZE_CMB_CMD_MOD, SIZE_STEALTH_MOD
from pf_tracker.domain.stances import stance_modifiers

_SAVE_ABILITY: dict[SaveKind, Ability] = {
    SaveKind.FORTITUDE: Ability.CON,
    SaveKind.REFLEX: Ability.DEX,
    SaveKind.WILL: Ability.WIS,
}
_STEALTH_SLUG = "sigilo"

# Encumbrance effects by load category, applied as if wearing medium/heavy armor.
_LOAD_MAX_DEX: dict[str, int] = {"medium": 3, "heavy": 1, "over": 1}
_LOAD_CHECK_PENALTY: dict[str, int] = {"medium": -3, "heavy": -6, "over": -6}


def load_category(load: CarryingLoad | None) -> str:
    """Classify the current load: none | light | medium | heavy | over."""
    if load is None:
        return "none"
    if load.carried_lb <= load.light_max:
        return "light"
    if load.carried_lb <= load.medium_max:
        return "medium"
    if load.carried_lb <= load.heavy_max:
        return "heavy"
    return "over"


# --------------------------------------------------------------------------- results
@dataclass(frozen=True, slots=True)
class AbilityScoreResult:
    ability: Ability
    base: int
    racial: int
    level_increment: int
    damage: int
    modifiers: ResolvedValue
    score: int
    modifier: int


@dataclass(frozen=True, slots=True)
class SaveResult:
    kind: SaveKind
    resolved: ResolvedValue


@dataclass(frozen=True, slots=True)
class ACResult:
    resolved: ResolvedValue
    touch: int
    flat_footed: int
    touch_applied: list[Modifier]
    flat_footed_applied: list[Modifier]
    max_dex_cap: int | None
    cap_binds: bool


@dataclass(frozen=True, slots=True)
class BabResult:
    total: int
    iteratives: list[int]


@dataclass(frozen=True, slots=True)
class AttackRoutine:
    weapon_name: str
    is_ranged: bool
    attack_bonuses: list[int]
    attack_line: str
    attack_breakdown: ResolvedValue
    damage_expression: str | None
    #: Set only when the first attack differs from the rest (Manyshot): the sheet
    #: shows both, since "2d8 then 1d8" is not one number.
    first_attack_damage_expression: str | None
    damage_breakdown: ResolvedValue
    threat_range: int
    crit_multiplier: int
    damage_type: str | None
    range_increment: str | None
    is_proficient: bool
    #: Prose annotations carried by the weapon (see :attr:`EquippedWeapon.notes`).
    notes: tuple[str, ...] = ()
    #: The CMB you have *while using this line*, set only when the line changes it.
    #: Power Attack's penalty applies to combat manoeuvres as well as to attacks, so
    #: a sheet showing only the character's CMB would overstate it by up to 6.
    cmb: ResolvedValue | None = None
    #: The AC you have while using this line, set only when it differs. Both hands on
    #: the weapon means the shield is not being used, so its bonus is not yours that
    #: round — the sheet's own AC assumes you are holding it.
    ac: ACResult | None = None
    #: See :attr:`EquippedWeapon.variant_label`.
    variant_label: str | None = None
    #: See :attr:`EquippedWeapon.variant_key`.
    variant_key: str | None = None


@dataclass(frozen=True, slots=True)
class SkillResult:
    slug: str
    name: str
    ability: Ability
    resolved: ResolvedValue
    is_class_skill: bool
    untrained_violation: bool
    #: The total split the way a player reads a skill line: ranks, the ability
    #: modifier, and everything else lumped together. The three always sum to
    #: ``resolved.total``, and ``resolved`` still carries the itemised breakdown —
    #: this partition exists so the UI never has to add anything up itself.
    ranks: int = 0
    ability_modifier: int = 0
    other_modifiers: int = 0
    #: ``resolved.applied`` minus the ranks and ability entries — what the "others"
    #: column's tooltip shows. Ranks and the ability modifier already have their own
    #: columns; repeating them here would just restate numbers the GM can already see.
    other_applied: list[Modifier] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class SpeedResult:
    base_ft: int
    final_ft: int
    reductions: list[str]


@dataclass(frozen=True, slots=True)
class CombatSheet:
    abilities: dict[Ability, AbilityScoreResult]
    ac: ACResult
    saves: dict[SaveKind, SaveResult]
    bab: BabResult
    initiative: ResolvedValue
    cmb: ResolvedValue
    cmd: ResolvedValue
    attacks: list[AttackRoutine]
    skills: list[SkillResult]
    speed: SpeedResult
    armor_check_penalty: int
    arcane_spell_failure: int
    max_hp: int
    current_hp: int
    temporary_hp: int
    nonlethal_damage: int
    carrying_capacity: dict[str, int] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------- helpers
def ability_modifier(score: int) -> int:
    """``(score - 10) // 2``, negative-safe, via the shared rounding helper."""
    return round_down(Fraction(score - 10, 2))


def base_bab(progression: BabProgression, level: int) -> int:
    """Base attack bonus a class contributes at ``level`` (``avance.bab_por_tipo``)."""
    if progression == BabProgression.FULL:
        return level
    if progression == BabProgression.THREE_QUARTER:
        return level * 3 // 4
    return level // 2


def iterative_bonuses(total_bab: int) -> list[int]:
    """Iterative attack bonuses from a total BAB (extra attack per +5 over +1, max 4)."""
    extra = min(4, max(0, (total_bab - 1) // 5))
    return [total_bab - 5 * step for step in range(extra + 1)]


def _struct(target: str, value: int, source: str, kind: SourceKind) -> Modifier:
    """An untyped 'structural' modifier (base, ability, size, BAB) for the breakdown."""
    return Modifier(target=target, value=value, bonus_type=None, source=source, source_kind=kind)


# --------------------------------------------------------------------------- abilities
def derive_abilities(character: Character) -> dict[Ability, AbilityScoreResult]:
    pool = [*character.modifiers, *condition_modifiers(character.conditions)]
    results: dict[Ability, AbilityScoreResult] = {}
    for ability in Ability:
        base = character.base_ability_scores.get(ability, 10)
        racial = character.racial_ability_modifiers.get(ability, 0)
        increment = character.level_ability_increments.get(ability, 0)
        damage = character.ability_damage.get(ability, 0)
        resolved = resolve(ability_target(ability), pool)
        score = max(0, base + racial + increment - damage + resolved.total)
        results[ability] = AbilityScoreResult(
            ability=ability,
            base=base,
            racial=racial,
            level_increment=increment,
            damage=damage,
            modifiers=resolved,
            score=score,
            modifier=ability_modifier(score),
        )
    return results


def _general_pool(character: Character, bab: int) -> list[Modifier]:
    """External + condition + stance modifiers shared by every derived value."""
    return [
        *character.modifiers,
        *condition_modifiers(character.conditions),
        *stance_modifiers(character.stances, bab),
    ]


# --------------------------------------------------------------------------- AC
def derive_ac(
    character: Character,
    abilities: dict[Ability, AbilityScoreResult],
    general_pool: list[Modifier],
) -> ACResult:
    dex_mod = abilities[Ability.DEX].modifier
    caps = [
        item.max_dex
        for item in (character.armor, character.shield)
        if item is not None and item.max_dex is not None
    ]
    load_cap = _LOAD_MAX_DEX.get(load_category(character.load))
    if load_cap is not None:
        caps.append(load_cap)
    cap = min(caps) if caps else None
    dex_denied = denies_dexterity(character.conditions)

    ac_mods: list[Modifier] = [_struct(ModifierTarget.AC.value, 10, "base", SourceKind.BASE)]

    if character.armor is not None:
        ac_mods.append(
            Modifier(
                ModifierTarget.AC.value,
                character.armor.ac_bonus,
                BonusType.ARMOR,
                character.armor.name,
                SourceKind.ARMOR,
            )
        )
    if character.shield is not None:
        ac_mods.append(
            Modifier(
                ModifierTarget.AC.value,
                character.shield.ac_bonus,
                BonusType.SHIELD,
                character.shield.name,
                SourceKind.SHIELD,
            )
        )
    if character.natural_armor_bonus:
        ac_mods.append(
            Modifier(
                ModifierTarget.AC.value,
                character.natural_armor_bonus,
                BonusType.NATURAL_ARMOR,
                "Armadura natural",
                SourceKind.RACE,
            )
        )
    if character.deflection_bonus:
        ac_mods.append(
            Modifier(
                ModifierTarget.AC.value,
                character.deflection_bonus,
                BonusType.DEFLECTION,
                "Deflexión",
                SourceKind.ITEM,
            )
        )
    if character.other_ac_modifiers:
        ac_mods.append(
            _struct(
                ModifierTarget.AC.value, character.other_ac_modifiers, "Otros", SourceKind.MANUAL
            )
        )

    dex_to_ac = dex_mod if cap is None else min(dex_mod, cap)
    cap_binds = cap is not None and dex_mod > cap
    if not dex_denied:
        label = "Destreza"
        if cap_binds:
            label = f"Destreza (limitada por armadura, máx. {cap:+d})"
        ac_mods.append(_struct(ModifierTarget.AC.value, dex_to_ac, label, SourceKind.ABILITY))

    size_mod = SIZE_AC_ATTACK_MOD[character.size]
    if size_mod:
        ac_mods.append(
            Modifier(ModifierTarget.AC.value, size_mod, BonusType.SIZE, "Tamaño", SourceKind.SIZE)
        )

    resolved = resolve(ModifierTarget.AC.value, [*general_pool, *ac_mods])

    excluded_touch = {BonusType.ARMOR, BonusType.SHIELD, BonusType.NATURAL_ARMOR}
    touch_applied = [m for m in resolved.applied if m.bonus_type not in excluded_touch]
    flat_applied = [
        m
        for m in resolved.applied
        if m.source_kind != SourceKind.ABILITY and m.bonus_type != BonusType.DODGE
    ]
    return ACResult(
        resolved=resolved,
        touch=sum(m.value for m in touch_applied),
        flat_footed=sum(m.value for m in flat_applied),
        touch_applied=touch_applied,
        flat_footed_applied=flat_applied,
        max_dex_cap=cap,
        cap_binds=cap_binds,
    )


# --------------------------------------------------------------------------- BAB / saves
def derive_bab(character: Character) -> BabResult:
    total = sum(base_bab(cl.bab_type, cl.level) for cl in character.class_levels)
    return BabResult(total=total, iteratives=iterative_bonuses(total))


def derive_saves(
    character: Character,
    abilities: dict[Ability, AbilityScoreResult],
    general_pool: list[Modifier],
) -> dict[SaveKind, SaveResult]:
    results: dict[SaveKind, SaveResult] = {}
    for kind in SaveKind:
        target = _SAVE_TARGET[kind]
        base = sum(cl.base_saves.get(kind, 0) for cl in character.class_levels)
        ability = _SAVE_ABILITY[kind]
        ability_mod = abilities[ability].modifier
        mods = [
            _struct(target, base, "Base (clases)", SourceKind.CLASS),
            _struct(target, ability_mod, ability.label, SourceKind.ABILITY),
        ]
        results[kind] = SaveResult(kind=kind, resolved=resolve(target, [*general_pool, *mods]))
    return results


_SAVE_TARGET: dict[SaveKind, str] = {
    SaveKind.FORTITUDE: ModifierTarget.SAVE_FORT.value,
    SaveKind.REFLEX: ModifierTarget.SAVE_REF.value,
    SaveKind.WILL: ModifierTarget.SAVE_WILL.value,
}


# --------------------------------------------------------------------------- init / CM
def derive_initiative(
    abilities: dict[Ability, AbilityScoreResult], general_pool: list[Modifier]
) -> ResolvedValue:
    dex = _struct(
        ModifierTarget.INITIATIVE.value,
        abilities[Ability.DEX].modifier,
        "Destreza",
        SourceKind.ABILITY,
    )
    return resolve(ModifierTarget.INITIATIVE.value, [*general_pool, dex])


def derive_cmb(
    character: Character,
    abilities: dict[Ability, AbilityScoreResult],
    bab: int,
    general_pool: list[Modifier],
    extra: Sequence[Modifier] = (),
) -> ResolvedValue:
    """The character's CMB, optionally with the modifiers one attack line adds.

    ``extra`` is how a line that costs CMB (Power Attack) states its price without
    the character having to carry a penalty it is not currently paying.
    """
    size = SIZE_CMB_CMD_MOD[character.size]
    # `Maniobras ágiles` swaps which ability feeds CMB. It is unconditional — unlike
    # Weapon Finesse there is no weapon to qualify and no shield clause — so it
    # applies as stated rather than as the better of the two.
    cmb_ability = Ability.DEX if character.cmb_uses_dexterity else Ability.STR
    mods = [
        _struct(ModifierTarget.CMB.value, bab, "Ataque base", SourceKind.BASE),
        _struct(
            ModifierTarget.CMB.value,
            abilities[cmb_ability].modifier,
            cmb_ability.label,
            SourceKind.ABILITY,
        ),
    ]
    if size:
        mods.append(
            Modifier(ModifierTarget.CMB.value, size, BonusType.SIZE, "Tamaño", SourceKind.SIZE)
        )
    return resolve(ModifierTarget.CMB.value, [*general_pool, *mods, *extra])


def derive_cmd(
    character: Character,
    abilities: dict[Ability, AbilityScoreResult],
    bab: int,
    general_pool: list[Modifier],
) -> ResolvedValue:
    size = SIZE_CMB_CMD_MOD[character.size]
    # `Entrenamiento en combate defensivo` counts Hit Dice here instead of base
    # attack, which is what makes it worth taking for a caster. It says explicitly
    # that CMB is unaffected, so the swap lives in this function only.
    if character.cmd_uses_hit_dice:
        attack_term, attack_label = character.total_level, "Dados de Golpe"
    else:
        attack_term, attack_label = bab, "Ataque base"
    mods = [
        _struct(ModifierTarget.CMD.value, 10, "base", SourceKind.BASE),
        _struct(ModifierTarget.CMD.value, attack_term, attack_label, SourceKind.BASE),
        _struct(
            ModifierTarget.CMD.value, abilities[Ability.STR].modifier, "Fuerza", SourceKind.ABILITY
        ),
    ]
    if not denies_dexterity(character.conditions):
        mods.append(
            _struct(
                ModifierTarget.CMD.value,
                abilities[Ability.DEX].modifier,
                "Destreza",
                SourceKind.ABILITY,
            )
        )
    if size:
        mods.append(
            Modifier(ModifierTarget.CMD.value, size, BonusType.SIZE, "Tamaño", SourceKind.SIZE)
        )
    return resolve(ModifierTarget.CMD.value, [*general_pool, *mods])


# --------------------------------------------------------------------------- attacks
def _twf_penalty(character: Character) -> int | None:
    twf = character.two_weapon_fighting
    if not twf.enabled:
        return None
    if twf.has_twf_feat:
        return -2
    if twf.has_light_off_hand:
        return -4
    return -6


def _str_damage(str_mod: int, weapon: EquippedWeapon) -> int:
    if weapon.is_ranged and not weapon.is_thrown:
        return 0
    if weapon.is_thrown:
        return str_mod
    if weapon.wield == Wield.TWO_HANDED:
        return scaled(str_mod, Fraction(3, 2))
    if weapon.wield == Wield.OFF_HAND:
        return scaled(str_mod, Fraction(1, 2))
    return str_mod


_DICE = re.compile(r"^(\d+)d(\d+)$")


def multiply_damage_dice(dice: str, factor: int) -> str:
    """Roll the same dice more times: ``1d8`` twice is ``2d8``.

    Anything that is not a plain ``NdM`` is returned untouched rather than guessed
    at, so an unexpected corpus notation degrades to the base expression.
    """
    if factor <= 1:
        return dice
    match = _DICE.match(dice.strip())
    if match is None:
        return dice
    count, faces = int(match.group(1)), match.group(2)
    return f"{count * factor}d{faces}"


def _damage_expression(dice: str | None, total: int, factor: int) -> str | None:
    """``2d6+7``: the dice (possibly multiplied) plus the resolved flat damage."""
    if dice is None:
        return None
    rolled = multiply_damage_dice(dice, factor)
    return f"{rolled}{total:+d}" if total else rolled


def _two_handed(weapon: EquippedWeapon) -> bool:
    """Whether this line occupies both hands. Ranged weapons are excluded: a bow is
    held in two hands but no shield rule turns on that, and treating it as such would
    strip an archer's shield for no reason the manual gives."""
    return weapon.wield is Wield.TWO_HANDED and not weapon.is_ranged


def _buckler_in_the_way(character: Character, weapon: EquippedWeapon) -> bool:
    """A buckler kept on while the shield arm helps hold the weapon."""
    shield = character.shield
    return _two_handed(weapon) and shield is not None and shield.is_buckler


def _shield_set_aside(character: Character, weapon: EquippedWeapon) -> bool:
    """A shield that simply cannot be used while both hands are on the weapon."""
    shield = character.shield
    return _two_handed(weapon) and shield is not None and not shield.is_buckler


def _finesse_choice(
    character: Character, abilities: dict[Ability, AbilityScoreResult]
) -> tuple[Ability, int]:
    """Which ability a finessable weapon should attack with, and what it costs.

    Weapon Finesse says you *may* use Dexterity, so the sheet shows the better of the
    two rather than assuming the feat is always taken up — a Strength build who took
    it for one weapon should not see their good attacks get worse.

    The comparison is not just the two modifiers: using Dexterity applies a carried
    shield's check penalty to the attack, which is enough to make Strength the better
    choice at equal ability scores.
    """
    shield_penalty = character.shield.armor_check_penalty if character.shield is not None else 0
    with_dex = abilities[Ability.DEX].modifier + shield_penalty
    if with_dex > abilities[Ability.STR].modifier:
        return Ability.DEX, shield_penalty
    return Ability.STR, 0


def _attack_routine(
    character: Character,
    weapon: EquippedWeapon,
    abilities: dict[Ability, AbilityScoreResult],
    bab: BabResult,
    general_pool: list[Modifier],
) -> AttackRoutine:
    is_ranged = weapon.is_ranged
    atk_target = (
        ModifierTarget.ATTACK_RANGED.value if is_ranged else ModifierTarget.ATTACK_MELEE.value
    )
    dmg_target = (
        ModifierTarget.DAMAGE_RANGED.value if is_ranged else ModifierTarget.DAMAGE_MELEE.value
    )
    hit_ability = Ability.DEX if is_ranged else Ability.STR
    finesse_shield_penalty = 0
    if not is_ranged and character.has_weapon_finesse and weapon.allows_finesse:
        hit_ability, finesse_shield_penalty = _finesse_choice(character, abilities)

    atk_mods: list[Modifier] = [
        _struct(atk_target, bab.total, "Ataque base", SourceKind.BASE),
        _struct(
            atk_target,
            abilities[hit_ability].modifier,
            hit_ability.label,
            SourceKind.ABILITY,
        ),
    ]
    if finesse_shield_penalty:
        # The price of the swap, stated by the feat: "si llevas escudo, su penalizador
        # por armadura se aplica a tus tiradas de ataque".
        atk_mods.append(
            _struct(
                atk_target,
                finesse_shield_penalty,
                "Escudo (Sutileza con las armas)",
                SourceKind.ARMOR,
            )
        )
    size_mod = SIZE_AC_ATTACK_MOD[character.size]
    if size_mod:
        atk_mods.append(Modifier(atk_target, size_mod, BonusType.SIZE, "Tamaño", SourceKind.SIZE))
    if weapon.enhancement_bonus:
        atk_mods.append(
            Modifier(
                atk_target,
                weapon.enhancement_bonus,
                BonusType.ENHANCEMENT,
                f"{weapon.name} +{weapon.enhancement_bonus}",
                SourceKind.ITEM,
            )
        )
    if not weapon.is_proficient:
        atk_mods.append(_struct(atk_target, -4, "No competente", SourceKind.MANUAL))
    if _buckler_in_the_way(character, weapon):
        # The buckler is the one shield you can keep while both hands are busy, and
        # the manual charges -1 for the arm it occupies.
        atk_mods.append(_struct(atk_target, -1, "Rodela (mano ocupada)", SourceKind.ARMOR))
    twf_penalty = _twf_penalty(character)
    if twf_penalty is not None:
        atk_mods.append(_struct(atk_target, twf_penalty, "Combate con dos armas", SourceKind.FEAT))
    atk_mods.extend(weapon.attack_modifiers)

    attack_breakdown = resolve(atk_target, [*general_pool, *atk_mods])
    first = attack_breakdown.total

    if weapon.wield == Wield.OFF_HAND:
        steps = (
            1
            + (1 if character.two_weapon_fighting.improved else 0)
            + (1 if character.two_weapon_fighting.greater else 0)
        )
        attack_bonuses = [first - 5 * step for step in range(steps)]
    elif weapon.single_attack:
        attack_bonuses = [first]
    else:
        attack_bonuses = [first - 5 * step for step in range(len(bab.iteratives))]

    # Extra attacks are made at the top bonus, so they lead the routine rather than
    # continuing the iterative sequence downwards.
    attack_bonuses = [first] * weapon.extra_attacks_at_full_bab + attack_bonuses

    # Damage
    dmg_mods: list[Modifier] = []
    str_dmg = _str_damage(abilities[Ability.STR].modifier, weapon)
    if str_dmg:
        dmg_mods.append(_struct(dmg_target, str_dmg, "Fuerza", SourceKind.ABILITY))
    if weapon.enhancement_bonus:
        dmg_mods.append(
            Modifier(
                dmg_target,
                weapon.enhancement_bonus,
                BonusType.ENHANCEMENT,
                f"{weapon.name} +{weapon.enhancement_bonus}",
                SourceKind.ITEM,
            )
        )
    dmg_mods.extend(weapon.damage_modifiers)
    damage_breakdown = resolve(dmg_target, [*general_pool, *dmg_mods])

    # Only the dice multiply: rolling 2d8 twice does not double the +4 from Strength.
    damage_expression = _damage_expression(weapon.damage_dice, damage_breakdown.total, 1)
    first_attack_damage_expression: str | None = None
    if weapon.damage_dice is not None and weapon.damage_dice_multiplier > 1:
        multiplied = _damage_expression(
            weapon.damage_dice, damage_breakdown.total, weapon.damage_dice_multiplier
        )
        if weapon.dice_multiplier_first_attack_only:
            first_attack_damage_expression = multiplied
        else:
            damage_expression = multiplied

    # A line that costs CMB states what it costs: the character's CMB is unchanged
    # until this is the line being used, so it is resolved here rather than folded
    # into the sheet's own number.
    line_cmb = (
        derive_cmb(character, abilities, bab.total, general_pool, weapon.cmb_modifiers)
        if weapon.cmb_modifiers
        else None
    )

    # A line that puts both hands on the weapon is not using the shield, so it does
    # not get its AC. Re-deriving from a shieldless copy keeps touch and flat-footed
    # honest too, rather than subtracting a number and hoping the rest still holds.
    line_ac = (
        derive_ac(replace(character, shield=None), abilities, general_pool)
        if _shield_set_aside(character, weapon)
        else None
    )

    return AttackRoutine(
        weapon_name=weapon.name,
        is_ranged=is_ranged,
        attack_bonuses=attack_bonuses,
        attack_line="/".join(f"{b:+d}" for b in attack_bonuses),
        attack_breakdown=attack_breakdown,
        damage_expression=damage_expression,
        first_attack_damage_expression=first_attack_damage_expression,
        damage_breakdown=damage_breakdown,
        threat_range=weapon.threat_range,
        crit_multiplier=weapon.crit_multiplier,
        damage_type=weapon.damage_type,
        range_increment=weapon.range_increment,
        is_proficient=weapon.is_proficient,
        notes=weapon.notes,
        cmb=line_cmb,
        ac=line_ac,
        variant_label=weapon.variant_label,
        variant_key=weapon.variant_key,
    )


# --------------------------------------------------------------------------- skills
def _armor_check_penalty(character: Character) -> int:
    """Armor + shield check penalty; a heavy load counts as the worse armor-side penalty.

    Armor and encumbrance do not stack — the more restrictive of the two applies —
    but a shield's penalty is always added on top.
    """
    armor_side = character.armor.armor_check_penalty if character.armor is not None else 0
    load_side = _LOAD_CHECK_PENALTY.get(load_category(character.load), 0)
    total = min(armor_side, load_side)
    if character.shield is not None:
        total += character.shield.armor_check_penalty
    return total


def _arcane_spell_failure(character: Character) -> int:
    total = 0
    if character.armor is not None:
        total += character.armor.arcane_spell_failure
    if character.shield is not None:
        total += character.shield.arcane_spell_failure
    return total


def derive_skills(
    character: Character,
    abilities: dict[Ability, AbilityScoreResult],
    general_pool: list[Modifier],
    acp: int,
) -> tuple[list[SkillResult], list[str]]:
    results: list[SkillResult] = []
    warnings: list[str] = []
    total_level = character.total_level
    for skill in character.skills:
        target = skill_target(skill.slug)
        # Held by name so the split below can pick them out of the applied list by
        # identity. Matching on the label instead would break the moment the corpus
        # or the UI language changed a word.
        ranks_mod = _struct(target, skill.ranks, "Rangos", SourceKind.CLASS)
        ability_mod = _struct(
            target,
            abilities[skill.ability].modifier,
            skill.ability.label,
            SourceKind.ABILITY,
        )
        mods: list[Modifier] = [ranks_mod, ability_mod]
        if skill.is_class_skill and skill.ranks >= 1:
            mods.append(_struct(target, 3, "Habilidad de clase", SourceKind.CLASS))
        if skill.uses_armor_check_penalty and acp:
            mods.append(_struct(target, acp, "Penalizador de armadura", SourceKind.ARMOR))
        if skill.misc_modifier:
            mods.append(_struct(target, skill.misc_modifier, "Varios", SourceKind.MANUAL))
        if skill.slug == _STEALTH_SLUG and SIZE_STEALTH_MOD[character.size]:
            mods.append(
                Modifier(
                    target,
                    SIZE_STEALTH_MOD[character.size],
                    BonusType.SIZE,
                    "Tamaño",
                    SourceKind.SIZE,
                )
            )

        resolved = resolve(target, [*general_pool, *mods])

        # Ranks and the ability modifier are untyped, so the engine never suppresses
        # them — but reading them back out of `applied` rather than assuming that
        # keeps the three columns summing to the total whatever the engine decides.
        ranks_applied = sum(m.value for m in resolved.applied if m is ranks_mod)
        ability_applied = sum(m.value for m in resolved.applied if m is ability_mod)
        other_applied = [m for m in resolved.applied if m is not ranks_mod and m is not ability_mod]

        untrained_violation = skill.ranks == 0 and not skill.untrained
        # Every skill is on the sheet, so this is only a mistake for a skill the
        # character actually put something into; otherwise it fires two dozen times
        # for a character who has simply not trained everything.
        if untrained_violation and skill.is_tracked:
            warnings.append(f"{skill.name}: no puede usarse sin entrenamiento (0 rangos)")
        if skill.ranks > total_level:
            warnings.append(f"{skill.name}: {skill.ranks} rangos superan el máximo ({total_level})")
        results.append(
            SkillResult(
                slug=skill.slug,
                name=skill.name,
                ability=skill.ability,
                resolved=resolved,
                is_class_skill=skill.is_class_skill,
                untrained_violation=untrained_violation,
                ranks=ranks_applied,
                ability_modifier=ability_applied,
                other_modifiers=resolved.total - ranks_applied - ability_applied,
                other_applied=other_applied,
            )
        )
    return results, warnings


# --------------------------------------------------------------------------- speed
def reduced_speed(base: int) -> int:
    """Speed under medium/heavy armor or encumbrance (CRB table; see assumptions)."""
    table = {5: 5, 10: 5, 15: 10, 20: 15, 30: 20, 40: 30, 50: 35, 60: 40}
    if base in table:
        return table[base]
    return max(5, (base // 5 * 5) - 5)


def derive_speed(character: Character) -> SpeedResult:
    reductions: list[str] = []
    final = character.base_speed_ft

    heavy_armor = character.armor is not None and character.armor.category in {
        "intermedia",
        "pesada",
    }
    encumbered = load_category(character.load) in {"medium", "heavy", "over"}

    if heavy_armor or encumbered:
        final = reduced_speed(final)
        if heavy_armor:
            reductions.append("armadura intermedia/pesada")
        if encumbered:
            reductions.append("carga")

    return SpeedResult(base_ft=character.base_speed_ft, final_ft=final, reductions=reductions)


# --------------------------------------------------------------------------- top level
def derive_combat_sheet(character: Character) -> CombatSheet:
    """Derive the full combat sheet for a resolved character."""
    abilities = derive_abilities(character)
    bab = derive_bab(character)
    general_pool = _general_pool(character, bab.total)

    ac = derive_ac(character, abilities, general_pool)
    saves = derive_saves(character, abilities, general_pool)
    initiative = derive_initiative(abilities, general_pool)
    cmb = derive_cmb(character, abilities, bab.total, general_pool)
    cmd = derive_cmd(character, abilities, bab.total, general_pool)
    acp = _armor_check_penalty(character)
    skills, skill_warnings = derive_skills(character, abilities, general_pool, acp)
    speed = derive_speed(character)

    warnings: list[str] = []
    blocked = prevents_actions(character.conditions)
    if character.stances.total_defense:
        attacks: list[AttackRoutine] = []
        warnings.append("Defensa total: no se permiten ataques este asalto")
    elif blocked:
        attacks = []
        warnings.append(f"No puede actuar ({', '.join(blocked)})")
    else:
        attacks = [
            _attack_routine(character, weapon, abilities, bab, general_pool)
            for weapon in character.weapons
        ]

    for weapon in character.weapons:
        if not weapon.is_proficient:
            warnings.append(f"{weapon.name}: no competente (-4 al ataque)")

    if character.load is not None and character.load.carried_lb > character.load.heavy_max:
        warnings.append("Carga por encima del máximo pesado")

    warnings.extend(skill_warnings)

    carrying = {}
    if character.load is not None:
        carrying = {
            "light_max": character.load.light_max,
            "medium_max": character.load.medium_max,
            "heavy_max": character.load.heavy_max,
        }

    return CombatSheet(
        abilities=abilities,
        ac=ac,
        saves=saves,
        bab=bab,
        initiative=initiative,
        cmb=cmb,
        cmd=cmd,
        attacks=attacks,
        skills=skills,
        speed=speed,
        armor_check_penalty=acp,
        arcane_spell_failure=_arcane_spell_failure(character),
        max_hp=character.max_hp,
        current_hp=character.current_hp,
        temporary_hp=character.temporary_hp,
        nonlethal_damage=character.nonlethal_damage,
        carrying_capacity=carrying,
        warnings=warnings,
    )
