"""Read-only rules catalog endpoints. Cacheable and ETagged; the UI is built on
these, so they are kept fast and complete."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from pf_tracker.api.deps import get_rules_repository, rules_cache
from pf_tracker.rules.catalog import (
    ArmorDTO,
    ClassProgressionRowDTO,
    ClassSummaryDTO,
    ConditionDTO,
    FeatDTO,
    MetaDTO,
    RaceDTO,
    SkillDTO,
    SpellDTO,
    WeaponDTO,
)
from pf_tracker.rules.repository import RulesRepository

router = APIRouter(prefix="/rules", tags=["rules"], dependencies=[Depends(rules_cache)])

RepoDep = Annotated[RulesRepository, Depends(get_rules_repository)]


def _parse_abilities(items: list[str]) -> dict[str, int]:
    """Parse ``["Fue:15", "Des=14"]`` into ``{"Fue": 15, "Des": 14}``."""
    scores: dict[str, int] = {}
    for item in items:
        separator = ":" if ":" in item else "=" if "=" in item else None
        if separator is None:
            continue
        key, _, value = item.partition(separator)
        try:
            scores[key.strip()] = int(value)
        except ValueError:
            continue
    return scores


@router.get("/meta", response_model=MetaDTO)
def get_meta(repo: RepoDep) -> MetaDTO:
    return repo.meta


@router.get("/races", response_model=list[RaceDTO])
def get_races(repo: RepoDep) -> list[RaceDTO]:
    return repo.races


@router.get("/classes", response_model=list[ClassSummaryDTO])
def get_classes(
    repo: RepoDep,
    include_prestige: Annotated[bool, Query()] = False,
) -> list[ClassSummaryDTO]:
    return repo.classes(include_prestige=include_prestige)


@router.get("/classes/{slug}/progression/{level}", response_model=ClassProgressionRowDTO)
def get_class_progression(repo: RepoDep, slug: str, level: int) -> ClassProgressionRowDTO:
    return repo.class_progression(slug, level)


@router.get("/skills", response_model=list[SkillDTO])
def get_skills(repo: RepoDep) -> list[SkillDTO]:
    return repo.skills


@router.get("/feats", response_model=list[FeatDTO])
def get_feats(
    repo: RepoDep,
    bab: Annotated[int, Query(ge=0)] = 0,
    abilities: Annotated[list[str], Query()] = [],  # noqa: B006 - FastAPI query default
    owned: Annotated[list[str], Query()] = [],  # noqa: B006 - FastAPI query default
    feat_type: Annotated[str | None, Query(alias="type")] = None,
) -> list[FeatDTO]:
    return repo.feats(
        bab=bab,
        abilities=_parse_abilities(abilities),
        owned=owned,
        feat_type=feat_type,
    )


@router.get("/weapons", response_model=list[WeaponDTO])
def get_weapons(
    repo: RepoDep,
    category: Annotated[str | None, Query()] = None,
    proficiency: Annotated[str | None, Query()] = None,
    search: Annotated[str | None, Query()] = None,
) -> list[WeaponDTO]:
    return repo.weapons(category=category, proficiency=proficiency, search=search)


@router.get("/armor", response_model=list[ArmorDTO])
def get_armor(
    repo: RepoDep,
    category: Annotated[str | None, Query()] = None,
) -> list[ArmorDTO]:
    return repo.armor(category=category)


@router.get("/conditions", response_model=list[ConditionDTO])
def get_conditions(repo: RepoDep) -> list[ConditionDTO]:
    return repo.conditions


@router.get("/spells", response_model=list[SpellDTO])
def get_spells(
    repo: RepoDep,
    character_class: Annotated[str | None, Query(alias="class")] = None,
    level: Annotated[int | None, Query(ge=0)] = None,
    search: Annotated[str | None, Query()] = None,
) -> list[SpellDTO]:
    return repo.spells(character_class=character_class, level=level, search=search)
