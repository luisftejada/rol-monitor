"""Translation of the feats corpus target vocabulary into domain modifier targets.

``dotes.esquema_efectos.objetivos`` declares 83 targets; the domain models 17 (plus
the parameterised ``SKILL:`` and ``ABILITY:`` forms). The gap is not an oversight:
most of the rest are spell mechanics, mounted combat, per-class resource pools and
per-maneuver variants, none of which this PC-combat milestone derives.

Every declared target is listed here — mapped or explicitly unmodelled — so a target
added to the corpus fails the contract test instead of being silently dropped. An
unmodelled target is not an error: the caller keeps the effect as an informational
note on the sheet rather than a number, per the brief.
"""

from __future__ import annotations

from collections.abc import Iterable

from pf_tracker.domain.enums import ModifierTarget, skill_target
from pf_tracker.rules.slug import slugify

#: Prefix the corpus uses for per-skill targets: ``prueba_habilidad.Acrobacias``.
SKILL_CHECK_PREFIX = "prueba_habilidad."

#: Prefix for per-ability checks: ``prueba_caracteristica.Constitucion``. The sheet
#: derives no ability-check line, so these are recognised but not modelled — the
#: ``ABILITY:`` domain target is an ability *score*, which is a different thing.
ABILITY_CHECK_PREFIX = "prueba_caracteristica."

#: Placeholders standing for "a skill chosen when the feat is taken" rather than a
#: named one. Resolving them needs the character's ``feat_options``, so they are
#: unmodelled here.
CHOSEN_SKILL_PLACEHOLDERS: frozenset[str] = frozenset({"Artesania_o_Profesion_elegida"})

#: Feat target -> domain target, for everything the derivation engine can apply.
_DIRECT_TARGETS: dict[str, ModifierTarget] = {
    # Attack
    "ataque": ModifierTarget.ALL_ATTACKS,
    "ataque_cuerpo_a_cuerpo": ModifierTarget.ATTACK_MELEE,
    "ataque_a_distancia": ModifierTarget.ATTACK_RANGED,
    # Damage. `dano_arma` is weapon damage generally, so it covers both groups.
    "dano_arma": ModifierTarget.ALL_DAMAGE,
    "dano_cuerpo_a_cuerpo": ModifierTarget.DAMAGE_MELEE,
    "dano_a_distancia": ModifierTarget.DAMAGE_RANGED,
    # Defence and manoeuvres
    "ca": ModifierTarget.AC,
    "dmc": ModifierTarget.CMD,
    "bmc": ModifierTarget.CMB,
    # Saves
    "salvacion_fortaleza": ModifierTarget.SAVE_FORT,
    "salvacion_reflejos": ModifierTarget.SAVE_REF,
    "salvacion_voluntad": ModifierTarget.SAVE_WILL,
    # Tempo and movement
    "iniciativa": ModifierTarget.INITIATIVE,
    "velocidad_base": ModifierTarget.SPEED,
}

#: Declared targets the domain deliberately does not model, grouped as the corpus
#: groups them. Listed exhaustively so the contract test can prove the union of this
#: set and the mapped ones covers every declared target.
UNMODELLED_TARGETS: frozenset[str] = frozenset(
    {
        # Attack variants that depend on a chosen weapon, a wielding, or a mount.
        "ataque_arma_seleccionada",
        "ataque_sin_armas",
        "ataque_escudo",
        "ataque_confirmacion_critico",
        "ataque_mano_principal_dos_armas",
        "ataque_mano_torpe_dos_armas",
        "ataque_a_distancia_montado",
        # Damage variants dispatched per weapon and grip, which derivation computes
        # itself rather than reading from a modifier.
        "dano_arma_seleccionada",
        "dano_una_mano",
        "dano_dos_manos",
        "dano_mano_torpe",
        "dano_escudo",
        "dano_adicional",
        "dano_sangrado_por_asalto",
        "dados_dano_arma",
        "dano_carga_montado",
        # Defences with no derived value on the sheet, and conditional CMD.
        "ocultacion",
        "ocultacion_vs_distancia",
        "puntos_de_golpe",
        "dmc_vs_arrollar",
        "dmc_vs_derribo",
        "dmc_vs_desarme",
        "dmc_vs_embestida",
        "dmc_vs_presa",
        "dmc_vs_romper",
        # Per-manoeuvre CMB; the sheet derives a single CMB.
        "bmc_arrollar",
        "bmc_derribo",
        "bmc_desarme",
        "bmc_embestida",
        "bmc_presa",
        "bmc_romper",
        # Checks that need a choice made when taking the feat.
        "prueba_habilidad_elegida",
        "prueba_caracteristica.<Caracteristica>",
        # Spellcasting: out of scope for this milestone.
        "nivel_conjuro",
        "alcance_conjuro",
        "area_conjuro",
        "duracion_conjuro",
        "efectos_variables_conjuro",
        "prueba_concentracion",
        "prueba_nivel_lanzador_rc",
        "cd_conjuros_escuela_elegida",
        "cd_canalizar",
        "cd_lanzar_a_la_defensiva_enemigo",
        "fallo_conjuro_arcano",
        # Action economy and per-class resource pools.
        "velocidad_carrera",
        "alcance_cuerpo_a_cuerpo",
        "terreno_dificil_ignorado_pies",
        "ataques_de_oportunidad_adicionales",
        "ataques_adicionales_a_distancia",
        "ataques_adicionales_mano_torpe",
        "ataques_adicionales_sin_armas",
        "tiempo_recarga",
        "usos_canalizar_dia",
        "asaltos_furia_dia",
        "usos_imposicion_manos_dia",
        "asaltos_interpretacion_dia",
        "puntos_ki",
        "mercedes_conocidas",
        # Everything else the corpus files under `otros`.
        "rango_amenaza_critico",
        "reduccion_dano_ignorada",
        "penalizador_no_competencia_arma",
        "penalizador_arma_improvisada",
        "penalizador_arma_improvisada_a_distancia",
        "dado_dano_arma_improvisada",
        "penalizador_por_incremento_alcance",
        "dano_mano_torpe_por_fuerza",
        "fuerza_criatura_convocada",
        "constitucion_criatura_convocada",
    }
)

#: The template form as declared; concrete uses carry a skill name after the dot.
SKILL_CHECK_TEMPLATE = f"{SKILL_CHECK_PREFIX}<Habilidad>"


#: Targets that stand for "the X you picked when you took this feat". The editor
#: needs to know which kind of thing to ask for; the derivation needs the answer.
_CHOICE_TARGETS: dict[str, str] = {
    "ataque_arma_seleccionada": "weapon",
    "dano_arma_seleccionada": "weapon",
    "prueba_habilidad_elegida": "skill",
    f"{SKILL_CHECK_PREFIX}Artesania_o_Profesion_elegida": "skill",
    "cd_conjuros_escuela_elegida": "school",
}


def choice_kind_for(targets: Iterable[str]) -> str | None:
    """What a feat asks the player to pick, if anything (``weapon``/``skill``/…)."""
    for target in targets:
        kind = _CHOICE_TARGETS.get(target)
        if kind is not None:
            return kind
    return None


def parse_feat_target(raw: str) -> str | None:
    """Translate a feats-vocabulary target into a domain modifier target.

    Returns ``None`` when the target is real but not modelled here, which is the
    common case and not an error — the effect is still shown, just not summed.
    Per-skill targets become ``SKILL:<slug>``, slugged the same way the skills
    catalog slugs its names, so the two agree.
    """
    if raw.startswith(ABILITY_CHECK_PREFIX):
        return None
    if raw.startswith(SKILL_CHECK_PREFIX):
        name = raw[len(SKILL_CHECK_PREFIX) :]
        if name in CHOSEN_SKILL_PLACEHOLDERS or name.startswith("<"):
            return None
        return skill_target(slugify(name))

    direct = _DIRECT_TARGETS.get(raw)
    return direct.value if direct is not None else None


def is_modelled_target(raw: str) -> bool:
    """Whether ``raw`` resolves to a target the derivation engine sums."""
    return parse_feat_target(raw) is not None


def is_classified_target(raw: str) -> bool:
    """Whether this module accounts for ``raw`` at all, mapped or not.

    Parameterised targets are recognised by prefix, since the corpus declares only
    their template form but uses concrete names.
    """
    return (
        raw in KNOWN_TARGETS
        or raw.startswith(SKILL_CHECK_PREFIX)
        or raw.startswith(ABILITY_CHECK_PREFIX)
    )


#: Every declared target this module accounts for, mapped or not.
KNOWN_TARGETS: frozenset[str] = frozenset(
    set(_DIRECT_TARGETS) | UNMODELLED_TARGETS | {SKILL_CHECK_TEMPLATE}
)
