import { useState } from "react";

import type { CharacterSummary } from "@/api/types";
import { CharacterTable } from "@/components/CharacterTable";
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
      <h1>{t("list.title")}</h1>

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
