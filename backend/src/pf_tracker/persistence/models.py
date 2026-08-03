"""ORM models.

A character is an aggregate always loaded and saved as a whole, so its nested
content lives in a portable JSON column. Identity, kind, name, and timestamps are
promoted to real columns for querying, filtering, and soft deletion. The ``kind``
discriminator lets an NPC variant reuse this table and the derivation engine.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from pf_tracker.persistence.database import Base


class CharacterRow(Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    kind: Mapped[str] = mapped_column(String(8), default="pc", index=True)
    name: Mapped[str] = mapped_column(String(200), index=True)
    player_name: Mapped[str | None] = mapped_column(String(200), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None, index=True
    )
    #: The full character document (schemas.character.CharacterRead, JSON-encoded).
    data: Mapped[dict[str, Any]] = mapped_column(JSON)
