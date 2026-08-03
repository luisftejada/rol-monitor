# Rules assumptions

When the corpus is ambiguous, or a `beneficio_resumen` is truncated (many feat
summaries end in `…`), we implement the mechanically obvious reading and record it
here rather than guessing silently.

Format: one entry per assumption, newest first.

| Date | Area | Assumption | Rationale |
| ---- | ---- | ---------- | --------- |
| 2026-08-03 | Multiclass saves | Prestige classes use their own CRB save tables, which do not match the by-type save formula (verified: base classes 0 mismatches, prestige 141). Base saves are therefore sourced from the per-row progression tables, and BAB from the by-type formula (which matches all 21 classes). See ADR 0004. | The by-type formulas are authoritative for BAB everywhere but only for base-class saves; prestige save rows are the only correct source. |
| 2026-08-03 | Prestige classes | Three prestige classes ship with incomplete `progresion` in the vendored corpus: `cronista_pathfinder` and `danzarin_sombrio` have 0 rows, `duelista` has only its level-10 row. The catalog exposes them with `max_level` equal to the highest defined level; requesting a level without a row returns 404. In derivation they contribute BAB (via formula), HP, and skills; missing save contributions are treated as 0 and a `warnings[]` entry is emitted. Nothing is invented. | The corpus is vendored, read-only, and the PC module is the milestone; prestige/NPC support is secondary. We surface what exists rather than inventing missing rows. A data-contract test pins the known-incomplete set so any change is caught. |
