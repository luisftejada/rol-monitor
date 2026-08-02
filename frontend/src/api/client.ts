/**
 * Minimal fetch wrapper for the pf-tracker API. Typed response models are
 * generated from the OpenAPI schema in later phases; this base client stays
 * hand-written and tiny.
 */
const API_BASE = "/api/v1";

export async function apiGet<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`);
  }
  return (await response.json()) as T;
}
