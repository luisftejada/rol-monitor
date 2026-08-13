import { Link, useParams } from "react-router-dom";

import { CombatCard } from "@/components/CombatCard";
import { CombatTracker } from "@/features/tracker/CombatTracker";
import { ExportButton } from "@/features/io/ExportButton";
import { useCharacter, useCombatSheet } from "@/hooks/useCharacters";
import { t } from "@/i18n";

export function CharacterPage(): React.JSX.Element {
  const { id = "" } = useParams();
  const character = useCharacter(id);
  const sheet = useCombatSheet(id);

  return (
    <section>
      <p className="page-actions">
        <Link to="/">← {t("common.back")}</Link>
        {character.data && (
          <Link className="button" to={`/characters/${id}/edit`}>
            {t("editor.edit")}
          </Link>
        )}
        {character.data && <ExportButton id={id} name={character.data.name} />}
      </p>

      {(character.isPending || sheet.isPending) && <p role="status">{t("common.loading")}</p>}

      {(character.isError || sheet.isError) && (
        <div role="alert">
          <p>{t("common.error")}</p>
          <button
            type="button"
            onClick={() => {
              void character.refetch();
              void sheet.refetch();
            }}
          >
            {t("common.retry")}
          </button>
        </div>
      )}

      {character.data && sheet.data && (
        <div className="combat-view">
          <CombatCard
            name={character.data.name}
            sheet={sheet.data}
            hiddenAttackLines={character.data.hidden_attack_lines}
          />
          <CombatTracker character={character.data} />
        </div>
      )}
    </section>
  );
}
