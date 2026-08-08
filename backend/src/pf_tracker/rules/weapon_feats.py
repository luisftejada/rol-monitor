"""Feats that belong to a weapon rather than to the character.

A global modifier cannot express "+2 damage, but only when this weapon is held in
two hands", so those targets were previously unmodelled. Resolving a feat *against a
specific weapon* makes them tractable: the weapon knows its own grip, its reach, and
whether the character picked it when taking the feat.

Two kinds live here:

``always`` — passive feats tied to a chosen weapon (``Soltura con un arma``,
``Especialización con un arma``). They belong to the weapon's own attack line and
apply whenever that weapon is used.

``optional`` — feats the GM declares per attack (``Ataque poderoso``, ``Puntería
mortal``). They do not change the base line; they describe an alternative one, which
the caller renders alongside it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from pf_tracker.domain.enums import ModifierTarget, SourceKind, Wield
from pf_tracker.domain.modifiers import Modifier
from pf_tracker.rules.catalog import FeatDTO, FeatModifierDTO
from pf_tracker.rules.feat_effects import PASSIVE, FeatContext, effect_holds
from pf_tracker.rules.feat_targets import parse_feat_target
from pf_tracker.rules.feat_vocabulary import is_scalar_feat_bonus, parse_feat_bonus_type

#: Damage targets that only make sense once the grip is known.
_DAMAGE_BY_GRIP: dict[str, Wield] = {
    "dano_una_mano": Wield.ONE_HANDED,
    "dano_dos_manos": Wield.TWO_HANDED,
    "dano_mano_torpe": Wield.OFF_HAND,
}

#: Targets that apply to the weapon the feat was taken for.
_CHOSEN_WEAPON_ATTACK = "ataque_arma_seleccionada"
_CHOSEN_WEAPON_DAMAGE = "dano_arma_seleccionada"

#: Threat range is multiplied, not summed; ``Crítico mejorado`` doubles its width.
THREAT_RANGE_TARGET = "rango_amenaza_critico"

#: The character's combat manoeuvre bonus. It is not a weapon number, yet two feats
#: penalise it as the price of the attack they describe, so a line that charges the
#: attack penalty must charge this one too.
CMB_TARGET = "bmc"

#: Rolls the weapon's damage dice more than once (``Golpe vital`` x2/x3/x4). Only the
#: dice repeat — the flat damage from Strength and the like is added once.
DAMAGE_DICE_TARGET = "dados_dano_arma"

#: Feats whose mechanic the corpus states only in prose, keyed by canonical name the
#: same way ``domain/conditions.py`` keys ``estados``. ``Disparos múltiples`` fires two
#: arrows on the *first* attack of a full attack, which is a dice multiplier that does
#: not apply to the iteratives — there is no modifier in the data to read it from.
_PROSE_DICE_MULTIPLIERS: dict[str, tuple[int, bool]] = {
    # name: (multiplier, first attack only)
    "Disparos múltiples": (2, True),
}

#: Targets that add attacks at the highest bonus, by the kind of weapon they apply
#: to. Adding an attack is not a bonus on a number, which is why these were
#: unmodelled until the line itself could carry them.
_EXTRA_ATTACK_TARGETS: dict[str, str] = {
    "ataques_adicionales_a_distancia": "ranged",
    "ataques_adicionales_sin_armas": "unarmed",
    "ataques_adicionales_mano_torpe": "off_hand",
}

#: Feats that are a way of attacking in their own right, not a modifier on a weapon
#: you carry. ``Ira de la medusa`` is a full-attack routine of unarmed strikes, so it
#: is built as its own line from the weapon it is based on. In Pathfinder you cannot
#: mix armed and unarmed attacks in one full attack, so it never combines with the
#: variants of a carried weapon — it is an alternative to the whole routine.
FEAT_WEAPONS: dict[str, str] = {
    "Ira de la medusa": "Impacto sin armas",
}

#: Activations that resolve as *one* attack rather than a full-attack routine. Vital
#: Strike explicitly forbids using it with a full attack, so a line carrying it keeps
#: only the highest attack bonus.
SINGLE_ATTACK_ACTIVATIONS: frozenset[str] = frozenset({"accion_de_ataque", "estandar"})

#: Feats that replace a weaker one outright: taking the higher one leaves the lower
#: with no effect at all, so the lower is dropped rather than merely not stacked.
#:
#: Keyed by the superseding feat. The corpus states this in prose ("Sustituye al
#: efecto de Golpe vital; no se apila con él"), which is why the table is explicit —
#: but a contract test checks every entry against that prose, so it cannot drift.
#: Prerequisites alone are not the signal: ``Combate con dos armas mejorado`` also
#: requires its base feat, yet adds to it rather than replacing it.
SUPERSEDED_FEATS: dict[str, frozenset[str]] = {
    "Golpe vital mejorado": frozenset({"Golpe vital"}),
    "Golpe vital mayor": frozenset({"Golpe vital", "Golpe vital mejorado"}),
    "Golpe perforante mayor": frozenset({"Golpe perforante"}),
}


def is_optional(feat: FeatDTO) -> bool:
    """Whether the feat describes an alternative attack rather than the base one."""
    return feat.activation != PASSIVE


#: Target families that land on a weapon's own line. A feat touching any of them is
#: rendered as an attack variant, so it must never also be offered as a stance.
_WEAPON_SLOT_PREFIXES = ("ataque", "dano", "dados_dano")


def is_global_feat_target(target: str) -> bool:
    """Whether a target belongs to the character rather than to a weapon's line.

    ``Pericia en combate`` penalises melee attacks *and* raises AC. The first half
    only means something per weapon, the second only makes sense for the character,
    so the two are rendered in different places and neither is applied twice.
    """
    if target.startswith(_WEAPON_SLOT_PREFIXES):
        return False
    return parse_feat_target(target) is not None


#: Effects that keep running on the *target* once triggered, round after round.
#: There is no opponent sheet to hold them yet, so they are offered as a toggle: the
#: GM records that it is in play and the tracker keeps showing what to apply.
ONGOING_TARGET_EFFECTS: frozenset[str] = frozenset({"dano_sangrado_por_asalto"})


def has_ongoing_target_effect(feat: FeatDTO) -> bool:
    """Whether the feat leaves something running on the opponent each round."""
    return any(
        modifier.target in ONGOING_TARGET_EFFECTS
        for effect in feat.effects
        for modifier in effect.modifiers
    )


def is_feat_stance(feat: FeatDTO) -> bool:
    """Whether a feat is a round-long choice the GM switches on.

    ``Acometer`` costs 2 AC to gain reach; ``Pericia en combate`` buys AC with an
    attack penalty. Both are declared, and both have an effect on the character that
    no weapon line can carry — that is what makes them belong beside charging and
    fighting defensively. They are offered only to characters who have them.

    Weapon-scoped feats are excluded even when they also touch a global value: their
    line already represents the choice, and a second toggle for the same feat would
    read as a separate decision. The exception is a feat that leaves an effect
    running on the opponent — ``Crítico sangrante`` bleeds 2d6 a round — which the GM
    must keep applying, and which no line can track.
    """
    if not is_optional(feat) or feat.name in FEAT_WEAPONS:
        return False
    # Something the GM must keep applying each round is worth toggling even though it
    # changes none of your numbers: the toggle is the reminder.
    if has_ongoing_target_effect(feat):
        return True
    if is_weapon_scoped(feat):
        return False
    return any(
        is_global_feat_target(modifier.target)
        for effect in feat.effects
        for modifier in effect.modifiers
    )


#: Feats that fire when a critical is confirmed. They apply a condition to the
#: *target*, so there is no number of yours to change — until the NPC module exists
#: they are annotations on the line, shown exactly when the GM confirms a crit.
CRITICAL_TRIGGER = "al_confirmar_critico"

#: Lifts the "one critical feat per critical hit" limit the corpus states.
CRITICAL_MASTERY = "Maestría con los críticos"


def critical_notes(feats: Sequence[FeatDTO]) -> tuple[str, ...]:
    """Annotations for the critical feats a character holds.

    The exclusivity rule is taken verbatim from the corpus rather than reworded, and
    only shown when it bites: more than one critical feat and no mastery to lift it.
    """
    triggered = [feat for feat in feats if feat.activation == CRITICAL_TRIGGER]
    if not triggered:
        return ()

    notes = [f"{feat.name}: {_critical_text(feat)}" for feat in triggered]
    if len(triggered) > 1 and not any(feat.name == CRITICAL_MASTERY for feat in feats):
        limit = next(
            (
                rule
                for feat in triggered
                for effect in feat.effects
                for rule in effect.rules
                if "una dote de crítico" in rule
            ),
            None,
        )
        if limit:
            notes.append(limit)
    return tuple(notes)


def _critical_text(feat: FeatDTO) -> str:
    """The feat's own summary, falling back to its rules when the corpus has none."""
    if feat.benefit:
        return feat.benefit
    return " ".join(rule for effect in feat.effects for rule in effect.rules)


def is_single_attack(feat: FeatDTO) -> bool:
    """Whether using this feat means one attack instead of a full routine."""
    return (feat.activation or "") in SINGLE_ATTACK_ACTIVATIONS


def drop_superseded(feats: Sequence[FeatDTO]) -> list[FeatDTO]:
    """Remove feats made redundant by a higher one the character also has.

    With all three Vital Strikes, only ``Golpe vital mayor`` remains: the others are
    not merely non-stacking, they have no effect at all. Their prerequisites force a
    character to hold all three, so this is the normal case, not a corner one.
    """
    held = {feat.name for feat in feats}
    superseded: set[str] = set()
    for name in held:
        superseded |= SUPERSEDED_FEATS.get(name, frozenset())
    return [feat for feat in feats if feat.name not in superseded]


@dataclass(frozen=True, slots=True)
class WeaponProfile:
    """What a feat needs to know about the weapon it is being resolved against."""

    name: str
    wield: Wield
    is_ranged: bool
    is_unarmed: bool = False


@dataclass(frozen=True, slots=True)
class WeaponFeatEffects:
    """Per-weapon contributions of one or more feats."""

    attack: tuple[Modifier, ...] = ()
    damage: tuple[Modifier, ...] = ()
    #: Penalty this line's feats put on the character's CMB (``Ataque poderoso``).
    #: It belongs to the character, not to the weapon, but it is only paid when this
    #: line is the one being used — so the line carries it.
    cmb: tuple[Modifier, ...] = ()
    #: Multiplier applied to the weapon's threat-range *width* (1 = unchanged).
    threat_range_factor: int = 1
    #: How many times the damage dice are rolled (1 = unchanged).
    damage_dice_multiplier: int = 1
    #: Whether that multiplier is limited to the first attack of a full attack.
    dice_multiplier_first_attack_only: bool = False
    #: Attacks added at the highest bonus (Rapid Shot, Medusa's Wrath).
    extra_attacks_at_full_bab: int = 0
    #: When the effect only applies in a situation the sheet cannot check, the text
    #: that says so, for the caller to label the line with.
    condition: str | None = None
    #: Prose the caller shows on the weapon line; not expressible as a number.
    notes: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WeaponFeatContext(FeatContext):
    """Character facts plus the weapon each feat was taken for."""

    #: ``feat name -> weapon name``, from the character's ``feat_options``.
    feat_options: Mapping[str, str] = field(default_factory=dict)

    def chosen_weapon(self, feat_name: str) -> str | None:
        return self.feat_options.get(feat_name)


def is_weapon_scoped(feat: FeatDTO) -> bool:
    """Whether any of this feat's modifiers only mean something for a weapon."""
    if feat.name in _PROSE_DICE_MULTIPLIERS:
        return True
    return any(
        modifier.target in _DAMAGE_BY_GRIP
        or modifier.target in {_CHOSEN_WEAPON_ATTACK, _CHOSEN_WEAPON_DAMAGE}
        or modifier.target in {THREAT_RANGE_TARGET, DAMAGE_DICE_TARGET}
        or modifier.target in _EXTRA_ATTACK_TARGETS
        for effect in feat.effects
        for modifier in effect.modifiers
    )


def resolve_for_weapon(
    feat: FeatDTO, weapon: WeaponProfile, context: WeaponFeatContext
) -> WeaponFeatEffects:
    """Resolve one feat against one weapon, ignoring its activation.

    Activation is the caller's concern: a passive feat's result belongs on the base
    line, a declared one's describes a variant of it.
    """
    if _targets_a_different_weapon(feat, weapon, context):
        return WeaponFeatEffects()

    attack: list[Modifier] = []
    damage: list[Modifier] = []
    cmb: list[Modifier] = []
    factor = 1
    extra_attacks = 0
    condition: str | None = None
    dice_factor, first_only = _PROSE_DICE_MULTIPLIERS.get(feat.name, (1, False))

    # A feat the GM can also switch on as a stance already charges its CMB penalty
    # there (``Pericia en combate``), so taking it here as well would charge it
    # twice. Only the feats the stance path never sees — the weapon-scoped ones,
    # ``Ataque poderoso`` above all — put their CMB penalty on the line.
    carries_cmb = not is_feat_stance(feat)

    for effect in feat.effects:
        # A situational effect is still shown for a weapon line: the GM can see the
        # numbers and judge whether the situation holds, which a global modifier
        # could not offer without silently applying itself.
        situational = not effect_holds(effect, context)
        if situational and not (effect.condition and effect.modifiers):
            continue
        for raw in effect.modifiers:
            extra = _EXTRA_ATTACK_TARGETS.get(raw.target)
            if extra is not None:
                if _accepts_extra_attacks(extra, weapon) and isinstance(raw.value, int):
                    extra_attacks += raw.value
                    if situational:
                        condition = effect.condition
                continue
            if raw.target == THREAT_RANGE_TARGET:
                factor *= _multiplier(raw.value)
                continue
            if raw.target == DAMAGE_DICE_TARGET:
                dice_factor *= _multiplier(raw.value)
                continue
            if situational:
                continue
            if raw.target == CMB_TARGET:
                if carries_cmb:
                    modifier = _modifier_for(feat, ModifierTarget.CMB.value, raw)
                    if modifier is not None:
                        cmb.append(modifier)
                continue
            slot = _slot_for(raw.target, weapon)
            if slot is None:
                continue
            modifier = _modifier_for(feat, slot, raw)
            if modifier is None:
                continue
            (attack if slot.startswith("ATTACK") else damage).append(modifier)

    return WeaponFeatEffects(
        attack=tuple(attack),
        damage=tuple(damage),
        cmb=tuple(cmb),
        threat_range_factor=factor,
        damage_dice_multiplier=dice_factor,
        dice_multiplier_first_attack_only=first_only,
        extra_attacks_at_full_bab=extra_attacks,
        condition=condition,
        notes=_prose_notes(feat),
    )


def _modifier_for(feat: FeatDTO, target: str, raw: FeatModifierDTO) -> Modifier | None:
    """Turn one corpus modifier into a domain one, or ``None`` if it is not a scalar.

    The corpus states some bonuses as prose or as a multiplier; those are handled by
    their own targets, so anything left that is not a plain integer is skipped rather
    than guessed at.
    """
    if not isinstance(raw.value, int) or not is_scalar_feat_bonus(raw.bonus_type):
        return None
    return Modifier(
        target=target,
        value=raw.value,
        bonus_type=parse_feat_bonus_type(raw.bonus_type),
        source=feat.name,
        source_kind=SourceKind.FEAT,
    )


def _accepts_extra_attacks(kind: str, weapon: WeaponProfile) -> bool:
    """Whether extra attacks of ``kind`` belong on this weapon's line."""
    if kind == "ranged":
        return weapon.is_ranged
    if kind == "unarmed":
        return weapon.is_unarmed
    return weapon.wield is Wield.OFF_HAND


def _targets_a_different_weapon(
    feat: FeatDTO, weapon: WeaponProfile, context: WeaponFeatContext
) -> bool:
    """A feat taken for a named weapon does nothing with any other one."""
    if not _names_a_chosen_weapon(feat):
        return False
    chosen = context.chosen_weapon(feat.name)
    return chosen is None or chosen != weapon.name


def _names_a_chosen_weapon(feat: FeatDTO) -> bool:
    return any(
        modifier.target in {_CHOSEN_WEAPON_ATTACK, _CHOSEN_WEAPON_DAMAGE}
        for effect in feat.effects
        for modifier in effect.modifiers
    )


def _slot_for(target: str, weapon: WeaponProfile) -> str | None:
    """Which of the weapon's two modifier slots ``target`` belongs in, if any."""
    if target == _CHOSEN_WEAPON_ATTACK:
        return _attack_slot(weapon)
    if target == _CHOSEN_WEAPON_DAMAGE:
        return _damage_slot(weapon)

    grip = _DAMAGE_BY_GRIP.get(target)
    if grip is not None:
        # Grip-based damage is a melee concept (Power Attack). A longbow is held in
        # two hands too, so matching on grip alone would hand an archer +6 damage.
        if weapon.is_ranged or weapon.wield is not grip:
            return None
        return _damage_slot(weapon)

    if target in {"ataque_cuerpo_a_cuerpo", "ataque_a_distancia", "ataque"}:
        wanted_ranged = target == "ataque_a_distancia"
        if target != "ataque" and wanted_ranged is not weapon.is_ranged:
            return None
        return _attack_slot(weapon)
    if target in {"dano_cuerpo_a_cuerpo", "dano_a_distancia", "dano_arma"}:
        wanted_ranged = target == "dano_a_distancia"
        if target != "dano_arma" and wanted_ranged is not weapon.is_ranged:
            return None
        return _damage_slot(weapon)
    return None


def _attack_slot(weapon: WeaponProfile) -> str:
    target = ModifierTarget.ATTACK_RANGED if weapon.is_ranged else ModifierTarget.ATTACK_MELEE
    return target.value


def _damage_slot(weapon: WeaponProfile) -> str:
    target = ModifierTarget.DAMAGE_RANGED if weapon.is_ranged else ModifierTarget.DAMAGE_MELEE
    return target.value


def _multiplier(value: object) -> int:
    """Parse the corpus' ``"x2"`` multiplier notation."""
    if isinstance(value, str) and value.startswith("x") and value[1:].isdigit():
        return int(value[1:])
    return 1


def _prose_notes(feat: FeatDTO) -> tuple[str, ...]:
    """Rules text for effects that carry no number, shown on the weapon line."""
    if any(effect.modifiers for effect in feat.effects):
        return ()
    return tuple(rule for effect in feat.effects for rule in effect.rules)


def widen_threat_range(threat_range: int, factor: int) -> int:
    """Double (or triple) the *width* of a threat range: 19-20 -> 17-20.

    A 20-only weapon threatens on 1 face, so doubling gives 19-20; 18-20 is 3 faces
    and gives 15-20. The range never extends below 2, which can never miss anyway.
    """
    if factor <= 1:
        return threat_range
    width = 21 - threat_range
    return max(2, 21 - width * factor)
