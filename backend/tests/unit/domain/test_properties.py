"""Property-based tests for the domain engine."""

from __future__ import annotations

from hypothesis import given
from hypothesis import strategies as st

from pf_tracker.domain.derivation import ability_modifier, derive_combat_sheet
from pf_tracker.domain.enums import (
    Ability,
    BabProgression,
    BonusType,
    ModifierTarget,
    Size,
    SourceKind,
)
from pf_tracker.domain.models import Character, ClassLevel, EquippedArmor
from pf_tracker.domain.modifiers import Modifier, resolve

_BONUS_TYPES = [None, *list(BonusType)]


@st.composite
def modifiers(draw: st.DrawFn, target: str = ModifierTarget.AC.value) -> Modifier:
    return Modifier(
        target=target,
        value=draw(st.integers(min_value=-10, max_value=10)),
        bonus_type=draw(st.sampled_from(_BONUS_TYPES)),
        source=draw(st.sampled_from(["A", "B", "C", "D"])),
        source_kind=SourceKind.MANUAL,
        is_active=draw(st.booleans()),
    )


@given(score=st.integers(min_value=0, max_value=60))
def test_ability_modifier_matches_formula(score: int) -> None:
    assert ability_modifier(score) == (score - 10) // 2


@given(a=st.integers(min_value=0, max_value=60), b=st.integers(min_value=0, max_value=60))
def test_ability_modifier_is_monotonic(a: int, b: int) -> None:
    if a <= b:
        assert ability_modifier(a) <= ability_modifier(b)


@given(mods=st.lists(modifiers(), max_size=8), data=st.data())
def test_resolve_is_order_invariant(mods: list[Modifier], data: st.DataObject) -> None:
    shuffled = data.draw(st.permutations(mods))
    assert (
        resolve(ModifierTarget.AC.value, mods).total
        == resolve(ModifierTarget.AC.value, list(shuffled)).total
    )


@given(mods=st.lists(modifiers(), max_size=8), value=st.integers(-10, 10))
def test_adding_inactive_modifier_never_changes_total(mods: list[Modifier], value: int) -> None:
    baseline = resolve(ModifierTarget.AC.value, mods).total
    inactive = Modifier(
        target=ModifierTarget.AC.value,
        value=value,
        bonus_type=None,
        source="dormido",
        source_kind=SourceKind.MANUAL,
        is_active=False,
    )
    assert resolve(ModifierTarget.AC.value, [*mods, inactive]).total == baseline


@st.composite
def ac_characters(draw: st.DrawFn) -> Character:
    def armor(is_shield: bool) -> EquippedArmor | None:
        if not draw(st.booleans()):
            return None
        return EquippedArmor(
            name="armadura",
            is_shield=is_shield,
            ac_bonus=draw(st.integers(0, 10)),
            max_dex=draw(st.one_of(st.none(), st.integers(0, 8))),
            armor_check_penalty=draw(st.integers(-8, 0)),
            arcane_spell_failure=0,
            category="ligera",
        )

    dex = draw(st.integers(3, 24))
    return Character(
        name="prop",
        size=draw(st.sampled_from(list(Size))),
        base_speed_ft=30,
        class_levels=(ClassLevel("guerrero", "Guerrero", 1, BabProgression.FULL, 10, {}),),
        base_ability_scores={Ability.DEX: dex},
        armor=armor(False),
        shield=armor(True),
        natural_armor_bonus=draw(st.integers(0, 8)),
        deflection_bonus=draw(st.integers(0, 5)),
    )


@given(character=ac_characters())
def test_touch_and_flatfooted_never_exceed_full_ac(character: Character) -> None:
    sheet = derive_combat_sheet(character)
    assert sheet.ac.touch <= sheet.ac.resolved.total
    dex_mod = sheet.abilities[Ability.DEX].modifier
    if dex_mod >= 0:
        assert sheet.ac.flat_footed <= sheet.ac.resolved.total
