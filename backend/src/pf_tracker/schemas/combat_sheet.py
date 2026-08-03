"""Combat-sheet response DTOs and the mapping from domain results.

Every numeric field is an object, never a bare int: it carries its breakdown and any
modifiers suppressed by the stacking rules, so a GM can expand any number into the
exact list of bonuses that produced it.
"""

from __future__ import annotations

from pydantic import BaseModel

from pf_tracker.domain.derivation import (
    ACResult,
    AttackRoutine,
    CombatSheet,
    SkillResult,
)
from pf_tracker.domain.modifiers import Modifier, ResolvedValue, SuppressedModifier


class BreakdownEntry(BaseModel):
    label: str
    value: int
    type: str | None
    source: str


class SuppressedEntry(BaseModel):
    label: str
    value: int
    type: str | None
    reason: str


class ValueBreakdown(BaseModel):
    total: int
    breakdown: list[BreakdownEntry]
    suppressed: list[SuppressedEntry]


class AbilityScoreDTO(BaseModel):
    score: int
    modifier: int
    base: int
    racial: int
    level_increment: int
    damage: int


class ACDTO(BaseModel):
    total: int
    touch: int
    flat_footed: int
    max_dex_cap: int | None
    breakdown: list[BreakdownEntry]
    suppressed: list[SuppressedEntry]


class BabDTO(BaseModel):
    total: int
    iteratives: list[int]


class AttackDTO(BaseModel):
    weapon: str
    is_ranged: bool
    attack_line: str
    attack: ValueBreakdown
    damage_expression: str | None
    damage: ValueBreakdown
    threat_range: int
    crit_multiplier: int
    damage_type: str | None
    range_increment: str | None
    is_proficient: bool


class SkillLineDTO(BaseModel):
    slug: str
    name: str
    ability: str
    total: int
    is_class_skill: bool
    untrained_violation: bool
    breakdown: list[BreakdownEntry]
    suppressed: list[SuppressedEntry]


class SpeedDTO(BaseModel):
    base_ft: int
    final_ft: int
    reductions: list[str]


class HpDTO(BaseModel):
    max: int
    current: int
    temporary: int
    nonlethal: int


class CombatSheetResponse(BaseModel):
    abilities: dict[str, AbilityScoreDTO]
    ac: ACDTO
    saves: dict[str, ValueBreakdown]
    bab: BabDTO
    initiative: ValueBreakdown
    cmb: ValueBreakdown
    cmd: ValueBreakdown
    attacks: list[AttackDTO]
    skills: list[SkillLineDTO]
    speed: SpeedDTO
    armor_check_penalty: int
    arcane_spell_failure: int
    hp: HpDTO
    carrying_capacity: dict[str, int]
    warnings: list[str]


def _entry(modifier: Modifier) -> BreakdownEntry:
    return BreakdownEntry(
        label=modifier.source,
        value=modifier.value,
        type=modifier.bonus_type.value if modifier.bonus_type else None,
        source=modifier.source_kind.value,
    )


def _suppressed(item: SuppressedModifier) -> SuppressedEntry:
    modifier = item.modifier
    return SuppressedEntry(
        label=modifier.source,
        value=modifier.value,
        type=modifier.bonus_type.value if modifier.bonus_type else None,
        reason=item.reason,
    )


def _value(resolved: ResolvedValue) -> ValueBreakdown:
    return ValueBreakdown(
        total=resolved.total,
        breakdown=[_entry(m) for m in resolved.applied],
        suppressed=[_suppressed(s) for s in resolved.suppressed],
    )


def _ac(ac: ACResult) -> ACDTO:
    return ACDTO(
        total=ac.resolved.total,
        touch=ac.touch,
        flat_footed=ac.flat_footed,
        max_dex_cap=ac.max_dex_cap,
        breakdown=[_entry(m) for m in ac.resolved.applied],
        suppressed=[_suppressed(s) for s in ac.resolved.suppressed],
    )


def _attack(routine: AttackRoutine) -> AttackDTO:
    return AttackDTO(
        weapon=routine.weapon_name,
        is_ranged=routine.is_ranged,
        attack_line=routine.attack_line,
        attack=_value(routine.attack_breakdown),
        damage_expression=routine.damage_expression,
        damage=_value(routine.damage_breakdown),
        threat_range=routine.threat_range,
        crit_multiplier=routine.crit_multiplier,
        damage_type=routine.damage_type,
        range_increment=routine.range_increment,
        is_proficient=routine.is_proficient,
    )


def _skill(skill: SkillResult) -> SkillLineDTO:
    return SkillLineDTO(
        slug=skill.slug,
        name=skill.name,
        ability=skill.ability.value,
        total=skill.resolved.total,
        is_class_skill=skill.is_class_skill,
        untrained_violation=skill.untrained_violation,
        breakdown=[_entry(m) for m in skill.resolved.applied],
        suppressed=[_suppressed(s) for s in skill.resolved.suppressed],
    )


def to_combat_sheet_response(sheet: CombatSheet) -> CombatSheetResponse:
    """Map the domain combat sheet to its API representation."""
    return CombatSheetResponse(
        abilities={
            ability.value: AbilityScoreDTO(
                score=result.score,
                modifier=result.modifier,
                base=result.base,
                racial=result.racial,
                level_increment=result.level_increment,
                damage=result.damage,
            )
            for ability, result in sheet.abilities.items()
        },
        ac=_ac(sheet.ac),
        saves={kind.value: _value(save.resolved) for kind, save in sheet.saves.items()},
        bab=BabDTO(total=sheet.bab.total, iteratives=sheet.bab.iteratives),
        initiative=_value(sheet.initiative),
        cmb=_value(sheet.cmb),
        cmd=_value(sheet.cmd),
        attacks=[_attack(a) for a in sheet.attacks],
        skills=[_skill(s) for s in sheet.skills],
        speed=SpeedDTO(
            base_ft=sheet.speed.base_ft,
            final_ft=sheet.speed.final_ft,
            reductions=sheet.speed.reductions,
        ),
        armor_check_penalty=sheet.armor_check_penalty,
        arcane_spell_failure=sheet.arcane_spell_failure,
        hp=HpDTO(
            max=sheet.max_hp,
            current=sheet.current_hp,
            temporary=sheet.temporary_hp,
            nonlethal=sheet.nonlethal_damage,
        ),
        carrying_capacity=sheet.carrying_capacity,
        warnings=sheet.warnings,
    )
