import type { ValueBreakdown } from "@/api/types";
import { StatBreakdown } from "@/components/StatBreakdown";
import { t, type MessageKey } from "@/i18n";
import { signed } from "@/lib/format";

const SAVE_ORDER = ["Fortaleza", "Reflejos", "Voluntad"] as const;

interface SectionProps {
  /** Derived save lines from `/derive`, keyed by name. Absent only while the first one loads. */
  saves?: Record<string, ValueBreakdown>;
}

/** Its own card, right below Características, so the saves a GM reaches for
 * mid-combat sit beside the ability scores they come from — not scrolled away
 * in the live preview. */
export function SavesSection({ saves }: SectionProps): React.JSX.Element {
  return (
    <section aria-labelledby="section-saves" className="editor__section">
      <h2 id="section-saves">{t("editor.section.saves")}</h2>
      <div className="card__saves">
        {SAVE_ORDER.map((kind) => {
          const save = saves?.[kind];
          return (
            <StatBreakdown
              key={kind}
              label={t(`sheet.save.${kind}` as MessageKey)}
              value={save ? signed(save.total) : "—"}
              breakdown={save?.breakdown ?? []}
              suppressed={save?.suppressed}
            />
          );
        })}
      </div>
    </section>
  );
}
