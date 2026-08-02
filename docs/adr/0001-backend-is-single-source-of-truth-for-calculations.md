# ADR 0001 — The backend is the single source of truth for calculations

- Status: Accepted
- Date: 2026-08-03

## Context

Both stacks could compute derived combat values (AC, attacks, saves…). Duplicating
Pathfinder arithmetic in TypeScript for a snappy UI is tempting, but the two copies
would inevitably drift, and the auditable bonus breakdown — the core value of the
product — would have two subtly different definitions of truth.

## Decision

All Pathfinder arithmetic lives in the backend `domain/`. The frontend renders what
`POST /derive` and `GET /combat-sheet` return, including the per-number breakdowns
and the list of suppressed modifiers. The live preview during character creation is
powered by a debounced call to `/derive`, not by client-side math.

## Consequences

- Zero Pathfinder formulas in TypeScript. A TS test asserting a game formula is a
  signal that logic landed in the wrong layer.
- The UI depends on the derive endpoints being fast; the rules catalog is cacheable
  and ETagged to compensate.
- The domain must be pure and exhaustively tested, since correctness lives entirely
  there.
