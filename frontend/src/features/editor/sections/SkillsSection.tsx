import type { CharacterCreate, SkillLineDTO } from "@/api/types";
import { SkillModifiers } from "@/features/editor/sections/SkillModifiers";
import { useClasses, useSkills } from "@/hooks/useRules";
import { t } from "@/i18n";
import { signed } from "@/lib/format";

interface SectionProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
  intModifier: number;
  /** Derived lines from `/derive`, by slug. Absent only while the first one loads. */
  derived?: SkillLineDTO[];
}

export function SkillsSection({
  draft,
  patch,
  intModifier,
  derived = [],
}: SectionProps): React.JSX.Element {
  const skills = useSkills();
  const classes = useClasses();

  const classLevels = draft.class_levels ?? [];
  const skillRanks = draft.skill_ranks ?? {};
  const classSlugs = new Set(classLevels.map((entry) => entry.class_slug));
  const totalLevel = classLevels.reduce((sum, entry) => sum + entry.level, 0);

  const available = classLevels.reduce(
    (sum, entry) => {
      const summary = (classes.data ?? []).find((cls) => cls.slug === entry.class_slug);
      const perLevel = Math.max(1, (summary?.skill_ranks_per_level ?? 0) + intModifier);
      return sum + perLevel * entry.level;
    },
    draft.race === "humano" ? totalLevel : 0,
  );

  const spent = Object.values(skillRanks).reduce((sum, ranks) => sum + ranks, 0);
  const bySlug = new Map(derived.map((line) => [line.slug, line]));

  const setRank = (slug: string, ranks: number): void => {
    const next = { ...skillRanks };
    if (ranks <= 0) {
      delete next[slug]; // only non-zero skills are persisted
    } else {
      next[slug] = ranks;
    }
    patch({ skill_ranks: next });
  };

  const isClassSkill = (classFor: string[]): boolean =>
    classFor.some((slug) => classSlugs.has(slug));

  const ordered = [...(skills.data ?? [])].sort((a, b) => {
    const classDelta = Number(isClassSkill(b.class_for)) - Number(isClassSkill(a.class_for));
    return classDelta !== 0 ? classDelta : a.name.localeCompare(b.name);
  });

  return (
    <section aria-labelledby="section-skills" className="editor__section">
      <h2 id="section-skills">{t("editor.section.skills")}</h2>
      <p className="counter" role="status">
        {t("skills.ranks", { spent, available })}
      </p>

      <table className="skills">
        <thead>
          <tr>
            <th scope="col">{t("skills.column.skill")}</th>
            <th scope="col">{t("skills.column.ranks")}</th>
            <th scope="col" title={t("skills.column.characteristic.full")}>
              {t("skills.column.characteristic")}
            </th>
            <th scope="col" title={t("skills.column.ability.full")}>
              {t("skills.column.ability")}
            </th>
            <th scope="col" title={t("skills.column.others.full")}>
              {t("skills.column.others")}
            </th>
            <th scope="col">{t("skills.column.total")}</th>
          </tr>
        </thead>
        <tbody>
          {ordered.map((skill) => {
            const ranks = skillRanks[skill.slug] ?? 0;
            const classSkill = isClassSkill(skill.class_for);
            const line = bySlug.get(skill.slug);
            return (
              <tr key={skill.slug} className={classSkill ? "is-class-skill" : undefined}>
                <th scope="row">
                  {skill.name}
                  {classSkill && <span title={t("skills.classSkill")}> ★</span>}
                </th>
                <td>
                  <span className="stepper">
                    <button
                      type="button"
                      aria-label={t("skills.decrement", { skill: skill.name })}
                      onClick={() => setRank(skill.slug, ranks - 1)}
                    >
                      −
                    </button>
                    <input
                      type="number"
                      aria-label={skill.name}
                      min={0}
                      value={ranks}
                      onChange={(event) => setRank(skill.slug, Number(event.target.value))}
                    />
                    <button
                      type="button"
                      aria-label={t("skills.increment", { skill: skill.name })}
                      onClick={() => setRank(skill.slug, ranks + 1)}
                    >
                      +
                    </button>
                  </span>
                </td>
                <td className="skills__characteristic">{skill.ability}</td>
                {/* Every number here comes from /derive. Deriving any of it in the
                    browser would put game arithmetic in the wrong layer, and the
                    three columns are guaranteed by the backend to sum to the total. */}
                <td className="skills__mod">{line ? signed(line.ability_modifier) : "—"}</td>
                <td className="skills__mod">
                  {line ? <SkillModifiers skill={skill.name} line={line} /> : "—"}
                </td>
                <td className="skills__total">{line ? signed(line.total) : "—"}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
