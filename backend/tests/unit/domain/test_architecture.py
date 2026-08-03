"""Architecture test: the domain layer must stay pure.

``domain/`` may not import from ``api``, ``persistence``, ``rules``, FastAPI, or
SQLAlchemy. That purity is what makes the calculation engine exhaustively testable.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pf_tracker.domain as domain_pkg

_DOMAIN_DIR = Path(domain_pkg.__file__).parent
_FORBIDDEN_ROOTS = {
    "pf_tracker.api",
    "pf_tracker.persistence",
    "pf_tracker.rules",
    "fastapi",
    "starlette",
    "sqlalchemy",
}


def _imported_modules(source: str) -> set[str]:
    tree = ast.parse(source)
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            modules.add(node.module)
    return modules


def _is_forbidden(module: str) -> bool:
    return any(module == root or module.startswith(f"{root}.") for root in _FORBIDDEN_ROOTS)


def test_domain_imports_are_pure() -> None:
    offenders: dict[str, set[str]] = {}
    for path in _DOMAIN_DIR.rglob("*.py"):
        imported = _imported_modules(path.read_text(encoding="utf-8"))
        forbidden = {module for module in imported if _is_forbidden(module)}
        if forbidden:
            offenders[path.name] = forbidden
    assert not offenders, f"domain imports forbidden modules: {offenders}"
