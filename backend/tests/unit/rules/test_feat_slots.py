"""The feat budget: how many a character may pick, and what is handed to them."""

from __future__ import annotations

from pf_tracker.rules.catalog import FeatSlotDTO
from pf_tracker.rules.feat_slots import ClassLevelRef, build_budget
from pf_tracker.rules.repository import RulesRepository

FEAT_LEVELS = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19]


def budget(**kwargs: object):  # type: ignore[no-untyped-def]
    defaults: dict[str, object] = {
        "feat_levels": FEAT_LEVELS,
        "class_levels": [],
        "class_slots": {},
        "race_name": None,
        "race_slots": [],
        "chosen": [],
    }
    return build_budget(**{**defaults, **kwargs})  # type: ignore[arg-type]


def test_base_feats_come_at_odd_levels() -> None:
    assert budget(class_levels=[ClassLevelRef("Guerrero", 1)]).available == 1
    assert budget(class_levels=[ClassLevelRef("Guerrero", 4)]).available == 2  # 1 and 3
    assert budget(class_levels=[ClassLevelRef("Guerrero", 20)]).available == 10


def test_class_slots_are_gated_on_the_level_in_that_class() -> None:
    """A cleric 8 / fighter 4 has the fighter's level-4 feat; the reverse does not."""
    fighter = [
        FeatSlotDTO(level=1, choice="tipos", types=["Combate"]),
        FeatSlotDTO(level=4, choice="tipos", types=["Combate"]),
    ]
    slots = {"Guerrero": fighter}

    front = budget(
        class_levels=[ClassLevelRef("Clérigo", 4), ClassLevelRef("Guerrero", 8)],
        class_slots=slots,
    )
    back = budget(
        class_levels=[ClassLevelRef("Clérigo", 8), ClassLevelRef("Guerrero", 4)],
        class_slots=slots,
    )
    # Same character level, so the same base feats; the class ones differ.
    assert front.available == back.available == 6 + 2  # 6 base at level 12, 2 fighter
    assert back.available == front.available

    low = budget(
        class_levels=[ClassLevelRef("Clérigo", 8), ClassLevelRef("Guerrero", 3)],
        class_slots=slots,
    )
    assert low.available == 6 + 1  # only the fighter's level-1 slot


def test_a_fixed_feat_is_granted_and_costs_no_choice() -> None:
    """A level-1 monk picks one feat, not three: the other two are handed over."""
    monk = [
        FeatSlotDTO(level=1, choice="fija", feat="Impacto sin arma mejorado"),
        FeatSlotDTO(level=1, choice="fija", feat="Puñetazo aturdidor"),
        FeatSlotDTO(level=1, choice="lista", list_key="dotes_adicionales_monje"),
    ]
    result = budget(class_levels=[ClassLevelRef("Monje", 1)], class_slots={"Monje": monk})

    assert result.granted == ("Impacto sin arma mejorado", "Puñetazo aturdidor")
    assert result.available == 2  # one base + the monk's own choice
    assert result.spent == 0


def test_a_granted_feat_listed_explicitly_is_not_charged_twice() -> None:
    monk = [FeatSlotDTO(level=1, choice="fija", feat="Impacto sin arma mejorado")]
    result = budget(
        class_levels=[ClassLevelRef("Monje", 1)],
        class_slots={"Monje": monk},
        chosen=["Impacto sin arma mejorado", "Esquiva"],
    )
    assert result.spent == 1  # only Esquiva
    assert not result.is_over_budget


def test_racial_feats_are_added() -> None:
    human = [FeatSlotDTO(level=1, choice="libre")]
    result = budget(
        class_levels=[ClassLevelRef("Guerrero", 1)],
        race_name="Humano",
        race_slots=human,
    )
    assert result.available == 2  # one base, one racial
    assert {s.source for s in result.slots} == {"base", "Humano"}


def test_over_budget_is_reported_not_prevented() -> None:
    result = budget(
        class_levels=[ClassLevelRef("Guerrero", 1)],
        chosen=["Esquiva", "Iniciativa mejorada", "Aguante"],
    )
    assert result.available == 1
    assert result.spent == 3
    assert result.is_over_budget


def test_a_level_zero_character_gets_nothing() -> None:
    result = budget(race_name="Humano", race_slots=[FeatSlotDTO(level=1, choice="libre")])
    assert result.available == 0
    assert result.slots == ()


def test_real_corpus_human_fighter_5(rules_repository: RulesRepository) -> None:
    """End to end against the vendored corpus: 3 base + 4 fighter + 1 human."""
    fighter = rules_repository.class_summary("guerrero")
    human = next(r for r in rules_repository.races if r.slug == "humano")
    assert fighter is not None

    result = build_budget(
        feat_levels=rules_repository.meta.feat_levels,
        class_levels=[ClassLevelRef(fighter.name, 5)],
        class_slots={fighter.name: fighter.bonus_feats},
        race_name=human.name,
        race_slots=human.bonus_feats,
        chosen=["Esquiva"],
    )
    # Base at 1, 3, 5; fighter at 1, 2, 4; human at 1.
    assert result.available == 7
    assert result.spent == 1
    assert result.granted == ()
