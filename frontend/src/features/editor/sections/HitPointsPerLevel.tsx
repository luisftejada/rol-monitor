import type { CharacterCreate, HpLevelIn } from "@/api/types";
import { useClasses } from "@/hooks/useRules";
import { t } from "@/i18n";

interface HitPointsPerLevelProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
}

/**
 * What each level contributed to hit points, and how it was decided.
 *
 * The value is not typed in: level 1 takes the die's maximum by rule, and later
 * levels come from one of the two rolls. Leaving it editable invited a number the
 * rules do not allow, so the field shows the result instead of asking for it.
 *
 * The die and the floor under a "never roll badly" roll both arrive from the backend
 * — they are rules figures. The roll happens here, because a random number is not a
 * Pathfinder formula.
 *
 * The Constitution modifier is deliberately absent: it applies per level and is
 * derived from the score, so it follows a belt of Constitution instead of going stale.
 */
export function HitPointsPerLevel({ draft, patch }: HitPointsPerLevelProps): React.JSX.Element {
  const classes = useClasses();
  const bySlug = new Map((classes.data ?? []).map((cls) => [cls.slug, cls]));
  const classLevels = draft.class_levels ?? [];
  const totalLevel = classLevels.reduce((sum, entry) => sum + entry.level, 0);
  const entries = draft.hp_per_level ?? [];

  const defaultClass = classLevels[0]?.class_slug ?? "";
  const rowFor = (level: number): HpLevelIn =>
    entries.find((entry) => entry.level === level) ?? {
      level,
      class_slug: defaultClass,
      value: 0,
      mode: "manual",
    };

  const write = (level: number, changes: Partial<HpLevelIn>): void => {
    const existing = rowFor(level);
    const next = entries.filter((entry) => entry.level !== level);
    next.push({ ...existing, ...changes });
    next.sort((a, b) => a.level - b.level);
    patch({ hp_per_level: next });
  };

  return (
    <div className="hp-levels">
      <h3>{t("hp.perLevel")}</h3>
      <table>
        <thead>
          <tr>
            <th scope="col">{t("classes.level")}</th>
            <th scope="col">{t("classes.class")}</th>
            <th scope="col">{t("hp.die")}</th>
            <th scope="col">{t("hp.value")}</th>
            <th scope="col">{t("hp.roll")}</th>
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: totalLevel }, (_, index) => {
            const level = index + 1;
            const row = rowFor(level);
            const cls = bySlug.get(row.class_slug);
            const faces = cls?.hit_die_faces ?? 0;
            const isFirst = level === 1;
            // Until the class catalog lands there is no die, and a "0" would read as
            // a rolled zero rather than as "not known yet".
            const shown = isFirst ? faces || null : row.value || null;

            return (
              <tr key={level}>
                <th scope="row">{level}</th>
                <td>
                  <select
                    aria-label={t("hp.classFor", { level })}
                    value={row.class_slug}
                    onChange={(event) => write(level, { class_slug: event.target.value })}
                  >
                    {classLevels.map((entry) => (
                      <option key={entry.class_slug} value={entry.class_slug}>
                        {bySlug.get(entry.class_slug)?.name ?? entry.class_slug}
                      </option>
                    ))}
                  </select>
                </td>
                <td className="hp-levels__die">{cls ? `1d${faces}` : "—"}</td>
                <td>
                  <output aria-label={t("hp.valueFor", { level })}>{shown ?? "—"}</output>
                  {isFirst && <span className="hp-levels__note">{t("hp.firstLevel")}</span>}
                </td>
                <td>
                  {/* Level 1 has no roll to make: it is the die's maximum by rule. */}
                  {!isFirst && faces > 0 && (
                    <>
                      <button
                        type="button"
                        aria-label={t("hp.rollFor", { level })}
                        onClick={() => write(level, { value: roll(faces), mode: "roll" })}
                      >
                        {t("hp.rollDie", { die: faces })}
                      </button>
                      <button
                        type="button"
                        aria-label={t("hp.rollFlooredFor", { level })}
                        onClick={() =>
                          write(level, {
                            // The floor is the backend's; taking the better of two
                            // numbers is arithmetic, not a rule.
                            value: Math.max(roll(faces), cls?.hit_points_floor ?? 1),
                            mode: "floored",
                          })
                        }
                      >
                        {t("hp.rollFloored", { floor: cls?.hit_points_floor ?? 0 })}
                      </button>
                    </>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

/** A plain die roll. Randomness, not a rule — which is why it lives here. */
function roll(faces: number): number {
  return Math.floor(Math.random() * faces) + 1;
}
