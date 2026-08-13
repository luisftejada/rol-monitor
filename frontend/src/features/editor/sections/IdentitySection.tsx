import type { CharacterCreate } from "@/api/types";
import { Combobox } from "@/components/Combobox";
import { useAlignments, useRaces } from "@/hooks/useRules";
import { t } from "@/i18n";

interface SectionProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
}

export function IdentitySection({ draft, patch }: SectionProps): React.JSX.Element {
  const races = useRaces();
  const raceOptions = (races.data ?? []).map((race) => ({ value: race.slug, label: race.name }));

  const alignments = useAlignments();
  // Alignment is optional, so the list leads with an entry that clears it — unlike
  // race, which every character must have.
  const alignmentOptions = [
    { value: "", label: t("identity.alignment.none") },
    ...(alignments.data ?? []).map((alignment) => ({
      value: alignment.code,
      label: alignment.name,
      hint: alignment.code,
    })),
  ];

  return (
    <section aria-labelledby="section-identity" className="editor__section">
      <h2 id="section-identity">{t("editor.section.identity")}</h2>

      <div className="field-grid">
        <label className="field">
          <span>{t("identity.name")}</span>
          <input value={draft.name} onChange={(event) => patch({ name: event.target.value })} />
        </label>

        <label className="field">
          <span>{t("identity.player")}</span>
          <input
            value={draft.player_name ?? ""}
            onChange={(event) => patch({ player_name: event.target.value || null })}
          />
        </label>

        <Combobox
          label={t("identity.race")}
          options={raceOptions}
          value={draft.race}
          onChange={(race) => patch({ race, racial_bonus_choices: {} })}
        />

        <Combobox
          label={t("identity.alignment")}
          options={alignmentOptions}
          value={draft.alignment ?? null}
          onChange={(alignment) => patch({ alignment: alignment || null })}
        />
      </div>
    </section>
  );
}
