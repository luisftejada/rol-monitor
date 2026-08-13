"""What one more level buys, and in which class."""

from __future__ import annotations

import pytest

from pf_tracker.rules.level_up import ClassLevelRef, level_up_report
from pf_tracker.rules.repository import RuleNotFoundError, RulesRepository


def _report(repo: RulesRepository, levels: list[ClassLevelRef], taking: str, **kwargs: int):
    return level_up_report(
        repo,
        class_levels=levels,
        taking=taking,
        constitution_modifier=kwargs.get("con", 2),
        intelligence_modifier=kwargs.get("int_", 1),
    )


def test_a_fighter_reaching_four(rules_repository: RulesRepository) -> None:
    """Level 4 is the interesting one: it is an ability-increment level for the
    character *and* a bonus-feat level for the fighter."""
    report = _report(rules_repository, [ClassLevelRef("guerrero", 3)], "guerrero")

    assert (report.class_level_before, report.class_level_after) == (3, 4)
    assert (report.base_attack_before, report.base_attack_after) == (3, 4)
    assert report.saves_before["Fortaleza"] == 3
    assert report.saves_after["Fortaleza"] == 4
    assert report.hit_die == 10
    assert report.constitution_modifier == 2
    assert report.skill_ranks == 3  # fighter's 2 + Int 1
    assert report.grants_ability_increment is True
    assert report.grants_feat is False  # feats land on odd levels
    assert report.class_features == ("Dote adicional",)
    assert [slot.level for slot in report.bonus_feat_slots] == [4]


def test_an_odd_level_grants_the_characters_feat(rules_repository: RulesRepository) -> None:
    report = _report(rules_repository, [ClassLevelRef("guerrero", 2)], "guerrero")
    assert report.grants_feat is True
    assert report.grants_ability_increment is False


def test_the_feat_and_the_increment_follow_the_total_not_the_class(
    rules_repository: RulesRepository,
) -> None:
    """A fighter 2 / rogue 1 taking a rogue level reaches character level 4: the
    ability increment is owed even though the rogue only reaches 2."""
    report = _report(
        rules_repository,
        [ClassLevelRef("guerrero", 2), ClassLevelRef("picaro", 1)],
        "picaro",
    )
    assert (report.class_level_before, report.class_level_after) == (1, 2)
    assert (report.total_level_before, report.total_level_after) == (3, 4)
    assert report.grants_ability_increment is True


def test_multiclassing_into_a_new_class_starts_at_one(rules_repository: RulesRepository) -> None:
    """ "Se suman pg, BAB y salvaciones de cada clase": the new class contributes from
    its own level 1, and a d8 class' good Will save arrives all at once."""
    report = _report(rules_repository, [ClassLevelRef("guerrero", 3)], "clerigo")

    assert (report.class_level_before, report.class_level_after) == (0, 1)
    assert report.class_name == "Clérigo"
    assert report.hit_die == 8
    # Fighter 3 keeps its +3 BAB; a cleric's first level adds none (3/4 at level 1).
    assert (report.base_attack_before, report.base_attack_after) == (3, 3)
    # Cleric level 1 brings Fortitude +2 and Will +2 on top of the fighter's.
    assert report.saves_after["Voluntad"] == report.saves_before["Voluntad"] + 2


def test_skill_ranks_never_fall_below_one(rules_repository: RulesRepository) -> None:
    """A low Intelligence cannot take the last rank away."""
    report = _report(rules_repository, [ClassLevelRef("guerrero", 1)], "guerrero", int_=-3)
    assert report.skill_ranks == 1


def test_the_favored_class_note_is_the_corpus_wording(rules_repository: RulesRepository) -> None:
    """It is a choice — +1 hp or +1 rank — so it is quoted, not applied."""
    favored = _report(rules_repository, [ClassLevelRef("guerrero", 1, is_favored=True)], "guerrero")
    assert favored.favored_class_note is not None
    assert "pg" in favored.favored_class_note

    plain = _report(rules_repository, [ClassLevelRef("guerrero", 1)], "guerrero")
    assert plain.favored_class_note is None


def test_going_past_a_prestige_class_maximum_warns(rules_repository: RulesRepository) -> None:
    """Warns rather than refuses: house rules are real, and the report only reports."""
    report = _report(
        rules_repository,
        [ClassLevelRef("guerrero", 5), ClassLevelRef("caballero_arcano", 10)],
        "caballero_arcano",
    )
    assert any("supera el máximo" in warning for warning in report.warnings)


def test_an_unknown_class_is_an_error_not_an_empty_report(
    rules_repository: RulesRepository,
) -> None:
    with pytest.raises(RuleNotFoundError):
        _report(rules_repository, [ClassLevelRef("guerrero", 1)], "no_existe")
