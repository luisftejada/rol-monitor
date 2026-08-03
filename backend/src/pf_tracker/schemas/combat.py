"""Request DTOs for live combat tracking (modifiers, conditions, round ticking)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ModifierCreate(BaseModel):
    """Body for adding an ad-hoc / spell / item modifier to a character."""

    model_config = ConfigDict(extra="forbid")

    target: str
    value: int
    bonus_type: str | None = None
    source: str
    source_kind: str = "manual"
    condition: str | None = None
    is_active: bool = True
    expires_in_rounds: int | None = None


class ModifierPatch(BaseModel):
    """Partial update of a modifier: toggle active or edit its duration/value."""

    model_config = ConfigDict(extra="forbid")

    is_active: bool | None = None
    value: int | None = None
    condition: str | None = None
    expires_in_rounds: int | None = None


class ConditionUpdate(BaseModel):
    """Apply or remove a condition (`estado`) by slug."""

    model_config = ConfigDict(extra="forbid")

    condition: str
    active: bool = True


class TickRequest(BaseModel):
    """Advance the combat clock by N rounds, expiring timed effects."""

    model_config = ConfigDict(extra="forbid")

    rounds: int = Field(default=1, ge=1)
