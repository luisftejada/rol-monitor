# ADR 0005 — Persist characters as a JSON document, not normalized tables

- Status: Accepted
- Date: 2026-08-03

## Context

A character aggregates deeply nested data — class levels, ability scores, skill
ranks, equipment, feats, first-class modifiers, conditions, timed effects. It is
always loaded and saved as a whole (the combat sheet derives from the entire
character), and it is never queried by its internal parts. We could model it as a
dozen normalized tables with foreign keys, or store the aggregate as a document.

## Decision

Store the character as a single JSON column (`characters.data`) validated by the
Pydantic `CharacterRead` schema, alongside a few promoted scalar columns
(`id`, `kind`, `name`, `player_name`, `created_at`, `updated_at`, `deleted_at`) for
querying, listing, soft deletion, and the NPC discriminator. SQLAlchemy's portable
`JSON` type works on both SQLite and Postgres.

## Consequences

- CRUD, duplication, and import/export are trivial — the document is the payload,
  and export/import is byte-for-byte the same shape.
- No migrations when the character shape evolves (only when the promoted columns
  change); the schema lives in Pydantic and is versioned with the code.
- Trade-off: we cannot query or aggregate across characters by inner fields in SQL.
  That is acceptable — nothing in the product needs it, and the derivation engine,
  not the database, is the source of truth for computed values (ADR 0001).
- First-class modifiers (ADR 0003) live inside the document with stable ids, which
  the combat-tracking endpoints add, patch, and expire.
