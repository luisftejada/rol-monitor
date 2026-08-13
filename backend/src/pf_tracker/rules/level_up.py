"""What a character gains by taking one more level, and in which class.

This reports; it decides nothing and changes nothing. The owner applies the result
by hand in the cards that already exist, so the job here is to be *complete* — a
number missing from this list is a number nobody will think to look up.

Multiclassing is the normal case, not a corner: the level goes to one class, and
base attack, saves and hit points come from that class while the feat and the
ability increment are owed to the character's *total* level.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from pf_tracker.domain.derivation import base_bab
from pf_tracker.domain.enums import BabProgression, SaveKind
from pf_tracker.rules.catalog import FeatSlotDTO
from pf_tracker.rules.repository import RuleNotFoundError, RulesRepository


@dataclass(frozen=True, slots=True)
class LevelUpReport:
    """Everything one level buys, stated as before → after where it is a number."""

    class_slug: str
    class_name: str
    #: Level in *that* class, and the character's total, each before and after.
    class_level_before: int
    class_level_after: int
    total_level_before: int
    total_level_after: int

    #: Hit points: the die you roll plus your Constitution modifier, which is the
    #: player's to roll, so it is reported rather than applied.
    hit_die: int
    constitution_modifier: int

    base_attack_before: int
    base_attack_after: int

    #: The three ways a level's hit points may be decided, as numbers the caller can
    #: use without knowing the rule. Rolling is randomness and belongs to whoever
    #: presses the button; the *floor* is a rules figure and belongs here.
    #: ``hit_points_floor`` is half the die plus one — 6 on a d10, 5 on a d8.
    hit_points_floor: int = 0
    #: True only for a character's very first level, which takes the die's maximum.
    #: A second class' first level is not special; the character's is.
    is_first_level: bool = False

    #: Save totals from class progression rows, summed across every class.
    saves_before: dict[str, int] = field(default_factory=dict)
    saves_after: dict[str, int] = field(default_factory=dict)

    #: Skill ranks the level grants: the class' own plus the Intelligence modifier,
    #: never below one.
    skill_ranks: int = 0

    #: Owed to the character's total level, not to the class taking it.
    grants_feat: bool = False
    grants_ability_increment: bool = False

    #: The class' own `especial` text for the level being taken, and any bonus feat
    #: slot it opens.
    class_features: tuple[str, ...] = ()
    bonus_feat_slots: tuple[FeatSlotDTO, ...] = ()

    #: The corpus' wording for the favored-class choice, when this class is one.
    favored_class_note: str | None = None
    #: Spells per day for the new level, when the class casts.
    spells_per_day: str | None = None
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ClassLevelRef:
    """A class the character has levels in."""

    slug: str
    level: int
    is_favored: bool = False


def level_up_report(
    repo: RulesRepository,
    *,
    class_levels: list[ClassLevelRef],
    taking: str,
    constitution_modifier: int,
    intelligence_modifier: int,
) -> LevelUpReport:
    """What the character gains by putting the next level into ``taking``.

    ``taking`` may be a class they already have or a new one, which is what makes
    this the multiclass path as well as the single-class one.
    """
    summary = repo.class_summary(taking)
    if summary is None:
        raise RuleNotFoundError(f"unknown class: {taking}")

    current = {entry.slug: entry for entry in class_levels}
    before = current.get(taking)
    class_before = before.level if before else 0
    class_after = class_before + 1
    total_before = sum(entry.level for entry in class_levels)

    after_levels = [
        ClassLevelRef(entry.slug, entry.level + 1 if entry.slug == taking else entry.level)
        for entry in class_levels
    ]
    if before is None:
        after_levels.append(ClassLevelRef(taking, 1))

    warnings: list[str] = []
    if summary.max_level and class_after > summary.max_level:
        warnings.append(
            f"{summary.name}: nivel {class_after} supera el máximo "
            f"de la clase ({summary.max_level})"
        )

    ranks = max(1, summary.skill_ranks_per_level + intelligence_modifier)
    die = summary.hit_die if isinstance(summary.hit_die, int) else _die(summary.hit_die)

    return LevelUpReport(
        class_slug=summary.slug,
        class_name=summary.name,
        class_level_before=class_before,
        class_level_after=class_after,
        total_level_before=total_before,
        total_level_after=total_before + 1,
        hit_die=die,
        constitution_modifier=constitution_modifier,
        hit_points_floor=_hp_floor(die),
        is_first_level=total_before == 0,
        base_attack_before=_total_bab(repo, class_levels),
        base_attack_after=_total_bab(repo, after_levels),
        saves_before=_total_saves(repo, class_levels, warnings),
        saves_after=_total_saves(repo, after_levels, warnings),
        skill_ranks=ranks,
        # A feat and an ability bump are owed to the character, so they are read off
        # the total level rather than the one the class reached.
        grants_feat=(total_before + 1) in repo.meta.feat_levels,
        grants_ability_increment=(total_before + 1) in repo.meta.ability_increment_levels,
        class_features=_features(repo, taking, class_after, warnings),
        bonus_feat_slots=tuple(slot for slot in summary.bonus_feats if slot.level == class_after),
        favored_class_note=(
            repo.meta.favored_class_note if before is not None and before.is_favored else None
        ),
        spells_per_day=_spells(repo, taking, class_after),
        warnings=tuple(warnings),
    )


def _hp_floor(die: int) -> int:
    """Half the die plus one: the "never roll badly" option, 6 on a d10.

    Integer division deliberately — the corpus rounds down unless it says otherwise,
    and a d6 floors at 4 rather than 4.5.
    """
    return die // 2 + 1 if die else 0


def _die(hit_die: str) -> int:
    """``"d10"`` -> 10. The corpus writes it as a die, not a number."""
    return int(hit_die.lstrip("dD")) if hit_die else 0


def _total_bab(repo: RulesRepository, levels: list[ClassLevelRef]) -> int:
    """Summed across classes, which is what the corpus' multiclass rule says."""
    total = 0
    for entry in levels:
        summary = repo.class_summary(entry.slug)
        if summary is not None:
            total += base_bab(BabProgression(summary.bab_progression), entry.level)
    return total


def _total_saves(
    repo: RulesRepository, levels: list[ClassLevelRef], warnings: list[str]
) -> dict[str, int]:
    """Save totals read off the progression rows, summed across classes.

    Read from the rows rather than recomputed from the formula: the rows are the
    authority, and three prestige classes ship without them.
    """
    totals = {kind.value: 0 for kind in SaveKind}
    for entry in levels:
        try:
            row = repo.class_progression(entry.slug, entry.level)
        except RuleNotFoundError:
            warnings.append(f"{entry.slug}: sin fila de progresión para el nivel {entry.level}")
            continue
        totals[SaveKind.FORTITUDE.value] += row.fort
        totals[SaveKind.REFLEX.value] += row.ref
        totals[SaveKind.WILL.value] += row.will
    return totals


def _features(repo: RulesRepository, slug: str, level: int, warnings: list[str]) -> tuple[str, ...]:
    try:
        row = repo.class_progression(slug, level)
    except RuleNotFoundError:
        warnings.append(f"{slug}: sin fila de progresión para el nivel {level}")
        return ()
    return (row.special,) if row.special else ()


def _spells(repo: RulesRepository, slug: str, level: int) -> str | None:
    try:
        row = repo.class_progression(slug, level)
    except RuleNotFoundError:
        return None
    return str(row.spells_per_day) if row.spells_per_day else None
