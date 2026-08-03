/**
 * Client-side accent-insensitive normalization, mirroring the backend `_norm`:
 * NFD-decompose, strip combining marks, lowercase, trim. Used for fuzzy catalog
 * search so "espada lar" matches "Espada larga".
 */
export function normalize(value: string): string {
  return value
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .trim();
}

/** True when every whitespace-separated token of `query` appears in `text`. */
export function fuzzyMatch(text: string, query: string): boolean {
  const haystack = normalize(text);
  const tokens = normalize(query).split(/\s+/).filter(Boolean);
  return tokens.every((token) => haystack.includes(token));
}
