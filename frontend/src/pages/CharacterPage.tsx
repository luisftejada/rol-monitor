import { Link, useParams } from "react-router-dom";

import { CombatCard } from "@/components/CombatCard";
import { useCharacter, useCombatSheet } from "@/hooks/useCharacters";
import { t } from "@/i18n";

export function CharacterPage(): React.JSX.Element {
  const { id = "" } = useParams();
  const character = useCharacter(id);
  const sheet = useCombatSheet(id);

  return (
    <section>
      <p>
        <Link to="/">← {t("common.back")}</Link>
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

      {character.data && sheet.data && <CombatCard name={character.data.name} sheet={sheet.data} />}
    </section>
  );
}
