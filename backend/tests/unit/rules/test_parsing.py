"""Unit tests for the corpus notation parsers."""

from __future__ import annotations

import pytest

from pf_tracker.rules.parsing import CriticalSpec, parse_bab, parse_critical


@pytest.mark.parametrize(
    ("bab", "expected"),
    [
        ("+0", [0]),
        ("+1", [1]),
        ("+6/+1", [6, 1]),
        ("+11/+6/+1", [11, 6, 1]),
        ("+16/+11/+6/+1", [16, 11, 6, 1]),
    ],
)
def test_parse_bab(bab: str, expected: list[int]) -> None:
    assert parse_bab(bab) == expected


def test_parse_bab_rejects_garbage() -> None:
    with pytest.raises(ValueError, match="unparseable BAB"):
        parse_bab("n/a")


@pytest.mark.parametrize(
    ("critical", "expected"),
    [
        ("×2", [CriticalSpec(20, 2)]),
        ("×3", [CriticalSpec(20, 3)]),
        ("×4", [CriticalSpec(20, 4)]),
        ("19–20/×2", [CriticalSpec(19, 2)]),
        ("18–20/×2", [CriticalSpec(18, 2)]),
        ("×3/×4", [CriticalSpec(20, 3), CriticalSpec(20, 4)]),
        ("—", []),
        (None, []),
        ("", []),
    ],
)
def test_parse_critical(critical: str | None, expected: list[CriticalSpec]) -> None:
    assert parse_critical(critical) == expected


def test_parse_critical_rejects_garbage() -> None:
    with pytest.raises(ValueError, match="unparseable critical"):
        parse_critical("crit!")
