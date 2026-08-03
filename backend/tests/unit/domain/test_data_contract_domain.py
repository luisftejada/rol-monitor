"""Data-contract tests tying the domain to the real corpus (catch drift)."""

from __future__ import annotations

from typing import Any

from pf_tracker.domain.enums import BonusType, Size
from pf_tracker.domain.sizes import (
    SIZE_AC_ATTACK_MOD,
    SIZE_CMB_CMD_MOD,
    SIZE_STEALTH_MOD,
)


def _base_type(label: str) -> str:
    """Strip qualifiers like 'circunstancia (de fuentes distintas)' -> 'circunstancia'."""
    return label.split("(")[0].strip()


def test_bonus_type_enum_covers_corpus(nucleo_raw: dict[str, Any]) -> None:
    classification = nucleo_raw["sistema"]["tipos_de_bonificador"]
    corpus_types = {
        _base_type(label)
        for label in [*classification["apilan_siempre"], *classification["no_apilan"]]
        if _base_type(label) != "sin tipo"
    }
    known = {member.value for member in BonusType}
    missing = corpus_types - known
    assert not missing, f"corpus has bonus types the enum does not know: {missing}"


def test_size_tables_match_corpus(nucleo_raw: dict[str, Any]) -> None:
    by_name = {row["tamano"]: row for row in nucleo_raw["tamanos"]}
    assert set(by_name) == {size.value for size in Size}, "size set drift"
    for size in Size:
        row = by_name[size.value]
        assert SIZE_AC_ATTACK_MOD[size] == row["mod_ca_ataque"], f"{size.value} AC/attack"
        assert SIZE_CMB_CMD_MOD[size] == row["mod_bmc_dmc"], f"{size.value} CMB/CMD"
        assert SIZE_STEALTH_MOD[size] == row["mod_sigilo"], f"{size.value} stealth"
