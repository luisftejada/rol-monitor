import type { CharacterCreate } from "@/api/types";

/** Ability order used across the editor (matches the corpus ability list). */
export const ABILITY_ORDER = ["Fue", "Des", "Con", "Int", "Sab", "Car"] as const;

/** The standard array preset (a common convention, offered as a UI starting point). */
export const STANDARD_ARRAY = [15, 14, 13, 12, 10, 8] as const;

/** Default point-buy budget; the editor lets the GM raise or lower it per table. */
export const POINT_BUY_BUDGET = 20;

/**
 * A fresh draft: a level-1 human fighter with the standard array, mirroring the
 * backend's create defaults, so the live combat card is never empty.
 */
export function defaultDraft(): CharacterCreate {
  return {
    kind: "pc",
    name: "Nuevo personaje",
    player_name: null,
    race: "humano",
    alignment: null,
    size: null,
    speed_ft: null,
    notes: null,
    portrait_url: null,
    class_levels: [{ class_slug: "guerrero", level: 1, is_prestige: false, is_favored: false }],
    base_scores: { Fue: 15, Des: 14, Con: 13, Int: 12, Sab: 10, Car: 8 },
    racial_bonus_choices: {},
    ability_damage: {},
    level_ability_increments: {},
    max_hp: 0,
    current_hp: 0,
    temporary_hp: 0,
    nonlethal_damage: 0,
    hp_roll_mode: "manual",
    skill_ranks: {},
    skill_misc_modifiers: {},
    feats: [],
    feat_options: {},
    armor: null,
    shield: null,
    weapons: [],
    natural_armor_bonus: 0,
    deflection_bonus: 0,
    other_ac_modifiers: 0,
    load_carried_lb: null,
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
  };
}
