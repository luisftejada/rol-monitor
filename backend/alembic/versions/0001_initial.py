"""initial characters table

Revision ID: 0001
Revises:
Create Date: 2026-08-03
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "characters",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("kind", sa.String(length=8), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("player_name", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_characters_kind", "characters", ["kind"])
    op.create_index("ix_characters_name", "characters", ["name"])
    op.create_index("ix_characters_deleted_at", "characters", ["deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_characters_deleted_at", table_name="characters")
    op.drop_index("ix_characters_name", table_name="characters")
    op.drop_index("ix_characters_kind", table_name="characters")
    op.drop_table("characters")
