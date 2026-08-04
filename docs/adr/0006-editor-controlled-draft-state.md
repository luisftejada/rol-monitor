# ADR 0006 — The character editor uses controlled draft state, not React Hook Form

- Status: Accepted
- Date: 2026-08-04

## Context

The stack calls for React Hook Form + Zod for forms. The character editor, however,
is not a conventional form of labelled inputs: it is a set of custom catalog widgets
(accent-insensitive comboboxes, point-buy steppers, a standard-array assigner, skill
rank steppers, an eligibility-annotated feat picker) over deeply nested state
(`base_scores` and `skill_ranks` dicts, `class_levels` and `weapons` arrays). It also
drives a live combat card recomputed from the whole draft on every change.

## Decision

Manage the whole draft as a single controlled state object with a typed
`patch(partial)` updater passed to each section. The draft is exactly the
`CharacterCreate` request body, so saving and the debounced `/derive` preview both
take it directly.

## Consequences

- Sections stay simple: each reads from `draft` and calls `patch({ ... })`; the live
  card is a pure function of the draft.
- Avoids RHF friction for this shape — `useFieldArray` for class levels/weapons,
  `Controller` wrappers around every custom widget, and `register` over dictionaries,
  none of which buy anything here since validation is intentionally non-blocking
  (problems surface as warnings from `/derive`, never as blocked saves).
- We forgo RHF's field-level dirty/touched tracking; the editor only needs a single
  dirty flag for the save-state indicator, which controlled state provides directly.
- If a future, more form-like flow appears (conventional inputs, blocking
  validation), RHF + Zod remains the right tool there; this decision is scoped to the
  character editor.
