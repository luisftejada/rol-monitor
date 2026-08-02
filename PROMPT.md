0. Role and mission

You are the lead engineer on a greenfield web application. Build a combat assistant for a Pathfinder 1st Edition tabletop game, whose single most important job is to track, explain, and audit the bonuses that apply to a character during combat.

The game master must be able to answer, in under three seconds and without opening a rulebook: "What is this character's AC right now, and exactly which bonuses make it up?"

This first milestone delivers the PC module (player characters) only. The NPC module is out of scope but the architecture must not make it painful later.

Hard constraints
All code artifacts in English: identifiers, comments, docstrings, commit messages, README, API paths, test names, error messages, log messages, documentation.
Domain data stays in Spanish: the rules corpus is Spanish (Espada larga, Fortaleza, Cota de mallas). Do not translate it. Treat Spanish strings as opaque canonical identifiers coming from the data files, and derive ASCII slugs from them for URLs and keys.
The UI is displayed in Spanish to the end user (it is a Spanish-language game table). Route all user-facing strings through an i18n layer (es as the only locale for now) rather than hardcoding them in components.
Python 3.14, dependency management with Poetry.
Unit tests are mandatory on both backend and frontend. Code without tests is not done.
1. Provided assets

Three files will be placed in data/ (backend) — vendored, read-only, never edited:

pathfinder_nucleo.yaml (~176 KB)

Top-level keys and the shapes you will actually consume:

Key	Shape	Notes
sistema	dict	tipos_de_bonificador → apilan_siempre (3 entries), no_apilan (15 entries), penalizadores (text). Also 20_natural, 1_natural, redondeo, multiplicadores, unidades, terminos_clave. This is the source of the stacking rules.
caracteristicas	dict	lista (6 × {nombre, abrev, usos}), modificador formula, coste_compra_puntos (point-buy table, score → cost), incrementos_por_nivel
tamanos	list (9)	{tamano, mod_ca_ataque, mod_bmc_dmc, mod_sigilo, espacio, alcance, carga} — note AC/attack and CMB/CMD size modifiers are different and inverse
avance	dict	px_por_nivel, niveles_con_dote, niveles_con_incremento_de_caracteristica, bab_por_tipo, salvacion_por_tipo, ataques_adicionales, multiclase
razas	list (7)	{nombre, clave, tamano, velocidad_pies, modificadores: {Des: 2, ...}, tipo, vision, rasgos[], idiomas}
clases	dict (11)	keyed by slug (guerrero, mago, …). Each: {nombre, dado_golpe: "d10", rangos: 2, bab: "completo", salvaciones_buenas: ["Fortaleza"], competencias, lanzador, habilidades_clase[], progresion[20]}; each progresion row is {nivel, bab: "+11/+6/+1", fort, ref, vol, especial}
clases_de_prestigio	dict (10)	same shape, 10 levels
habilidades	dict	reglas (ranks/level, max ranks, class bonus, ACP) + lista (35 × {nombre, caracteristica: "Des", sin_entrenar: bool, penalizador_armadura: bool, clases[]})
dotes	dict	reglas + lista (174 × {nombre, tipos[], prerrequisitos: str|null, beneficio_resumen}) — prerequisites are free text, parse leniently
equipo	dict	armas (87 × {nombre, competencia, categoria, coste, danyo_P, danyo_M, critico: "19–20/×2", alcance, peso, tipo_danyo, especial}), armaduras_y_escudos (18 × {nombre, categoria: ligera|intermedia|pesada|escudo, precio_po, bonificador_armadura, max_destreza, penalizador_armadura, fallo_conjuros_arcanos_pct, velocidad_30, velocidad_20, peso}), materiales_especiales, capacidad_de_carga
combate	dict	iniciativa, clase_de_armadura (formulas for full/touch/flat-footed), ataque, tipos_de_accion, acciones_comunes (charge, withdraw, total defense, fighting defensively, two-weapon fighting penalties), ataques_de_oportunidad, maniobras (CMB/CMD formulas + list), modificadores_de_combate, heridas_y_muerte, movimiento
magia	dict	cd_salvacion, concentracion, componentes, escuelas, …
estados	list (34)	{nombre, efecto} — conditions such as Apresado, Asustado, Aterrado, Cegado
objetos_magicos	dict	bonificadores_arma, bonificadores_armadura, ranuras_del_cuerpo
pathfinder_conjuros.yaml (~202 KB)

{meta, conjuros: [...]}. Each spell has at least nombre, escuela, niveles: {clase: nivel}, plus descriptive fields. Only needed in this milestone for buff spells applied as timed combat modifiers — do not build a spellcasting subsystem.

pathfinder_reglas.py (~330 lines)

An existing Spanish-API loader/query layer: Reglas.cargar(), .clase(), .bab(), .pg_medios(), .habilidades_de_clase(), .bonif_habilidad(), .dotes_disponibles(), .arma(), .carga(), .estado(), .raza(), .conjuros_de(), etc.

Vendor it unmodified at backend/src/pf_tracker/rules/vendor/pathfinder_reglas.py and wrap it in an English-facing adapter rules/repository.py exposing RulesRepository. Rationale: the file is a known-good asset; wrapping keeps the English-code constraint without forking upstream. Where the vendored helper is insufficient (e.g. dotes_disponibles explicitly returns a superset), extend in the adapter, do not patch the vendored file.

2. Scope
In scope

Full CRUD for player characters, holding only what a combat round needs, plus a live combat sheet with a complete, auditable bonus breakdown.

Out of scope (build the seams, not the features)
NPC/monster module — but model characters so an NPC variant can reuse the derivation engine (see §5).
Encounter/initiative tracker across multiple combatants — keep the domain free of assumptions that block it.
Spell slot management, character advancement/XP, inventory economy, wealth, crafting, multi-user auth.
3. Technology stack

Backend

Python 3.14, Poetry (package-mode = true, src/ layout)
FastAPI + Uvicorn
Pydantic v2 for schemas; SQLAlchemy 2.0 (typed, Mapped[...]) + Alembic; SQLite (aiosqlite), Postgres-compatible types
pytest, pytest-asyncio, pytest-cov, httpx.ASGITransport, hypothesis
ruff (lint + format), mypy --strict, pre-commit

Frontend

React 18 + TypeScript (strict) + Vite
TanStack Query for server state; React Hook Form + Zod for forms; Zustand only if a genuine cross-page store appears
Tailwind CSS; headless accessible primitives (Radix or equivalent) — combobox behaviour must be keyboard-complete
vitest + React Testing Library + @testing-library/user-event + MSW for network mocking
TypeScript API types generated from the OpenAPI schema (openapi-typescript), never hand-written

Prefer the boring option. If you are about to add a dependency not listed here, justify it in one line in the commit message or don't add it.

4. Repository layout
.
├── CLAUDE.md
├── README.md
├── Makefile
├── docker-compose.yml
├── .pre-commit-config.yaml
├── backend/
│   ├── pyproject.toml
│   ├── data/                       # vendored YAML corpus (read-only)
│   ├── alembic/
│   ├── src/pf_tracker/
│   │   ├── main.py                 # app factory, lifespan, DI wiring
│   │   ├── config.py               # pydantic-settings
│   │   ├── api/v1/                 # routers: characters, rules, derive, health
│   │   ├── domain/                 # PURE: no FastAPI, no SQLAlchemy, no I/O
│   │   │   ├── enums.py            # BonusType, DamageType, Ability, SaveKind, Size…
│   │   │   ├── models.py           # frozen dataclasses / pydantic models
│   │   │   ├── modifiers.py        # ★ stacking engine
│   │   │   ├── derivation.py       # ★ AC, attacks, saves, skills, CMB/CMD…
│   │   │   └── conditions.py       # `estados` → modifier sets
│   │   ├── rules/
│   │   │   ├── vendor/pathfinder_reglas.py
│   │   │   ├── repository.py       # English adapter + slugs + caching
│   │   │   └── catalog.py          # DTOs for UI pickers
│   │   ├── persistence/            # ORM models, repositories, session
│   │   ├── schemas/                # request/response DTOs
│   │   └── services/               # use cases orchestrating domain + persistence
│   └── tests/{unit,integration,fixtures}/
└── frontend/
    ├── package.json
    ├── src/{api,components,features,hooks,pages,i18n,test}/
    └── vitest.config.ts

Layering rule, enforced by an import-linter test: domain imports nothing from api, persistence, rules, or FastAPI. It is pure functions over frozen data. That is what makes it exhaustively testable.

5. Domain model
Character (persisted aggregate)
Identity: id (UUID), name, player_name?, race (slug), alignment?, size (defaults from race, overridable), speed_ft (defaults from race), notes?, portrait_url?, created_at, updated_at
Classes: class_levels: list[ClassLevel] where ClassLevel = {class_slug, level, is_prestige, is_favored} — multiclass from day one; total level is derived
Abilities: base_scores: dict[Ability, int] (the raw rolled/bought value, before racial modifiers), plus ability_damage: dict[Ability, int] and temporary_ability_modifiers handled as modifiers, not as edits to the base score
Hit points: max_hp, current_hp, temporary_hp, nonlethal_damage, hp_roll_mode (manual | average | max_first_then_average)
Skills: skill_ranks: dict[str, int] + skill_misc_modifiers: dict[str, int] — store only skills with a non-zero value
Feats: feats: list[str] (canonical Spanish names) + feat_options: dict[str, str] for feats that take a parameter (Soltura con un arma → Espada larga)
Equipment:
armor?: EquippedArmor = {catalog_name, enhancement_bonus, is_masterwork, material?, custom_overrides?}
shield?: EquippedArmor
weapons: list[EquippedWeapon] = {id, catalog_name, enhancement_bonus, is_masterwork, material?, wielding: one_handed | two_handed | off_hand | natural, size_category, ammo?, notes?, custom_overrides?}
natural_armor_bonus, deflection_bonus, other_ac_modifiers
load_carried_lb? (for encumbrance)
Combat state: active_conditions: list[str] (from estados), active_effects: list[ActiveEffect], initiative_misc, is_flat_footed, dexterity_denied
Extensibility seam: kind: Literal["pc", "npc"] = "pc" with a discriminator column, so the NPC module reuses persistence and derivation.
Modifier — the heart of the application
python
@dataclass(frozen=True, slots=True)
class Modifier:
    target: ModifierTarget      # AC, AC_TOUCH, ATTACK_MELEE, DAMAGE_MELEE, SAVE_FORT,
                                # SKILL:Acrobacias, INITIATIVE, CMB, CMD, SPEED, ALL_SAVES…
    value: int
    bonus_type: BonusType | None      # None == untyped
    source: str                       # "Cota de mallas", "Ataque poderoso", "Bendecir", "Ira"
    source_kind: SourceKind           # ARMOR, FEAT, RACE, CLASS, SPELL, ITEM, CONDITION,
                                      # STANCE, MANUAL
    condition: str | None = None      # free-text applicability note, e.g. "vs. miedo"
    is_active: bool = True
    expires_in_rounds: int | None = None

BonusType is an enum whose members map 1:1 to the Spanish strings in sistema.tipos_de_bonificador (ALCHEMICAL→alquimia, ARMOR→armadura, NATURAL_ARMOR→armadura natural, COMPETENCE→competencia, SHIELD→escudo, INHERENT→inherente, INSIGHT→introspección, MORALE→moral, ENHANCEMENT→potenciador, PROFANE→profano, RACIAL→racial, RESISTANCE→resistencia, SACRED→sagrado, LUCK→suerte, SIZE→tamaño, plus the always-stacking DODGE→esquiva, CIRCUMSTANCE→circunstancia, and untyped). Load the classification from the YAML at startup and assert the enum covers it — a test must fail if the data file gains a bonus type the code doesn't know.

ModifierEngine (domain/modifiers.py)
python
def resolve(target: ModifierTarget, modifiers: Sequence[Modifier]) -> ResolvedValue

Returns {total: int, applied: list[Modifier], suppressed: list[tuple[Modifier, str]]}.

Rules, taken from sistema.tipos_de_bonificador:

Filter to active modifiers whose target matches (including group targets such as ALL_SAVES).
Split positives and negatives. Penalties always stack, except duplicates of the same named effect — dedupe negatives by (source, target).
Untyped, DODGE, and CIRCUMSTANCE bonuses stack with everything, including with themselves.
Every other bonus type: only the largest of that type applies; the rest are returned in suppressed with a human-readable reason. Suppressed modifiers must be surfaced to the UI — a GM needs to see that the bendecir is doing nothing because the weapon's enhancement bonus is bigger.
Never mutate inputs; the function is pure and deterministic.
derivation.py — required outputs

Every one of these returns a value plus its breakdown:

ability_modifier(score) = (score - 10) // 2 (floor division, negative-safe)
Final ability scores = base + racial (razas[].modificadores) + level increments + modifiers
AC: 10 + armor + shield + min(dex_mod, armor_max_dex) + size(mod_ca_ataque) + natural + dodge + deflection + other
Touch AC: excludes armor, shield, natural armor
Flat-footed AC: excludes Dex and dodge
Max-Dex cap comes from the more restrictive of armor and shield; report the cap in the breakdown when it actually binds
Initiative: dex_mod + modifiers (Iniciativa mejorada = +4)
BAB: sum across class_levels using each class's progresion[level].bab; parse the "+11/+6/+1" string into a list. For multiclass, sum the first value of each class and regenerate the iterative sequence per avance.ataques_adicionales (extra attack per full +5 above +1, max 4)
Full attack routine per weapon: for each iteration, 1d20 + BAB_iter + str_or_dex_mod + size + enhancement + feat/stance modifiers, rendered as +13/+8/+3
Melee uses Str; ranged uses Dex; two-handed melee damage uses Str × 1.5; off-hand damage uses Str × 0.5; thrown weapons use Dex to hit, Str to damage
Two-weapon fighting: -6/-6, -4/-4 with a light off-hand, -2/-2 with Combate con dos armas; Combate con dos armas mejorado/mayor add extra off-hand iterations at -5/-10
Report damage_expression (1d8+7), critical (parse "19–20/×2" → threat_range=19, multiplier=2), damage_types, range_increment
Non-proficiency penalty (-4) when the weapon's competencia is not covered by class/race/feat proficiencies
Saves: for each of Fortaleza/Reflejos/Voluntad, sum(class base at its level) + ability_mod + modifiers
CMB = BAB + Str + tamanos[].mod_bmc_dmc; CMD = 10 + BAB + Str + Dex + mod_bmc_dmc (note the different size column from AC)
Skills: ranks + ability_mod + racial + (3 if class skill and ranks ≥ 1) + ACP (if flagged, already negative) + modifiers; flag untrained-use violations as warnings, not errors
Armor check penalty: armor + shield, applied only to flagged skills
Arcane spell failure: armor + shield percentages, summed
Speed: from velocidad_30/velocidad_20 columns by armor category and base speed, then encumbrance from equipo.capacidad_de_carga (×4 capacity per +10 Str, per the vendored carga())
Carrying capacity: light/medium/heavy thresholds
Stances as toggles (each emits modifiers, none mutates the character): Cargar (+2 attack, −2 AC), Luchar a la defensiva (−4 attack, +2 dodge AC), Defensa total (+4 dodge AC, no attacks), Ataque poderoso (−1 attack / +2 damage, scaling per +4 BAB; ×1.5 damage two-handed), Pericia en combate (−1 attack / +1 dodge AC, scaling per +4 BAB), Flanqueo (+2 attack), Superioridad de altura (+1)
Conditions: map each of the 34 estados to a modifier set where mechanically expressible (Asustado → −2 to attacks, saves and checks; Aterrado → −2 AC and loses Dex); where the effect is not numeric, still attach it as an informational flag on the sheet

Rounding rule: the corpus specifies round-down everywhere unless stated. Implement one shared helper; do not scatter int()/// across the codebase.

6. API surface (/api/v1)

Rules catalog — read-only, cacheable, ETaged (the UI is built on these; make them fast and complete):

GET  /rules/meta                     # bonus types, sizes, abilities, action types, units
GET  /rules/races
GET  /rules/classes                  # + ?include_prestige=true
GET  /rules/classes/{slug}/progression/{level}
GET  /rules/skills
GET  /rules/feats                    # ?bab=&abilities=&owned=&type=  → eligibility-filtered
GET  /rules/weapons                  # ?category=&proficiency=&search=
GET  /rules/armor                    # ?category=
GET  /rules/conditions
GET  /rules/spells                   # ?class=&level=&search=  (buff picker only)

Characters:

GET    /characters                   # list, paginated, searchable
POST   /characters
GET    /characters/{id}
PUT    /characters/{id}
PATCH  /characters/{id}              # partial, for fast inline edits
DELETE /characters/{id}              # soft delete
POST   /characters/{id}/duplicate
GET    /characters/{id}/combat-sheet # ★ full derived sheet + breakdowns
POST   /characters/{id}/modifiers    # add an ad-hoc / spell / item modifier
DELETE /characters/{id}/modifiers/{modifier_id}
PATCH  /characters/{id}/modifiers/{modifier_id}   # toggle active, edit duration
POST   /characters/{id}/conditions   # apply/remove `estado`
POST   /characters/{id}/tick         # advance N rounds, expire timed effects
GET    /characters/{id}/export       # portable JSON
POST   /characters/import

Stateless derivation (powers the live preview during creation):

POST   /derive                       # body = draft character, returns combat sheet; no persistence

CombatSheet response shape — every numeric field is an object, never a bare int:

json
{
  "ac": { "total": 21, "breakdown": [
      {"label": "Base", "value": 10, "type": null, "source": "base"},
      {"label": "Cota de mallas", "value": 6, "type": "armadura", "source": "armor"},
      {"label": "Escudo pesado de acero", "value": 2, "type": "escudo", "source": "shield"},
      {"label": "Destreza (limitada por armadura, máx. +2)", "value": 2, "type": null, "source": "ability"},
      {"label": "Esquiva", "value": 1, "type": "esquiva", "source": "feat"}
    ],
    "suppressed": [
      {"label": "Escudo de fe", "value": 1, "type": "deflexión", "reason": "superado por Anillo de protección +2"}
    ]
  }
}

Also: POST /derive and GET /combat-sheet must return a warnings: list[str] array for rules-faithful problems that should not block saving (over-max skill ranks, missing feat prerequisites, non-proficiency, encumbrance beyond heavy load).

7. UI — optimised for speed of entry

This is the requirement most likely to be under-served. The goal is that a GM can enter a level-7 multiclass character in under two minutes, and that nothing in the flow ever blocks on a modal.

Layout: two panes. Left = the form. Right = a live combat card, always visible, always current, recomputed via debounced POST /derive (250 ms). Every number on the card is clickable and expands its bonus breakdown inline.

Creation flow — a single scrollable page with anchored sections, not a locking wizard. Sections: Identidad → Características → Clases y nivel → Habilidades → Dotes → Equipo → Revisión. Any section can be filled in any order; the card fills in as you go.

Autofill everywhere:

Pick a race → ability modifiers, size, base speed, racial traits, bonus languages
Pick a class + level → hit die, BAB progression, base saves, class skills highlighted, proficiencies, skill ranks per level
Pick armor → armor bonus, max Dex, ACP, arcane spell failure, weight, speed column
Pick a weapon → damage by size (danyo_P/danyo_M chosen from the character's size), crit, range, damage type, special properties
Feat picker → pre-filtered by eligibility using dotes_disponibles(bab, abilities, owned), with ineligible feats shown greyed-out and their unmet prerequisite spelled out (never silently hidden — the GM may be overriding)

Input ergonomics:

Abilities: toggle between point-buy (using caracteristicas.coste_compra_puntos, live points-remaining counter), manual entry, and standard array. Show base → racial → final as three columns.
Every catalog field is a combobox with accent-insensitive fuzzy search (_norm-equivalent on the client: NFD + strip combining marks + lowercase). Typing espada lar must match Espada larga.
Skills table: class skills sorted first and visually marked; +/− steppers plus direct numeric entry; a running "ranks spent / ranks available" counter; only non-zero skills persisted.
Keyboard-first: Tab order follows visual order, / focuses global search, Enter commits a combobox selection, Esc reverts a field, Cmd/Ctrl+S saves. Every interactive element reachable without a mouse.
Autosave drafts to the API (or IndexedDB if unsaved), with an explicit save-state indicator. Never lose typed data on a refresh.
Validation is non-blocking: warnings appear as inline amber notes; the GM can always save an "illegal" character, because house rules and edge cases are real.
Sensible defaults: new character starts as a level-1 human fighter with a standard array, so the card is never empty.

Character list: dense table with the numbers that matter at the table — name, class/level, HP, AC/touch/flat-footed, initiative, saves, best attack line. Inline HP editing. Duplicate and export actions.

Combat card / active tracking:

HP widget: damage/heal/temp-HP with a numeric pad and negative-HP handling
Condition chips from estados, one click to toggle
Stance toggles (charge, fighting defensively, total defense, power attack with a scale slider, combat expertise, flanking)
Timed effects list with a round counter and a "next round" button that ticks durations and auto-expires
A permanently visible "why?" affordance next to AC, attack, and saves

Accessibility: WCAG 2.1 AA. Semantic HTML, labelled inputs, aria-live on the recomputed card, visible focus rings, no colour-only signalling.

8. Testing requirements

Tests are part of the deliverable, not a follow-up.

Backend

tests/unit/domain/ is the priority: ≥ 95 % coverage on domain/, ≥ 85 % overall. Enforce with --cov-fail-under.
Stacking engine: table-driven cases covering — two same-type bonuses (larger wins, smaller reported as suppressed), two dodge bonuses (both apply), two untyped (both apply), bonus + penalty of the same type, duplicate penalties from the same source (dedupe), circumstance bonuses from distinct vs. identical sources, inactive modifiers excluded, empty input.
Golden characters: build 5–6 fully specified fixtures with hand-computed expected values, each exercising a different corner — a level-1 fighter in scale mail with a shield; a level-5 rogue with two-weapon fighting; a level-8 wizard in no armor with mage armor and shield spells active; a level-12 fighter/rogue multiclass with iterative attacks; a Small halfling with size modifiers; a heavily encumbered character. Store them as YAML in tests/fixtures/ and drive them parametrically. These are the regression net.
Property tests (hypothesis): ability_modifier is monotonic and matches (s-10)//2 for s ∈ [0, 60]; resolved totals are invariant under input ordering; adding an inactive modifier never changes a total; touch AC ≤ full AC; flat-footed AC ≤ full AC when Dex mod ≥ 0.
Data-contract tests against the real YAML: every class has 20 progression rows (10 for prestige); every BAB string parses; every crit string parses; every skill's caracteristica is a known ability; every skill's clases[] entries exist in clases; every armor has a valid categoria; the BonusType enum covers sistema.tipos_de_bonificador exhaustively. These catch corpus drift.
API integration: httpx.ASGITransport against a per-test SQLite database via fixtures; full CRUD lifecycle; 404/422 paths; import/export round-trip equality; PATCH partial semantics.
Architecture test: assert domain/ imports nothing from api, persistence, rules, fastapi, or sqlalchemy.

Frontend

≥ 80 % coverage on src/, with components and hooks tested via React Testing Library — query by accessible role and label, never by test id where a role exists.
MSW handlers built from the generated OpenAPI types so mocks cannot drift from the contract.
Cover: combobox search including accent-insensitivity (espada lar → Espada larga); point-buy counter arithmetic and boundaries; skill-ranks counter; autofill on race/class/armor/weapon selection; live-card refresh on form change (debounce with fake timers); breakdown expand/collapse; non-blocking warning display; keyboard-only completion of the create flow; error and loading states.
No duplicated rules logic in TypeScript — the frontend renders what /derive returns. Any test asserting a Pathfinder formula in TS is a signal you put logic in the wrong layer.
Optional if time allows: one Playwright smoke test — create a character, verify the card, save, reload, verify persistence.
9. Tooling and quality gates
Makefile: install, dev, test, test-backend, test-frontend, lint, format, typecheck, coverage, migrate, seed, check (runs everything)
.pre-commit-config.yaml: ruff lint + format, mypy, prettier, eslint, trailing whitespace, YAML validity
mypy --strict on backend/src, TypeScript strict: true + noUncheckedIndexedAccess
GitHub Actions: matrix job running lint → typecheck → tests → coverage thresholds on both stacks
docker-compose.yml for one-command startup
README.md (English): what it is, prerequisites, setup, running, testing, project structure, architecture decisions, and a short section on how the rules corpus is consumed
CLAUDE.md: conventions, layering rules, "domain is pure", "Spanish data / English code", how to add a new modifier source, how to add a golden fixture
docs/adr/: short ADRs for the choices that will be questioned later — single source of truth for calculations in the backend; vendoring rather than forking pathfinder_reglas.py; modifiers as first-class persisted entities rather than precomputed totals
10. Execution plan

Work in phases. At the end of each phase: tests green, lint clean, one atomic commit. Do not start a phase before the previous one is green. After each phase, print a short summary of what was built and what you deliberately deferred.

Phase	Deliverable
0	Repo skeleton, Poetry + Vite projects, tooling, CI, CLAUDE.md, health endpoint, one passing test on each side
1	rules/ adapter + catalog DTOs + /rules/* endpoints, with data-contract tests over the real YAML
2	domain/: enums, models, modifier engine, full derivation — pure, with the golden fixtures and property tests. This phase is the project. Do not rush it.
3	Persistence, migrations, services, character CRUD + /derive + /combat-sheet, integration tests
4	Frontend shell, generated API types, character list, combat card with breakdowns
5	Creation/edit form with autofill, comboboxes, point-buy, skills, feats, equipment; full frontend test suite
6	Combat tracking: conditions, stances, timed effects, round ticking, HP widget
7	Import/export, polish, accessibility pass, README + ADRs, coverage gates enforced
11. Definition of done
make check passes from a clean clone.
Coverage gates enforced in CI, not just documented.
All golden fixtures reproduce their hand-computed values.
A GM can create, edit, duplicate, and delete a character, and read a combat sheet where every number can be expanded into the exact list of bonuses that produced it, including the ones that were suppressed by stacking rules.
Zero Pathfinder arithmetic implemented in TypeScript.
Zero English domain data invented; zero Spanish identifiers in code.
12. Working agreement
Ask before assuming on anything that would be expensive to reverse (schema shape, stacking edge cases, multiclass BAB handling). Ask once, batched, then proceed.
When the rules corpus is ambiguous or its beneficio_resumen is truncated (many feat summaries end in ….), implement the mechanically obvious reading, and record the assumption in docs/assumptions.md rather than silently guessing.
Prefer a small, correct, well-tested core over broad, shallow coverage. A perfect AC breakdown beats a half-working spell system.
Do not scaffold placeholder files you don't implement in the same phase.