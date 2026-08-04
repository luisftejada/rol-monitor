import { useState } from "react";
import { Link } from "react-router-dom";

import type { CharacterSummary } from "@/api/types";
import { CharacterTable } from "@/components/CharacterTable";
import { ImportButton } from "@/features/io/ImportButton";
import { useCharacters, useDeleteCharacter, useDuplicateCharacter } from "@/hooks/useCharacters";
import { t } from "@/i18n";

export function CharacterListPage(): React.JSX.Element {
  const [search, setSearch] = useState("");
  const { data, isPending, isError, refetch } = useCharacters({ search: search || undefined });
  const duplicate = useDuplicateCharacter();
  const remove = useDeleteCharacter();

  const handleDelete = (character: CharacterSummary): void => {
    if (window.confirm(t("list.confirmDelete", { name: character.name }))) {
      remove.mutate(character.id);
    }
  };

  return (
    <section>
      <div className="list__header">
        <h1>{t("list.title")}</h1>
        <div className="list__actions">
          <ImportButton />
          <Link className="button" to="/new">
            {t("list.action.new")}
          </Link>
        </div>
      </div>

      <label className="search">
        <span>{t("list.search")}</span>
        <input type="search" value={search} onChange={(event) => setSearch(event.target.value)} />
      </label>

      {isPending && <p role="status">{t("common.loading")}</p>}

      {isError && (
        <div role="alert">
          <p>{t("common.error")}</p>
          <button type="button" onClick={() => void refetch()}>
            {t("common.retry")}
          </button>
        </div>
      )}

      {data &&
        (data.items.length === 0 ? (
          <p>{t("list.empty")}</p>
        ) : (
          <CharacterTable
            characters={data.items}
            onDuplicate={(id) => duplicate.mutate(id)}
            onDelete={handleDelete}
            busyId={remove.variables ?? duplicate.variables}
          />
        ))}
    </section>
  );
}
