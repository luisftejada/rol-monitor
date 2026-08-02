# pf-tracker

A combat assistant for a **Pathfinder 1st Edition** tabletop game. Its single most
important job is to **track, explain, and audit the bonuses** that apply to a
character during combat, so the game master can answer — in under three seconds and
without opening a rulebook — *"What is this character's AC right now, and exactly
which bonuses make it up?"*

This first milestone delivers the **player-character (PC) module** only. The NPC
module is out of scope, but the architecture leaves the seams open for it.

## Prerequisites

- **Python 3.14** and **[Poetry](https://python-poetry.org/) 2.x** (backend)
- **Node.js 20+** and **npm** (frontend)
- GNU Make (optional, for the convenience targets)

> This repository does not commit any interpreter or runtime; install the versions
> above with your tool of choice (`pyenv`, `nvm`, system packages, …).

## Setup

```bash
make install          # installs backend (Poetry) and frontend (npm) dependencies
```

Or per stack:

```bash
cd backend  && poetry install
cd frontend && npm install
```

## Running

```bash
make dev              # backend on :8000, frontend (Vite) on :5173
```

Or per stack:

```bash
cd backend  && poetry run uvicorn pf_tracker.main:app --reload
cd frontend && npm run dev
```

The health probe lives at `GET /api/v1/health`.

## Testing

```bash
make test             # backend + frontend test suites
make test-backend
make test-frontend
make coverage         # enforces coverage thresholds
make check            # lint + typecheck + tests, both stacks (the CI gate)
```

## Project structure

```
backend/   FastAPI service. Pure, testable domain engine; English-facing adapter
           over a vendored Spanish rules loader; SQLAlchemy persistence.
frontend/  React + TypeScript + Vite. Renders what the backend derives — no
           Pathfinder arithmetic lives here.
data/      (backend/data) vendored, read-only YAML rules corpus + loader.
docs/      Architecture Decision Records and recorded rules assumptions.
```

See [CLAUDE.md](CLAUDE.md) for the layering rules and conventions.

## Architecture decisions

- **Single source of truth for calculations is the backend.** The frontend never
  re-implements a Pathfinder formula; it renders the breakdowns `/derive` returns.
- **Spanish data, English code.** The rules corpus is Spanish and treated as opaque
  canonical identifiers; all code artifacts are English; the UI is localised to `es`
  through an i18n layer.
- **The vendored rules loader is wrapped, not forked.** See
  [docs/adr/](docs/adr/).

## How the rules corpus is consumed

Three vendored, read-only files under `backend/data/` are the source of truth for
game rules:

- `pathfinder_nucleo.yaml` — classes, races, skills, feats, equipment, the stacking
  rules, conditions, and combat formulas.
- `pathfinder_conjuros.yaml` — spells (used only as buff modifiers in this milestone).
- `pathfinder_reglas.py` — a known-good Spanish-API loader/query layer.

The loader is vendored unmodified at
`backend/src/pf_tracker/rules/vendor/pathfinder_reglas.py` and wrapped by an
English-facing `RulesRepository`. Spanish strings are kept verbatim as canonical
identifiers; ASCII slugs are derived from them for URLs and keys.
