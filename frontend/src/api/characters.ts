import { apiDelete, apiGet, apiPost } from "./client";
import type {
  CharacterCreate,
  CharacterListResponse,
  CharacterRead,
  CombatSheetResponse,
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
  return apiDelete(`/characters/${id}`);
}
