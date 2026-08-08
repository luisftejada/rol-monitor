import { Link } from "react-router-dom";

import type { CharacterSummary } from "@/api/types";
import { CopyIcon, PencilIcon, TrashIcon } from "@/components/icons";
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
              {/* Icon-only actions: `title` gives the hover tooltip, `aria-label`
                  gives the same words to a screen reader, so the icon never has to
                  be guessed at. */}
              <div className="row-actions">
                <Link
                  className="icon-button"
                  to={`/characters/${character.id}/edit`}
                  title={t("list.action.edit")}
                  aria-label={t("list.action.edit")}
                >
                  <PencilIcon />
                </Link>
                <button
                  type="button"
                  className="icon-button"
                  title={t("list.action.duplicate")}
                  aria-label={t("list.action.duplicate")}
                  onClick={() => onDuplicate(character.id)}
                  disabled={busyId === character.id}
                >
                  <CopyIcon />
                </button>
                <button
                  type="button"
                  className="icon-button icon-button--danger"
                  title={t("list.action.delete")}
                  aria-label={t("list.action.delete")}
                  onClick={() => onDelete(character)}
                  disabled={busyId === character.id}
                >
                  <TrashIcon />
                </button>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
