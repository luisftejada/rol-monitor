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
export type LevelUpResponse = Schemas["LevelUpResponse"];
export type LevelSnapshotIn = Schemas["LevelSnapshotIn"];
export type HpLevelIn = Schemas["HpLevelIn"];

// Rules catalog
export type MetaDTO = Schemas["MetaDTO"];
export type ItemSlotDTO = Schemas["ItemSlotDTO"];
export type MagicItemIn = Schemas["MagicItemIn"];
export type AlignmentDTO = Schemas["AlignmentDTO"];
export type RaceDTO = Schemas["RaceDTO"];
export type ClassSummaryDTO = Schemas["ClassSummaryDTO"];
export type SkillDTO = Schemas["SkillDTO"];
export type FeatDTO = Schemas["FeatDTO"];
export type FeatBudgetDTO = Schemas["FeatBudgetDTO"];
export type WeaponDTO = Schemas["WeaponDTO"];
export type ArmorDTO = Schemas["ArmorDTO"];

export type ConditionDTO = Schemas["ConditionDTO"];

// Character editing
export type CharacterPatch = Schemas["CharacterPatch"];
export type ClassLevelIn = Schemas["ClassLevelIn"];
export type EquippedArmorIn = Schemas["EquippedArmorIn"];
export type EquippedWeaponIn = Schemas["EquippedWeaponIn"];
export type ModifierIn = Schemas["ModifierIn"];
export type ActiveEffectIn = Schemas["ActiveEffectIn"];
export type StancesIn = Schemas["StancesIn"];

// Combat tracking
export type ModifierCreate = Schemas["ModifierCreate"];
export type ModifierPatch = Schemas["ModifierPatch"];
export type ConditionUpdate = Schemas["ConditionUpdate"];
export type TickRequest = Schemas["TickRequest"];
