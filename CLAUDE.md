# CLAUDE.md — conventions and guardrails

This file is the working contract for anyone (human or agent) touching this repo.
Read it before writing code.

> **Fresh clone, or picking the work up again?** Read
> [docs/HANDOFF.md](docs/HANDOFF.md) first: it has the one-command bootstrap
> (`./setup.sh`), where the work stands, what is open, and the traps that already
> cost time here. Then [docs/assumptions.md](docs/assumptions.md) before touching
> derivation — it records why each rules decision was made, not just what.

## Never start the app

**The owner starts and stops the app manually, always.** Do not run `./start.sh`,
`make dev`, `uvicorn`, or `npm run dev` — not to verify a change, not to take a
screenshot, not "just this once". If a change needs checking in a running app, say
so and let the owner start it.

Why: a stale server left running silently serves old code, and a second copy
fights for ports 8000/5173. The owner keeps a single instance under their own
control.

Tests, linters, type-checkers and builds are unaffected — run those freely.

## The two hard rules

1. **Spanish data, English code.** The rules corpus (`backend/data/*.yaml`) is
   Spanish and is the single source of truth for game content. Treat Spanish
   strings (`Espada larga`, `Fortaleza`, `Cota de mallas`) as **opaque canonical
   identifiers**. Do not translate them in code. Derive ASCII slugs from them for
   URLs and keys. Every code artifact — identifiers, comments, docstrings, commit
   messages, tests, errors, logs — is in **English**. The UI is shown in Spanish,
   but only through the i18n layer (`frontend/src/i18n`), never hardcoded.

2. **The domain is pure.** `backend/src/pf_tracker/domain/` imports nothing from
   `api`, `persistence`, `rules`, FastAPI, or SQLAlchemy. It is pure functions over
   frozen data. An import-linter test enforces this. That purity is what makes the
   calculation engine exhaustively testable, and it is the whole point of the
   project.

## Layering

```
api  ──▶ services ──▶ domain          (domain never imports upward)
          │             ▲
          ▼             │
      persistence     rules (adapter over vendored loader)
```

- `domain/` — enums, frozen models, the modifier stacking engine, derivation.
- `rules/` — English-facing adapter (`RulesRepository`) over the **vendored**
  `pathfinder_reglas.py`, plus slugging and caching, plus catalog DTOs.
- `services/` — use cases orchestrating domain + persistence.
- `persistence/` — SQLAlchemy models, repositories, session.
- `api/` — FastAPI routers and request/response wiring only.

## Single source of truth for calculations

All Pathfinder arithmetic lives in the **backend** `domain/`. The frontend renders
what `/derive` and `/combat-sheet` return. **Zero Pathfinder formulas in
TypeScript** — a TS test asserting a game formula means logic landed in the wrong
layer.

## The vendored loader

`backend/src/pf_tracker/rules/vendor/pathfinder_reglas.py` is a known-good upstream
asset. **Vendor it unmodified; never patch it.** Where it is insufficient (e.g.
`dotes_disponibles` returns a superset), extend in the adapter, not the vendored
file. Ruff, mypy, and coverage all exclude vendored paths.

## Rounding

The corpus rounds down unless stated otherwise. Use the **one** shared rounding
helper; never scatter `int()` / `//` across the codebase.

## How to add a new modifier source

1. Emit `Modifier` values from the right producer (a feat, a stance, a condition,
   an item) — never mutate the character to apply a bonus.
2. Set `bonus_type` from `BonusType` (it maps 1:1 to
   `sistema.tipos_de_bonificador`); use `None` for untyped.
3. Point `target` at the correct `ModifierTarget` (including group targets like
   `ALL_SAVES`).
4. Let the stacking engine (`domain/modifiers.py`) decide what applies; do not
   pre-sum. Suppressed modifiers must still surface to the UI.
5. Add table-driven tests covering stacking against existing bonuses of the same
   type.

## How to add a golden fixture

1. Add a fully specified character as YAML under `backend/tests/fixtures/`.
2. Include hand-computed expected values for every derived number.
3. It is picked up by the parametric golden-fixture test automatically. Pick a
   corner not already covered (size mods, TWF, iteratives, encumbrance, casting
   buffs).

## Conventions

- Python 3.14, Poetry, `src/` layout, `mypy --strict`, ruff (lint + format).
- TypeScript strict + `noUncheckedIndexedAccess`; ESLint + Prettier.
- Tests are part of the deliverable. Backend: ≥95% on `domain/`, ≥85% overall.
  Frontend: ≥80% on `src/`. Query the DOM by accessible role/label, not test ids.
- Record rules assumptions in `docs/assumptions.md`; record contested design
  choices as ADRs in `docs/adr/`.
- End of each phase: tests green, lint clean, one atomic commit.
