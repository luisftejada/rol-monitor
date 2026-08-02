# ADR 0002 — Vendor the rules loader unmodified rather than forking it

- Status: Accepted
- Date: 2026-08-03

## Context

`pathfinder_reglas.py` is an existing, known-good Spanish-API loader/query layer
over the YAML corpus. We need English-facing code, and in a few places the loader is
intentionally approximate (e.g. `dotes_disponibles` returns a superset of eligible
feats). We could fork and rewrite it, or wrap it.

## Decision

Vendor the file **unmodified** at
`backend/src/pf_tracker/rules/vendor/pathfinder_reglas.py` and wrap it with an
English-facing `RulesRepository` in `rules/repository.py`. Slugging and caching live
in the adapter. Where the loader is insufficient, extend in the adapter — never
patch the vendored file. Ruff, mypy, and coverage exclude vendored paths.

## Consequences

- Upstream fixes to the corpus loader can be dropped in verbatim.
- The English-code constraint is satisfied at the adapter boundary without a fork to
  maintain.
- Some behavior (e.g. lenient prerequisite parsing) is inherited as-is and refined
  in the adapter where the milestone needs precision.
