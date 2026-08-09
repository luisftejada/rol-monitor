# Handoff — picking this up on another machine

Read this after `CLAUDE.md`. It says how to get running from a fresh clone, where the
work stands, and which mistakes already cost time here so they need not cost it twice.

## 1. Bootstrap

```bash
./setup.sh
```

Idempotent, and it needs no PATH set up first. It finds or installs Python 3.14 —
any 3.14.x pyenv already has, else compiling the pinned patch, a few minutes — creates
`backend/.venv`, runs `poetry install`, finds Node wherever it lives (or fetches it
with nvm), runs `npm ci`, copies `backend/.env` from the example, and migrates.

It stops with a clear message if Poetry is missing, or if there is neither a Python
3.14 nor a pyenv to build one, or neither a Node nor an nvm to fetch one: installing
those is a decision about the machine, not about this project.

## 2. Verify

```bash
make check     # lint + format + typecheck + tests + coverage, both stacks
```

Everything should be green: **384 backend tests, 101 frontend tests**, coverage 96%+
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
filters by what each slot accepts. The five armour and shield proficiencies are among
what a class grants, which is what makes the ten feats gated on them reachable.

An attack line carries a CMB of its own when the way of attacking costs one —
`Ataque poderoso` penalises combat manoeuvres as well as attacks — so the sheet's
CMB stays what you have when that line is not in use.

**Every non-obvious rules decision is in `docs/assumptions.md`** — read it before
changing derivation. It records not just what was decided but why, including the bugs
that motivated each choice.

## What is open

Roughly in order of value:

1. **Choice-gated feat sources**: cleric domains, arcane schools, rogue talents and
   the lore master's secrets. All four hang off a choice rather than a level, so
   they wait on their own subsystems; a schema is proposed but **not applied** in
   `docs/corpus/DISENO_dominios_talentos.md`. The `opcion` key added for the dragon
   disciple is the mechanism for pointing at one branch of an existing list.
2. **Armour proficiency is granted but never checked.** The five feats now exist on
   the character, and `_is_proficient` only ever asks about weapons — wearing plate
   as a wizard costs nothing. Deriving the penalty (armour check to attacks, and to
   every skill involving movement) is the next thing those feats unlock.
3. **Skill and school feat options.** `FeatDTO.choice_kind` already reports them; only
   the weapon picker is built, because the engine acts on nothing else yet.
4. **Ranger combat style and sorcerer bloodline.** Their restricted lists resolve to
   the *union* of all branches, which is wider than the truth, because the sheet does
   not model the choice. The corpus caveat is shown alongside. `opcion` is how a slot
   pins one branch once the sheet can say which it is.

## Traps that already cost time here

- **`make install` is not the bootstrap; `./setup.sh` is.** `make install` runs
  `poetry install`, which puts the venv wherever Poetry likes — its cache, normally —
  and leaves `backend/.venv` missing, which is the one thing `start.sh` checks. The
  symptom is a loop: `start.sh` says dependencies are missing, `poetry install` says
  there is nothing to install. `start.sh` now names `./setup.sh` in that message.
- **A `python3.14` on PATH may be a pyenv shim that does not run.** pyenv installs the
  shim on every machine that has pyenv at all, and it refuses unless 3.14 is the
  selected version — which it usually is not. `command -v` plus a `-x` test both pass
  and the interpreter still fails at the first call, so `setup.sh` probes by *running*
  the candidate. It also accepts any 3.14.x pyenv already has rather than insisting on
  the pinned patch, which otherwise triggers a pointless from-source build.
- **Node installed outside PATH fails in a way that does not look like PATH.** npm's
  shebang is `env node`, so it reports `node: No such file or directory` even when
  called by absolute path. `scripts/node-bin.sh` now finds it — on PATH, under
  `~/.local/node`, `/usr/local/node`, `/opt/node`, or nvm — and `setup.sh`,
  `start.sh` and the Makefile all put its answer on PATH themselves. Nothing needs
  exporting by hand. If a fourth entry point ever shells out to npm, give it the
  same two lines rather than a note in the README.
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
- **A frontend test that fails only under `make check`** is almost certainly the
  1-second default on Testing Library's `findBy*`, not a real regression. `make check`
  runs vitest across every core right after the backend suite, and a view rendering
  from an API round trip misses that window. `asyncUtilTimeout` is raised in
  `src/test/setup.ts`. Raising vitest's own `testTimeout` does nothing here — it is a
  different timer, and the file-level one was never the one being hit.
- **Generated types are generated.** After changing a DTO run `make gen-api`; do not
  hand-edit `frontend/src/api/schema.ts`. Typed test fixtures will fail to compile
  until they carry the new field, which is the mechanism working as intended.

## Conventions worth re-reading

`CLAUDE.md` is the contract: Spanish data / English code, a pure domain, one shared
rounding helper, and tests as part of the deliverable. `PROMPT_LOG.md` is the running
log of every change and why — append to it, newest first.
