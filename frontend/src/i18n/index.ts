import { es, type MessageKey } from "./es";

const catalogs = { es } as const;

export type Locale = keyof typeof catalogs;

export const DEFAULT_LOCALE: Locale = "es";

/**
 * Translate a message key for the active locale. Interpolates `{name}`-style
 * placeholders from `params`. Missing keys fall back to the key itself so a
 * gap is visible rather than silently blank.
 *
 * A template may carry two forms separated by `|` — `"{count} rango|{count} rangos"`
 * — and the one matching `params.count` is used. Keeping that here rather than
 * writing `n === 1 ? … : …` at each call site is what stops a plural rule from being
 * scattered through components that have no business knowing Spanish grammar.
 */
export function translate(
  key: MessageKey,
  params?: Record<string, string | number>,
  locale: Locale = DEFAULT_LOCALE,
): string {
  let template: string = catalogs[locale][key] ?? key;

  if (template.includes("|")) {
    const [one = "", other = ""] = template.split("|");
    template = Number(params?.count) === 1 ? one : other;
  }

  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (match, name: string) =>
    name in params ? String(params[name]) : match,
  );
}

/** Convenience alias mirroring the common `t()` idiom. */
export const t = translate;

export type { MessageKey };
