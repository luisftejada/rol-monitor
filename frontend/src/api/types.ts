/**
 * Convenience aliases over the generated OpenAPI schema. The schema is generated
 * from the backend (`npm run gen:api`); never hand-edit `schema.ts`.
 */
import type { components } from "./schema";

type Schemas = components["schemas"];

export type Health = Schemas["HealthResponse"];
export type CharacterCreate = Schemas["CharacterCreate"];
export type CharacterRead = Schemas["CharacterRead"];
export type CharacterSummary = Schemas["CharacterSummary"];
export type CharacterListResponse = Schemas["CharacterListResponse"];
export type CombatSheetResponse = Schemas["CombatSheetResponse"];
export type ValueBreakdown = Schemas["ValueBreakdown"];
export type BreakdownEntry = Schemas["BreakdownEntry"];
export type SuppressedEntry = Schemas["SuppressedEntry"];
export type ACDTO = Schemas["ACDTO"];
export type AbilityScoreDTO = Schemas["AbilityScoreDTO"];
export type AttackDTO = Schemas["AttackDTO"];
export type SkillLineDTO = Schemas["SkillLineDTO"];
export type SpeedDTO = Schemas["SpeedDTO"];
export type HpDTO = Schemas["HpDTO"];
export type BabDTO = Schemas["BabDTO"];

// Rules catalog
export type MetaDTO = Schemas["MetaDTO"];
export type RaceDTO = Schemas["RaceDTO"];
export type ClassSummaryDTO = Schemas["ClassSummaryDTO"];
export type SkillDTO = Schemas["SkillDTO"];
export type FeatDTO = Schemas["FeatDTO"];
export type WeaponDTO = Schemas["WeaponDTO"];
export type ArmorDTO = Schemas["ArmorDTO"];

// Character editing
export type ClassLevelIn = Schemas["ClassLevelIn"];
export type EquippedArmorIn = Schemas["EquippedArmorIn"];
export type EquippedWeaponIn = Schemas["EquippedWeaponIn"];
