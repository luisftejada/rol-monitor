"""Character use cases: CRUD, duplication, derivation, and the combat sheet."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from pf_tracker.domain.derivation import derive_combat_sheet
from pf_tracker.domain.enums import SaveKind
from pf_tracker.persistence.repository import CharacterRepository
from pf_tracker.rules.repository import RulesRepository
from pf_tracker.schemas.character import (
    CharacterCreate,
    CharacterListResponse,
    CharacterPatch,
    CharacterRead,
    CharacterSummary,
    new_character,
)
from pf_tracker.schemas.combat_sheet import CombatSheetResponse, to_combat_sheet_response
from pf_tracker.services.assembler import assemble


def _now() -> datetime:
    return datetime.now(UTC)


class CharacterService:
    def __init__(self, session: AsyncSession, rules: RulesRepository) -> None:
        self._repo = CharacterRepository(session)
        self._rules = rules

    # ------------------------------------------------------------------ CRUD
    async def create(self, data: CharacterCreate) -> CharacterRead:
        return await self._repo.create(new_character(data))

    async def get(self, character_id: str) -> CharacterRead | None:
        return await self._repo.get(character_id)

    async def replace(self, character_id: str, data: CharacterCreate) -> CharacterRead | None:
        existing = await self._repo.get(character_id)
        if existing is None:
            return None
        updated = CharacterRead(
            id=existing.id,
            created_at=existing.created_at,
            updated_at=_now(),
            **data.model_dump(),
        )
        return await self._repo.replace(updated)

    async def patch(self, character_id: str, patch: CharacterPatch) -> CharacterRead | None:
        existing = await self._repo.get(character_id)
        if existing is None:
            return None
        merged = existing.model_dump()
        merged.update(patch.model_dump(exclude_unset=True))
        merged["updated_at"] = _now()
        return await self._repo.replace(CharacterRead.model_validate(merged))

    async def delete(self, character_id: str) -> bool:
        return await self._repo.soft_delete(character_id, _now())

    async def duplicate(self, character_id: str) -> CharacterRead | None:
        existing = await self._repo.get(character_id)
        if existing is None:
            return None
        clone = CharacterCreate(**existing.model_dump(exclude={"id", "created_at", "updated_at"}))
        clone.name = f"{clone.name} (copia)"
        return await self.create(clone)

    async def list(self, *, limit: int, offset: int, search: str | None) -> CharacterListResponse:
        characters, total = await self._repo.list(limit=limit, offset=offset, search=search)
        return CharacterListResponse(
            items=[self._summary(character) for character in characters],
            total=total,
            limit=limit,
            offset=offset,
        )

    # ------------------------------------------------------------- derivation
    def derive(self, data: CharacterCreate) -> CombatSheetResponse:
        """Stateless derivation for the live creation preview (no persistence)."""
        return self._combat_sheet(new_character(data))

    async def combat_sheet(self, character_id: str) -> CombatSheetResponse | None:
        character = await self._repo.get(character_id)
        if character is None:
            return None
        return self._combat_sheet(character)

    def _combat_sheet(self, character: CharacterRead) -> CombatSheetResponse:
        assembled = assemble(character, self._rules)
        sheet = derive_combat_sheet(assembled.character)
        response = to_combat_sheet_response(sheet)
        # Assembler warnings (unknown catalog entries, incomplete data) come first.
        response.warnings = [*assembled.warnings, *response.warnings]
        return response

    # ---------------------------------------------------------------- summary
    def _summary(self, character: CharacterRead) -> CharacterSummary:
        assembled = assemble(character, self._rules)
        sheet = derive_combat_sheet(assembled.character)
        classes = " / ".join(
            f"{cl.class_name} {cl.level}" for cl in assembled.character.class_levels
        )
        return CharacterSummary(
            id=character.id,
            name=character.name,
            player_name=character.player_name,
            kind=character.kind,
            classes=classes,
            total_level=assembled.character.total_level,
            max_hp=character.max_hp,
            current_hp=character.current_hp,
            armor_class=sheet.ac.resolved.total,
            touch_ac=sheet.ac.touch,
            flat_footed_ac=sheet.ac.flat_footed,
            initiative=sheet.initiative.total,
            fortitude=sheet.saves[SaveKind.FORTITUDE].resolved.total,
            reflex=sheet.saves[SaveKind.REFLEX].resolved.total,
            will=sheet.saves[SaveKind.WILL].resolved.total,
            updated_at=character.updated_at,
        )
