# Prompt log

### 2026-08-12 — Disparo a bocajarro becomes a weapon-line variant, not a warning
**Prompt:** Flindi has a longbow and Disparo a bocajarro (Point-Blank Shot); shouldn't
that generate an extra attack line showing the bonus for targets within 30 feet, the
way Ataque poderoso does?
**Files affected:** `backend/src/pf_tracker/rules/weapon_feats.py`,
`backend/src/pf_tracker/services/assembler.py`,
`backend/tests/unit/rules/test_weapon_feats.py`,
`backend/tests/unit/services/test_assembler.py`, `docs/assumptions.md`,
`docs/HANDOFF.md`.
**Summary:** It was a real gap, not a documented decision — `docs/assumptions.md`
had nothing saying it was deliberate. `distancia_pies` correctly isn't a predicate
the sheet can decide (per the existing 2026-08-07 assumption), so the feat's effect
fell to `apply_feats`'s generic path: a bare "sólo objetivo a 30 pies…" warning, no
numbers, indistinguishable from a feat gated on a fact the app simply doesn't track.
But the gating fact is per-*attack*, exactly what a declared feat like Ataque
poderoso already models as an alternative weapon line. Added
`has_situational_weapon_effect()` — true only for a *passive* feat with exactly one
situational effect whose modifiers are all weapon attack/damage targets — and
pooled it into `_weapon_lines`'s combination machinery alongside declared feats;
`resolve_for_weapon` now keeps such a modifier instead of dropping it, tagging the
line with the existing `— sólo <condición>` suffix. Deliberately narrow, confirmed
by auditing every corpus feat sharing a generic `ataque_*`/`dano_*` target before
touching anything: broadening `is_weapon_scoped()` itself would also catch Pericia
en combate, whose AC half only works by staying excluded from it (would silently
drop that half), and keeping situational modifiers for *declared* feats in general
would stack Golpe arcano's five mutually-exclusive caster-level bands at once,
since none of them can be verified false either. Result: an archer with the feat
now sees "Arco largo (Disparo a bocajarro — sólo objetivo a 30 pies (9 m) o menos)"
with +1/+1 computed, combinable with Puntería mortal same as two declared feats
combine; the old warning is gone for this feat specifically (superseded by the
line), Golpe arcano's is untouched. 10 new backend tests (situational-effect
classification, the resolved line's numbers, the melee-weapon no-op, the
declared-feat danger case proven safe, the full combined-line assembly). 444
backend / 125 frontend tests, lint, types, and coverage all pass.

---

### 2026-08-12 — Three columns for an attack line's bonus, damage and crit
**Prompt:** In the Ataques card, put the attack bonus, damage, and critical into
three columns instead of stacking them.
**Files affected:** `frontend/src/components/AttackLines.tsx`,
`frontend/src/index.css`.
**Summary:** Wrapped the three (`StatBreakdown` attack bonus, `StatBreakdown`
damage — including the Manyshot first-attack variant when present — and the
plain-text crit line) in a new `.attack__stats` flex-wrap row, the same layout
`.card__saves`/`.card__tactics` already use for AC/BMC/DMC. Gave `.attack__crit`
tile chrome (border, padding, min-width) matching `.stat` so it reads as a third
column beside the two toggles rather than plain caption text — it stays a plain
`<p>`, since threat range/crit multiplier have no breakdown to expand. BMC and the
notes list stay their own full-width rows below, since the ask was specifically
these three. `AttackLines` is shared by `CombatCard` and the editor's
`AttacksSection`, so both picked up the change from one edit. 434 backend / 125
frontend tests, lint, types, and coverage all pass unmodified.

---

### 2026-08-12 — Ataques card below Equipo
**Prompt:** Below the Equipo card, add an Ataques card listing every selected
weapon with its attack bonus, damage, etc. A weapon with more than one way of
being used (Ataque poderoso, Puntería mortal, ...) must appear once per way.
**Files affected:** `frontend/src/components/AttackLines.tsx` (new),
`frontend/src/components/CombatCard.tsx`,
`frontend/src/features/editor/sections/AttacksSection.tsx` (new, + test),
`frontend/src/features/editor/CharacterEditor.tsx`, `frontend/src/i18n/es.ts`.
**Summary:** `/derive`'s `attacks` array already has one entry per alternative —
that is how the read-only `CombatCard` has shown Power Attack lines etc. since the
feats phase — so this is a second consumer of data the backend already computes,
not new derivation. Extracted the block that renders one `.attack` line
(bonus/damage/crit/CMB/notes, each a `StatBreakdown`) out of `CombatCard` into a
shared `AttackLines` component so the editor's new card and the read-only view
can't drift apart; `CombatCard`'s own rendered output is unchanged; its existing
tests (including the one with two lines for the same weapon) cover `AttackLines`
too. `AttacksSection` follows the other editor cards' shape (`editor__section`,
`ac`/`saves`-style optional prop fed by `sheet?.attacks`) and shows a placeholder
until a weapon is equipped. Registered it in the nav and rendered it right after
`EquipmentSection` in the editor's left column. 434 backend / 125 frontend tests,
lint, types, and coverage all pass.

---

### 2026-08-12 — Widen the page and split the editor with Habilidades on the right
**Prompt:** Make the page wider, and split the character editor into two columns
with the Habilidades card on the right.
**Files affected:** `frontend/src/features/editor/CharacterEditor.tsx`,
`frontend/src/index.css`.
**Summary:** Raised `.layout__main`'s max-width from 72rem to 96rem (site-wide —
every page centers and caps its width there, and nothing asked for the editor
alone to differ). Split `.editor__form` into a two-column grid at the existing
60rem breakpoint: a left `.editor__column` with Identidad, Características,
Salvaciones, Clases y nivel, Dotes and Equipo stacked as before, and a right
`.editor__column--skills` holding only `SkillsSection`, sticky so it stays in
view while the longer left column scrolls — the same treatment the removed
live-preview `<aside>` used to get. The `<form>` element still wraps both
columns, so submit/Ctrl+S behavior is unchanged. 434 backend / 118 frontend
tests, lint, types, and coverage all pass unmodified — no test asserted the
single-column DOM order.

---

### 2026-08-12 — Drop the editor's live-preview panel
**Prompt:** Remove the right-hand panel from the character editor page (the live
combat-card preview); keep only the left-column form cards — Identidad,
Características, Salvaciones, Clases y nivel, Habilidades, Dotes, Equipo.
**Files affected:** `frontend/src/features/editor/CharacterEditor.tsx`,
`frontend/src/features/editor/CharacterEditor.test.tsx`, `frontend/src/a11y.test.tsx`,
`frontend/src/i18n/es.ts`, `frontend/src/index.css`.
**Summary:** Now that AC, saves, and BAB/initiative/BMC/DMC live in the form's own
section cards (see the last few entries), the `<aside>` running a second live
`CombatCard` next to the form duplicated the same numbers without adding
information, so it is gone — `CombatCard` itself is untouched and still used
read-only during play (`CharacterPage`). Dropped the now-unused two-column
`.editor__panes`/`.editor__preview` CSS and the `editor.livePreview` i18n key; the
form (`.editor__form`) now renders directly, full width within the page's existing
72rem `.layout__main` cap. Removed the test that asserted the preview card's mere
existence and the one that watched it refresh on equipment changes, keeping the
same equipment-recompute behavior as a test against the Equipo section's own AC
figure instead of a `within(preview)`-scoped duplicate. The a11y test for the editor
now waits on that same figure (a stand-in for "the page has finished its first
derivation") instead of the removed preview card. 434 backend / 118 frontend tests,
lint, types, and coverage all pass.

---

### 2026-08-12 — Fix node-bin.sh's nvm depth bug, with a regression test
**Prompt:** Fix the `scripts/node-bin.sh` bug found while verifying the pending
editor work (its nvm fallback used `find -maxdepth 2`, one level too shallow to
ever reach `nvm_root/vX.Y.Z/bin/node`), with a test.
**Files affected:** `scripts/node-bin.sh`, `scripts/node-bin.test.sh` (new),
`Makefile`, `docs/HANDOFF.md`.
**Summary:** Changed the nvm search from `-maxdepth 2` to `-maxdepth 3` — nvm's
real layout is `nvm_root/vX.Y.Z/bin/node`, three levels down, so depth 2 silently
matched nothing and was indistinguishable from "no nvm installs", which is how it
went unnoticed. There is no shell-test framework in the repo, so
`scripts/node-bin.test.sh` is a small self-contained bash harness: it isolates each
case with a scratch `HOME`/`NVM_DIR` and a `PATH` that cannot see a real Node, uses
fake `node` stubs that only answer `--version`, and reproduces the bug against the
unfixed script before confirming the fix (three levels deep is found; newest-usable
selection and the too-old/no-match cases still behave). Wired it into `make
check` as a new `test-scripts` step, since nothing was exercising this script at
all before. Noted the fix in `docs/HANDOFF.md`'s traps section.

---

### 2026-08-12 — Verify the pending editor work and fix the bootstrap gap that blocked it
**Prompt:** Continue from where the previous session left off: verify that the
uncommitted equipment/skills/saves editor changes are still green before doing
anything else with them.
**Files affected:** `docs/HANDOFF.md`
**Summary:** `make check` failed outright in this environment before any real work
could continue: Poetry refused every command because the shell's active interpreter
was 3.11.8 while `backend/.venv` already had 3.14.6 sitting unused (fixed by
exporting `VIRTUAL_ENV`/`PATH` the same way `setup.sh` already does — nothing in the
repo changed), and `node` on PATH was v14.19 with `scripts/node-bin.sh`'s nvm
fallback silently returning nothing. That fallback is a real, separate bug — its
`find -maxdepth 2` can never reach `<version>/bin/node`, which sits three levels
under `nvm_root`, not two — left unfixed here and flagged for the owner rather than
touched without being asked. Once a working Node was put on PATH by hand, the full
gate passed clean: 434 backend tests, 119 frontend tests, ruff, mypy --strict,
eslint, prettier, coverage 96.94% overall / 98% on `domain/`. Corrected
`docs/HANDOFF.md`'s stale test count (110 → 119 frontend) to match. The three
uncommitted batches of editor work from the previous session (equipment AC/penalty
display, skills characteristic column, saves card + combat stats in the editor) are
verified and ready to commit; nothing in them changed.

---

### 2026-08-10 — Feats that replace a term instead of adding one
**Prompt:** si, dale
**Files affected:** `backend/src/pf_tracker/rules/feat_substitutions.py` (new),
`backend/src/pf_tracker/rules/{catalog,repository}.py`,
`backend/src/pf_tracker/domain/{models,derivation}.py`,
`backend/src/pf_tracker/services/assembler.py`,
`backend/tests/unit/rules/test_feat_substitutions.py` (new),
`backend/tests/unit/domain/test_derivation_extra.py`,
`backend/tests/unit/services/test_assembler.py`,
`backend/tests/fixtures/{loader.py,golden/07_elf_rogue_l4_finesse.yaml}` (new),
`backend/openapi.json`, `frontend/src/api/schema.ts`,
`frontend/src/test/catalog.ts`, `docs/{assumptions,HANDOFF}.md`, `PROMPT_LOG.md`
**Summary:** The `sustituciones` block had sat unread since the corpus was written,
so `Sutileza con las armas`, `Maniobras ágiles` and `Entrenamiento en combate
defensivo` did nothing at all — melee attacks always used Strength. These are not
bonuses: they change *which* number feeds a formula, which the stacking engine cannot
express, so they resolve to flags the derivation reads. Finesse shows the **better**
of Dexterity and Strength, because the feat is permission rather than obligation and
a carried shield charges its check penalty for taking it up — enough to flip the
choice back at equal scores. Damage stays on Strength. Coverage is by weapon: light,
unarmed, or one of the four the feat names, none of which is light. Each feat's prose
bounds the other two ("no afecta a tu DMC") and the tests quote those lines. A new
golden fixture computes the whole sheet by hand for the corner. The vocabulary is
listed exhaustively with a contract test, so a fourth substitution fails loudly
rather than silently doing nothing — which is exactly how this one hid.

Caught while doing it: the previous commit changed `RaceDTO` without running
`make gen-api`, so the committed TS types had drifted from the API. Nothing fails
when you skip it, and `openapi.json` is gitignored, so `git status` says nothing
either — noted in the traps.

---

### 2026-08-09 — Racial weapon familiarity
**Prompt:** tengo un personaje élfico, con dote sutileza con las armas. al elegir
espada curva élfica, indica que no es competente con esta espada… sin embargo es
élfica
**Files affected:** `backend/data/pathfinder_nucleo.yaml`,
`backend/src/pf_tracker/rules/{catalog,repository}.py`,
`backend/src/pf_tracker/services/assembler.py`,
`backend/tests/unit/rules/test_data_contract.py`,
`backend/tests/unit/services/test_assembler.py`, `docs/{assumptions,HANDOFF}.md`,
`docs/corpus/README.md`, `PROMPT_LOG.md`
**Summary:** A real bug, and wider than reported: `_is_proficient` built its haystack
from class proficiency lines only, so the **race was never consulted at all** — five
races have weapon familiarity and none of it reached the sheet. It is two mechanics
and conflating them is the trap: named weapons are proficiencies outright (an elf
wizard *can* hold a rapier), while the race's word makes a weapon count as *martial*
— the elven curve blade stops being exotic, and it still takes a class with martial
weapons to swing it. So the elf fighter is now proficient and the elf wizard,
correctly, is not. Cross-checking each race's paragraph against the manual turned up
two more corpus errors: the dwarf's trait listed the waraxe and urgrosh as outright
proficiencies when the manual only makes them martial (it was arming dwarf wizards),
and the half-orc's named the wrong two weapons. **Not fixed, and now the top open
item:** `Sutileza con las armas` does nothing at all — melee attacks always use
Strength, so the reporter's Dex-built elf is still a point light. The corpus already
carries the mechanic as a structured `sustituciones` block that no code reads.

---

### 2026-08-09 — The combat card says where the ranks went
**Prompt:** quiero ver en qué habilidades hay asignado al menos 1 rango
**Files affected:** `frontend/src/components/{StatBreakdown,CombatCard}.tsx` and
tests, `frontend/src/i18n/{index,es}.ts`, `frontend/src/i18n/i18n.test.ts` (new),
`frontend/src/index.css`, `PROMPT_LOG.md`
**Summary:** Fallout from listing all 35 skills: with three dozen rows a bonus alone
no longer tells you where the ranks went. `ranks` was already on the DTO from the
previous change, so this is presentation only — `StatBreakdown` grew an optional
`note` shown beside the label, and a trained row reads "Montar ★ 3 rangos +8". The
count is *text*, and part of the row's accessible name; the heavier label and the
rule down the side only help the eye, and the row still reads correctly with both
stripped. "1 rangos" forced the issue on plurals, so `translate` now understands a
`singular|plural` template selected by `params.count` — better there than a
`n === 1 ? … : …` in every component that happens to render a count. `translate` had
no test of its own despite being shared by everything; it has one now, and the i18n
module went from 66% branches to 100%.

---

### 2026-08-09 — Skills show ability, others and total, with the bonuses behind them
**Prompt:** en habilidades, además de ver la columna de rangos, quiero ver cuál es el
bonificador final que aplica, y otra columna con bonificador por característica,
además, otra columna que indique "otros"… al hacer hover se tienen que mostrar
desglosados todos los bonos que aplican
**Files affected:** `backend/src/pf_tracker/domain/{enums,models,derivation}.py`,
`backend/src/pf_tracker/services/assembler.py`,
`backend/src/pf_tracker/schemas/combat_sheet.py`, backend tests,
`backend/openapi.json`, `frontend/src/api/schema.ts`,
`frontend/src/features/editor/sections/{SkillsSection,SkillModifiers}.tsx` and tests,
`frontend/src/features/editor/CharacterEditor.tsx`, `frontend/src/test/fixtures.ts`,
`frontend/src/i18n/es.ts`, `frontend/src/index.css`, `docs/assumptions.md`,
`PROMPT_LOG.md`
**Summary:** Four columns per skill, every number from `/derive` — the frontend adds
up nothing. The split (`ranks`, `ability_modifier`, `other_modifiers`) is computed in
the domain, where "others" is the residue of the total rather than a filter over the
breakdown, and the two named parts are picked out of the applied list by object
identity rather than by label. A golden test asserts the three sum to the total for
every fixture. `/derive` now returns all 35 skills rather than only the invested
ones, since the editor needs an ability modifier for every row; the untrained warning
moved behind a new `is_tracked` flag so it does not fire two dozen times per
character. Agreed with the owner that the combat card lists them all too, which is
what a paper sheet does. The tooltip lists the *whole* breakdown, not the "others"
part: it is what was asked for, and picking entries apart by label would be rules
knowledge in the frontend. It opens on hover **and** focus, and pins on click — hover
alone is unreachable by keyboard and dead on touch. Found and fixed on the way: three
call sites labelled ability modifiers with the enum's English member name, so
breakdowns read "Dex" and "Cha" next to "Habilidad de clase".

---

### 2026-08-09 — The bootstrap works on a machine that has the tools
**Prompt:** como lo instalo?
**Files affected:** `setup.sh`, `start.sh`, `docs/HANDOFF.md`, `PROMPT_LOG.md`
**Summary:** Three bugs on the fresh-clone path, found by watching it fail. (1)
`start.sh` said "Run: make install", which cannot fix it: `make install` runs
`poetry install`, whose venv goes to Poetry's cache, leaving `backend/.venv` — the
thing `start.sh` checks — missing. The result is a loop where the app says
dependencies are missing and Poetry says there is nothing to install. It now names
`./setup.sh`, and also checks `backend/.env`, whose absence used to surface later and
less clearly. (2) `setup.sh` picked `python3.14` off PATH after an existence check,
but on any machine with pyenv that is a shim which refuses to run unless 3.14 is the
selected version. It now probes by *running* the candidate, and takes any 3.14.x
pyenv already has instead of insisting on the pinned patch and building from source
for nothing. (3) The Node failure message did not mention PATH, which is the usual
cause — npm's `env node` shebang makes it report a missing `node` even when called by
absolute path.

**Follow-up ("¿y no puedes modificar el script para que lo incluya?"):** yes — telling
the reader to `export PATH` before a script whose job is to set the machine up is not
a bootstrap. `scripts/node-bin.sh` finds a Node >=18 on PATH, under `~/.local/node`,
`/usr/local/node`, `/opt/node` or nvm, and prints its directory; `setup.sh`,
`start.sh` and the **Makefile** each put that on PATH themselves. The Makefile was the
worst of the three — every `make check` needed a manual export. `make check` now
passes from a shell with no Node on PATH at all.

---

### 2026-08-09 — Armour proficiency becomes a feat; weapons stay prose
**Prompt:** explicame que hay que decidir → ok a tu recomendacion C
**Files affected:** `backend/data/pathfinder_nucleo.yaml`, `.gitignore`,
`backend/tests/unit/rules/{test_data_contract,test_feat_slots}.py`,
`backend/tests/unit/services/test_assembler.py`, `frontend/src/test/setup.ts`,
`docs/{assumptions,HANDOFF}.md`, `docs/corpus/README.md`, `PROMPT_LOG.md`
**Summary:** The same fact — "this class is proficient with shields" — lived in two
incompatible forms: free prose in `competencias`, and feats other feats name as
prerequisites. Eligibility matches names, so prose was invisible to it and a level-6
fighter was told they could not take any of the ten feats gated on `Competencia con
escudo`. With the manual now to hand, the split turned out not to be a judgement
call: armour reads *"disponen automáticamente de X como dote adicional"*, weapons
read *"son competentes con"* — proficiency without the feat. So the five armour and
shield feats are granted by the eight classes that get them (24 `fija` slots, and
they cost no choice), and prose keeps weapons, where all the irregular detail lives.
Cross-checking every class' proficiency paragraph against the five feats' "Especial"
lines — they agree on all 11 classes — turned up a second corpus error beside the
known ranger one: the cleric was getting heavy armour. Both fixed and pinned. The
manual itself is gitignored; it is a 90 MB commercial book.

Also fixed a flaky gate found on the way: two frontend tests failed only under
`make check`, never alone. Not a regression and not vitest's `testTimeout` (raising
that changed nothing) — it is Testing Library's 1-second `findBy*` default, which a
view rendering from an API round trip misses when vitest runs across every core right
after the backend suite. `asyncUtilTimeout` raised in `src/test/setup.ts`.

---

### 2026-08-08 — Prestige classes grant their bonus feats
**Prompt:** sigue
**Files affected:** `backend/data/pathfinder_nucleo.yaml`,
`backend/src/pf_tracker/rules/{catalog,repository}.py`,
`backend/src/pf_tracker/services/assembler.py`,
`backend/src/pf_tracker/schemas/combat_sheet.py`,
`backend/tests/unit/rules/{test_data_contract,test_repository}.py`,
`backend/tests/unit/services/test_assembler.py`, `backend/openapi.json`,
`frontend/src/api/schema.ts`, `docs/{assumptions,HANDOFF}.md`,
`docs/corpus/README.md`, `PROMPT_LOG.md`
**Summary:** First of the corpus errands from the manual sweep. `caballero_arcano`
(Combat feat at 1/5/9) and `discipulo_del_dragon` (2/5/8) now declare
`dotes_adicionales`; no code was needed to make them count, since prestige classes
already went through the same slot mapping — that is what "the container exists and
is empty" meant. The disciple needed one new thing: a slot can pin *one branch* of a
list keyed by a choice (`opcion: draconico`), so it resolves to the exact 7 draconic
feats instead of the 40-feat union a sorcerer's own slot still gets. Resolved lists
are filed under `key/branch`, because a sorcerer 7 / dragon disciple 2 references
both. A branch that does not exist resolves to nothing, never to the union: an empty
picker is visibly wrong, a plausible wrong answer is not. A new contract test walks
all 42 bonus-feat slots in the corpus and checks every `lista`, `opcion`, `dote` and
`tipos` hits a real target. `maestro_del_saber` was left out on purpose — its feats
hang off a *secret*, which is a choice, not a level, so it belongs with domains,
schools and rogue talents.

---

### 2026-08-08 — An attack line that costs CMB says so
**Prompt:** seguimos
**Files affected:** `backend/src/pf_tracker/rules/weapon_feats.py`,
`backend/src/pf_tracker/domain/{models,derivation}.py`,
`backend/src/pf_tracker/services/assembler.py`,
`backend/src/pf_tracker/schemas/combat_sheet.py`,
`backend/tests/unit/rules/test_weapon_feats.py`,
`backend/tests/unit/domain/test_derivation_extra.py`,
`backend/tests/unit/services/test_assembler.py`,
`backend/tests/integration/test_characters_api.py`, `backend/openapi.json`,
`frontend/src/api/schema.ts`, `frontend/src/components/CombatCard.tsx` and its
tests, `frontend/src/i18n/es.ts`, `docs/{assumptions,HANDOFF}.md`, `PROMPT_LOG.md`
**Summary:** Closed the last open residue of the feats work. The corpus has
`Ataque poderoso` penalise attacks *and* `bmc` in the same breath, but only the
attack half reached the sheet: the feat is weapon-scoped, so it is never offered as
a stance, and a weapon line had nowhere to put a character-level number. A line now
carries its own CMB, resolved through the same `derive_cmb` so it arrives with a
full breakdown, and it is present only when the line changes it — the character's
CMB is what you have when that line is not in use. `Pericia en combate`, the only
other feat touching `bmc`, still leaves its penalty to its stance: charging it in
both places would take it twice from a GM who uses both halves.

---

### 2026-08-08 — The feat picker filters by the slot being spent
**Prompt:** Yes, let's build it.
**Files affected:** `backend/src/pf_tracker/rules/{repository,feat_slots}.py`,
`backend/src/pf_tracker/services/assembler.py`,
`backend/src/pf_tracker/schemas/combat_sheet.py`,
`backend/tests/unit/rules/test_repository.py`, `backend/openapi.json`,
`frontend/src/api/schema.ts`,
`frontend/src/features/editor/sections/FeatsSection.tsx` and its tests,
`frontend/src/i18n/es.ts`, `frontend/src/test/{catalog,fixtures}.ts`,
`docs/assumptions.md`, `PROMPT_LOG.md`
**Summary:** The type filter now leads with what the character's own slots accept:
"Combate — Guerrero" filters by category, "Lista de Monje" by the resolved list. The
four restricted lists are resolved to feat names in the repository — the corpus
states them in four different shapes, and walking those in TypeScript would be rules
logic in the wrong layer — keyed by level so a later slot sees more. Where the list
depends on a choice the sheet does not model, the union is returned and the corpus'
caveat is shown with it. A bug worth remembering: YAML parses `2:` as an int, so the
first level filter never fired and every list came back at full size.

---

### 2026-08-08 — Feat budget per level, class and race
**Prompt:** Implement the feat limits per level now that the corpus carries them.
**Files affected:** `backend/src/pf_tracker/rules/{catalog,repository,feat_slots}.py`
(new module), `backend/src/pf_tracker/services/{assembler,character_service}.py`,
`backend/src/pf_tracker/schemas/combat_sheet.py`, backend tests,
`backend/openapi.json`, `frontend/src/api/{schema,types}.ts`,
`frontend/src/features/editor/sections/FeatsSection.tsx` and its tests,
`frontend/src/features/editor/CharacterEditor.tsx`, `frontend/src/i18n/es.ts`,
`frontend/src/index.css`, `frontend/src/test/{catalog,fixtures}.ts`,
`docs/assumptions.md`, `PROMPT_LOG.md`
**Summary:** The sheet now derives a feat budget — base levels, class slots gated on
the level in that class, and racial slots — exposed with its breakdown so the editor
renders "Dotes: 1 / 2" and where each slot came from without counting anything
itself. Fixed slots are granted rather than charged, and the granted names join the
character's effective feats: that alone fixed a monk taking -4 with their own fists,
since proficiency was reading the typed list. Over budget warns and never blocks.

---

### 2026-08-07 — Corpus feat progression landed; provenance docs filed
**Prompt:** Here is what Claude returned (inventory, schema design, patched corpus).
The documents were uploaded to the data folder; place them where appropriate.
**Files affected:** `docs/corpus/` (new: README, inventory, design, schema fragment,
sweep script — all moved out of `backend/data/`), `PROMPT_LOG.md`
**Summary:** The corpus now carries `clases.<slug>.dotes_adicionales`,
`razas[].dotes_adicionales` and `dotes.listas_restringidas`, with page citations.
Validated against the five criteria from the brief: every fixed feat name, every
`tipos` value and every `lista` key resolves, and each slot cites a page — zero real
errors. Moved the working documents and the extraction script out of `backend/data/`,
which CLAUDE.md defines as the vendored read-only corpus, into `docs/corpus/` with a
README saying what each is and that the schema fragment is a proposal, not a patch.
354 backend and 95 frontend tests still pass against the new corpus.

---

### 2026-08-07 — Page title, and icon actions on the roster
**Prompt:** "Personajes" should be styled as a title. Replace the row buttons with
icon buttons that show the action on hover — copy for duplicate, a bin for delete —
and add a pencil to edit.
**Files affected:** `frontend/src/components/icons.tsx` (new),
`frontend/src/components/CharacterTable.tsx`,
`frontend/src/pages/CharacterListPage.test.tsx`, `frontend/src/i18n/es.ts`,
`frontend/src/index.css`, `PROMPT_LOG.md`
**Summary:** `h1` is styled once globally — Tailwind's preflight had left every page
title rendering as body text. Row actions became icon buttons: a pencil linking to
the editor, a copy glyph, and a bin. Each carries the word in `title` for the hover
tooltip and in `aria-label` for the accessible name, so the glyph never has to be
guessed at and the existing tests still find them by name. The icons are inline SVG
rather than a package: three glyphs do not justify a dependency, and `currentColor`
makes them follow the button in either theme. The bin turns red only on hover, and
never signals by colour alone.

---

### 2026-08-07 — start.sh restarts instead of refusing
**Prompt:** On startup, check whether an instance is already running; if so, kill it
and bring the service back up.
**Files affected:** `start.sh`, `PROMPT_LOG.md`
**Summary:** The port preflight now stops a previous instance and carries on, since
restarting is the common case. Candidates are the processes *listening on* 8000 and
5173, confirmed as ours by a working directory under this checkout — an early
attempt matched command lines instead and put an innocent shell on the kill list
merely for mentioning "node_modules/.bin/vite" inside the project. Anything still
holding a port afterwards is reported, never killed. Verified with decoy listeners
on an isolated port and root: ours is stopped and the port freed, a listener outside
the project survives, and a running instance launched by the previous version of the
script is still recognised.

---

### 2026-08-07 — Mounted feats deferred
**Prompt:** Leave these three aside for now; in principle as stances.
**Files affected:** `backend/tests/unit/rules/test_weapon_feats.py`,
`docs/assumptions.md`, `PROMPT_LOG.md`
**Summary:** No behaviour change. The three mounted-charge feats are pinned as a
known-deferred set with a test asserting they contribute nothing today, following
the same pattern as the incomplete prestige progressions: when someone makes them
stances the test fails and the assumption entry has to be updated with what was
decided. This closes the feat review — every one of the 176 is now applied,
rendered as a weapon line or stance, surfaced as a note, or explicitly deferred.

---

### 2026-08-07 — Bleeding Critical as a combat stance
**Prompt:** Bleeding Critical can be handled as a stance — an effect to apply in
combat.
**Files affected:** `backend/src/pf_tracker/rules/weapon_feats.py`, backend tests,
`backend/openapi.json`, `frontend/src/api/schema.ts`,
`frontend/src/features/tracker/StanceToggles.tsx`,
`frontend/src/features/tracker/CombatTracker.test.tsx`,
`frontend/src/i18n/es.ts`, `frontend/src/index.css`, `docs/assumptions.md`,
`PROMPT_LOG.md`
**Summary:** A feat that leaves an effect running on the target each round now
qualifies as a stance even though it changes none of the character's numbers — the
toggle is the reminder, and a test pins that switching it on leaves the sheet
untouched. Today that is only `Crítico sangrante`; the other critical feats resolve
on the hit and stay notes on the weapon line. While a stance is active the tracker
shows what it does on screen rather than in a tooltip, since a number the GM must
apply every round is useless behind a hover.

---

### 2026-08-07 — Critical feats as notes on the weapon line
**Prompt:** For now, a note on the weapon line. We will come back to it when we
model combat.
**Files affected:** `backend/src/pf_tracker/domain/{models,derivation}.py`,
`backend/src/pf_tracker/schemas/combat_sheet.py`,
`backend/src/pf_tracker/rules/weapon_feats.py`,
`backend/src/pf_tracker/services/assembler.py`, backend tests,
`backend/openapi.json`, `frontend/src/api/schema.ts`,
`frontend/src/components/CombatCard.tsx`,
`frontend/src/components/CombatCard.test.tsx`, `frontend/src/index.css`,
`frontend/src/test/fixtures.ts`, `docs/assumptions.md`, `PROMPT_LOG.md`
**Summary:** A weapon line can carry prose annotations, shown under its critical
range — where the GM looks when confirming a crit. Critical feats produce one note
each from their own corpus summary, plus the corpus' "one per critical hit" rule
verbatim, shown only when the character holds more than one and lacks the mastery
that lifts it. They change no number, so nothing else on the sheet moves; applying
the condition to the target stays manual until there is an NPC to apply it to.

---

### 2026-08-07 — Combat Expertise as stance and variant
**Prompt:** Stance and variant, with a clarifying note.
**Files affected:** `backend/src/pf_tracker/rules/weapon_feats.py`,
`backend/src/pf_tracker/services/assembler.py`, backend tests,
`backend/openapi.json`, `frontend/src/api/schema.ts`,
`frontend/src/features/tracker/StanceToggles.tsx`,
`frontend/src/features/tracker/CombatTracker.test.tsx`,
`frontend/src/i18n/es.ts`, `frontend/src/index.css`, `docs/assumptions.md`,
`PROMPT_LOG.md`
**Summary:** A feat can now be a stance *and* an attack variant, each half rendered
where it can apply: `is_global_feat_target` splits the character's values (AC, CMB)
from the weapon's (attack, damage), so neither is applied twice. The tracker
explains the split, since otherwise half of Combat Expertise looks missing.
Verifying it caught the stance summing all six BAB bands at once — +21 AC at level
8 — because it was not checking each effect's condition; it now respects them, so
BAB 8 gives -3 attack, +3 AC, -3 CMB.

---

### 2026-08-07 — Lunge as a feat-gated stance
**Prompt:** Acometer fits as a stance that requires the feat.
**Files affected:** `backend/src/pf_tracker/domain/models.py`,
`backend/src/pf_tracker/schemas/character.py`,
`backend/src/pf_tracker/rules/{catalog,repository,weapon_feats}.py`,
`backend/src/pf_tracker/services/assembler.py`, backend tests,
`backend/openapi.json`, `frontend/src/api/schema.ts`,
`frontend/src/features/tracker/StanceToggles.tsx`,
`frontend/src/features/tracker/CombatTracker.test.tsx`,
`frontend/src/features/editor/sections/FeatsSection.test.tsx`,
`frontend/src/i18n/es.ts`, `frontend/src/test/catalog.ts`, `docs/assumptions.md`,
`PROMPT_LOG.md`
**Summary:** Stances can now come from feats: `Stances.feat_stances` holds the
declared feats switched on this round, and their modifiers are read from the corpus
rather than recomputed. `FeatDTO.is_stance` classifies them in the backend, so the
tracker renders a toggle only for feats the character holds and never decides on
rules grounds. The classification excludes anything already rendered as an attack
variant, so the same feat can never be applied twice — a test pins that for Power
Attack, Combat Expertise, Deadly Aim and Rapid Shot.

---

### 2026-08-07 — Medusa's Wrath as a weapon of its own
**Prompt:** The best way to implement this is to define a new weapon, "Ira de la
medusa", based on the unarmed strike, adding two attacks at the highest bonus. It
removes the possibility of combining armed and unarmed attacks.
**Files affected:** `backend/src/pf_tracker/domain/{models,derivation}.py`,
`backend/src/pf_tracker/rules/weapon_feats.py`,
`backend/src/pf_tracker/services/assembler.py`,
`backend/tests/unit/rules/test_weapon_feats.py`,
`backend/tests/unit/services/test_assembler.py`, `backend/openapi.json`,
`frontend/src/api/schema.ts`, `docs/assumptions.md`, `PROMPT_LOG.md`
**Summary:** A weapon line can now carry extra attacks made at the highest bonus,
and a feat can *be* a weapon: `FEAT_WEAPONS` builds the Medusa's Wrath line from
`Impacto sin armas`, standing alone rather than combining with a carried weapon's
variants. The count comes from the corpus modifier, not a literal. Situational
effects on a weapon line are now generated and labelled with their condition
instead of dropped, since the GM can judge the situation the sheet cannot. The same
mechanism fixed `Disparo rápido`, which showed its -2 without its extra shot, and
surfaced that a monk took -4 with their own fists: `Impacto sin arma mejorado` now
grants unarmed proficiency, since the monk's proficiency text never says "sencilla".

---

### 2026-08-07 — Vital Strike: single attack and supersession
**Prompt:** Vital Strike changes the attack modifier — with several attacks only the
highest bonus remains — and it stacks with the weapon like Deadly Aim. New rule:
taking the higher feat leaves the lower one with no effect.
**Files affected:** `backend/src/pf_tracker/domain/{models,derivation}.py`,
`backend/src/pf_tracker/rules/weapon_feats.py`,
`backend/src/pf_tracker/services/assembler.py`,
`backend/tests/unit/rules/test_weapon_feats.py`,
`backend/tests/unit/services/test_assembler.py`, `docs/assumptions.md`,
`PROMPT_LOG.md`
**Summary:** A weapon line can now be a single attack: feats activated as
`accion_de_ataque` or `estandar` keep only the highest attack bonus, since Vital
Strike trades the iteratives for extra dice on one blow. Added feat supersession —
a feat replaced by a higher one is dropped entirely, before it can fold into the
base line or spawn a variant. Without it, prerequisites forced a level-16 fighter
to hold all three Vital Strikes and the sheet derived x24 dice over eight lines.
The table is explicit but a contract test checks each entry against the corpus prose
that states it, and against `Combate con dos armas mejorado`, which shares the
prerequisite shape without superseding.

---

### 2026-08-07 — Drop the two stance toggles; Manyshot doubles the first arrow
**Prompt:** Do points 1 and 2, and do not ask for confirmation until they are done.
**Files affected:** `backend/src/pf_tracker/domain/{models,stances,derivation}.py`,
`backend/src/pf_tracker/schemas/{character,combat_sheet}.py`,
`backend/src/pf_tracker/services/assembler.py`,
`backend/src/pf_tracker/rules/weapon_feats.py`, backend tests,
`backend/openapi.json`, `frontend/src/api/schema.ts`,
`frontend/src/features/tracker/StanceToggles.tsx`,
`frontend/src/features/tracker/CombatTracker.test.tsx`,
`frontend/src/components/CombatCard.tsx`, `frontend/src/features/editor/draft.ts`,
`frontend/src/i18n/es.ts`, `frontend/src/test/fixtures.ts`, `docs/assumptions.md`,
`PROMPT_LOG.md`
**Summary:** Removed Power Attack and Combat Expertise from the stances across all
four layers, taking `scale_step` and `power_attack_damage_bonus` with them — the
corpus states that scaling, so recomputing it was a second source of truth. Added a
damage-dice multiplier to the weapon line: `Golpe vital` reads it from
`dados_dano_arma`, while `Disparos múltiples` is keyed by name since the corpus
states it only in prose, and applies to the first attack alone. Only the dice
multiply; flat damage is added once. The sheet exposes the first attack's
expression separately and the card renders it above the normal one.

---

### 2026-08-07 — Weapon choice for weapon-scoped feats
**Prompt:** Build the feat options in the editor.
**Files affected:** `backend/src/pf_tracker/rules/{feat_targets,catalog,repository}.py`,
`backend/tests/unit/rules/test_feat_targets.py`, `backend/openapi.json`,
`frontend/src/api/schema.ts`,
`frontend/src/features/editor/sections/FeatsSection.tsx`,
`frontend/src/features/editor/sections/FeatsSection.test.tsx`,
`frontend/src/i18n/es.ts`, `frontend/src/test/catalog.ts`, `PROMPT_LOG.md`
**Summary:** `FeatDTO` now reports `choice_kind` (`weapon` / `skill` / `school`),
derived from the corpus targets rather than a hand-kept list, so the editor never
decides on rules grounds what a feat asks for. Feats needing a weapon show a picker
on their chip, over the whole catalog since a feat can be taken for a weapon not yet
carried; clearing it removes the entry, and removing the feat drops the option so a
stale choice cannot reappear. Only the weapon picker is rendered — the engine acts
on nothing else yet, and a control that does nothing is worse than none.

---

### 2026-08-07 — Weapon variants: a feat becomes a second weapon line
**Prompt:** Do point 1 — generate the attack variants. Leave the doubtful feats for
the end.
**Files affected:** `backend/src/pf_tracker/services/assembler.py`,
`backend/tests/unit/services/test_assembler.py`, `PROMPT_LOG.md`
**Summary:** The assembler now emits one `EquippedWeapon` per combination of the
optional feats that apply to it, so "Mandoble" and "Mandoble (Ataque poderoso)"
are literally two weapons and the whole derivation works unchanged. Passive
weapon-scoped feats fold into the base line instead, reading `feat_options` for
the weapon they were taken for, and Improved Critical widens the threat range.
Only four optional feats ever produce numbers per weapon, split melee/ranged, so a
weapon reaches at most four lines; a documented cap guards against a future corpus.
Verified end to end: a level-5 fighter with a greatsword and four feats derives
+10/2d6+8 and +8/2d6+14, crit 17-20.

---

### 2026-08-07 — Weapon-scoped feats: the resolver
**Prompt:** Power Attack is not a global toggle — a fighter with a greatsword has
two weapons: the greatsword, and the greatsword with Power Attack. Build feat
options, Improved Critical (19-20 becomes 17-20), drop the two stance toggles, and
treat Manyshot as doubling the first attack's damage dice.
**Files affected:** `backend/src/pf_tracker/rules/weapon_feats.py` (new),
`backend/src/pf_tracker/rules/feat_effects.py`,
`backend/tests/unit/rules/test_weapon_feats.py` (new), `PROMPT_LOG.md`
**Summary:** First slice: a resolver that applies a feat *against one weapon*, which
makes the grip-specific targets tractable — a greatsword picks up `dano_dos_manos`,
a longsword `dano_una_mano`. Chosen-weapon feats (Weapon Focus, Specialization) read
`feat_options` and apply to nothing when no weapon was picked, rather than guessing.
Improved Critical doubles the threat-range *width*. Prose-only feats surface their
rules text. A test caught grip matching alone handing an archer Power Attack's +6,
since a longbow is also two-handed: grip damage is now melee-only.

---

### 2026-08-07 — Feats finally contribute their modifiers
**Prompt:** Continue: build the producer that turns feat effects into modifiers and
wire it into the assembler.
**Files affected:** `backend/src/pf_tracker/rules/feat_effects.py` (new),
`backend/src/pf_tracker/rules/{catalog,repository}.py`,
`backend/src/pf_tracker/services/assembler.py`,
`backend/tests/unit/rules/test_feat_effects.py` (new),
`backend/tests/unit/services/test_assembler.py`, `backend/openapi.json`,
`frontend/src/api/schema.ts`, `frontend/src/test/catalog.ts`,
`docs/assumptions.md`, `PROMPT_LOG.md`
**Summary:** Closes the gap flagged on day one: `Esquiva` now adds its +1 dodge to
AC and `Iniciativa mejorada` its +4, with the source and bonus type in the
breakdown. `FeatDTO` exposes `activation` and structured `effects`; a producer
translates them through the two vocabulary mappings and the assembler folds them
into the modifier pool. Only `pasiva` feats apply automatically, so the Power
Attack stance is not double-counted, and conditional effects apply only when their
predicate is decidable and holds. Everything not turned into a number — declared
feats, situational conditions, multipliers, unmodelled targets — comes back as a
warning rather than disappearing.

---

### 2026-08-07 — Map the feat target vocabulary onto the domain
**Prompt:** Continue with the modifier-target mapping (98 feat targets vs the
domain's 17).
**Files affected:** `backend/src/pf_tracker/rules/feat_targets.py` (new),
`backend/tests/unit/rules/test_feat_targets.py` (new), `docs/assumptions.md`,
`PROMPT_LOG.md`
**Summary:** Classified all 83 declared targets: 15 map onto `ModifierTarget`,
per-skill checks become `SKILL:<slug>` via the catalog's own slugify, and the
remaining 68 are listed verbatim as deliberately unmodelled (spells, mounted
combat, per-manoeuvre CMB, per-grip damage, class resources). Unmodelled targets
return `None` rather than raising, since the effect is still shown as a note.
Contract tests prove every declared and every used target is classified, and that
each named skill exists in the catalog. Combined with the bonus-type mapping, 110
of 227 feat modifiers (48%, across 34 feats) are now machine-applicable.

---

### 2026-08-06 — Reconcile the two bonus-type vocabularies
**Prompt:** Back to feats: first solve the "two different bonus-type vocabularies"
problem.
**Files affected:** `backend/src/pf_tracker/rules/feat_vocabulary.py` (new),
`backend/tests/unit/rules/test_feat_vocabulary.py` (new),
`docs/assumptions.md`, `PROMPT_LOG.md`
**Summary:** Added an adapter-layer translation from the feats dialect (ASCII
slugs, different words for five types) into `BonusType`, so the stacking engine
keeps one vocabulary. `sin_tipo` and `penalizador` map to untyped since penalties
are read from the sign. `multiplicador`/`formula`/`variable` describe the shape of
`valor`, not a stacking type, so they raise rather than resolve to untyped.
Contract tests check the mapping against both the corpus' declaration and actual
usage, and assert the corpus' stacking classification agrees with the engine's.

---

### 2026-08-06 — Two-level weapon picker with details
**Prompt:** Do for weapons what was done for feats: two levels (weapon type, then
the weapon), a hover summary, and a details modal on click.
**Files affected:**
`frontend/src/features/editor/sections/EquipmentSection.tsx`,
`frontend/src/features/editor/sections/FeatsSection.tsx`,
`frontend/src/features/editor/sections/sections.test.tsx`,
`frontend/src/components/Modal.tsx`, `frontend/src/i18n/es.ts`,
`frontend/src/index.css`, `frontend/src/test/catalog.ts`, `PROMPT_LOG.md`
**Summary:** No backend change was needed — `WeaponDTO` already carries the full
stat block. Replaced the weapon combobox with the same browsable list used for
feats, filtered by the corpus' five `categoria` values plus an accent-insensitive
search, with a hover stat line, a details dialog, and a separate equip button.
Generalised the picker CSS and the chip-name class so both sections share one
implementation, and moved the dialog's close label to a `modal.*` key.

---

### 2026-08-06 — Review the feat parsing after the corpus rewrite
**Prompt:** `pathfinder_nucleo.yaml` was updated and the whole feats section
changed; review the code that parses it.
**Files affected:** `backend/tests/integration/test_rules_api.py`,
`backend/tests/unit/rules/test_data_contract.py`, `PROMPT_LOG.md`
**Summary:** Parsing survives the rewrite — only two hardcoded feat counts broke
(174 → 176), now pinned in one named constant. `beneficio_resumen` is no longer
truncated anywhere (was 45/172). Feats gained `activacion` and machine-readable
`efectos` that the adapter does not yet expose; added data-contract tests pinning
those fields and checking activations, modifier targets and penalty signs against
the corpus' own `esquema_efectos`. Those tests surfaced two feats encoding
"removes the standard penalty" as `valor: 0`, a no-op for an additive engine.

---

### 2026-08-06 — Selected feats get the tooltip and the details dialog too
**Prompt:** Hovering an already-selected feat should show the same message as the
unselected ones, and clicking it should open the dialog as well.
**Files affected:**
`frontend/src/features/editor/sections/FeatsSection.tsx`,
`frontend/src/features/editor/sections/FeatsSection.test.tsx`,
`frontend/src/index.css`, `PROMPT_LOG.md`
**Summary:** Selected feats are persisted as names, so the chip now looks its
entry up in the catalog and renders the name as a control carrying the same
`title` summary and opening the same dialog. A feat with no catalog entry (an
imported or house-ruled one) stays plain text but remains removable. The chip name
opts out of the button chrome so the pill keeps its shape.

---

### 2026-08-06 — Cache validator ignored response-shape changes
**Prompt:** The "Tipo de dote" selector only offers "Todas (alfabéticamente)"; the
corpus feat types are missing.
**Files affected:** `backend/src/pf_tracker/rules/catalog.py`,
`backend/src/pf_tracker/api/deps.py`,
`backend/tests/integration/test_rules_api.py`, `PROMPT_LOG.md`
**Summary:** `/rules/*` ETags were derived from the corpus bytes alone, so adding
`feat_types` to `MetaDTO` changed no validator, and clients kept serving the
cached, field-less `meta` for up to the hour allowed by `max-age=3600` — the
selector then rendered an empty type list. The ETag now also covers a fingerprint
of the catalog DTO schemas, and the freshness window drops to 60s with
`must-revalidate` since a 304 costs almost nothing. Regression test verified
failing without the fix.

---

### 2026-08-06 — The owner starts the app, never the agent
**Prompt:** Stop the service. I will always start it manually myself — record that
in the instructions.
**Files affected:** `CLAUDE.md`, `PROMPT_LOG.md`
**Summary:** Stopped both servers and recorded the rule as the opening section of
`CLAUDE.md`: never run `./start.sh`, `make dev`, `uvicorn` or `npm run dev`, for
any reason. Tests, linters, type-checkers and builds are explicitly unaffected.
When a change needs checking in a running app, say so and let the owner start it.

---

### 2026-08-06 — Two-level feat picker with details
**Prompt:** Feat selection should work in two levels: pick the feat type first,
then the feat. Add an "all alphabetically" option that skips the type filter, and
a "with requirements" option that shows only feats whose prerequisites are met.
When browsing feats, show a short explanation on hover and/or a modal with that
information on click — both if possible.
**Files affected:** `backend/src/pf_tracker/rules/{catalog,repository}.py`,
`backend/tests/unit/rules/{test_repository,test_data_contract}.py`,
`backend/openapi.json`, `frontend/src/api/schema.ts`,
`frontend/src/components/Modal.tsx` (new),
`frontend/src/features/editor/sections/FeatsSection.tsx`,
`frontend/src/features/editor/sections/FeatsSection.test.tsx`,
`frontend/src/i18n/es.ts`, `frontend/src/index.css`,
`frontend/src/test/catalog.ts`, `PROMPT_LOG.md`
**Summary:** Exposed the corpus' canonical feat categories (`dotes.reglas.tipos`)
through `MetaDTO` rather than inferring them from the feats, with a data-contract
test that fails if a feat ever carries an undeclared type. Replaced the feat
combobox with a browsable list filtered by type, by met prerequisites, and by
accent-insensitive search. Each row carries the benefit as a `title` tooltip and
opens a details dialog on click; a separate add button keeps bulk entry off the
modal path, since the brief requires the flow never to block on one.

---

### 2026-08-05 — "Bonif" column in the abilities table
**Prompt:** Add a "Bonif" column to the abilities table showing the modifier that
applies to each score (e.g. -2 for 7, +1 for 12).
**Files affected:**
`frontend/src/features/editor/sections/AbilitiesSection.tsx`,
`frontend/src/features/editor/CharacterEditor.tsx`, `frontend/src/i18n/es.ts`,
`frontend/src/features/editor/sections/AbilitiesSection.test.tsx`,
`frontend/src/features/editor/CharacterEditor.test.tsx`, `PROMPT_LOG.md`
**Summary:** The ability modifier is a Pathfinder formula, so it is not computed
in TypeScript: `/derive` already returns `modifier` per ability, and the editor
now threads those values into the section the same way it does for the skills and
feats sections. The column renders an em dash until the first derivation lands.
Tests cover rendering from supplied values and the wiring from `/derive`
(verified failing when the prop is not passed) without asserting the formula.

---

### 2026-08-05 — Configurable point-buy budget, defaulting to 20
**Prompt:** Next to the ability-assignment method, add a value with (+) and (−)
buttons to set the number of points, defaulting to 20.
**Files affected:** `frontend/src/features/editor/draft.ts`,
`frontend/src/features/editor/sections/AbilitiesSection.tsx`,
`frontend/src/features/editor/sections/AbilitiesSection.test.tsx`,
`frontend/src/i18n/es.ts`, `frontend/src/index.css`, `PROMPT_LOG.md`
**Summary:** Raised the default budget from 15 to 20 and added a labelled
stepper (buttons plus direct entry) on the method row, shown only for the
point-buy method. The counter and the over-budget warning now track the chosen
budget. The budget is editor state, not character data — it drives only the
non-blocking warning and is not persisted.

---

### 2026-08-05 — Align the steppers in the Base column
**Prompt:** The buttons in the "Base" column of the abilities table need aligning.
**Files affected:** `frontend/src/index.css`, `PROMPT_LOG.md`
**Summary:** The point-buy value renders as a bare `<span>`, so its width tracked
the digit count and pulled the "+" button left on single-digit scores (9, 8).
Gave the value a fixed `min-width` with centred, tabular figures so every stepper
lines up down the column. Verified in the browser with mixed one- and two-digit
scores.

---

### 2026-08-05 — Card titles and a page background that contrasts
**Prompt:** "Identidad" is the card title but does not read as one — give it a
centred, distinctive title style. The card also does not stand out from the very
soft ivory background; use a soft blue or another better-contrasting colour.
**Files affected:** `frontend/src/index.css`, `PROMPT_LOG.md`
**Summary:** The ivory page sat at 1.05:1 against a white card, so cards had no
edge; the page is now a soft blue (1.34:1 plus a hue shift) and cards carry a
shadow. Section headings became full-bleed centred title bands — Tailwind's
preflight strips heading size and weight, which is why they read as body text.
Also fixed inline radio/checkbox groups running together as one string, visible
once the abilities section was legible.

---

### 2026-08-05 — Combobox reopens on click
**Prompt:** Fix the combobox in the component itself: after committing a
selection, clicking the field again did not reopen the option list.
**Files affected:** `frontend/src/components/Combobox.tsx`,
`frontend/src/components/Combobox.test.tsx`,
`frontend/src/features/editor/sections/sections.test.tsx`, `PROMPT_LOG.md`
**Summary:** The list opened only from `onFocus`, but committing an option keeps
focus on the input (options call `preventDefault` on mousedown), so a later click
emitted no focus event and the list stayed shut — same after dismissing with
Escape. Added an `onClick` opener, covered both paths with regression tests
(verified failing without the fix), and simplified the alignment test that had
worked around the bug with a keyboard gesture.

---

### 2026-08-05 — Alignment becomes a catalog dropdown
**Prompt:** In the character editor, alignment should be a dropdown just like race.
**Files affected:** `backend/src/pf_tracker/rules/catalog.py`,
`backend/src/pf_tracker/rules/repository.py`,
`backend/src/pf_tracker/api/v1/rules.py`,
`backend/tests/unit/rules/test_repository.py`,
`backend/tests/unit/rules/test_data_contract.py`,
`backend/tests/integration/test_rules_api.py`, `backend/openapi.json`,
`frontend/src/api/{schema,types,rules}.ts`, `frontend/src/hooks/useRules.ts`,
`frontend/src/features/editor/sections/IdentitySection.tsx`,
`frontend/src/i18n/es.ts`, `frontend/src/test/{catalog,handlers}.ts`,
`frontend/src/features/editor/sections/sections.test.tsx`, `start.sh`,
`PROMPT_LOG.md`
**Summary:** The corpus already carries `alineamiento` (codes plus Spanish
names), so the nine alignments are served from a new `GET /rules/alignments`
catalog endpoint rather than being hardcoded in TypeScript. The editor now uses
the same accent-insensitive `Combobox` as race, persisting the corpus code and
displaying the Spanish name, with a leading entry that clears the optional field.
Also added a port-in-use preflight to `start.sh` after a stale server silently
shadowed the new endpoint.

---

### 2026-08-05 — Raise contrast on buttons and form fields
**Prompt:** Colour contrast is too soft: the Duplicar/Eliminar buttons and the
data-entry fields are almost white and cannot be distinguished. Make them more
evident, with stronger colour contrast.
**Files affected:** `frontend/src/index.css`, `PROMPT_LOG.md`
**Summary:** Secondary buttons and fields were drawn with `--border` (1.23:1
against a white surface, below the 3:1 WCAG 1.4.11 floor) on a white fill.
Added `--border-strong` (4.76:1 light, 5.71:1 dark), `--control-bg` and
`--field-bg`, gave secondary buttons a filled grey face, and moved field styling
to a global `input/select/textarea` rule so no form can ship an invisible field.

---

### 2026-08-05 — Actions must look like buttons, links only for sections
**Prompt:** The "Duplicar" action renders as a link. Every action must render as a
button; only sections may appear as tabs or links.
**Files affected:** `frontend/src/index.css`,
`frontend/src/pages/CharacterPage.tsx`,
`frontend/src/pages/CharacterListPage.test.tsx`, `PROMPT_LOG.md`
**Summary:** Tailwind's preflight had stripped the native button appearance and no
rule replaced it, so every bare `<button>` (Duplicar, Eliminar, Exportar, the
steppers) rendered as plain text and read as a link. Added a base button style
plus primary/compact variants, promoted the "Editar" action to button styling,
and pinned the convention with a regression test.

---

### 2026-08-05 — One-command launcher for non-technical use
**Prompt:** Make the app startable without knowing the toolchain details, and
explain to a non-technical user how to run and use it.
**Files affected:** `start.sh` (new), `PROMPT_LOG.md`
**Summary:** Added `start.sh`, which checks that dependencies are installed,
switches to a Node 20 runtime via nvm when the current Node is too old, and runs
the API and the Vite dev server together, stopping both cleanly on Ctrl+C
(job control + per-child process-group kill, since `npm run` does not forward
signals to Vite). Verified startup and shutdown leave no orphan processes.

---

### 2026-08-05 — Build and verify the existing pf-tracker checkout
**Prompt:** Understand this application and build it: install the toolchain and
dependencies for both stacks, run every quality gate, apply migrations, and boot
the app end to end to confirm it actually works.
**Files affected:** `backend/poetry.toml` (new, `virtualenvs.in-project = true`),
`backend/.env` (new, copied from `.env.example`), `PROMPT_LOG.md` (new).
No source files were modified.
**Summary:** Installed Python 3.14.6 via pyenv and Node 20.11.1 via nvm, installed
both dependency trees, ran the full CI gate green (241 backend tests, 58 frontend
tests, ruff, mypy --strict, eslint, prettier, tsc, coverage 97% backend / 98%
frontend), migrated SQLite, and verified the running stack via the REST API and the
Vite dev server. Found one spec gap: numeric feat modifiers are never emitted.

---

### 2026-08-11 — Skills table: characteristic column, filtered "others" tooltip
**Prompt:** In the character editor's skills table, add a column between Ranks and
the ability-modifier column showing the key characteristic's abbreviation (Int,
Des, Fue, ...); remove the redundant "(ability)" label next to the skill name;
restrict the "others" column's hover tooltip to only the modifiers that make up
`other_modifiers` (excluding ranks and the ability modifier, which already have
their own columns); confirm the total already equals ranks + ability modifier +
others, as guaranteed by the backend (`test_skill_columns_always_sum_to_the_total`)
— no frontend arithmetic was introduced, per the "zero Pathfinder formulas in
TypeScript" rule.
**Files affected:** `backend/src/pf_tracker/domain/derivation.py`,
`backend/src/pf_tracker/schemas/combat_sheet.py`,
`backend/tests/unit/domain/test_derivation_extra.py`, `backend/openapi.json`
(regenerated, gitignored), `frontend/src/api/schema.ts` (regenerated),
`frontend/src/features/editor/sections/SkillsSection.tsx`,
`frontend/src/features/editor/sections/SkillModifiers.tsx`,
`frontend/src/features/editor/sections/SkillsSection.test.tsx`,
`frontend/src/i18n/es.ts`, `frontend/src/index.css`, `frontend/src/test/fixtures.ts`.
**Summary:** Added `SkillResult.other_applied` / `SkillLineDTO.other_breakdown` on
the backend (ranks and ability modifier entries excluded, by identity, from the
already-existing full `breakdown` used by the read-only combat sheet) and wired the
editor's "others" tooltip to the new field; added a "Car." characteristic column
sourced from the skills catalog (not `/derive`, so it renders before the first
derivation); renamed the ability-modifier column header to "Mod." to avoid a label
collision. All backend (434) and frontend (111) tests, mypy, ruff, eslint, and
prettier pass.

---

### 2026-08-11 — Show armor/shield AC bonus and penalties in the equipment section
**Prompt:** In the character editor's equipment section, both the Armadura and
Escudo pickers need to reflect the item's AC bonus and its negative modifiers
(Dex cap, armor check penalty) once one is selected.
**Files affected:** `frontend/src/features/editor/sections/EquipmentSection.tsx`,
`frontend/src/i18n/es.ts`, `frontend/src/index.css`,
`frontend/src/features/editor/sections/sections.test.tsx`,
`frontend/src/features/editor/CharacterEditor.test.tsx`.
**Summary:** Added an `armorSummary()` helper that reads the selected armor/shield's
catalog fields verbatim (`armor_bonus`, `max_dex`, `armor_check_penalty` — no
derivation, so the "no Pathfinder formulas in the frontend" rule still holds) and
shows them as a stat line ("CA +5 · Máx. Des +3 · Penalización -4") both under the
selected item and as a hint on each option in the picker dropdown. Updated the two
existing tests that selected an armor/shield option by exact accessible name, since
the option's name now includes its hint text.

---

### 2026-08-11 — Move derived combat figures into the editor's own section cards
**Prompt:** In the character editor form (not the read-only combat-sheet preview),
show the total AC next to the armor picker in the Equipo card; give the saving
throws their own card right below Características; and add base attack,
initiative, BMC, and DMC to the Características card.
**Files affected:** `frontend/src/features/editor/CharacterEditor.tsx`,
`frontend/src/features/editor/sections/AbilitiesSection.tsx` (+ test),
`frontend/src/features/editor/sections/EquipmentSection.tsx`,
`frontend/src/features/editor/sections/SavesSection.tsx` (new, + test),
`frontend/src/features/editor/sections/sections.test.tsx`, `frontend/src/i18n/es.ts`,
`frontend/src/index.css`.
**Summary:** Threaded `/derive`'s `ac`, `bab`, `initiative`, `cmb`, and `cmd`
down from `CharacterEditor` into the relevant editor sections and rendered them
with the existing `StatBreakdown` component, matching how the read-only
`CombatCard` already shows the same figures — `CombatCard` itself (used both here
as the live preview and in `CharacterPage` during play) was left untouched, so the
numbers are now visible in both places rather than moved. Added a new
`SavesSection` card between Características and Clases y nivel. Fixed two
pre-existing test-selector collisions this surfaced: `StatBreakdown`'s toggle has
no `aria-label` (its accessible name is label + value, so exact-string role
queries silently required a regex once a real value was rendered), and the
editor's live preview now duplicates the "Clase de armadura" label from Equipo, so
`CharacterEditor.test.tsx` needed to scope its query to the preview pane.

---
