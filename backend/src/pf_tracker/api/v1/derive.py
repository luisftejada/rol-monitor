"""Stateless derivation: powers the live combat card during character creation."""

from __future__ import annotations

from fastapi import APIRouter

from pf_tracker.api.deps import CharacterServiceDep
from pf_tracker.schemas.character import CharacterCreate
from pf_tracker.schemas.combat_sheet import CombatSheetResponse, LevelUpResponse

router = APIRouter(tags=["derive"])


@router.post("/derive", response_model=CombatSheetResponse)
async def derive(service: CharacterServiceDep, body: CharacterCreate) -> CombatSheetResponse:
    return service.derive(body)


@router.post("/level-up-preview", response_model=LevelUpResponse)
async def level_up_preview(
    service: CharacterServiceDep, body: CharacterCreate, taking: str
) -> LevelUpResponse:
    """Report what the next level buys, in the class named by ``taking``.

    A POST because it takes the whole character, and stateless because pressing the
    button must change nothing: the owner applies the result by hand.
    """
    return service.level_up_preview(body, taking)
