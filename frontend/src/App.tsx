import { HealthBadge } from "@/components/HealthBadge";
import { t } from "@/i18n";

export function App(): React.JSX.Element {
  return (
    <main className="mx-auto max-w-3xl p-8">
      <h1 className="text-2xl font-bold">{t("app.title")}</h1>
      <p className="text-slate-600">{t("app.tagline")}</p>
      <HealthBadge />
    </main>
  );
}
