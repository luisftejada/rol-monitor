import { es, type MessageKey } from "./es";

const catalogs = { es } as const;

export type Locale = keyof typeof catalogs;

export const DEFAULT_LOCALE: Locale = "es";

/**
 * Translate a message key for the active locale. Interpolates `{name}`-style
 * placeholders from `params`. Missing keys fall back to the key itself so a
 * gap is visible rather than silently blank.
 */
export function translate(
  key: MessageKey,
  params?: Record<string, string | number>,
  locale: Locale = DEFAULT_LOCALE,
): string {
  const template: string = catalogs[locale][key] ?? key;
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in params ? String(params[name]) : match,
  );
}

/** Convenience alias mirroring the common `t()` idiom. */
export const t = translate;

export type { MessageKey };
