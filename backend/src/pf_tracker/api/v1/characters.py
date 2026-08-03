"""Character CRUD, duplication, export/import, and the derived combat sheet."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Response, status

from pf_tracker.api.deps import CharacterServiceDep
from pf_tracker.schemas.character import (
    CharacterCreate,
    CharacterImport,
    CharacterListResponse,
    CharacterPatch,
    CharacterRead,
)
from pf_tracker.schemas.combat import (
    ConditionUpdate,
    ModifierCreate,
    ModifierPatch,
    TickRequest,
)
from pf_tracker.schemas.combat_sheet import CombatSheetResponse

router = APIRouter(prefix="/characters", tags=["characters"])

_NOT_FOUND = HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="character not found")


@router.get("", response_model=CharacterListResponse)
async def list_characters(
    service: CharacterServiceDep,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    search: Annotated[str | None, Query()] = None,
) -> CharacterListResponse:
    return await service.list(limit=limit, offset=offset, search=search)


@router.post("", response_model=CharacterRead, status_code=status.HTTP_201_CREATED)
async def create_character(service: CharacterServiceDep, body: CharacterCreate) -> CharacterRead:
    return await service.create(body)


@router.post("/import", response_model=CharacterRead, status_code=status.HTTP_201_CREATED)
async def import_character(service: CharacterServiceDep, body: CharacterImport) -> CharacterRead:
    return await service.create(CharacterCreate.model_validate(body.model_dump()))


@router.get("/{character_id}", response_model=CharacterRead)
async def get_character(service: CharacterServiceDep, character_id: str) -> CharacterRead:
    character = await service.get(character_id)
    if character is None:
        raise _NOT_FOUND
    return character


@router.get("/{character_id}/export", response_model=CharacterRead)
async def export_character(service: CharacterServiceDep, character_id: str) -> CharacterRead:
    character = await service.get(character_id)
    if character is None:
        raise _NOT_FOUND
    return character


@router.put("/{character_id}", response_model=CharacterRead)
async def replace_character(
    service: CharacterServiceDep, character_id: str, body: CharacterCreate
) -> CharacterRead:
    character = await service.replace(character_id, body)
    if character is None:
        raise _NOT_FOUND
    return character


@router.patch("/{character_id}", response_model=CharacterRead)
async def patch_character(
    service: CharacterServiceDep, character_id: str, body: CharacterPatch
) -> CharacterRead:
    character = await service.patch(character_id, body)
    if character is None:
        raise _NOT_FOUND
    return character


@router.delete("/{character_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_character(service: CharacterServiceDep, character_id: str) -> Response:
    if not await service.delete(character_id):
        raise _NOT_FOUND
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{character_id}/duplicate",
    response_model=CharacterRead,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_character(service: CharacterServiceDep, character_id: str) -> CharacterRead:
    character = await service.duplicate(character_id)
    if character is None:
        raise _NOT_FOUND
    return character


@router.get("/{character_id}/combat-sheet", response_model=CombatSheetResponse)
async def combat_sheet(service: CharacterServiceDep, character_id: str) -> CombatSheetResponse:
    sheet = await service.combat_sheet(character_id)
    if sheet is None:
        raise _NOT_FOUND
    return sheet


# ---------------------------------------------------------------- combat tracking
@router.post(
    "/{character_id}/modifiers",
    response_model=CharacterRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_modifier(
    service: CharacterServiceDep, character_id: str, body: ModifierCreate
) -> CharacterRead:
    character = await service.add_modifier(character_id, body)
    if character is None:
        raise _NOT_FOUND
    return character


@router.patch("/{character_id}/modifiers/{modifier_id}", response_model=CharacterRead)
async def patch_modifier(
    service: CharacterServiceDep, character_id: str, modifier_id: str, body: ModifierPatch
) -> CharacterRead:
    character = await service.patch_modifier(character_id, modifier_id, body)
    if character is None:
        raise _NOT_FOUND
    return character


@router.delete("/{character_id}/modifiers/{modifier_id}", response_model=CharacterRead)
async def remove_modifier(
    service: CharacterServiceDep, character_id: str, modifier_id: str
) -> CharacterRead:
    character = await service.remove_modifier(character_id, modifier_id)
    if character is None:
        raise _NOT_FOUND
    return character


@router.post("/{character_id}/conditions", response_model=CharacterRead)
async def set_condition(
    service: CharacterServiceDep, character_id: str, body: ConditionUpdate
) -> CharacterRead:
    character = await service.set_condition(character_id, body.condition, body.active)
    if character is None:
        raise _NOT_FOUND
    return character


@router.post("/{character_id}/tick", response_model=CharacterRead)
async def tick(service: CharacterServiceDep, character_id: str, body: TickRequest) -> CharacterRead:
    character = await service.tick(character_id, body.rounds)
    if character is None:
        raise _NOT_FOUND
    return character
