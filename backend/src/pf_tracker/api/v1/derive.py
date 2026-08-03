"""Stateless derivation: powers the live combat card during character creation."""

from __future__ import annotations

from fastapi import APIRouter

from pf_tracker.api.deps import CharacterServiceDep
from pf_tracker.schemas.character import CharacterCreate
from pf_tracker.schemas.combat_sheet import CombatSheetResponse

router = APIRouter(tags=["derive"])


@router.post("/derive", response_model=CombatSheetResponse)
async def derive(service: CharacterServiceDep, body: CharacterCreate) -> CombatSheetResponse:
    return service.derive(body)
