"""Load golden-character fixtures (YAML) into domain models for parametric tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

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
    Character,
    ClassLevel,
    EquippedArmor,
    EquippedWeapon,
    SkillState,
    Stances,
    TwoWeaponFighting,
)
from pf_tracker.domain.modifiers import Modifier

FIXTURES_DIR = Path(__file__).parent / "golden"


def _abilities(raw: dict[str, int]) -> dict[Ability, int]:
    return {Ability(abbr): value for abbr, value in raw.items()}


def _saves(raw: dict[str, int]) -> dict[SaveKind, int]:
    return {SaveKind(name): value for name, value in raw.items()}


def _modifier(raw: dict[str, Any]) -> Modifier:
    bonus_type = raw.get("bonus_type")
    return Modifier(
        target=raw["target"],
        value=raw["value"],
        bonus_type=BonusType(bonus_type) if bonus_type else None,
        source=raw["source"],
        source_kind=SourceKind(raw.get("source_kind", "manual")),
        condition=raw.get("condition"),
        is_active=raw.get("is_active", True),
        expires_in_rounds=raw.get("expires_in_rounds"),
    )


def _armor(raw: dict[str, Any] | None) -> EquippedArmor | None:
    if raw is None:
        return None
    return EquippedArmor(
        name=raw["name"],
        is_shield=raw["is_shield"],
        ac_bonus=raw["ac_bonus"],
        max_dex=raw.get("max_dex"),
        armor_check_penalty=raw["armor_check_penalty"],
        arcane_spell_failure=raw["arcane_spell_failure"],
        category=raw["category"],
    )


def _weapon(raw: dict[str, Any]) -> EquippedWeapon:
    return EquippedWeapon(
        name=raw["name"],
        wield=Wield(raw["wield"]),
        is_ranged=raw.get("is_ranged", False),
        threat_range=raw["threat_range"],
        crit_multiplier=raw["crit_multiplier"],
        is_thrown=raw.get("is_thrown", False),
        damage_dice=raw.get("damage_dice"),
        damage_type=raw.get("damage_type"),
        range_increment=raw.get("range_increment"),
        # A fixture states the magic bonus the way a magic weapon has it — one number
        # for both sides — and may split it when it needs to (masterwork).
        attack_enhancement=raw.get("attack_enhancement", raw.get("enhancement_bonus", 0)),
        damage_enhancement=raw.get("damage_enhancement", raw.get("enhancement_bonus", 0)),
        is_proficient=raw.get("is_proficient", True),
        allows_finesse=raw.get("allows_finesse", False),
        attack_modifiers=tuple(_modifier(m) for m in raw.get("attack_modifiers", [])),
        damage_modifiers=tuple(_modifier(m) for m in raw.get("damage_modifiers", [])),
    )


def _skill(raw: dict[str, Any]) -> SkillState:
    return SkillState(
        slug=raw["slug"],
        name=raw["name"],
        ability=Ability(raw["ability"]),
        ranks=raw.get("ranks", 0),
        is_class_skill=raw.get("is_class_skill", False),
        uses_armor_check_penalty=raw.get("uses_armor_check_penalty", False),
        untrained=raw.get("untrained", True),
        misc_modifier=raw.get("misc_modifier", 0),
    )


def build_character(data: dict[str, Any]) -> Character:
    """Build a domain :class:`Character` from a fixture's ``input`` mapping."""
    load_raw = data.get("load")
    return Character(
        name=data.get("name", "fixture"),
        size=Size(data["size"]),
        base_speed_ft=data["base_speed_ft"],
        class_levels=tuple(
            ClassLevel(
                class_slug=cl["class_slug"],
                class_name=cl["class_name"],
                level=cl["level"],
                bab_type=BabProgression(cl["bab_type"]),
                hit_die=cl["hit_die"],
                base_saves=_saves(cl["base_saves"]),
                is_prestige=cl.get("is_prestige", False),
                is_favored=cl.get("is_favored", False),
            )
            for cl in data["class_levels"]
        ),
        base_ability_scores=_abilities(data["base_ability_scores"]),
        racial_ability_modifiers=_abilities(data.get("racial_ability_modifiers", {})),
        level_ability_increments=_abilities(data.get("level_ability_increments", {})),
        ability_damage=_abilities(data.get("ability_damage", {})),
        armor=_armor(data.get("armor")),
        shield=_armor(data.get("shield")),
        weapons=tuple(_weapon(w) for w in data.get("weapons", [])),
        natural_armor_bonus=data.get("natural_armor_bonus", 0),
        deflection_bonus=data.get("deflection_bonus", 0),
        other_ac_modifiers=data.get("other_ac_modifiers", 0),
        max_hp=data.get("max_hp", 0),
        current_hp=data.get("current_hp", 0),
        temporary_hp=data.get("temporary_hp", 0),
        nonlethal_damage=data.get("nonlethal_damage", 0),
        skills=tuple(_skill(s) for s in data.get("skills", [])),
        feats=tuple(data.get("feats", [])),
        conditions=tuple(data.get("conditions", [])),
        stances=Stances(**data.get("stances", {})),
        two_weapon_fighting=TwoWeaponFighting(**data.get("two_weapon_fighting", {})),
        cmb_uses_dexterity=data.get("cmb_uses_dexterity", False),
        cmd_uses_hit_dice=data.get("cmd_uses_hit_dice", False),
        has_weapon_finesse=data.get("has_weapon_finesse", False),
        modifiers=tuple(_modifier(m) for m in data.get("modifiers", [])),
        load=CarryingLoad(**load_raw) if load_raw else None,
    )


def load_fixtures() -> list[tuple[str, dict[str, Any]]]:
    """Return ``(name, document)`` for every golden fixture, sorted by filename."""
    fixtures: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(FIXTURES_DIR.glob("*.yaml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        fixtures.append((path.stem, document))
    return fixtures
