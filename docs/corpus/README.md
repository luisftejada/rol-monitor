# Corpus provenance

How the rules corpus under `backend/data/` came to say what it says. Nothing here is
loaded by the application: these are the working documents behind corpus changes,
kept so a number on the sheet can be traced back to a page of the manual.

| File | What it is |
| ---- | ---------- |
| `INVENTARIO_dotes_fuera_de_progresion.md` | Sweep of all 577 pages for feats granted outside `clases.<slug>.progresion`, with page citations and two corrections to an earlier report. |
| `DISENO_dominios_talentos.md` | Proposed schema for domains, arcane schools and rogue talents. A design, not applied. |
| `propuesta_esquema.yaml` | Reference fragment for that design. Validates against the real corpus; **not a patch** — do not paste it in. |
| `barrido.py` | The throwaway extraction script behind the inventory. Provenance only; it needs PDF column dumps, so it wants the manual present (below). |

The corpus itself stays vendored and read-only in `backend/data/`, per CLAUDE.md.

## Checking a claim against the manual

Put the PDF at `backend/data/*.pdf` — it is **gitignored**, being a ~90 MB commercial
book (© Devir Iberia). The YAML derived from it is what this repo vendors.

Printed page = PDF page − 1. `pdftotext -f N -l N file.pdf -` is enough for most
pages; the two-column layout interleaves paragraphs, so when that matters, dump a
range and grep for the sentence rather than trusting line adjacency. Cropping with
`-x/-W` does not work on this file's geometry.

## Applied from the inventory

| Date | What | Where |
| ---- | ---- | ----- |
| 2026-08-09 | Automatic proficiencies (§4): the five armour/shield feats granted as `fija` slots by the eight classes that get them, 24 entries. The two weapon proficiencies stay prose — the manual grants armour "como dote adicional" but says only that a class "es competente con" simple and martial weapons. | `clases.<slug>.dotes_adicionales` |
| 2026-08-08 | Prestige-class bonus feats: `caballero_arcano` (1/5/9, p. 380) and `discipulo_del_dragon` (2/5/8, p. 387). The disciple points at the existing draconic bloodline list through a new `opcion` key rather than duplicating it. `maestro_del_saber` was left out on purpose — its feats hang off a *secret*, which is a choice, not a level. | `clases_de_prestigio.{caballero_arcano,discipulo_del_dragon}.dotes_adicionales` |

Still open from the inventory: the choice-gated axes — domains, arcane schools, rogue
talents and the lore master's secrets — which wait on their own subsystems
(`DISENO_dominios_talentos.md`), and the animal companion's `Ataque múltiple`, which
is not in the core feat list at all.

## Corrected corpus errors

| Date | Where | Said | Manual says |
| ---- | ----- | ---- | ----------- |
| 2026-08-09 | `clases.explorador.competencias` | "armaduras ligeras y escudos (no pavés)" | light **and medium** (p. 55, confirmed by the feat's Especial on p. 121) |
| 2026-08-09 | `clases.clerigo.competencias` | "todas las armaduras y escudos (no pavés)" | light and medium only (p. 40; heavy armour's Especial on p. 121 lists only fighters and paladins) |

Both were found by cross-checking every class' "Competencia con armas y armaduras"
paragraph against the five feats' "Especial" lines — the two agree on all 11 classes,
which is what makes the check worth repeating for any future proficiency work. A test
pins both corrections.
