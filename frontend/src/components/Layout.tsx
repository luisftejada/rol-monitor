import { Link, Outlet } from "react-router-dom";

import { HealthBadge } from "@/components/HealthBadge";
import { t } from "@/i18n";

export function Layout(): React.JSX.Element {
  return (
    <div className="layout">
      <a className="skip-link" href="#main">
        {t("skip.toContent")}
      </a>
      <header className="layout__header">
        <Link to="/" className="layout__brand">
          <strong>{t("app.title")}</strong>
          <span className="layout__tagline">{t("app.tagline")}</span>
        </Link>
        <HealthBadge />
      </header>
      <main id="main" className="layout__main">
        <Outlet />
      </main>
    </div>
  );
}
