import { Link } from "react-router-dom";

import type { CharacterSummary } from "@/api/types";
import { t } from "@/i18n";
import { signed } from "@/lib/format";

interface CharacterTableProps {
  characters: CharacterSummary[];
  onDuplicate: (id: string) => void;
  onDelete: (character: CharacterSummary) => void;
  busyId?: string;
}

export function CharacterTable({
  characters,
  onDuplicate,
  onDelete,
  busyId,
}: CharacterTableProps): React.JSX.Element {
  return (
    <table className="roster">
      <thead>
        <tr>
          <th scope="col">{t("list.col.name")}</th>
          <th scope="col">{t("list.col.class")}</th>
          <th scope="col">{t("list.col.hp")}</th>
          <th scope="col">{t("list.col.ac")}</th>
          <th scope="col">{t("list.col.touch")}</th>
          <th scope="col">{t("list.col.flat")}</th>
          <th scope="col">{t("list.col.init")}</th>
          <th scope="col">{t("list.col.saves")}</th>
          <th scope="col">{t("list.col.actions")}</th>
        </tr>
      </thead>
      <tbody>
        {characters.map((character) => (
          <tr key={character.id}>
            <td>
              <Link to={`/characters/${character.id}`}>{character.name}</Link>
            </td>
            <td>{character.classes}</td>
            <td>
              {character.current_hp}/{character.max_hp}
            </td>
            <td>{character.armor_class}</td>
            <td>{character.touch_ac}</td>
            <td>{character.flat_footed_ac}</td>
            <td>{signed(character.initiative)}</td>
            <td>
              {signed(character.fortitude)} / {signed(character.reflex)} / {signed(character.will)}
            </td>
            <td>
              <button
                type="button"
                onClick={() => onDuplicate(character.id)}
                disabled={busyId === character.id}
              >
                {t("list.action.duplicate")}
              </button>
              <button
                type="button"
                onClick={() => onDelete(character)}
                disabled={busyId === character.id}
              >
                {t("list.action.delete")}
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
