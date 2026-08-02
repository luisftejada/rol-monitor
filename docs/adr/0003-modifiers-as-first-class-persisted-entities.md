# ADR 0003 — Modifiers are first-class entities, not precomputed totals

- Status: Accepted
- Date: 2026-08-03

## Context

We could persist a character's derived combat values (a computed AC of 21) or
persist the individual bonuses that produce them and derive totals on demand. The
product requirement is that a GM can expand any number into the exact list of
bonuses that produced it — including the ones suppressed by the stacking rules.

## Decision

Persist `Modifier` values as first-class entities (target, value, bonus type,
source, source kind, condition, active flag, duration). Never store precomputed
totals. The stacking engine resolves them at read time into a total plus `applied`
and `suppressed` lists.

## Consequences

- Every derived number is auditable and reproducible from its inputs.
- Toggling a stance or condition, or ticking timed effects, is a change to the set
  of modifiers, not a recomputation the client has to trust.
- Ad-hoc, spell, and item modifiers use the same shape, so the NPC module can reuse
  the derivation engine unchanged.
