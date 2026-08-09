import { useId, useState } from "react";

import type { BreakdownEntry, SuppressedEntry } from "@/api/types";
import { t } from "@/i18n";
import { signed } from "@/lib/format";

interface StatBreakdownProps {
  label: string;
  value: string;
  breakdown: BreakdownEntry[];
  suppressed?: SuppressedEntry[];
  /**
   * A short qualifier shown beside the label and read as part of it — what makes
   * this row different from its neighbours. Text rather than styling, so it survives
   * a screen reader and a monochrome print.
   */
  note?: string;
}

/**
 * A derived number that expands, inline, into the exact list of bonuses that
 * produced it — including the ones suppressed by the stacking rules. This is the
 * "why?" affordance the whole product is built around.
 */
export function StatBreakdown({
  label,
  value,
  breakdown,
  suppressed = [],
  note,
}: StatBreakdownProps): React.JSX.Element {
  const [open, setOpen] = useState(false);
  const regionId = useId();

  return (
    <div className={note ? "stat stat--noted" : "stat"}>
      <button
        type="button"
        className="stat__toggle"
        aria-expanded={open}
        aria-controls={regionId}
        onClick={() => setOpen((prev) => !prev)}
      >
        <span className="stat__label">{label}</span>
        {note && <span className="stat__note">{note}</span>}
        <span className="stat__value">{value}</span>
        <span aria-hidden="true">{open ? "▾" : "▸"}</span>
      </button>

      {open && (
        <div id={regionId} role="region" aria-label={t("breakdown.show", { label })}>
          {breakdown.length === 0 ? (
            <p>{t("breakdown.empty")}</p>
          ) : (
            <ul className="stat__breakdown">
              {breakdown.map((entry, index) => (
                <li key={`${entry.source}-${entry.label}-${index}`}>
                  <span>{entry.label}</span>
                  {entry.type ? <span className="stat__type"> ({entry.type})</span> : null}
                  <span className="stat__delta"> {signed(entry.value)}</span>
                </li>
              ))}
            </ul>
          )}

          {suppressed.length > 0 && (
            <>
              <p className="stat__suppressed-title">{t("breakdown.suppressed")}</p>
              <ul className="stat__suppressed">
                {suppressed.map((entry, index) => (
                  <li key={`${entry.label}-${index}`}>
                    <span>{entry.label}</span>
                    <span className="stat__delta"> {signed(entry.value)}</span>
                    <span className="stat__reason"> — {entry.reason}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}
