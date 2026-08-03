"""Unit tests for ASCII slug derivation."""

from __future__ import annotations

import pytest

from pf_tracker.rules.slug import slugify


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("Espada larga", "espada-larga"),
        ("Cota de mallas", "cota-de-mallas"),
        ("Saber (dungeons)", "saber-dungeons"),
        ("Saber (ingeniería)", "saber-ingenieria"),
        ("Introspección", "introspeccion"),
        ("Tamaño", "tamano"),
        ("Cimitarra +1", "cimitarra-1"),
        ("  Bendecir  ", "bendecir"),
        ("Flechas (20)", "flechas-20"),
    ],
)
def test_slugify(name: str, expected: str) -> None:
    assert slugify(name) == expected


def test_slugify_is_idempotent() -> None:
    once = slugify("Armadura natural")
    assert slugify(once) == once
