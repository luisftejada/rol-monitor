import type { CharacterCreate, ClassLevelIn } from "@/api/types";
import { Combobox } from "@/components/Combobox";
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
    </section>
  );
}
