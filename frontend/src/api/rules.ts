import { apiGet } from "./client";
import type {
  ArmorDTO,
  ClassSummaryDTO,
  FeatDTO,
  MetaDTO,
  RaceDTO,
  SkillDTO,
  WeaponDTO,
} from "./types";

export function getMeta(): Promise<MetaDTO> {
  return apiGet<MetaDTO>("/rules/meta");
}

export function getRaces(): Promise<RaceDTO[]> {
  return apiGet<RaceDTO[]>("/rules/races");
}

export function getClasses(includePrestige = false): Promise<ClassSummaryDTO[]> {
  return apiGet<ClassSummaryDTO[]>(
    `/rules/classes${includePrestige ? "?include_prestige=true" : ""}`,
  );
}

export function getSkills(): Promise<SkillDTO[]> {
  return apiGet<SkillDTO[]>("/rules/skills");
}

export interface FeatParams {
  bab?: number;
  abilities?: Record<string, number>;
  owned?: string[];
  type?: string;
}

export function getFeats(params: FeatParams = {}): Promise<FeatDTO[]> {
  const query = new URLSearchParams();
  if (params.bab !== undefined) query.set("bab", String(params.bab));
  for (const [abbr, score] of Object.entries(params.abilities ?? {})) {
    query.append("abilities", `${abbr}:${score}`);
  }
  for (const owned of params.owned ?? []) query.append("owned", owned);
  if (params.type) query.set("type", params.type);
  const suffix = query.toString();
  return apiGet<FeatDTO[]>(`/rules/feats${suffix ? `?${suffix}` : ""}`);
}

export function getWeapons(): Promise<WeaponDTO[]> {
  return apiGet<WeaponDTO[]>("/rules/weapons");
}

export function getArmor(): Promise<ArmorDTO[]> {
  return apiGet<ArmorDTO[]>("/rules/armor");
}
