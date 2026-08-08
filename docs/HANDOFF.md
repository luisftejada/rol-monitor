# Handoff — picking this up on another machine

Read this after `CLAUDE.md`. It says how to get running from a fresh clone, where the
work stands, and which mistakes already cost time here so they need not cost it twice.

## 1. Bootstrap

```bash
./setup.sh
```

Idempotent. It installs Python 3.14 (via pyenv, compiling if needed — a few minutes),
creates `backend/.venv`, runs `poetry install`, switches to Node 20 via nvm, runs
`npm ci`, copies `backend/.env` from the example, and applies the migrations.

It stops with a clear message if Poetry, pyenv or nvm are missing, since installing
those is a decision about the machine, not about this project.

## 2. Verify

```bash
make check     # lint + format + typecheck + tests + coverage, both stacks
```

Everything should be green: **377 backend tests, 101 frontend tests**, coverage 96%+
overall and 97% on `domain/`. If something fails on a clean clone, that is a real
regression, not a setup problem.

## 3. Run

```bash
./start.sh     # API on :8000, UI on :5173
```

**The owner starts and stops the app — an agent must not.** See the first section of
`CLAUDE.md` for why. `start.sh` stops a previous instance of *this* checkout and
relaunches; anything else holding the ports is reported, never killed.

## Where the work stands

The PC module is complete and the combat sheet is auditable: every derived number
carries the list of bonuses that produced it, including the ones stacking rules
suppressed.

The last long stretch was **feats**, and it is finished. All 176 in the corpus are
accounted for, each in exactly one place:

| Treatment | Examples |
| --------- | -------- |
| Applied to the character | Esquiva (+1 dodge AC), Iniciativa mejorada (+4) |
| Folded into a weapon's line | Soltura con un arma, Especialización, Crítico mejorado |
| An alternative attack line | Ataque poderoso, Puntería mortal, Disparo rápido, Golpe vital |
| A weapon of its own | Ira de la medusa (unarmed, +2 attacks at full BAB) |
| A stance the GM toggles | Acometer, Pericia en combate, Hendedura, Crítico sangrante |
| A note on the weapon line | The eight `Crítico X`, Disparos múltiples |
| Deliberately deferred | The three mounted-charge feats |

Feat budgets are derived too: base levels + class slots (gated on the level *in that
class*) + racial slots, with fixed feats granted rather than charged. The picker
filters by what each slot accepts.

An attack line carries a CMB of its own when the way of attacking costs one —
`Ataque poderoso` penalises combat manoeuvres as well as attacks — so the sheet's
CMB stays what you have when that line is not in use.

**Every non-obvious rules decision is in `docs/assumptions.md`** — read it before
changing derivation. It records not just what was decided but why, including the bugs
that motivated each choice.

## What is open

Roughly in order of value:

1. **Automatic proficiencies** (5 feats), sized in §4 of
   `docs/corpus/INVENTARIO_dotes_fuera_de_progresion.md`. They live in
   `clases.<slug>.competencias` as free prose today; making them real feats unlocks
   chained prerequisite validation — Competencia con escudo gates Golpear con el
   escudo mejorado, which is in the ranger's two-weapon style list. Decide which of
   the two is the source of truth before writing. Fold the known ranger-armour error
   below into the same errand.
2. **Choice-gated feat sources**: cleric domains, arcane schools, rogue talents and
   the lore master's secrets. All four hang off a choice rather than a level, so
   they wait on their own subsystems; a schema is proposed but **not applied** in
   `docs/corpus/DISENO_dominios_talentos.md`. The `opcion` key added for the dragon
   disciple is the mechanism for pointing at one branch of an existing list.
3. **A known corpus error**, harmless today, listed in `docs/corpus/README.md`:
   the ranger's armour proficiency says light where the manual says light and medium.
4. **Skill and school feat options.** `FeatDTO.choice_kind` already reports them; only
   the weapon picker is built, because the engine acts on nothing else yet.
5. **Ranger combat style and sorcerer bloodline.** Their restricted lists resolve to
   the *union* of all branches, which is wider than the truth, because the sheet does
   not model the choice. The corpus caveat is shown alongside. `opcion` is how a slot
   pins one branch once the sheet can say which it is.

## Traps that already cost time here

- **Poetry 2.x refuses `poetry env use`** when the interpreter running Poetry is older
  than the project requires. `setup.sh` creates the venv directly instead.
- **YAML parses `2:` as an int, not a string.** A level filter keyed on
  `key.isdigit()` silently never fires and returns every level at once.
- **Rules-catalog responses are ETagged from the corpus bytes *and* a fingerprint of
  the DTO schemas.** Without the second part, adding a field to a DTO leaves clients
  serving a cached response that lacks it. If a new field seems not to arrive in the
  browser, restart the API and hard-reload once.
- **`pgrep -f` matches your own shell** if its command line contains the pattern. Never
  build a kill list from command lines alone; `start.sh` matches listeners on the port
  and confirms ownership by working directory.
- **The frontend must contain no Pathfinder arithmetic.** When a number is needed in
  the UI, derive it in the backend and send it. A TS test asserting a game formula
  means the logic landed in the wrong layer.
- **Generated types are generated.** After changing a DTO run `make gen-api`; do not
  hand-edit `frontend/src/api/schema.ts`. Typed test fixtures will fail to compile
  until they carry the new field, which is the mechanism working as intended.

## Conventions worth re-reading

`CLAUDE.md` is the contract: Spanish data / English code, a pure domain, one shared
rounding helper, and tests as part of the deliverable. `PROMPT_LOG.md` is the running
log of every change and why — append to it, newest first.
