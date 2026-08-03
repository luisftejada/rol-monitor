import type { CharacterCreate } from "@/api/types";
import { useClasses, useSkills } from "@/hooks/useRules";
import { t } from "@/i18n";

interface SectionProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
  intModifier: number;
}

export function SkillsSection({ draft, patch, intModifier }: SectionProps): React.JSX.Element {
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
        <tbody>
          {ordered.map((skill) => {
            const ranks = skillRanks[skill.slug] ?? 0;
            const classSkill = isClassSkill(skill.class_for);
            return (
              <tr key={skill.slug} className={classSkill ? "is-class-skill" : undefined}>
                <th scope="row">
                  {skill.name}
                  {classSkill && <span title={t("skills.classSkill")}> ★</span>} ({skill.ability})
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
              </tr>
            );
          })}
        </tbody>
      </table>
    </section>
  );
}
