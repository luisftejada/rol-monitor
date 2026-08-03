"""Character repository: CRUD over :class:`CharacterRow`, in terms of DTOs."""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from pf_tracker.persistence.models import CharacterRow
from pf_tracker.schemas.character import CharacterRead


class CharacterRepository:
    """Async CRUD for characters. Soft-deleted rows are invisible to reads."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _to_row(character: CharacterRead) -> CharacterRow:
        return CharacterRow(
            id=character.id,
            kind=character.kind,
            name=character.name,
            player_name=character.player_name,
            created_at=character.created_at,
            updated_at=character.updated_at,
            deleted_at=None,
            data=character.model_dump(mode="json"),
        )

    @staticmethod
    def _to_model(row: CharacterRow) -> CharacterRead:
        return CharacterRead.model_validate(row.data)

    async def _row(self, character_id: str) -> CharacterRow | None:
        row = await self._session.get(CharacterRow, character_id)
        if row is None or row.deleted_at is not None:
            return None
        return row

    async def create(self, character: CharacterRead) -> CharacterRead:
        self._session.add(self._to_row(character))
        await self._session.flush()
        return character

    async def get(self, character_id: str) -> CharacterRead | None:
        row = await self._row(character_id)
        return None if row is None else self._to_model(row)

    async def replace(self, character: CharacterRead) -> CharacterRead | None:
        row = await self._row(character.id)
        if row is None:
            return None
        row.kind = character.kind
        row.name = character.name
        row.player_name = character.player_name
        row.updated_at = character.updated_at
        row.data = character.model_dump(mode="json")
        await self._session.flush()
        return character

    async def soft_delete(self, character_id: str, when: object) -> bool:
        row = await self._row(character_id)
        if row is None:
            return False
        row.deleted_at = when  # type: ignore[assignment]
        await self._session.flush()
        return True

    async def list(
        self, *, limit: int, offset: int, search: str | None = None
    ) -> tuple[list[CharacterRead], int]:
        conditions: list[ColumnElement[bool]] = [CharacterRow.deleted_at.is_(None)]
        if search:
            pattern = f"%{search}%"
            conditions.append(
                CharacterRow.name.ilike(pattern) | CharacterRow.player_name.ilike(pattern)
            )

        total = await self._session.scalar(
            select(func.count()).select_from(CharacterRow).where(*conditions)
        )
        rows = (
            await self._session.scalars(
                select(CharacterRow)
                .where(*conditions)
                .order_by(CharacterRow.updated_at.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
        return [self._to_model(row) for row in rows], int(total or 0)
