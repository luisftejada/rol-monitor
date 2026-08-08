"""The producer that turns corpus feat effects into domain modifiers."""

from __future__ import annotations

import pytest

from pf_tracker.domain.enums import BonusType, ModifierTarget, SourceKind
from pf_tracker.rules.catalog import FeatDTO, FeatEffectDTO, FeatModifierDTO
from pf_tracker.rules.feat_effects import FeatContext, apply_feat, apply_feats
from pf_tracker.rules.repository import RulesRepository


def feat(
    name: str,
    *,
    activation: str = "pasiva",
    effects: list[FeatEffectDTO] | None = None,
) -> FeatDTO:
    return FeatDTO(
        slug=name.lower().replace(" ", "-"),
        name=name,
        types=["General"],
        activation=activation,
        effects=effects or [],
    )


def effect(
    *modifiers: FeatModifierDTO,
    condition: str | None = None,
    when: dict[str, object] | None = None,
) -> FeatEffectDTO:
    return FeatEffectDTO(condition=condition, when=when or {}, modifiers=list(modifiers))


def test_emits_a_modifier_for_a_passive_feat() -> None:
    applied = apply_feat(
        feat(
            "Esquiva", effects=[effect(FeatModifierDTO(target="ca", bonus_type="esquiva", value=1))]
        ),
        FeatContext(),
    )

    assert len(applied.modifiers) == 1
    modifier = applied.modifiers[0]
    assert modifier.target == ModifierTarget.AC.value
    assert modifier.value == 1
    assert modifier.bonus_type is BonusType.DODGE
    assert modifier.source == "Esquiva"
    assert modifier.source_kind is SourceKind.FEAT


def test_untyped_bonus_carries_no_bonus_type() -> None:
    applied = apply_feat(
        feat(
            "Iniciativa mejorada",
            effects=[effect(FeatModifierDTO(target="iniciativa", bonus_type="sin_tipo", value=4))],
        ),
        FeatContext(),
    )
    assert applied.modifiers[0].bonus_type is None
    assert applied.modifiers[0].target == ModifierTarget.INITIATIVE.value


def test_a_declared_feat_is_reported_but_not_applied() -> None:
    """`Ataque poderoso` is already a stance toggle; applying it here too would
    count it twice."""
    applied = apply_feat(
        feat(
            "Ataque poderoso",
            activation="opcional_declarada_antes_del_ataque",
            effects=[
                effect(
                    FeatModifierDTO(
                        target="ataque_cuerpo_a_cuerpo", bonus_type="penalizador", value=-1
                    )
                )
            ],
        ),
        FeatContext(base_attack_bonus=5),
    )

    assert applied.modifiers == ()
    assert "se declara al usarla" in applied.notes[0]


def test_a_declared_feat_with_no_numbers_produces_no_note() -> None:
    applied = apply_feat(feat("Correr", activation="rapida"), FeatContext())
    assert applied == apply_feat(feat("Correr", activation="rapida"), FeatContext())
    assert applied.modifiers == ()
    assert applied.notes == ()


@pytest.mark.parametrize(
    ("bab", "expected"),
    [(0, 0), (1, 1), (3, 1), (4, 0)],
)
def test_a_static_predicate_gates_the_effect(bab: int, expected: int) -> None:
    """`ataque_base: {min: 1, max: 3}` applies only inside that band."""
    applied = apply_feat(
        feat(
            "Escalonada",
            effects=[
                effect(
                    FeatModifierDTO(target="ca", bonus_type="sin_tipo", value=2),
                    when={"ataque_base": {"min": 1, "max": 3}},
                )
            ],
        ),
        FeatContext(base_attack_bonus=bab),
    )
    assert len(applied.modifiers) == expected


def test_a_skill_rank_predicate_reads_the_targeted_skill() -> None:
    """`Acrobático` gives +2 below 10 ranks in the skill it targets."""
    below = apply_feat(
        feat(
            "Acrobático",
            effects=[
                effect(
                    FeatModifierDTO(
                        target="prueba_habilidad.Acrobacias", bonus_type="sin_tipo", value=2
                    ),
                    when={"rangos_habilidad": {"max": 9}},
                )
            ],
        ),
        FeatContext(skill_ranks={"acrobacias": 4}),
    )
    assert below.modifiers[0].target == "SKILL:acrobacias"

    above = apply_feat(
        feat(
            "Acrobático",
            effects=[
                effect(
                    FeatModifierDTO(
                        target="prueba_habilidad.Acrobacias", bonus_type="sin_tipo", value=2
                    ),
                    when={"rangos_habilidad": {"max": 9}},
                )
            ],
        ),
        FeatContext(skill_ranks={"acrobacias": 12}),
    )
    assert above.modifiers == ()


def test_a_situational_predicate_is_never_assumed_true() -> None:
    """Silently adding a crit-confirmation bonus to every attack would be worse than
    leaving it to the GM."""
    applied = apply_feat(
        feat(
            "Crítico agotador",
            effects=[
                effect(
                    FeatModifierDTO(target="ca", bonus_type="sin_tipo", value=2),
                    when={"al_confirmar_critico": True},
                )
            ],
        ),
        FeatContext(),
    )
    assert applied.modifiers == ()
    assert applied.notes


def test_a_prose_only_condition_is_situational() -> None:
    applied = apply_feat(
        feat(
            "Disparo preciso",
            effects=[
                effect(
                    FeatModifierDTO(target="ataque_a_distancia", bonus_type="penalizador", value=0),
                    condition="objetivo trabado en combate cuerpo a cuerpo",
                )
            ],
        ),
        FeatContext(),
    )
    assert applied.modifiers == ()
    assert "sólo objetivo trabado" in applied.notes[0]


def test_non_scalar_values_are_noted_rather_than_summed() -> None:
    """Adding "x2" as if it were +2 is exactly the failure this must avoid."""
    applied = apply_feat(
        feat(
            "Correr",
            effects=[
                effect(
                    FeatModifierDTO(
                        target="velocidad_carrera", bonus_type="multiplicador", value="x5"
                    )
                )
            ],
        ),
        FeatContext(),
    )
    assert applied.modifiers == ()
    assert "x5" in applied.notes[0]


def test_an_unmodelled_target_is_noted_rather_than_dropped() -> None:
    applied = apply_feat(
        feat(
            "Combate a la defensiva",
            effects=[effect(FeatModifierDTO(target="puntos_ki", bonus_type="sin_tipo", value=1))],
        ),
        FeatContext(),
    )
    assert applied.modifiers == ()
    assert "puntos_ki" in applied.notes[0]


def test_apply_feats_folds_over_several() -> None:
    applied = apply_feats(
        [
            feat(
                "Esquiva",
                effects=[effect(FeatModifierDTO(target="ca", bonus_type="esquiva", value=1))],
            ),
            feat(
                "Iniciativa mejorada",
                effects=[
                    effect(FeatModifierDTO(target="iniciativa", bonus_type="sin_tipo", value=4))
                ],
            ),
        ],
        FeatContext(),
    )
    assert {m.source for m in applied.modifiers} == {"Esquiva", "Iniciativa mejorada"}


def test_real_corpus_feats_produce_the_expected_modifiers(
    rules_repository: RulesRepository,
) -> None:
    """End to end against the vendored corpus, not hand-built DTOs."""
    catalog = {f.name: f for f in rules_repository.feats()}
    context = FeatContext(base_attack_bonus=5, hit_dice=5)

    dodge = apply_feat(catalog["Esquiva"], context)
    assert [(m.target, m.value, m.bonus_type) for m in dodge.modifiers] == [
        (ModifierTarget.AC.value, 1, BonusType.DODGE)
    ]

    initiative = apply_feat(catalog["Iniciativa mejorada"], context)
    assert [(m.target, m.value) for m in initiative.modifiers] == [
        (ModifierTarget.INITIATIVE.value, 4)
    ]

    # Power Attack is a stance in this app, so it must not be applied here.
    assert apply_feat(catalog["Ataque poderoso"], context).modifiers == ()
