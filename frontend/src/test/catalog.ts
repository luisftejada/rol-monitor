/**
 * Typed rules-catalog fixtures for the editor tests. Typed against the generated
 * OpenAPI models so a mock that drifts from the contract fails to compile.
 */
import type {
  ArmorDTO,
  ClassSummaryDTO,
  FeatDTO,
  MetaDTO,
  RaceDTO,
  SkillDTO,
  WeaponDTO,
} from "@/api/types";

export const meta: MetaDTO = {
  bonus_types: {
    always_stack: ["esquiva"],
    do_not_stack: ["armadura"],
    penalties: "…",
    note: null,
  },
  abilities: [],
  sizes: [],
  action_types: [],
  units: {},
  point_buy_costs: {
    "7": -4,
    "8": -2,
    "9": -1,
    "10": 0,
    "11": 1,
    "12": 2,
    "13": 3,
    "14": 5,
    "15": 7,
    "16": 10,
    "17": 13,
    "18": 17,
  },
};

export const races: RaceDTO[] = [
  {
    slug: "humano",
    key: "humano",
    name: "Humano",
    size: "Mediano",
    speed_ft: 30,
    ability_modifiers: { cualquiera: 2 },
    type: "humanoide",
    vision: null,
    traits: [],
    languages: { inicio: ["común"], adicionales: [] },
  },
  {
    slug: "mediano",
    key: "mediano",
    name: "Mediano",
    size: "Pequeño",
    speed_ft: 20,
    ability_modifiers: { Des: 2, Car: 2, Fue: -2 },
    type: "humanoide",
    vision: null,
    traits: [],
    languages: { inicio: ["común"], adicionales: [] },
  },
];

export const classes: ClassSummaryDTO[] = [
  {
    slug: "guerrero",
    name: "Guerrero",
    hit_die: "d10",
    skill_ranks_per_level: 2,
    bab_progression: "completo",
    good_saves: ["Fortaleza"],
    proficiencies: "todas las armas sencillas y marciales",
    class_skills: ["Intimidar", "Trepar"],
    is_spellcaster: false,
    is_prestige: false,
    max_level: 20,
  },
  {
    slug: "mago",
    name: "Mago",
    hit_die: "d6",
    skill_ranks_per_level: 2,
    bab_progression: "1/2",
    good_saves: ["Voluntad"],
    proficiencies: "bastón, daga",
    class_skills: ["Saber (arcano)"],
    is_spellcaster: true,
    is_prestige: false,
    max_level: 20,
  },
];

export const skills: SkillDTO[] = [
  {
    slug: "intimidar",
    name: "Intimidar",
    ability: "Car",
    untrained: true,
    armor_check_penalty: false,
    class_for: ["guerrero"],
  },
  {
    slug: "trepar",
    name: "Trepar",
    ability: "Fue",
    untrained: true,
    armor_check_penalty: true,
    class_for: ["guerrero"],
  },
  {
    slug: "acrobacias",
    name: "Acrobacias",
    ability: "Des",
    untrained: true,
    armor_check_penalty: true,
    class_for: ["picaro"],
  },
];

export const feats: FeatDTO[] = [
  {
    slug: "esquiva",
    name: "Esquiva",
    types: ["Combate"],
    prerequisites: null,
    benefit: "+1 CA",
    is_eligible: true,
  },
  {
    slug: "acometer",
    name: "Acometer",
    types: ["Combate"],
    prerequisites: "ataque base +6",
    benefit: "…",
    is_eligible: false,
  },
];

export const weapons: WeaponDTO[] = [
  {
    slug: "espada-larga",
    name: "Espada larga",
    proficiency: "marcial",
    category: "Armas cuerpo a cuerpo a una mano",
    cost: "15 po",
    damage_small: "1d6",
    damage_medium: "1d8",
    critical: [{ threat_range: 19, multiplier: 2 }],
    range_increment: null,
    weight: "4 libras",
    damage_type: "Cor",
    special: null,
  },
];

export const armor: ArmorDTO[] = [
  {
    slug: "cota-de-escamas",
    name: "Cota de escamas",
    category: "intermedia",
    price_gp: 50,
    armor_bonus: 5,
    max_dex: 3,
    armor_check_penalty: -4,
    arcane_spell_failure_pct: 25,
    speed_30: null,
    speed_20: null,
    weight: "30 libras",
  },
  {
    slug: "escudo-pesado-de-acero",
    name: "Escudo pesado de acero",
    category: "escudo",
    price_gp: 20,
    armor_bonus: 2,
    max_dex: null,
    armor_check_penalty: -2,
    arcane_spell_failure_pct: 15,
    speed_30: null,
    speed_20: null,
    weight: "15 libras",
  },
];
