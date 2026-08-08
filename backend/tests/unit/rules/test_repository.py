"""Unit tests for the RulesRepository English adapter, over the real corpus."""

from __future__ import annotations

import pytest

from pf_tracker.rules.repository import RuleNotFoundError, RulesRepository


def test_meta_exposes_stacking_classification(rules_repository: RulesRepository) -> None:
    meta = rules_repository.meta
    assert "esquiva" in meta.bonus_types.always_stack
    assert "armadura" in meta.bonus_types.do_not_stack
    assert [a.abbr for a in meta.abilities] == ["Fue", "Des", "Con", "Int", "Sab", "Car"]
    assert len(meta.sizes) == 9
    assert meta.units  # non-empty units map
    assert meta.feat_types == ["General", "Combate", "Metamágica", "Creación de objeto", "Crítico"]


def test_size_ac_and_cmb_modifiers_are_inverse(rules_repository: RulesRepository) -> None:
    menudo = next(s for s in rules_repository.meta.sizes if s.name == "Menudo")
    assert menudo.ac_attack_mod == 8
    assert menudo.cmb_cmd_mod == -8


def test_races_carry_modifiers_and_languages(rules_repository: RulesRepository) -> None:
    elf = next(r for r in rules_repository.races if r.slug == "elfo")
    assert elf.ability_modifiers == {"Des": 2, "Int": 2, "Con": -2}
    assert "inicio" in elf.languages
    assert isinstance(elf.languages["inicio"], list)


def test_classes_split_base_and_prestige(rules_repository: RulesRepository) -> None:
    base = rules_repository.classes()
    combined = rules_repository.classes(include_prestige=True)
    assert len(base) == 11
    assert len(combined) == 21
    assert all(not c.is_prestige for c in base)
    assert any(c.is_prestige for c in combined)


def test_spellcaster_flag(rules_repository: RulesRepository) -> None:
    by_slug = {c.slug: c for c in rules_repository.classes()}
    assert by_slug["mago"].is_spellcaster is True
    assert by_slug["guerrero"].is_spellcaster is False


def test_class_progression_parses_bab(rules_repository: RulesRepository) -> None:
    row = rules_repository.class_progression("guerrero", 11)
    assert row.bab == "+11/+6/+1"
    assert row.bab_iteratives == [11, 6, 1]
    assert row.will == 3


def test_class_progression_includes_spells_for_casters(rules_repository: RulesRepository) -> None:
    row = rules_repository.class_progression("mago", 1)
    assert row.spells_per_day is not None


def test_class_progression_unknown_class_raises(rules_repository: RulesRepository) -> None:
    with pytest.raises(RuleNotFoundError):
        rules_repository.class_progression("noexiste", 1)


def test_class_progression_bad_level_raises(rules_repository: RulesRepository) -> None:
    with pytest.raises(RuleNotFoundError):
        rules_repository.class_progression("guerrero", 99)


def test_skills_have_slug_and_class_refs(rules_repository: RulesRepository) -> None:
    acro = next(s for s in rules_repository.skills if s.slug == "acrobacias")
    assert acro.ability == "Des"
    assert acro.armor_check_penalty is True
    assert "picaro" in acro.class_for


def test_feats_annotate_eligibility_without_hiding(rules_repository: RulesRepository) -> None:
    at_zero = {f.name: f for f in rules_repository.feats(bab=0)}
    at_six = {f.name: f for f in rules_repository.feats(bab=6)}
    # Same population regardless of eligibility (nothing hidden).
    assert set(at_zero) == set(at_six)
    # "Acometer" requires base attack +6.
    assert at_zero["Acometer"].is_eligible is False
    assert at_six["Acometer"].is_eligible is True


def test_feats_type_filter(rules_repository: RulesRepository) -> None:
    combat = rules_repository.feats(feat_type="Combate")
    assert combat
    assert all(any(t.lower() == "combate" for t in f.types) for f in combat)


def test_feats_ability_prerequisite(rules_repository: RulesRepository) -> None:
    low = {f.name: f for f in rules_repository.feats(bab=1, abilities={"Fue": 10})}
    high = {f.name: f for f in rules_repository.feats(bab=1, abilities={"Fue": 15})}
    # Power Attack requires Str 13.
    assert low["Ataque poderoso"].is_eligible is False
    assert high["Ataque poderoso"].is_eligible is True


def test_weapons_search_is_accent_insensitive(rules_repository: RulesRepository) -> None:
    result = rules_repository.weapons(search="espada lar")
    assert [w.name for w in result] == ["Espada larga"]


def test_weapons_category_and_proficiency_filters(rules_repository: RulesRepository) -> None:
    exotic = rules_repository.weapons(proficiency="exótica")
    assert exotic
    assert all(w.proficiency == "exótica" for w in exotic)


def test_weapons_category_filter(rules_repository: RulesRepository) -> None:
    ranged = rules_repository.weapons(category="Armas a distancia")
    assert ranged
    assert all(w.category == "Armas a distancia" for w in ranged)


def test_weapon_critical_parsing(rules_repository: RulesRepository) -> None:
    cimitarra = rules_repository.weapons(search="cimitarra")[0]
    assert [(c.threat_range, c.multiplier) for c in cimitarra.critical] == [(18, 2)]
    hammer = rules_repository.weapons(search="ganchudo")[0]
    assert [(c.threat_range, c.multiplier) for c in hammer.critical] == [(20, 3), (20, 4)]


def test_armor_filter_and_penalty_sign(rules_repository: RulesRepository) -> None:
    heavy = rules_repository.armor(category="pesada")
    assert heavy
    assert all(a.category == "pesada" for a in heavy)
    assert all(a.armor_check_penalty <= 0 for a in heavy)


def test_alignments_follow_corpus_order(rules_repository: RulesRepository) -> None:
    alignments = rules_repository.alignments
    assert [a.code for a in alignments] == ["LB", "NB", "CB", "LN", "N", "CN", "LM", "NM", "CM"]
    assert next(a for a in alignments if a.code == "LN").name == "Legal neutral"


def test_conditions_present(rules_repository: RulesRepository) -> None:
    conditions = rules_repository.conditions
    assert len(conditions) == 34
    assert any(c.slug == "apresado" for c in conditions)


def test_spells_filter_by_class_and_level(rules_repository: RulesRepository) -> None:
    result = rules_repository.spells(character_class="mago", level=3)
    assert result
    assert all(3 in s.levels.values() for s in result)


def test_spells_search(rules_repository: RulesRepository) -> None:
    result = rules_repository.spells(search="bola de fuego")
    assert any(s.name == "Bola de fuego" for s in result)


def test_spells_filter_by_level_only(rules_repository: RulesRepository) -> None:
    result = rules_repository.spells(level=0)
    assert result
    assert all(0 in s.levels.values() for s in result)


def test_spells_class_and_search_combined(rules_repository: RulesRepository) -> None:
    result = rules_repository.spells(character_class="mago", search="bola de fuego")
    assert result
    assert all("bola de fuego" in s.name.lower() for s in result)


def test_spells_unfiltered_returns_all(rules_repository: RulesRepository) -> None:
    assert len(rules_repository.spells()) == 623


def test_restricted_feat_lists_resolve_and_scale_with_level(
    rules_repository: RulesRepository,
) -> None:
    """The corpus states these four lists in four different shapes; resolving them
    here is what keeps that structure out of the frontend."""
    monk_1 = rules_repository.restricted_feat_list("dotes_adicionales_monje", 1)
    monk_6 = rules_repository.restricted_feat_list("dotes_adicionales_monje", 6)
    assert monk_1 and set(monk_1) < set(monk_6), "later levels add to the list"

    # A type filter plus explicit extras (wizard) resolves to real feat names.
    wizard = rules_repository.restricted_feat_list("dotes_adicionales_mago", 5)
    known = {f.name for f in rules_repository.feats()}
    assert wizard and set(wizard) <= known

    # A choice the sheet does not model yet (the ranger's style) unions its branches.
    ranger = rules_repository.restricted_feat_list("estilo_de_combate_explorador", 2)
    assert "Disparo a bocajarro" in ranger and "Combate con dos armas" in ranger
    assert rules_repository.restricted_list_note("estilo_de_combate_explorador")


def test_an_unknown_restricted_list_resolves_to_nothing(
    rules_repository: RulesRepository,
) -> None:
    assert rules_repository.restricted_feat_list("no_existe", 20) == []
