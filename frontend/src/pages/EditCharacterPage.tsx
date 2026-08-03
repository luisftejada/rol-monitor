import { useNavigate, useParams } from "react-router-dom";

import type { CharacterCreate, CharacterRead } from "@/api/types";
import { CharacterEditor } from "@/features/editor/CharacterEditor";
import { useCharacter } from "@/hooks/useCharacters";
import { t } from "@/i18n";

export function EditCharacterPage(): React.JSX.Element {
  const { id = "" } = useParams();
  const navigate = useNavigate();
  const character = useCharacter(id);

  if (character.isPending) return <p role="status">{t("common.loading")}</p>;
  if (character.isError || !character.data) {
    return (
      <div role="alert">
        <p>{t("common.error")}</p>
      </div>
    );
  }

  const editable: Partial<CharacterRead> = { ...character.data };
  delete editable.id;
  delete editable.created_at;
  delete editable.updated_at;
  return (
    <CharacterEditor
      initialDraft={editable as CharacterCreate}
      mode="edit"
      characterId={id}
      onSaved={() => navigate(`/characters/${id}`)}
    />
  );
}
