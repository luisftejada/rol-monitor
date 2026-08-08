# Corpus provenance

How the rules corpus under `backend/data/` came to say what it says. Nothing here is
loaded by the application: these are the working documents behind corpus changes,
kept so a number on the sheet can be traced back to a page of the manual.

| File | What it is |
| ---- | ---------- |
| `INVENTARIO_dotes_fuera_de_progresion.md` | Sweep of all 577 pages for feats granted outside `clases.<slug>.progresion`, with page citations and two corrections to an earlier report. |
| `DISENO_dominios_talentos.md` | Proposed schema for domains, arcane schools and rogue talents. A design, not applied. |
| `propuesta_esquema.yaml` | Reference fragment for that design. Validates against the real corpus; **not a patch** — do not paste it in. |
| `barrido.py` | The throwaway extraction script behind the inventory. Provenance only; it needs PDF column dumps that are not vendored, so it does not run from here. |

The corpus itself stays vendored and read-only in `backend/data/`, per CLAUDE.md.

## Applied from the inventory

| Date | What | Where |
| ---- | ---- | ----- |
| 2026-08-08 | Prestige-class bonus feats: `caballero_arcano` (1/5/9, p. 380) and `discipulo_del_dragon` (2/5/8, p. 387). The disciple points at the existing draconic bloodline list through a new `opcion` key rather than duplicating it. `maestro_del_saber` was left out on purpose — its feats hang off a *secret*, which is a choice, not a level. | `clases_de_prestigio.{caballero_arcano,discipulo_del_dragon}.dotes_adicionales` |

Still open from the inventory: automatic proficiencies (§4, five feats, they unlock
chained prerequisite validation), and the choice-gated axes — domains, arcane
schools, rogue talents and the lore master's secrets — which wait on their own
subsystems (`DISENO_dominios_talentos.md`).

## Known corpus errors, not yet corrected

| Where | Says | Manual says | Impact today |
| ----- | ---- | ----------- | ------------ |
| `clases.explorador.competencias` | "armaduras ligeras y escudos (no pavés)" | light **and medium** armour (p. 55, confirmed p. 121) | None. Armour proficiency is not modelled — `_armor_slot` never sees the character — and the string is only read to match *weapon* proficiency, where "sencillas y marciales" still matches. It starts to matter the day non-proficient armour penalises attacks. |

Fold these into the next corpus errand rather than spending a PDF session on them
alone.
