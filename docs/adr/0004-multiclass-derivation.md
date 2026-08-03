# ADR 0004 — Multiclass derivation: sum per class, BAB by formula, saves by table

- Status: Accepted
- Date: 2026-08-03

## Context

Characters are multiclass from day one (`class_levels: list[ClassLevel]`), and all
prestige classes are entered via multiclass (e.g. Pícaro 6 / Danzarín sombrío 10).
Phase 2 must derive BAB, saves, HP, and skills across an arbitrary mix of base and
prestige classes. Two data facts, verified against the corpus, shape the approach:

- The by-type BAB formulas (`avance.bab_por_tipo`: `completo=nivel`, `3/4=nivel*3//4`,
  `1/2=nivel//2`) reproduce the per-row `bab` for **all 21 classes** — base and
  prestige — with zero mismatches.
- The by-type save formulas (`avance.salvacion_por_tipo`) reproduce base-class rows
  exactly, but **not** prestige rows (141 mismatches): prestige classes ship their
  own CRB save tables, which do not reduce to a single formula.
- Three prestige classes ship with missing progression rows (see docs/assumptions.md).

## Decision

Per `avance.multiclase` ("se suman pg, BAB y salvaciones de cada clase; las
habilidades de clase se acumulan"), derive by summing each class's contribution at
its own level:

- **Total level** = Σ class levels. Feats (odd levels) and ability increments
  (every 4) key off total level.
- **BAB**: sum `base_bab(class, level)` computed from `bab_por_tipo`, then regenerate
  the iterative sequence from the total (one extra attack per full +5 above +1, max
  4). BAB is sourced from the **formula**, which also covers incomplete-data classes.
- **Saves**: sum `base_save(class, level)` read from the **per-row tables** (they are
  authoritative and prestige differs from any formula). This preserves the RAW quirk
  that each class's level-1 good save contributes +2. Base-class formula agreement is
  pinned by a property test.
- **HP**: sum hit dice per class level; **skills**: class-skill sets accumulate
  (union), the +3 class bonus applies if a skill is a class skill for any class, max
  ranks = total level.
- **Prestige `requisitos`**: parsed leniently, surfaced as non-blocking warnings.

For the three prestige classes with missing rows, derive what the corpus supports
(BAB via formula, HP, skills); missing save contributions are treated as 0 and a
`warnings[]` entry is emitted. Nothing is invented. See docs/assumptions.md.

## Consequences

- Every base-class multiclass build is fully and faithfully derivable.
- Prestige builds are derivable where the corpus has data; gaps are explicit, never
  silent.
- BAB and save derivation each have a single source of truth, property-tested.
