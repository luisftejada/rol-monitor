# Rules assumptions

When the corpus is ambiguous, or a `beneficio_resumen` is truncated (many feat
summaries end in `…`), we implement the mechanically obvious reading and record it
here rather than guessing silently.

Format: one entry per assumption, newest first.

| Date | Area | Assumption | Rationale |
| ---- | ---- | ---------- | --------- |
| 2026-08-03 | Prestige classes | Three prestige classes ship with incomplete `progresion` in the vendored corpus: `cronista_pathfinder` and `danzarin_sombrio` have 0 rows, `duelista` has 1. The catalog exposes them with `max_level` equal to the rows present; requesting a progression level beyond that returns 404. | The corpus is vendored, read-only, and the PC module is the milestone; prestige/NPC support is secondary. We surface what exists rather than inventing missing rows. A data-contract test pins the known-incomplete set so any change is caught. |
