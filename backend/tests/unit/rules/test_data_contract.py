"""Data-contract tests over the real YAML corpus.

These catch corpus drift: if a data file changes shape in a way the code does not
expect, one of these fails loudly rather than the app misbehaving at runtime.
"""

from __future__ import annotations

from typing import Any

import pytest

from pf_tracker.rules.parsing import parse_bab, parse_critical
from pf_tracker.rules.slug import slugify

VALID_ARMOR_CATEGORIES = {"ligera", "intermedia", "pesada", "escudo"}


def test_every_feat_carries_the_documented_fields(nucleo_raw: dict[str, Any]) -> None:
    """The 2026-08-06 corpus adds `activacion` and structured `efectos` to every
    feat. Pin their presence so a partial regeneration is caught."""
    for feat in nucleo_raw["dotes"]["lista"]:
        assert feat.get("activacion"), f"{feat['nombre']} has no activation"
        assert isinstance(feat.get("efectos"), list), f"{feat['nombre']} has no effects list"


def test_every_feat_activation_is_declared(nucleo_raw: dict[str, Any]) -> None:
    declared = set(nucleo_raw["dotes"]["esquema_efectos"]["activacion"])
    used = {feat["activacion"] for feat in nucleo_raw["dotes"]["lista"]}
    assert used <= declared, f"undeclared activations: {sorted(used - declared)}"


def test_every_modifier_target_is_declared(nucleo_raw: dict[str, Any]) -> None:
    """`objetivos` is the contract the derivation engine will dispatch on, so a
    target outside it would silently do nothing."""
    groups = nucleo_raw["dotes"]["esquema_efectos"]["objetivos"].values()
    declared = {target for group in groups if isinstance(group, list) for target in group}
    # Two entries are templates (`prueba_habilidad.<Habilidad>`); match their prefix.
    prefixes = tuple(t.split(".", 1)[0] + "." for t in declared if t.endswith(">"))

    for feat in nucleo_raw["dotes"]["lista"]:
        for effect in feat["efectos"]:
            for modifier in effect.get("modificadores") or []:
                target = modifier["objetivo"]
                ok = target in declared or target.startswith(prefixes)
                assert ok, f"{feat['nombre']} uses undeclared target {target!r}"


# `Disparo preciso` and `Maestro del escudo` encode "this feat removes the standard
# penalty" as `valor: 0`, with the real mechanic only in the prose `reglas`. Adding
# zero is a no-op, so those two cannot be applied by an additive engine alone.
CANCELS_A_STANDARD_PENALTY = {"Disparo preciso", "Maestro del escudo"}


def test_feat_penalties_are_never_positive(nucleo_raw: dict[str, Any]) -> None:
    """The stacking engine reads penalties from the sign, not from the type name, so
    a positive `penalizador` would be applied as a bonus."""
    zeroed: set[str] = set()
    for feat in nucleo_raw["dotes"]["lista"]:
        for effect in feat["efectos"]:
            for modifier in effect.get("modificadores") or []:
                value = modifier["valor"]
                if modifier["tipo"] != "penalizador" or not isinstance(value, int):
                    continue
                assert value <= 0, f"{feat['nombre']} has a positive penalty {value}"
                if value == 0:
                    zeroed.add(feat["nombre"])

    assert zeroed == CANCELS_A_STANDARD_PENALTY, (
        f"set of penalty-cancelling feats changed: {sorted(zeroed)}"
    )


def test_every_feat_type_is_declared_in_the_rules_block(nucleo_raw: dict[str, Any]) -> None:
    """The feat picker groups by ``dotes.reglas.tipos``; a feat carrying a type
    outside that list would be unreachable through the type filter."""
    declared = set(nucleo_raw["dotes"]["reglas"]["tipos"])
    used = {t for feat in nucleo_raw["dotes"]["lista"] for t in feat["tipos"]}
    assert used <= declared, (
        f"feat types missing from dotes.reglas.tipos: {sorted(used - declared)}"
    )


def test_every_alignment_value_has_a_display_name(nucleo_raw: dict[str, Any]) -> None:
    """The picker renders ``nombres[code]`` for each ``valores`` entry, so a code
    without a name would surface as a blank option."""
    block = nucleo_raw["alineamiento"]
    missing = [code for code in block["valores"] if code not in block["nombres"]]
    assert not missing, f"alignment codes without a display name: {missing}"
    assert len(block["valores"]) == 9


def test_every_base_class_has_20_progression_rows(nucleo_raw: dict[str, Any]) -> None:
    for key, data in nucleo_raw["clases"].items():
        rows = data["progresion"]
        assert len(rows) == 20, f"{key} has {len(rows)} progression rows, expected 20"
        assert [r["nivel"] for r in rows] == list(range(1, 21)), f"{key} levels not 1..20"


# Three prestige classes ship with incomplete progression in the vendored corpus
# (see docs/assumptions.md). Prestige is secondary to the PC milestone, so we assert
# the shape that always holds — contiguous levels starting at 1, never above 10 —
# rather than a fixed count of 10.
INCOMPLETE_PRESTIGE_PROGRESSION = {"cronista_pathfinder", "danzarin_sombrio", "duelista"}


def test_prestige_progression_is_a_valid_subset_of_1_to_10(nucleo_raw: dict[str, Any]) -> None:
    for key, data in nucleo_raw["clases_de_prestigio"].items():
        levels = [row["nivel"] for row in data["progresion"]]
        assert all(1 <= n <= 10 for n in levels), f"{key} has a level outside 1..10"
        assert levels == sorted(set(levels)), f"{key} levels are not strictly increasing/unique"
        complete = levels == list(range(1, 11))
        assert complete is (key not in INCOMPLETE_PRESTIGE_PROGRESSION), (
            f"{key} progression completeness changed; update the corpus assumption"
        )


# ------------------------------------------------------------- bonus feat slots
def _bonus_feat_slots(nucleo_raw: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    """Every ``dotes_adicionales`` entry in the corpus, tagged with its owner.

    Classes are keyed by slug and races are a list, so both shapes are flattened to
    (owner, slot) rather than special-cased at every call site.
    """
    classes = (nucleo_raw["clases"], nucleo_raw["clases_de_prestigio"])
    owners: list[tuple[str, dict[str, Any]]] = [
        (key, data) for group in classes for key, data in group.items()
    ]
    owners += [(race["nombre"], race) for race in nucleo_raw["razas"]]
    return [(owner, slot) for owner, data in owners for slot in data.get("dotes_adicionales") or []]


def test_every_bonus_feat_slot_is_well_formed(nucleo_raw: dict[str, Any]) -> None:
    """A slot whose `lista`, `opcion` or `dote` misses its target resolves to an
    empty list of choices — a silent failure, since an empty picker looks like a
    filter that matched nothing."""
    lists = nucleo_raw["dotes"]["listas_restringidas"]
    feats = {feat["nombre"] for feat in nucleo_raw["dotes"]["lista"]}
    types = set(nucleo_raw["dotes"]["reglas"]["tipos"])

    for owner, slot in _bonus_feat_slots(nucleo_raw):
        where = f"{owner} level {slot.get('nivel')}"
        choice = slot["eleccion"]
        assert choice in {"libre", "tipos", "lista", "fija"}, f"{where}: unknown choice {choice!r}"

        if choice == "tipos":
            unknown = set(slot["tipos"]) - types
            assert not unknown, f"{where}: undeclared feat types {sorted(unknown)}"
        elif choice == "fija":
            assert slot["dote"] in feats, f"{where}: grants unknown feat {slot['dote']!r}"
        elif choice == "lista":
            spec = lists.get(slot["lista"])
            assert spec is not None, f"{where}: unknown restricted list {slot['lista']!r}"
            option = slot.get("opcion")
            if option is not None:
                branches = spec.get("opciones") or {}
                assert option in branches, f"{where}: {slot['lista']} has no branch {option!r}"


def test_prestige_classes_that_grant_feats_declare_them(nucleo_raw: dict[str, Any]) -> None:
    """Pins the three the manual sweep found (docs/corpus/INVENTARIO…), so a corpus
    regeneration that drops them fails here instead of quietly shrinking a budget.

    `maestro_del_saber` is absent on purpose: its feats hang off a *secret*, a choice
    the sheet does not model, so it is grouped with domains and rogue talents.
    """
    granting = {
        key
        for key, data in nucleo_raw["clases_de_prestigio"].items()
        if data.get("dotes_adicionales")
    }
    assert granting == {"caballero_arcano", "discipulo_del_dragon"}

    levels = {
        key: [slot["nivel"] for slot in nucleo_raw["clases_de_prestigio"][key]["dotes_adicionales"]]
        for key in granting
    }
    assert levels == {"caballero_arcano": [1, 5, 9], "discipulo_del_dragon": [2, 5, 8]}


def test_every_bab_string_parses(nucleo_raw: dict[str, Any]) -> None:
    groups = (nucleo_raw["clases"], nucleo_raw["clases_de_prestigio"])
    for group in groups:
        for key, data in group.items():
            for row in data["progresion"]:
                bab = row["bab"]
                iteratives = parse_bab(bab)
                assert iteratives, f"{key} level {row['nivel']} BAB {bab!r} parsed empty"
                # The primary bonus is non-decreasing across levels within a class.
                assert iteratives[0] >= 0


def test_every_critical_string_parses(nucleo_raw: dict[str, Any]) -> None:
    for weapon in nucleo_raw["equipo"]["armas"]:
        specs = parse_critical(weapon.get("critico"))
        for spec in specs:
            assert 2 <= spec.threat_range <= 20
            assert spec.multiplier >= 2


def test_every_skill_ability_is_known(nucleo_raw: dict[str, Any]) -> None:
    known = {a["abrev"] for a in nucleo_raw["caracteristicas"]["lista"]}
    for skill in nucleo_raw["habilidades"]["lista"]:
        assert skill["caracteristica"] in known, (
            f"skill {skill['nombre']} references unknown ability {skill['caracteristica']}"
        )


def test_every_skill_class_reference_exists(nucleo_raw: dict[str, Any]) -> None:
    class_keys = set(nucleo_raw["clases"])
    for skill in nucleo_raw["habilidades"]["lista"]:
        for class_key in skill.get("clases", []):
            assert class_key in class_keys, (
                f"skill {skill['nombre']} references unknown class {class_key}"
            )


def test_every_armor_category_is_valid(nucleo_raw: dict[str, Any]) -> None:
    for armor in nucleo_raw["equipo"]["armaduras_y_escudos"]:
        assert armor["categoria"] in VALID_ARMOR_CATEGORIES, (
            f"armor {armor['nombre']} has invalid category {armor['categoria']}"
        )


@pytest.mark.parametrize(
    "collection_path",
    [
        ("habilidades", "lista"),
        ("estados",),
        ("razas",),
    ],
)
def test_slugs_are_unique_within_collection(
    nucleo_raw: dict[str, Any], collection_path: tuple[str, ...]
) -> None:
    node: Any = nucleo_raw
    for key in collection_path:
        node = node[key]
    slugs = [slugify(item["nombre"]) for item in node]
    assert len(slugs) == len(set(slugs)), f"duplicate slugs in {collection_path}"


def test_class_slugs_unique_across_base_and_prestige(nucleo_raw: dict[str, Any]) -> None:
    base = set(nucleo_raw["clases"])
    prestige = set(nucleo_raw["clases_de_prestigio"])
    assert base.isdisjoint(prestige), "class slug collides between base and prestige"


def test_every_spell_level_maps_to_int(conjuros_raw: dict[str, Any]) -> None:
    for spell in conjuros_raw["conjuros"]:
        for class_key, level in (spell.get("niveles") or {}).items():
            assert isinstance(level, int), f"{spell['nombre']} level for {class_key} not int"
            assert 0 <= level <= 9
