import { useQuery } from "@tanstack/react-query";

import { getHealth } from "@/api/health";
import { t } from "@/i18n";

/** A small live indicator that the backend is reachable. */
export function HealthBadge(): React.JSX.Element {
  const { isPending, isError, data } = useQuery({
    queryKey: ["health"],
    queryFn: getHealth,
  });

  if (isPending) {
    return (
      <p role="status" aria-live="polite">
        {t("health.checking")}
      </p>
    );
  }

  if (isError) {
    return <p role="alert">{t("health.error")}</p>;
  }

  return (
    <p role="status" aria-live="polite">
      {t("health.ok")} · v{data.version}
    </p>
  );
}
