"""Table-driven tests for the modifier stacking engine."""

from __future__ import annotations

from pf_tracker.domain.enums import BonusType, ModifierTarget, SourceKind
from pf_tracker.domain.modifiers import Modifier, resolve


def mod(
    value: int,
    bonus_type: BonusType | None,
    source: str,
    *,
    target: str = ModifierTarget.AC.value,
    is_active: bool = True,
) -> Modifier:
    return Modifier(
        target=target,
        value=value,
        bonus_type=bonus_type,
        source=source,
        source_kind=SourceKind.MANUAL,
        is_active=is_active,
    )


def test_empty_input_totals_zero() -> None:
    result = resolve(ModifierTarget.AC.value, [])
    assert result.total == 0
    assert result.applied == []
    assert result.suppressed == []


def test_two_same_type_bonuses_largest_wins_smaller_suppressed() -> None:
    small = mod(1, BonusType.DEFLECTION, "Escudo de fe")
    big = mod(2, BonusType.DEFLECTION, "Anillo de protección +2")
    result = resolve(ModifierTarget.AC.value, [small, big])
    assert result.total == 2
    assert result.applied == [big]
    assert len(result.suppressed) == 1
    assert result.suppressed[0].modifier is small
    assert "superado" in result.suppressed[0].reason


def test_two_dodge_bonuses_both_apply() -> None:
    a = mod(1, BonusType.DODGE, "Esquiva")
    b = mod(1, BonusType.DODGE, "Movilidad")
    result = resolve(ModifierTarget.AC.value, [a, b])
    assert result.total == 2
    assert set(result.applied) == {a, b}
    assert result.suppressed == []


def test_two_untyped_bonuses_both_apply() -> None:
    a = mod(2, None, "Bendición improvisada")
    b = mod(3, None, "Ventaja del terreno")
    result = resolve(ModifierTarget.AC.value, [a, b])
    assert result.total == 5
    assert result.suppressed == []


def test_bonus_and_penalty_of_same_type_both_apply() -> None:
    bonus = mod(2, BonusType.ENHANCEMENT, "Armadura +2")
    penalty = mod(-2, BonusType.ENHANCEMENT, "Óxido")
    result = resolve(ModifierTarget.AC.value, [bonus, penalty])
    # Penalties always apply; the positive is the sole enhancement bonus.
    assert result.total == 0
    assert set(result.applied) == {bonus, penalty}
    assert result.suppressed == []


def test_duplicate_penalties_from_same_source_dedupe() -> None:
    p1 = mod(-2, None, "Fatigado")
    p2 = mod(-2, None, "Fatigado")
    result = resolve(ModifierTarget.AC.value, [p1, p2])
    assert result.total == -2
    assert len(result.applied) == 1
    assert len(result.suppressed) == 1
    assert "duplicada" in result.suppressed[0].reason


def test_distinct_penalties_stack() -> None:
    p1 = mod(-2, None, "Fatigado")
    p2 = mod(-1, None, "Enfermo")
    result = resolve(ModifierTarget.AC.value, [p1, p2])
    assert result.total == -3
    assert len(result.applied) == 2


def test_circumstance_from_distinct_sources_stack() -> None:
    a = mod(2, BonusType.CIRCUMSTANCE, "Flanqueo")
    b = mod(1, BonusType.CIRCUMSTANCE, "Terreno elevado")
    result = resolve(ModifierTarget.AC.value, [a, b])
    assert result.total == 3
    assert result.suppressed == []


def test_circumstance_from_identical_source_dedupes() -> None:
    a = mod(2, BonusType.CIRCUMSTANCE, "Ayudar a otro")
    b = mod(2, BonusType.CIRCUMSTANCE, "Ayudar a otro")
    result = resolve(ModifierTarget.AC.value, [a, b])
    assert result.total == 2
    assert len(result.applied) == 1
    assert "circunstancia duplicada" in result.suppressed[0].reason


def test_inactive_modifiers_excluded() -> None:
    active = mod(2, BonusType.ENHANCEMENT, "Anillo")
    inactive = mod(5, BonusType.ENHANCEMENT, "Anillo mayor", is_active=False)
    result = resolve(ModifierTarget.AC.value, [active, inactive])
    assert result.total == 2
    assert result.applied == [active]
    # An inactive modifier is neither applied nor reported as suppressed.
    assert result.suppressed == []


def test_target_filtering_and_groups() -> None:
    ac = mod(2, None, "A", target=ModifierTarget.AC.value)
    all_saves = mod(
        1, BonusType.RESISTANCE, "Capa de resistencia", target=ModifierTarget.ALL_SAVES.value
    )
    fort_only = mod(2, BonusType.RESISTANCE, "Poción", target=ModifierTarget.SAVE_FORT.value)

    fort = resolve(ModifierTarget.SAVE_FORT.value, [ac, all_saves, fort_only])
    # Group ALL_SAVES contributes to Fort; two resistance bonuses -> largest (2).
    assert fort.total == 2
    assert fort.applied == [fort_only]

    reflex = resolve(ModifierTarget.SAVE_REF.value, [ac, all_saves, fort_only])
    assert reflex.total == 1
    assert reflex.applied == [all_saves]


def test_inputs_are_never_mutated() -> None:
    a = mod(1, BonusType.ENHANCEMENT, "A")
    b = mod(2, BonusType.ENHANCEMENT, "B")
    modifiers = [a, b]
    resolve(ModifierTarget.AC.value, modifiers)
    assert modifiers == [a, b]
