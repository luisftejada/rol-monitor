"""The modifier stacking engine.

``resolve`` takes a target and a sequence of modifiers and returns the total plus
the audit trail: which modifiers applied and which were suppressed (and why). It is
pure and deterministic and never mutates its inputs. The stacking rules come from
``sistema.tipos_de_bonificador``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace

from pf_tracker.domain.enums import (
    BonusType,
    SourceKind,
    target_matches,
)


@dataclass(frozen=True, slots=True)
class Modifier:
    """A single contribution to a derived value."""

    target: str
    value: int
    bonus_type: BonusType | None
    source: str
    source_kind: SourceKind
    condition: str | None = None
    is_active: bool = True
    expires_in_rounds: int | None = None


@dataclass(frozen=True, slots=True)
class SuppressedModifier:
    """A modifier that did not apply, with a human-readable reason."""

    modifier: Modifier
    reason: str


@dataclass(frozen=True, slots=True)
class ResolvedValue:
    """The outcome of resolving a target: a total plus its full audit trail."""

    target: str
    total: int
    applied: list[Modifier] = field(default_factory=list)
    suppressed: list[SuppressedModifier] = field(default_factory=list)


def resolve(target: str, modifiers: Sequence[Modifier]) -> ResolvedValue:
    """Resolve ``target`` over ``modifiers`` into a total with applied/suppressed lists.

    Rules:

    - Only active modifiers whose target matches (including group targets such as
      ``ALL_SAVES``) participate.
    - Penalties (negative values) always stack, except exact duplicates of the same
      named effect, deduplicated by ``(source, target)``.
    - Untyped, dodge, and circumstance bonuses stack with everything, including with
      themselves.
    - For every other bonus type, only the largest of that type applies; the rest are
      suppressed with a reason.
    """
    relevant = [m for m in modifiers if m.is_active and target_matches(m.target, target)]

    positives = [m for m in relevant if m.value > 0]
    nonpositives = [m for m in relevant if m.value <= 0]

    applied: list[Modifier] = []
    suppressed: list[SuppressedModifier] = []

    _resolve_penalties(nonpositives, applied, suppressed)
    _resolve_bonuses(positives, applied, suppressed)

    total = sum(m.value for m in applied)
    # Present applied modifiers largest-first so the breakdown reads naturally,
    # keeping penalties (equal magnitude aside) in a stable order.
    applied.sort(key=lambda m: m.value, reverse=True)
    return ResolvedValue(target=target, total=total, applied=applied, suppressed=suppressed)


def _resolve_penalties(
    nonpositives: Sequence[Modifier],
    applied: list[Modifier],
    suppressed: list[SuppressedModifier],
) -> None:
    """Penalties stack, but the same named penalty applied twice counts once.

    Duplicates are grouped by ``(source, target)``; the most restrictive (most
    negative) of each group applies and the rest are suppressed. Selecting by value
    keeps the result independent of input ordering.
    """
    groups: dict[tuple[str, str], list[Modifier]] = {}
    for modifier in nonpositives:
        groups.setdefault((modifier.source, modifier.target), []).append(modifier)

    for group in groups.values():
        worst = min(group, key=lambda m: m.value)
        for modifier in group:
            if modifier is worst:
                applied.append(modifier)
            else:
                suppressed.append(
                    SuppressedModifier(
                        modifier=modifier,
                        reason=f"penalización duplicada de «{modifier.source}»",
                    )
                )


def _resolve_bonuses(
    positives: Sequence[Modifier],
    applied: list[Modifier],
    suppressed: list[SuppressedModifier],
) -> None:
    """Untyped and dodge always stack; circumstance stacks across distinct sources;
    every other type keeps only its largest."""
    # Group circumstance bonuses by source (largest per source applies); track the
    # best bonus per other non-stacking type.
    best_by_type: dict[BonusType, Modifier] = {}
    circumstance_by_source: dict[str, list[Modifier]] = {}

    for modifier in positives:
        bonus_type = modifier.bonus_type
        if bonus_type is None or bonus_type == BonusType.DODGE:
            applied.append(modifier)
        elif bonus_type == BonusType.CIRCUMSTANCE:
            circumstance_by_source.setdefault(modifier.source, []).append(modifier)
        else:
            current = best_by_type.get(bonus_type)
            if current is None or modifier.value > current.value:
                best_by_type[bonus_type] = modifier

    # Non-stacking typed bonuses: the largest of each type applies, the rest are
    # suppressed. Selecting by value keeps the outcome order-independent.
    for modifier in positives:
        bonus_type = modifier.bonus_type
        if bonus_type is None or bonus_type in (BonusType.DODGE, BonusType.CIRCUMSTANCE):
            continue
        winner = best_by_type[bonus_type]
        if modifier is winner:
            applied.append(modifier)
        else:
            suppressed.append(_supersede(modifier, winner))

    # Circumstance bonuses stack across distinct sources; within a source the
    # largest applies and the rest are suppressed as duplicates.
    for group in circumstance_by_source.values():
        best = max(group, key=lambda m: m.value)
        for modifier in group:
            if modifier is best:
                applied.append(modifier)
            else:
                suppressed.append(
                    SuppressedModifier(
                        modifier=modifier,
                        reason=f"circunstancia duplicada de «{modifier.source}»",
                    )
                )


def _supersede(loser: Modifier, winner: Modifier) -> SuppressedModifier:
    type_label = loser.bonus_type.value if loser.bonus_type else "sin tipo"
    return SuppressedModifier(
        modifier=loser,
        reason=f"bonificador de {type_label} superado por «{winner.source}» (+{winner.value})",
    )


def deactivate(modifier: Modifier) -> Modifier:
    """Return a copy of ``modifier`` marked inactive (never mutates the original)."""
    return replace(modifier, is_active=False)
