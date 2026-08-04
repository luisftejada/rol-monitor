import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { importCharacter } from "@/api/characters";
import { characterKeys } from "@/hooks/useCharacters";
import { t } from "@/i18n";

export function ImportButton(): React.JSX.Element {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [error, setError] = useState<string | null>(null);

  const importMutation = useMutation({
    mutationFn: (document: unknown) => importCharacter(document),
    onSuccess: (character) => {
      void queryClient.invalidateQueries({ queryKey: characterKeys.all });
      navigate(`/characters/${character.id}`);
    },
    onError: () => setError(t("list.importError")),
  });

  const readText = (file: File): Promise<string> =>
    new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = () => resolve(String(reader.result));
      reader.onerror = () => reject(reader.error);
      reader.readAsText(file);
    });

  const onFile = async (file: File): Promise<void> => {
    try {
      const parsed: unknown = JSON.parse(await readText(file));
      setError(null);
      importMutation.mutate(parsed);
    } catch {
      setError(t("list.importError"));
    }
  };

  return (
    <>
      <label className="button">
        {t("list.action.import")}
        <input
          type="file"
          accept="application/json"
          hidden
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) void onFile(file);
          }}
        />
      </label>
      {error && <p role="alert">{error}</p>}
    </>
  );
}
