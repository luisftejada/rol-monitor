/**
 * Typed test fixtures. Typing them with the generated OpenAPI models means a mock
 * that drifts from the backend contract fails to compile.
 */
import type {
  BreakdownEntry,
  CharacterListResponse,
  CharacterRead,
  CharacterSummary,
  CombatSheetResponse,
  SuppressedEntry,
  ValueBreakdown,
} from "@/api/types";

export function value(
  total: number,
  breakdown: BreakdownEntry[] = [],
  suppressed: SuppressedEntry[] = [],
): ValueBreakdown {
  return { total, breakdown, suppressed };
}

export const fighterSummary: CharacterSummary = {
  id: "char-1",
  name: "Aldous",
  player_name: "Ana",
  kind: "pc",
  classes: "Guerrero 1",
  total_level: 1,
  max_hp: 12,
  current_hp: 12,
  armor_class: 18,
  touch_ac: 11,
  flat_footed_ac: 17,
  initiative: 1,
  fortitude: 4,
  reflex: 1,
  will: 1,
  updated_at: "2026-08-03T00:00:00Z",
};

// Response models include every default-valued field, so a full document is built.
const characterDefaults = {
  kind: "pc",
  name: "Aldous",
  race: "humano",
  class_levels: [{ class_slug: "guerrero", level: 1, is_prestige: false, is_favored: false }],
  base_scores: { Fue: 15, Des: 13, Con: 14, Int: 10, Sab: 12, Car: 8 },
  racial_bonus_choices: { Fue: 2 },
  ability_damage: {},
  level_ability_increments: {},
  max_hp: 12,
  current_hp: 12,
  temporary_hp: 0,
  nonlethal_damage: 0,
  hp_roll_mode: "manual",
  skill_ranks: {},
  skill_misc_modifiers: {},
  feats: [],
  feat_options: {},
  weapons: [],
  natural_armor_bonus: 0,
  deflection_bonus: 0,
  other_ac_modifiers: 0,
  active_conditions: [],
  active_effects: [],
  modifiers: [],
  stances: {
    charge: false,
    fighting_defensively: false,
    total_defense: false,
    flanking: false,
    higher_ground: false,
  },
  initiative_misc: 0,
  is_flat_footed: false,
  dexterity_denied: false,
} satisfies Partial<CharacterRead>;

export const fighterCharacter: CharacterRead = {
  ...characterDefaults,
  id: "char-1",
  created_at: "2026-08-03T00:00:00Z",
  updated_at: "2026-08-03T00:00:00Z",
};

export const trackedCharacter: CharacterRead = {
  ...fighterCharacter,
  current_hp: 12,
  max_hp: 12,
  active_conditions: ["fatigado"],
  modifiers: [
    {
      id: "mod-1",
      target: "ALL_ATTACKS",
      value: 1,
      bonus_type: "moral",
      source: "Bendecir",
      source_kind: "spell",
      condition: null,
      is_active: true,
      expires_in_rounds: 3,
    },
  ],
};

export const fighterSheet: CombatSheetResponse = {
  abilities: {
    Fue: { score: 17, modifier: 3, base: 15, racial: 2, level_increment: 0, damage: 0 },
    Des: { score: 13, modifier: 1, base: 13, racial: 0, level_increment: 0, damage: 0 },
    Con: { score: 14, modifier: 2, base: 14, racial: 0, level_increment: 0, damage: 0 },
    Int: { score: 10, modifier: 0, base: 10, racial: 0, level_increment: 0, damage: 0 },
    Sab: { score: 12, modifier: 1, base: 12, racial: 0, level_increment: 0, damage: 0 },
    Car: { score: 8, modifier: -1, base: 8, racial: 0, level_increment: 0, damage: 0 },
  },
  ac: {
    total: 18,
    touch: 11,
    flat_footed: 17,
    max_dex_cap: 3,
    breakdown: [
      { label: "base", value: 10, type: null, source: "base" },
      { label: "Cota de escamas", value: 5, type: "armadura", source: "armor" },
      { label: "Escudo pesado de acero", value: 2, type: "escudo", source: "shield" },
      { label: "Destreza", value: 1, type: null, source: "ability" },
    ],
    suppressed: [
      {
        label: "Escudo de fe",
        value: 1,
        type: "deflexión",
        reason: "superado por Anillo de protección +2",
      },
    ],
  },
  saves: {
    Fortaleza: value(4, [{ label: "Base (clases)", value: 2, type: null, source: "class" }]),
    Reflejos: value(1),
    Voluntad: value(1),
  },
  bab: { total: 1, iteratives: [1] },
  initiative: value(1),
  cmb: value(4),
  cmd: value(15),
  attacks: [
    {
      weapon: "Espada larga",
      is_ranged: false,
      attack_line: "+4",
      attack: value(4, [
        { label: "Ataque base", value: 1, type: null, source: "base" },
        { label: "Fue", value: 3, type: null, source: "ability" },
      ]),
      damage_expression: "1d8+3",
      damage: value(3, [{ label: "Fue", value: 3, type: null, source: "ability" }]),
      threat_range: 19,
      crit_multiplier: 2,
      damage_type: "Cor",
      range_increment: null,
      is_proficient: true,
      notes: ["Crítico agotador: tu oponente queda exhausto."],
    },
  ],
  skills: [
    {
      slug: "intimidar",
      name: "Intimidar",
      ability: "Car",
      // 1 rank − 1 Charisma + 3 class skill. The three columns sum to the total,
      // which is the invariant the backend guarantees and the UI relies on.
      total: 3,
      ranks: 1,
      ability_modifier: -1,
      other_modifiers: 3,
      is_class_skill: true,
      untrained_violation: false,
      breakdown: [
        { label: "Habilidad de clase", value: 3, type: null, source: "class" },
        { label: "Rangos", value: 1, type: null, source: "class" },
        { label: "Carisma", value: -1, type: null, source: "ability" },
      ],
      suppressed: [],
    },
  ],
  speed: { base_ft: 30, final_ft: 20, reductions: ["armadura intermedia/pesada"] },
  armor_check_penalty: -6,
  arcane_spell_failure: 40,
  hp: { max: 12, current: 12, temporary: 0, nonlethal: 0 },
  carrying_capacity: {},
  feats: {
    available: 2,
    spent: 1,
    granted: ["Impacto sin arma mejorado"],
    slots: [
      { level: 1, source: "base", choice: "libre", types: [] },
      { level: 1, source: "Humano", choice: "libre", types: [] },
    ],
    lists: {},
    list_notes: {},
  },
  warnings: [],
};

export const listResponse: CharacterListResponse = {
  items: [fighterSummary],
  total: 1,
  limit: 50,
  offset: 0,
};
