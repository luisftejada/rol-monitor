"""English-facing adapter over the vendored Spanish rules loader.

``RulesRepository`` wraps the vendored :class:`Reglas` query layer, exposes
English methods that return catalog DTOs, derives ASCII slugs, and caches the
static lists. The vendored loader is never modified; where it is insufficient the
adapter extends it (see :meth:`feats`). See docs/adr/0002.
"""

from __future__ import annotations

import hashlib
import re
from functools import cached_property
from pathlib import Path
from typing import Any

from pf_tracker.rules.catalog import (
    AbilityDTO,
    ActionTypeDTO,
    AlignmentDTO,
    ArmorDTO,
    BonusTypesDTO,
    ClassProgressionRowDTO,
    ClassSummaryDTO,
    ConditionDTO,
    CriticalDTO,
    FeatDTO,
    FeatEffectDTO,
    FeatModifierDTO,
    FeatSlotDTO,
    FeatSubstitutionDTO,
    ItemSlotDTO,
    MetaDTO,
    RaceDTO,
    SizeDTO,
    SkillDTO,
    SpellDTO,
    WeaponDTO,
)
from pf_tracker.rules.feat_targets import choice_kind_for
from pf_tracker.rules.parsing import parse_bab, parse_critical
from pf_tracker.rules.slug import slugify
from pf_tracker.rules.vendor.pathfinder_reglas import (
    CONJUROS_POR_DEFECTO,
    NUCLEO_POR_DEFECTO,
    Reglas,
    _norm,
)
from pf_tracker.rules.weapon_feats import is_feat_stance


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
        items = self._nucleo["objetos_magicos"]
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
            point_buy_costs={
                int(score): cost
                for score, cost in self._nucleo["caracteristicas"]["coste_compra_puntos"].items()
            },
            feat_levels=list(self._nucleo["avance"]["niveles_con_dote"]),
            feat_types=list(self._nucleo["dotes"]["reglas"]["tipos"]),
            item_slots=[_item_slot(name) for name in items["ranuras_del_cuerpo"]],
            item_categories=list(items["categorias"]),
            item_activations=list(items["activacion"]),
            max_item_enhancement=items["bonificadores_arma"]["max_potenciador"],
        )

    # ------------------------------------------------------------- alignments
    @cached_property
    def alignments(self) -> list[AlignmentDTO]:
        """The nine alignments, in corpus order (``valores`` drives the ordering)."""
        block = self._nucleo["alineamiento"]
        names = block["nombres"]
        return [AlignmentDTO(code=code, name=names[code]) for code in block["valores"]]

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
                bonus_feats=_feat_slots(r),
                weapon_proficiencies=list((r.get("competencias_armas") or {}).get("armas") or []),
                weapon_words=list((r.get("competencias_armas") or {}).get("palabras") or []),
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
            bonus_feats=_feat_slots(data),
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
                    activation=d.get("activacion"),
                    is_stance=False,  # filled below, once the DTO exists
                    choice_kind=choice_kind_for(
                        m["objetivo"]
                        for e in d.get("efectos") or []
                        for m in e.get("modificadores") or []
                    ),
                    effects=[_feat_effect(e) for e in d.get("efectos") or []],
                )
            )
        # `is_stance` is decided from the assembled DTO, since it depends on how the
        # rest of the fields classify the feat.
        return [f.model_copy(update={"is_stance": is_feat_stance(f)}) for f in feats]

    # ------------------------------------------------- restricted feat lists
    @cached_property
    def _restricted_feat_lists(self) -> dict[str, Any]:
        return dict(self._nucleo["dotes"].get("listas_restringidas") or {})

    def restricted_feat_list(self, key: str, level: int, option: str | None = None) -> list[str]:
        """Feat names that may fill a slot restricted to ``key`` at ``level``.

        The corpus states these four lists in four different shapes: a type filter
        plus extras (wizard), levels to feats (monk), style to levels to feats
        (ranger), and bloodline to feats (sorcerer). They are resolved here so the
        frontend never has to walk that structure — it would be rules logic in the
        wrong layer, and the shapes would leak into TypeScript.

        Where the list depends on a choice the sheet does not model yet — the
        ranger's combat style, the sorcerer's bloodline — the union across choices
        is returned. It is wider than the truth, and the caller says so. ``option``
        pins that choice where the slot already makes it: a dragon disciple draws
        from the draconic bloodline by definition, so its list is exact.
        """
        spec = self._restricted_feat_lists.get(key)
        if spec is None:
            return []
        names: set[str] = set()

        wanted_types = {_norm(t) for t in spec.get("tipos") or []}
        if wanted_types:
            names |= {
                d["nombre"]
                for d in self._r.dotes
                if any(_norm(t) in wanted_types for t in d["tipos"])
            }
        names |= set(spec.get("dotes") or [])
        names |= _collect_feat_names(_branch(spec.get("opciones"), option), level)
        return sorted(names)

    def restricted_list_note(self, key: str, option: str | None = None) -> str | None:
        """The corpus' own caveat for a list, if it has one.

        A pinned branch drops the parent's warning about accumulation across levels
        only if the branch states its own; otherwise the parent's still applies.
        """
        spec = self._restricted_feat_lists.get(key)
        if spec is None:
            return None
        branch = _branch(spec.get("opciones"), option)
        if isinstance(branch, dict) and branch.get("nota"):
            note: str = branch["nota"]
            return note
        parent: str | None = spec.get("nota")
        return parent

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

    # --------------------------------------------------------------- lookups
    # Single-entity lookups used by the assembler (service layer). They return None
    # rather than raising so the assembler can attach a warning and carry on.
    def race(self, slug: str) -> RaceDTO | None:
        target = _norm(slug)
        return next((r for r in self.races if _norm(r.slug) == target), None)

    def class_summary(self, slug: str) -> ClassSummaryDTO | None:
        target = _norm(slug)
        return next(
            (c for c in self.classes(include_prestige=True) if _norm(c.slug) == target), None
        )

    def weapon(self, name: str) -> WeaponDTO | None:
        target = _norm(name)
        return next((w for w in self._all_weapons if _norm(w.name) == target), None)

    def armor_item(self, name: str) -> ArmorDTO | None:
        target = _norm(name)
        return next((a for a in self._all_armor if _norm(a.name) == target), None)

    def skill(self, slug: str) -> SkillDTO | None:
        target = _norm(slug)
        return next((s for s in self.skills if _norm(s.slug) == target), None)

    def condition_name(self, slug: str) -> str | None:
        """Canonical Spanish name for a condition slug (or the input if unknown)."""
        target = _norm(slug)
        return next((c.name for c in self.conditions if _norm(c.slug) == target), None)

    def carrying_capacity(self, strength: int) -> tuple[int, int, int]:
        """Return (light_max, medium_max, heavy_max) for a Strength score."""
        table = self._r.carga(strength)
        return int(table["ligera_max"]), int(table["media"][1]), int(table["pesada"][1])

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


def _branch(options: Any, option: str | None) -> Any:
    """One named branch of an ``opciones`` block, or the whole block.

    An option the corpus does not have yields nothing rather than silently falling
    back to the union: a slot pinned to a branch that no longer exists is a corpus
    error, and returning every bloodline would hide it behind a plausible answer.
    """
    if option is None:
        return options
    if not isinstance(options, dict):
        return None
    return options.get(option)


def _collect_feat_names(node: Any, level: int) -> set[str]:
    """Walk an ``opciones`` block, honouring level keys.

    Numeric keys are levels and accumulate: a slot taken at 14 chooses from
    everything unlocked up to it. Anything else is a named choice (a style, a
    bloodline) whose branches are unioned.
    """
    names: set[str] = set()
    if isinstance(node, list):
        names |= {x for x in node if isinstance(x, str)}
    elif isinstance(node, dict):
        for key, value in node.items():
            if key == "concreciones":
                continue  # parameters for a feat, not feats themselves
            # YAML parses `2:` as an int, not a string, so both forms appear.
            is_level = isinstance(key, int) or (isinstance(key, str) and key.isdigit())
            if is_level and int(key) > level:
                continue
            names |= _collect_feat_names(value, level)
    return names


def _feat_slots(raw: dict[str, Any]) -> list[FeatSlotDTO]:
    """Map ``dotes_adicionales`` entries, keeping the corpus vocabulary."""
    return [
        FeatSlotDTO(
            level=s["nivel"],
            choice=s["eleccion"],
            types=list(s.get("tipos") or []),
            list_key=s.get("lista"),
            list_option=s.get("opcion"),
            feat=s.get("dote"),
            note=s.get("nota"),
            page=s.get("fuente"),
        )
        for s in raw.get("dotes_adicionales") or []
    ]


def _feat_effect(raw: dict[str, Any]) -> FeatEffectDTO:
    """Map one ``dotes.lista[].efectos[]`` entry, keeping the corpus vocabulary."""
    return FeatEffectDTO(
        condition=raw.get("condicion"),
        when=dict(raw.get("cuando") or {}),
        modifiers=[
            FeatModifierDTO(target=m["objetivo"], bonus_type=m["tipo"], value=m["valor"])
            for m in raw.get("modificadores") or []
        ],
        substitutions=[
            FeatSubstitutionDTO(target=s["en"], use=s["usar"], instead_of=s["en_lugar_de"])
            for s in raw.get("sustituciones") or []
        ],
        rules=list(raw.get("reglas") or []),
    )


_SLOT_CAPACITY = re.compile(r"^(?P<name>.+?)\s*\(×(?P<capacity>\d+)\)$")


def _item_slot(name: str) -> ItemSlotDTO:
    """Split a body slot's capacity out of its name.

    The corpus writes the only multi-item slot as ``"anillo (×2)"``. Parsing it keeps
    the count where the rules put it instead of in a table here that could drift.
    """
    match = _SLOT_CAPACITY.match(name)
    if match is None:
        return ItemSlotDTO(name=name, slug=slugify(name), capacity=1)
    bare = match.group("name")
    return ItemSlotDTO(name=name, slug=slugify(bare), capacity=int(match.group("capacity")))


def _hash_corpus(directory: Path) -> str:
    """Fingerprint the corpus bytes so cache validators change when data changes."""
    digest = hashlib.sha256()
    for name in (NUCLEO_POR_DEFECTO, CONJUROS_POR_DEFECTO):
        path = directory / name
        if path.exists():
            digest.update(path.read_bytes())
    return digest.hexdigest()[:16]
