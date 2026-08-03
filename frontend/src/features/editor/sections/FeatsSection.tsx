import type { CharacterCreate } from "@/api/types";
import { Combobox, type ComboboxOption } from "@/components/Combobox";
import { useFeats } from "@/hooks/useRules";
import { t } from "@/i18n";

interface SectionProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
  bab: number;
  abilities: Record<string, number>;
}

export function FeatsSection({ draft, patch, bab, abilities }: SectionProps): React.JSX.Element {
  const ownedFeats = draft.feats ?? [];
  const feats = useFeats({ bab, abilities, owned: ownedFeats });
  const owned = new Set(ownedFeats);

  // Ineligible feats are shown (never hidden) with their unmet prerequisite as a hint,
  // and remain selectable — the GM may be overriding.
  const options: ComboboxOption[] = (feats.data ?? [])
    .filter((feat) => !owned.has(feat.name))
    .map((feat) => ({
      value: feat.name,
      label: feat.name,
      hint: feat.is_eligible
        ? undefined
        : t("feats.ineligible", { prereq: feat.prerequisites ?? "?" }),
    }));

  const add = (name: string): void => {
    if (!owned.has(name)) patch({ feats: [...ownedFeats, name] });
  };

  const remove = (name: string): void => {
    patch({ feats: ownedFeats.filter((feat) => feat !== name) });
  };

  return (
    <section aria-labelledby="section-feats" className="editor__section">
      <h2 id="section-feats">{t("editor.section.feats")}</h2>

      <Combobox
        label={t("feats.add")}
        options={options}
        value={null}
        onChange={add}
        placeholder={t("feats.add")}
      />

      <ul className="owned-feats" aria-label={t("feats.owned")}>
        {ownedFeats.map((feat) => (
          <li key={feat}>
            {feat}
            <button
              type="button"
              aria-label={t("feats.remove", { feat })}
              onClick={() => remove(feat)}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
