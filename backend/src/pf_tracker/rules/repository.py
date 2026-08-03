"""English-facing adapter over the vendored Spanish rules loader.

``RulesRepository`` wraps the vendored :class:`Reglas` query layer, exposes
English methods that return catalog DTOs, derives ASCII slugs, and caches the
static lists. The vendored loader is never modified; where it is insufficient the
adapter extends it (see :meth:`feats`). See docs/adr/0002.
"""

from __future__ import annotations

import hashlib
from functools import cached_property
from pathlib import Path
from typing import Any

from pf_tracker.rules.catalog import (
    AbilityDTO,
    ActionTypeDTO,
    ArmorDTO,
    BonusTypesDTO,
    ClassProgressionRowDTO,
    ClassSummaryDTO,
    ConditionDTO,
    CriticalDTO,
    FeatDTO,
    MetaDTO,
    RaceDTO,
    SizeDTO,
    SkillDTO,
    SpellDTO,
    WeaponDTO,
)
from pf_tracker.rules.parsing import parse_bab, parse_critical
from pf_tracker.rules.slug import slugify
from pf_tracker.rules.vendor.pathfinder_reglas import (
    CONJUROS_POR_DEFECTO,
    NUCLEO_POR_DEFECTO,
    Reglas,
    _norm,
)


class RuleNotFoundError(LookupError):
    """Raised when a requested rules entity does not exist; mapped to HTTP 404."""


class RulesRepository:
    """Cached, English-facing view of the rules corpus."""

    def __init__(self, reglas: Reglas, version: str) -> None:
        self._r = reglas
        self.version = version

    @classmethod
    def from_data_dir(cls, data_dir: str | Path) -> RulesRepository:
        """Load the corpus from ``data_dir`` and fingerprint it for cache headers."""
        directory = Path(data_dir)
        reglas = Reglas.cargar(directory)
        return cls(reglas, version=_hash_corpus(directory))

    @property
    def _nucleo(self) -> dict[str, Any]:
        return self._r.nucleo

    # ------------------------------------------------------------------- meta
    @cached_property
    def meta(self) -> MetaDTO:
        sistema = self._nucleo["sistema"]
        bonus = sistema["tipos_de_bonificador"]
        return MetaDTO(
            bonus_types=BonusTypesDTO(
                always_stack=list(bonus["apilan_siempre"]),
                do_not_stack=list(bonus["no_apilan"]),
                penalties=bonus["penalizadores"],
                note=bonus.get("nota"),
            ),
            abilities=[
                AbilityDTO(name=a["nombre"], abbr=a["abrev"], uses=a["usos"])
                for a in self._nucleo["caracteristicas"]["lista"]
            ],
            sizes=[
                SizeDTO(
                    slug=slugify(s["tamano"]),
                    name=s["tamano"],
                    ac_attack_mod=s["mod_ca_ataque"],
                    cmb_cmd_mod=s["mod_bmc_dmc"],
                    stealth_mod=s["mod_sigilo"],
                    space=str(s["espacio"]),
                    reach=str(s["alcance"]),
                    load_multiplier=float(s["carga"]),
                )
                for s in self._nucleo["tamanos"]
            ],
            action_types=[
                ActionTypeDTO(type=a["tipo"], notes=a.get("notas"))
                for a in self._nucleo["combate"]["tipos_de_accion"]
            ],
            units=dict(sistema["unidades"]),
        )

    # ------------------------------------------------------------------ races
    @cached_property
    def races(self) -> list[RaceDTO]:
        return [
            RaceDTO(
                slug=slugify(r["nombre"]),
                key=r["clave"],
                name=r["nombre"],
                size=r["tamano"],
                speed_ft=r["velocidad_pies"],
                ability_modifiers=dict(r.get("modificadores") or {}),
                type=r["tipo"],
                vision=r.get("vision"),
                traits=list(r.get("rasgos") or []),
                languages={k: list(v) for k, v in (r.get("idiomas") or {}).items()},
            )
            for r in self._nucleo["razas"]
        ]

    # ---------------------------------------------------------------- classes
    def _class_summary(
        self, key: str, data: dict[str, Any], *, is_prestige: bool
    ) -> ClassSummaryDTO:
        return ClassSummaryDTO(
            slug=key,
            name=data["nombre"],
            hit_die=data["dado_golpe"],
            skill_ranks_per_level=data["rangos"],
            bab_progression=data["bab"],
            good_saves=list(data.get("salvaciones_buenas") or []),
            proficiencies=data.get("competencias"),
            class_skills=list(data.get("habilidades_clase") or []),
            is_spellcaster=bool(data.get("lanzador")),
            is_prestige=is_prestige,
            max_level=max((row["nivel"] for row in data["progresion"]), default=0),
        )

    @cached_property
    def _base_classes(self) -> list[ClassSummaryDTO]:
        return [
            self._class_summary(k, v, is_prestige=False) for k, v in self._nucleo["clases"].items()
        ]

    @cached_property
    def _prestige_classes(self) -> list[ClassSummaryDTO]:
        return [
            self._class_summary(k, v, is_prestige=True)
            for k, v in self._nucleo["clases_de_prestigio"].items()
        ]

    def classes(self, *, include_prestige: bool = False) -> list[ClassSummaryDTO]:
        if include_prestige:
            return [*self._base_classes, *self._prestige_classes]
        return list(self._base_classes)

    def class_progression(self, slug: str, level: int) -> ClassProgressionRowDTO:
        try:
            clase = self._r.clase(slug)
        except KeyError as exc:
            raise RuleNotFoundError(f"unknown class: {slug}") from exc
        try:
            row = clase.nivel(level)
        except ValueError as exc:
            raise RuleNotFoundError(f"{slug}: level {level} out of range") from exc
        return ClassProgressionRowDTO(
            level=row["nivel"],
            bab=row["bab"],
            bab_iteratives=parse_bab(row["bab"]),
            fort=row["fort"],
            ref=row["ref"],
            will=row["vol"],
            special=row.get("especial"),
            spells_per_day=row.get("conjuros"),
        )

    # ----------------------------------------------------------------- skills
    @cached_property
    def skills(self) -> list[SkillDTO]:
        return [
            SkillDTO(
                slug=slugify(h["nombre"]),
                name=h["nombre"],
                ability=h["caracteristica"],
                untrained=h["sin_entrenar"],
                armor_check_penalty=h["penalizador_armadura"],
                class_for=list(h.get("clases") or []),
            )
            for h in self._nucleo["habilidades"]["lista"]
        ]

    # ------------------------------------------------------------------ feats
    def feats(
        self,
        *,
        bab: int = 0,
        abilities: dict[str, int] | None = None,
        owned: list[str] | None = None,
        feat_type: str | None = None,
    ) -> list[FeatDTO]:
        """Return every feat annotated with eligibility (never hides ineligible ones).

        Eligibility comes from the vendored ``dotes_disponibles`` (a deliberate
        superset over numeric prerequisites); the GM may override, so ineligible
        feats are flagged, not dropped. ``feat_type`` is a hard filter.
        """
        eligible = self._r.dotes_disponibles(
            bab=bab, caracteristicas=abilities or {}, dotes_poseidas=owned or []
        )
        eligible_names = {_norm(d["nombre"]) for d in eligible}
        wanted_type = _norm(feat_type) if feat_type else None

        feats: list[FeatDTO] = []
        for d in self._r.dotes:
            if wanted_type is not None and not any(_norm(t) == wanted_type for t in d["tipos"]):
                continue
            feats.append(
                FeatDTO(
                    slug=slugify(d["nombre"]),
                    name=d["nombre"],
                    types=list(d["tipos"]),
                    prerequisites=d.get("prerrequisitos"),
                    benefit=d.get("beneficio_resumen"),
                    is_eligible=_norm(d["nombre"]) in eligible_names,
                )
            )
        return feats

    # ---------------------------------------------------------------- weapons
    @cached_property
    def _all_weapons(self) -> list[WeaponDTO]:
        return [
            WeaponDTO(
                slug=slugify(a["nombre"]),
                name=a["nombre"],
                proficiency=a["competencia"],
                category=a["categoria"],
                cost=a.get("coste"),
                damage_small=a.get("danyo_P"),
                damage_medium=a.get("danyo_M"),
                critical=[
                    CriticalDTO(threat_range=c.threat_range, multiplier=c.multiplier)
                    for c in parse_critical(a.get("critico"))
                ],
                range_increment=a.get("alcance"),
                weight=a.get("peso"),
                damage_type=a.get("tipo_danyo"),
                special=a.get("especial"),
            )
            for a in self._r.armas
        ]

    def weapons(
        self,
        *,
        category: str | None = None,
        proficiency: str | None = None,
        search: str | None = None,
    ) -> list[WeaponDTO]:
        result = self._all_weapons
        if category is not None:
            target = _norm(category)
            result = [w for w in result if _norm(w.category) == target]
        if proficiency is not None:
            target = _norm(proficiency)
            result = [w for w in result if _norm(w.proficiency) == target]
        if search is not None:
            needle = _norm(search)
            result = [w for w in result if needle in _norm(w.name)]
        return list(result)

    # ------------------------------------------------------------------ armor
    @cached_property
    def _all_armor(self) -> list[ArmorDTO]:
        return [
            ArmorDTO(
                slug=slugify(a["nombre"]),
                name=a["nombre"],
                category=a["categoria"],
                price_gp=float(a["precio_po"]),
                armor_bonus=a["bonificador_armadura"],
                max_dex=a.get("max_destreza"),
                armor_check_penalty=a["penalizador_armadura"],
                arcane_spell_failure_pct=a["fallo_conjuros_arcanos_pct"],
                speed_30=a.get("velocidad_30"),
                speed_20=a.get("velocidad_20"),
                weight=a.get("peso"),
            )
            for a in self._r.armaduras
        ]

    def armor(self, *, category: str | None = None) -> list[ArmorDTO]:
        result = self._all_armor
        if category is not None:
            target = _norm(category)
            result = [a for a in result if _norm(a.category) == target]
        return list(result)

    # ------------------------------------------------------------- conditions
    @cached_property
    def conditions(self) -> list[ConditionDTO]:
        return [
            ConditionDTO(slug=slugify(e["nombre"]), name=e["nombre"], effect=e["efecto"])
            for e in self._nucleo["estados"]
        ]

    # ----------------------------------------------------------------- spells
    def _spell_dto(self, data: dict[str, Any]) -> SpellDTO:
        return SpellDTO(
            slug=slugify(data["nombre"]),
            name=data["nombre"],
            school=data.get("escuela"),
            levels={k: int(v) for k, v in (data.get("niveles") or {}).items()},
            descriptors=list(data.get("descriptores") or []),
            casting_time=data.get("lanzamiento"),
            components=data.get("componentes"),
            range=data.get("alcance"),
            duration=data.get("duracion"),
            saving_throw=data.get("salvacion"),
            spell_resistance=data.get("rc"),
        )

    def spells(
        self,
        *,
        character_class: str | None = None,
        level: int | None = None,
        search: str | None = None,
    ) -> list[SpellDTO]:
        """Buff-picker view of the spell list; filtering delegates to the loader."""
        if character_class is not None:
            source = self._r.conjuros_de(character_class, level)
        elif search is not None:
            source = self._r.buscar_conjuros(search)
        else:
            source = self._r.conjuros

        result = [self._spell_dto(c.datos) for c in source]

        if character_class is None and level is not None:
            result = [s for s in result if level in s.levels.values()]
        if character_class is not None and search is not None:
            needle = _norm(search)
            result = [s for s in result if needle in _norm(s.name)]
        return result


def _hash_corpus(directory: Path) -> str:
    """Fingerprint the corpus bytes so cache validators change when data changes."""
    digest = hashlib.sha256()
    for name in (NUCLEO_POR_DEFECTO, CONJUROS_POR_DEFECTO):
        path = directory / name
        if path.exists():
            digest.update(path.read_bytes())
    return digest.hexdigest()[:16]
