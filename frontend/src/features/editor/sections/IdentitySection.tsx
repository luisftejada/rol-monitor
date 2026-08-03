import type { CharacterCreate } from "@/api/types";
import { Combobox } from "@/components/Combobox";
import { useRaces } from "@/hooks/useRules";
import { t } from "@/i18n";

interface SectionProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
}

export function IdentitySection({ draft, patch }: SectionProps): React.JSX.Element {
  const races = useRaces();
  const raceOptions = (races.data ?? []).map((race) => ({ value: race.slug, label: race.name }));

  return (
    <section aria-labelledby="section-identity" className="editor__section">
      <h2 id="section-identity">{t("editor.section.identity")}</h2>

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

      <label className="field">
        <span>{t("identity.alignment")}</span>
        <input
          value={draft.alignment ?? ""}
          onChange={(event) => patch({ alignment: event.target.value || null })}
        />
      </label>
    </section>
  );
}
