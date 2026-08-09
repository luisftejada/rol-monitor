import { describe, expect, it } from "vitest";

import { t, type MessageKey } from "@/i18n";

describe("translate", () => {
  it("interpolates named placeholders", () => {
    expect(t("skills.ranks", { spent: 2, available: 4 })).toBe("Rangos: 2 / 4");
  });

  it("picks the singular form only for a count of one", () => {
    expect(t("sheet.skill.ranks", { count: 1 })).toBe("1 rango");
    expect(t("sheet.skill.ranks", { count: 2 })).toBe("2 rangos");
    // Spanish takes the plural at zero, which is why the rule is `=== 1` and not
    // `> 1`: "0 rango" would be wrong.
    expect(t("sheet.skill.ranks", { count: 0 })).toBe("0 rangos");
  });

  it("falls back to the key itself when a message is missing", () => {
    // A visible key beats a blank space: the gap shows up in review instead of
    // reading as an intentionally empty label.
    expect(t("no.existe" as MessageKey)).toBe("no.existe");
  });

  it("leaves a placeholder alone when no value is given for it", () => {
    expect(t("skills.ranks", { spent: 2 })).toBe("Rangos: 2 / {available}");
  });
});
