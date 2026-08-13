"""Character use cases: CRUD, duplication, derivation, and the combat sheet."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from pf_tracker.domain.derivation import derive_combat_sheet
from pf_tracker.domain.enums import Ability, SaveKind
from pf_tracker.persistence.repository import CharacterRepository
from pf_tracker.rules.level_up import ClassLevelRef, level_up_report
from pf_tracker.rules.repository import RulesRepository
from pf_tracker.schemas.character import (
    CharacterCreate,
    CharacterListResponse,
    CharacterPatch,
    CharacterRead,
    CharacterSummary,
    ModifierIn,
    new_character,
)
from pf_tracker.schemas.combat import ModifierCreate, ModifierPatch
from pf_tracker.schemas.combat_sheet import (
    CombatSheetResponse,
    LevelUpResponse,
    to_combat_sheet_response,
    to_feat_budget_response,
    to_level_up_response,
)
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

    # ------------------------------------------------------ combat tracking
    async def _save(self, character: CharacterRead) -> CharacterRead | None:
        character.updated_at = _now()
        return await self._repo.replace(character)

    async def add_modifier(self, character_id: str, data: ModifierCreate) -> CharacterRead | None:
        character = await self._repo.get(character_id)
        if character is None:
            return None
        character.modifiers = [*character.modifiers, ModifierIn(**data.model_dump())]
        return await self._save(character)

    async def remove_modifier(self, character_id: str, modifier_id: str) -> CharacterRead | None:
        character = await self._repo.get(character_id)
        if character is None:
            return None
        remaining = [m for m in character.modifiers if m.id != modifier_id]
        if len(remaining) == len(character.modifiers):
            return None  # modifier not found -> 404
        character.modifiers = remaining
        return await self._save(character)

    async def patch_modifier(
        self, character_id: str, modifier_id: str, patch: ModifierPatch
    ) -> CharacterRead | None:
        character = await self._repo.get(character_id)
        if character is None:
            return None
        changes = patch.model_dump(exclude_unset=True)
        updated: list[ModifierIn] = []
        found = False
        for modifier in character.modifiers:
            if modifier.id == modifier_id:
                found = True
                updated.append(modifier.model_copy(update=changes))
            else:
                updated.append(modifier)
        if not found:
            return None
        character.modifiers = updated
        return await self._save(character)

    async def set_condition(
        self, character_id: str, condition: str, active: bool
    ) -> CharacterRead | None:
        character = await self._repo.get(character_id)
        if character is None:
            return None
        conditions = [c for c in character.active_conditions if c != condition]
        if active:
            conditions.append(condition)
        character.active_conditions = conditions
        return await self._save(character)

    async def tick(self, character_id: str, rounds: int) -> CharacterRead | None:
        """Advance N rounds: decrement timed durations and drop expired effects."""
        character = await self._repo.get(character_id)
        if character is None:
            return None

        kept_modifiers: list[ModifierIn] = []
        for modifier in character.modifiers:
            if modifier.expires_in_rounds is None:
                kept_modifiers.append(modifier)
                continue
            remaining = modifier.expires_in_rounds - rounds
            if remaining > 0:
                kept_modifiers.append(modifier.model_copy(update={"expires_in_rounds": remaining}))
        character.modifiers = kept_modifiers

        kept_effects = []
        for effect in character.active_effects:
            if effect.remaining_rounds is None:
                kept_effects.append(effect)
                continue
            remaining = effect.remaining_rounds - rounds
            if remaining > 0:
                kept_effects.append(effect.model_copy(update={"remaining_rounds": remaining}))
        character.active_effects = kept_effects

        return await self._save(character)

    async def list(self, *, limit: int, offset: int, search: str | None) -> CharacterListResponse:
        characters, total = await self._repo.list(limit=limit, offset=offset, search=search)
        return CharacterListResponse(
            items=[self._summary(character) for character in characters],
            total=total,
            limit=limit,
            offset=offset,
        )

    # ------------------------------------------------------------- derivation
    def level_up_preview(self, data: CharacterCreate, taking: str) -> LevelUpResponse:
        """What the character would gain by putting the next level into ``taking``.

        Stateless on purpose: pressing the button changes nothing, so the same call
        works from the editor's unsaved draft as from a stored character.
        """
        abilities = derive_combat_sheet(assemble(new_character(data), self._rules).character)
        report = level_up_report(
            self._rules,
            class_levels=[
                ClassLevelRef(entry.class_slug, entry.level, entry.is_favored)
                for entry in data.class_levels
            ],
            taking=taking,
            constitution_modifier=abilities.abilities[Ability.CON].modifier,
            intelligence_modifier=abilities.abilities[Ability.INT].modifier,
        )
        return to_level_up_response(report)

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
        response = to_combat_sheet_response(sheet, to_feat_budget_response(assembled.feats))
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
