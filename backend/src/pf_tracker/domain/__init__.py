"""Pure domain: enums, frozen models, the modifier stacking engine, and derivation.

This package imports nothing from ``api``, ``persistence``, ``rules``, FastAPI, or
SQLAlchemy. It is pure functions over frozen data — that purity is what makes the
calculation engine exhaustively testable. An architecture test enforces it.
"""
