import { useMutation } from "@tanstack/react-query";

import { deriveCharacter, levelUpPreview } from "@/api/characters";
import type { CharacterCreate, ClassLevelIn, LevelUpResponse } from "@/api/types";
import { CombatCard } from "@/components/CombatCard";
import { Combobox } from "@/components/Combobox";
import { Modal } from "@/components/Modal";
import { LevelUpDialog } from "@/features/editor/sections/LevelUpDialog";
import { useClasses } from "@/hooks/useRules";
import { t } from "@/i18n";

interface SectionProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
}

export function ClassesSection({ draft, patch }: SectionProps): React.JSX.Element {
  const classes = useClasses();
  const options = (classes.data ?? []).map((cls) => ({ value: cls.slug, label: cls.name }));
  const classLevels = draft.class_levels ?? [];

  const update = (index: number, next: Partial<ClassLevelIn>): void => {
    patch({
      class_levels: classLevels.map((entry, i) => (i === index ? { ...entry, ...next } : entry)),
    });
  };

  const add = (): void => {
    const first = options[0]?.value ?? "guerrero";
    patch({
      class_levels: [
        ...classLevels,
        { class_slug: first, level: 1, is_prestige: false, is_favored: false },
      ],
    });
  };

  const remove = (index: number): void => {
    patch({ class_levels: classLevels.filter((_, i) => i !== index) });
  };

  // Both run against the draft as it stands, so neither needs the character saved
  // and neither changes anything: one reports, the other renders a past copy.
  const preview = useMutation({ mutationFn: (taking: string) => levelUpPreview(draft, taking) });
  const past = useMutation({ mutationFn: (data: CharacterCreate) => deriveCharacter(data) });

  /** Take the level: the class goes up by one — or joins the character at 1 — and
   * the new level gets a hit-point row of its own, waiting to be rolled. Everything
   * else the report lists is a choice, and belongs to the card that owns it. */
  const applyLevel = (report: LevelUpResponse): void => {
    const taken = classLevels.some((entry) => entry.class_slug === report.class_slug);
    const nextLevels = taken
      ? classLevels.map((entry) =>
          entry.class_slug === report.class_slug ? { ...entry, level: entry.level + 1 } : entry,
        )
      : [
          ...classLevels,
          {
            class_slug: report.class_slug,
            level: 1,
            is_prestige: false,
            is_favored: false,
          },
        ];

    patch({
      class_levels: nextLevels,
      hp_per_level: [
        ...(draft.hp_per_level ?? []),
        {
          level: report.total_level_after,
          class_slug: report.class_slug,
          // Level 1 is the die's maximum by rule; anything later waits for a roll.
          value: report.is_first_level ? report.hit_die : 0,
          mode: report.is_first_level ? ("max" as const) : ("roll" as const),
        },
      ],
    });
  };

  const history = draft.level_history ?? [];
  const totalLevel = classLevels.reduce((sum, entry) => sum + entry.level, 0);

  return (
    <section aria-labelledby="section-classes" className="editor__section">
      <h2 id="section-classes">{t("editor.section.classes")}</h2>

      {classLevels.map((entry, index) => (
        <div key={index} className="class-row">
          <Combobox
            label={t("classes.class")}
            options={options}
            value={entry.class_slug}
            onChange={(slug) => update(index, { class_slug: slug })}
          />
          <label className="field field--narrow">
            <span>{t("classes.level")}</span>
            <input
              type="number"
              min={1}
              value={entry.level}
              onChange={(event) => update(index, { level: Number(event.target.value) })}
            />
          </label>
          {classLevels.length > 1 && (
            <button type="button" onClick={() => remove(index)}>
              {t("classes.remove")}
            </button>
          )}
        </div>
      ))}

      <button type="button" onClick={add}>
        {t("classes.add")}
      </button>

      {/* One button per class, because taking the level *is* the choice of class —
          that is what multiclassing is, and asking after the fact would be a second
          dialog for a decision already made. */}
      <div className="level-up__actions">
        {classLevels.map((entry, index) => (
          <button
            key={index}
            type="button"
            className="button"
            onClick={() => preview.mutate(entry.class_slug)}
          >
            {t("levelUp.button", {
              class: options.find((o) => o.value === entry.class_slug)?.label ?? entry.class_slug,
            })}
          </button>
        ))}
      </div>

      <h3>{t("levelUp.history")}</h3>
      <ul className="levels" aria-label={t("levelUp.history")}>
        {history.map((snapshot) => (
          <li key={snapshot.level}>
            <button
              type="button"
              onClick={() => past.mutate(snapshot.data as unknown as CharacterCreate)}
              aria-label={t("levelUp.view", { level: snapshot.level })}
            >
              {t("levelUp.level", { level: snapshot.level })}
            </button>
          </li>
        ))}
        {/* The character as it is now closes the list, so the sequence reads whole. */}
        <li className="levels__current">{t("levelUp.currentLevel", { level: totalLevel })}</li>
      </ul>

      {preview.data && (
        <LevelUpDialog
          report={preview.data as LevelUpResponse}
          onApply={() => {
            applyLevel(preview.data as LevelUpResponse);
            preview.reset();
          }}
          onClose={() => preview.reset()}
        />
      )}
      {past.data && (
        <Modal title={t("levelUp.pastCharacter")} onClose={() => past.reset()}>
          {/* Derived from the copy, so a past level is read with the same card as the
              present one instead of a second, thinner view that could disagree. */}
          <CombatCard name={draft.name ?? ""} sheet={past.data} />
        </Modal>
      )}
    </section>
  );
}
