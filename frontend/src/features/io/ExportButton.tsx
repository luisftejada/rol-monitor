import { useMutation } from "@tanstack/react-query";

import { exportCharacter } from "@/api/characters";
import { t } from "@/i18n";
import { downloadJson, toFileStem } from "@/lib/download";

interface ExportButtonProps {
  id: string;
  name: string;
}

export function ExportButton({ id, name }: ExportButtonProps): React.JSX.Element {
  const exportMutation = useMutation({
    mutationFn: () => exportCharacter(id),
    onSuccess: (character) => downloadJson(`${toFileStem(name)}.json`, character),
  });

  return (
    <button
      type="button"
      onClick={() => exportMutation.mutate()}
      disabled={exportMutation.isPending}
    >
      {t("sheet.action.export")}
    </button>
  );
}
