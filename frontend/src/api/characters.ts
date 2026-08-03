import { apiDelete, apiGet, apiPatch, apiPost, apiPut } from "./client";
import type {
  CharacterCreate,
  CharacterListResponse,
  CharacterPatch,
  CharacterRead,
  CombatSheetResponse,
  ConditionUpdate,
  ModifierCreate,
  ModifierPatch,
} from "./types";

export interface ListParams {
  limit?: number;
  offset?: number;
  search?: string;
}

export function getCharacters(params: ListParams = {}): Promise<CharacterListResponse> {
  const query = new URLSearchParams();
  if (params.limit !== undefined) query.set("limit", String(params.limit));
  if (params.offset !== undefined) query.set("offset", String(params.offset));
  if (params.search) query.set("search", params.search);
  const suffix = query.toString();
  return apiGet<CharacterListResponse>(`/characters${suffix ? `?${suffix}` : ""}`);
}

export function getCharacter(id: string): Promise<CharacterRead> {
  return apiGet<CharacterRead>(`/characters/${id}`);
}

export function createCharacter(body: CharacterCreate): Promise<CharacterRead> {
  return apiPost<CharacterRead>("/characters", body);
}

export function updateCharacter(id: string, body: CharacterCreate): Promise<CharacterRead> {
  return apiPut<CharacterRead>(`/characters/${id}`, body);
}

export function getCombatSheet(id: string): Promise<CombatSheetResponse> {
  return apiGet<CombatSheetResponse>(`/characters/${id}/combat-sheet`);
}

export function deriveCharacter(body: CharacterCreate): Promise<CombatSheetResponse> {
  return apiPost<CombatSheetResponse>("/derive", body);
}

export function duplicateCharacter(id: string): Promise<CharacterRead> {
  return apiPost<CharacterRead>(`/characters/${id}/duplicate`);
}

export function deleteCharacter(id: string): Promise<void> {
  return apiDelete<void>(`/characters/${id}`);
}

export function patchCharacter(id: string, body: CharacterPatch): Promise<CharacterRead> {
  return apiPatch<CharacterRead>(`/characters/${id}`, body);
}

// --- combat tracking ---
export function addModifier(id: string, body: ModifierCreate): Promise<CharacterRead> {
  return apiPost<CharacterRead>(`/characters/${id}/modifiers`, body);
}

export function patchModifier(
  id: string,
  modifierId: string,
  body: ModifierPatch,
): Promise<CharacterRead> {
  return apiPatch<CharacterRead>(`/characters/${id}/modifiers/${modifierId}`, body);
}

export function removeModifier(id: string, modifierId: string): Promise<CharacterRead> {
  return apiDelete<CharacterRead>(`/characters/${id}/modifiers/${modifierId}`);
}

export function setCondition(id: string, body: ConditionUpdate): Promise<CharacterRead> {
  return apiPost<CharacterRead>(`/characters/${id}/conditions`, body);
}

export function tickRounds(id: string, rounds: number): Promise<CharacterRead> {
  return apiPost<CharacterRead>(`/characters/${id}/tick`, { rounds });
}
