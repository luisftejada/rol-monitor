import { useNavigate } from "react-router-dom";

import { CharacterEditor } from "@/features/editor/CharacterEditor";
import { defaultDraft } from "@/features/editor/draft";

export function CreateCharacterPage(): React.JSX.Element {
  const navigate = useNavigate();
  return (
    <CharacterEditor
      initialDraft={defaultDraft()}
      mode="create"
      onSaved={(character) => navigate(`/characters/${character.id}`)}
    />
  );
}
