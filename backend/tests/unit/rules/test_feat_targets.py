"""The feats corpus names 83 targets; the domain models 17. These tests pin which
is which, and fail if the corpus grows a target nobody has classified.
"""

from __future__ import annotations

from typing import Any

import pytest

from pf_tracker.domain.enums import ModifierTarget
from pf_tracker.rules.feat_targets import (
    KNOWN_TARGETS,
    SKILL_CHECK_PREFIX,
    UNMODELLED_TARGETS,
    is_classified_target,
    is_modelled_target,
    parse_feat_target,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("ca", ModifierTarget.AC),
        ("iniciativa", ModifierTarget.INITIATIVE),
        ("bmc", ModifierTarget.CMB),
        ("dmc", ModifierTarget.CMD),
        ("velocidad_base", ModifierTarget.SPEED),
        ("ataque", ModifierTarget.ALL_ATTACKS),
        ("ataque_cuerpo_a_cuerpo", ModifierTarget.ATTACK_MELEE),
        ("ataque_a_distancia", ModifierTarget.ATTACK_RANGED),
        ("dano_arma", ModifierTarget.ALL_DAMAGE),
        ("salvacion_fortaleza", ModifierTarget.SAVE_FORT),
        ("salvacion_reflejos", ModifierTarget.SAVE_REF),
        ("salvacion_voluntad", ModifierTarget.SAVE_WILL),
    ],
)
def test_maps_the_targets_the_engine_can_apply(raw: str, expected: ModifierTarget) -> None:
    assert parse_feat_target(raw) == expected.value


def test_per_skill_targets_become_skill_targets() -> None:
    """Slugged the same way the skills catalog slugs its names, so the two agree."""
    assert parse_feat_target("prueba_habilidad.Acrobacias") == "SKILL:acrobacias"
    assert parse_feat_target("prueba_habilidad.Averiguar intenciones") == (
        "SKILL:averiguar-intenciones"
    )


def test_a_skill_chosen_at_selection_time_is_not_modelled() -> None:
    """Resolving it needs the character's feat options, which live outside the rules."""
    assert parse_feat_target("prueba_habilidad.Artesania_o_Profesion_elegida") is None
    assert parse_feat_target("prueba_habilidad.<Habilidad>") is None


def test_ability_checks_are_recognised_but_not_modelled() -> None:
    """The sheet derives no ability-check line, and the domain's ``ABILITY:`` target
    means an ability *score*, which is a different thing."""
    assert parse_feat_target("prueba_caracteristica.Constitucion") is None
    assert is_classified_target("prueba_caracteristica.Constitucion")


@pytest.mark.parametrize("raw", ["nivel_conjuro", "puntos_ki", "bmc_desarme", "dano_dos_manos"])
def test_unmodelled_targets_resolve_to_none_rather_than_raising(raw: str) -> None:
    """An unmodelled target is expected, not exceptional: the effect is still shown,
    it just is not summed into a derived number."""
    assert parse_feat_target(raw) is None
    assert not is_modelled_target(raw)


def test_every_declared_target_is_classified(nucleo_raw: dict[str, Any]) -> None:
    groups = nucleo_raw["dotes"]["esquema_efectos"]["objetivos"].values()
    declared = {target for group in groups if isinstance(group, list) for target in group}
    # The ability-check template is filed under `unmodelled` verbatim.
    unclassified = declared - KNOWN_TARGETS
    assert not unclassified, f"targets nobody classified: {sorted(unclassified)}"


def test_every_target_used_by_a_feat_is_classified(nucleo_raw: dict[str, Any]) -> None:
    """Concrete per-skill uses expand the template, so usage is checked separately."""
    for feat in nucleo_raw["dotes"]["lista"]:
        for effect in feat["efectos"]:
            for modifier in effect.get("modificadores") or []:
                target = modifier["objetivo"]
                assert is_classified_target(target), (
                    f"{feat['nombre']} uses unclassified target {target!r}"
                )


def test_named_skill_targets_exist_in_the_skills_catalog(nucleo_raw: dict[str, Any]) -> None:
    """A misspelt skill would slug into a target no skill ever queries."""
    known = {skill["nombre"] for skill in nucleo_raw["habilidades"]["lista"]}
    for feat in nucleo_raw["dotes"]["lista"]:
        for effect in feat["efectos"]:
            for modifier in effect.get("modificadores") or []:
                target = modifier["objetivo"]
                if not target.startswith(SKILL_CHECK_PREFIX):
                    continue
                name = target[len(SKILL_CHECK_PREFIX) :]
                if parse_feat_target(target) is None:
                    continue  # a placeholder, already covered above
                assert name in known, f"{feat['nombre']} names unknown skill {name!r}"


def test_mapped_and_unmodelled_sets_are_disjoint() -> None:
    """A target in both would make the classification ambiguous."""
    mapped = {t for t in KNOWN_TARGETS if is_modelled_target(t)}
    assert not (mapped & UNMODELLED_TARGETS)


def test_choice_kind_is_derived_from_the_targets(rules_repository: object) -> None:
    """The editor needs to know what to ask for; the engine needs the answer."""
    catalog = {f.name: f for f in rules_repository.feats()}  # type: ignore[attr-defined]
    assert catalog["Soltura con un arma"].choice_kind == "weapon"
    assert catalog["Especialización mayor con un arma"].choice_kind == "weapon"
    assert catalog["Soltura con una habilidad"].choice_kind == "skill"
    assert catalog["Soltura con los conjuros"].choice_kind == "school"
    assert catalog["Esquiva"].choice_kind is None


def test_every_feat_needing_a_choice_is_flagged(rules_repository: object) -> None:
    """A feat that names a chosen weapon but is not flagged would silently apply to
    nothing, since the resolver has no option to read."""
    for feat in rules_repository.feats():  # type: ignore[attr-defined]
        names_a_choice = any(
            m.target in {"ataque_arma_seleccionada", "dano_arma_seleccionada"}
            for e in feat.effects
            for m in e.modifiers
        )
        assert names_a_choice is (feat.choice_kind == "weapon"), feat.name
