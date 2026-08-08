"""Turn a feat's corpus effects into domain :class:`Modifier` values.

Two rules govern what this producer will emit, both forced by the data:

**Only passive feats apply on their own.** 42 of the applicable modifiers belong to
feats activated by declaring them (``Ataque poderoso``, ``Pericia en combate``),
which the app already models as stance toggles. Emitting those here as well would
double-count them, so anything other than ``pasiva`` is skipped.

**A conditional effect applies only when its predicate is known to hold.** Some
predicates are static character facts (``ataque_base``, ``dados_de_golpe``,
``rangos_habilidad``) and can be decided here. The rest are situational — "on a
confirmed critical", "while fighting defensively", "within 30 feet" — and are never
assumed true, because a bonus silently added to every attack is worse than one the
GM applies by hand.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from pf_tracker.domain.enums import SKILL_TARGET_PREFIX, SourceKind
from pf_tracker.domain.modifiers import Modifier
from pf_tracker.rules.catalog import FeatDTO, FeatEffectDTO, FeatModifierDTO
from pf_tracker.rules.feat_targets import parse_feat_target
from pf_tracker.rules.feat_vocabulary import is_scalar_feat_bonus, parse_feat_bonus_type

#: Only this activation applies without the GM declaring it.
PASSIVE = "pasiva"

#: Predicates decidable from the character sheet alone. Anything else is situational.
_STATIC_PREDICATES = frozenset({"ataque_base", "dados_de_golpe", "rangos_habilidad"})


@dataclass(frozen=True, slots=True)
class FeatContext:
    """The character facts a conditional feat effect can be judged against."""

    base_attack_bonus: int = 0
    hit_dice: int = 0
    #: Ranks per skill slug, used by ``rangos_habilidad`` predicates.
    skill_ranks: Mapping[str, int] = field(default_factory=dict)

    def ranks_in(self, skill_slug: str) -> int:
        return self.skill_ranks.get(skill_slug, 0)


@dataclass(frozen=True, slots=True)
class FeatApplication:
    """What a feat contributed, and what it could not."""

    modifiers: tuple[Modifier, ...] = ()
    #: Human-readable notes for effects that exist but were not turned into numbers.
    notes: tuple[str, ...] = ()


def apply_feat(feat: FeatDTO, context: FeatContext) -> FeatApplication:
    """Emit the modifiers a feat contributes passively, plus notes for the rest."""
    if feat.activation != PASSIVE:
        return FeatApplication(notes=_declared_note(feat))

    modifiers: list[Modifier] = []
    notes: list[str] = []

    for effect in feat.effects:
        if not effect_holds(effect, context):
            if effect.modifiers:
                notes.append(_conditional_note(feat, effect))
            continue
        for raw in effect.modifiers:
            modifier = _to_modifier(feat, raw)
            if modifier is None:
                notes.append(f"«{feat.name}»: {raw.target} {raw.value}")
            else:
                modifiers.append(modifier)

    return FeatApplication(modifiers=tuple(modifiers), notes=tuple(notes))


def apply_feats(feats: Sequence[FeatDTO], context: FeatContext) -> FeatApplication:
    """Fold :func:`apply_feat` over several feats."""
    modifiers: list[Modifier] = []
    notes: list[str] = []
    for feat in feats:
        applied = apply_feat(feat, context)
        modifiers.extend(applied.modifiers)
        notes.extend(applied.notes)
    return FeatApplication(modifiers=tuple(modifiers), notes=tuple(notes))


def _declared_note(feat: FeatDTO) -> tuple[str, ...]:
    """Feats the GM declares are listed, not applied."""
    if not any(effect.modifiers for effect in feat.effects):
        return ()
    return (f"«{feat.name}»: se declara al usarla ({feat.activation})",)


def _conditional_note(feat: FeatDTO, effect: FeatEffectDTO) -> str:
    detail = effect.condition or ", ".join(sorted(effect.when))
    return f"«{feat.name}»: sólo {detail}"


def _to_modifier(feat: FeatDTO, raw: FeatModifierDTO) -> Modifier | None:
    """Translate one corpus modifier, or return ``None`` if it cannot be summed."""
    if not isinstance(raw.value, int) or not is_scalar_feat_bonus(raw.bonus_type):
        return None  # multipliers, dice and formulas are dispatched elsewhere
    target = parse_feat_target(raw.target)
    if target is None:
        return None

    return Modifier(
        target=target,
        value=raw.value,
        bonus_type=parse_feat_bonus_type(raw.bonus_type),
        source=feat.name,
        source_kind=SourceKind.FEAT,
    )


def effect_holds(effect: FeatEffectDTO, context: FeatContext) -> bool:
    """Whether a conditional effect is known to apply to this character.

    Public because the per-weapon resolver gates on the same predicates.
    """
    if not effect.when:
        # A prose-only `condicion` with no predicate is situational by definition.
        return effect.condition is None
    if not set(effect.when) <= _STATIC_PREDICATES:
        return False

    for key, bound in effect.when.items():
        if key == "ataque_base":
            actual = context.base_attack_bonus
        elif key == "dados_de_golpe":
            actual = context.hit_dice
        else:
            actual = _ranks_for(effect, context)
        if not _within(actual, bound):
            return False
    return True


def _ranks_for(effect: FeatEffectDTO, context: FeatContext) -> int:
    """Ranks in the skill the effect targets; ``rangos_habilidad`` is about it."""
    for modifier in effect.modifiers:
        target = parse_feat_target(modifier.target)
        if target and target.startswith(SKILL_TARGET_PREFIX):
            return context.ranks_in(target[len(SKILL_TARGET_PREFIX) :])
    return 0


def _within(actual: int, bound: object) -> bool:
    if not isinstance(bound, Mapping):
        return False
    low = bound.get("min")
    high = bound.get("max")
    if isinstance(low, int) and actual < low:
        return False
    return not (isinstance(high, int) and actual > high)
