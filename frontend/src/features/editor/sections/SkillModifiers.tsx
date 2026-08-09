import { useId, useState } from "react";

import type { SkillLineDTO } from "@/api/types";
import { t } from "@/i18n";
import { signed } from "@/lib/format";

interface SkillModifiersProps {
  skill: string;
  line: SkillLineDTO;
}

/**
 * The "others" figure on a skill row, with the bonuses behind it.
 *
 * The tooltip lists the *whole* breakdown rather than the part that is not ranks or
 * the ability modifier: those two have their own columns, but a GM asking "why is
 * this +7?" wants the whole sum, and picking entries apart by their label here would
 * put rules knowledge in the frontend — the labels are corpus strings.
 *
 * It opens on hover and on focus, and stays open on click. Hover alone would make it
 * unreachable by keyboard and unusable on touch, and the number it explains is the
 * only place several bonuses are ever shown.
 */
export function SkillModifiers({ skill, line }: SkillModifiersProps): React.JSX.Element {
  const [open, setOpen] = useState(false);
  const [pinned, setPinned] = useState(false);
  const tooltipId = useId();
  const visible = open || pinned;

  return (
    <span className="skill-others">
      <button
        type="button"
        className="skill-others__value"
        aria-label={t("skills.others.show", { skill })}
        aria-describedby={visible ? tooltipId : undefined}
        aria-expanded={visible}
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={() => setPinned((prev) => !prev)}
      >
        {signed(line.other_modifiers)}
      </button>

      {visible && (
        <span role="tooltip" id={tooltipId} className="skill-others__tip">
          <ul className="stat__breakdown">
            {line.breakdown.map((entry, index) => (
              <li key={`${entry.source}-${entry.label}-${index}`}>
                <span>{entry.label}</span>
                {entry.type ? <span className="stat__type"> ({entry.type})</span> : null}
                <span className="stat__delta"> {signed(entry.value)}</span>
              </li>
            ))}
          </ul>

          {/* A bonus the stacking rules dropped is still worth showing: without it
              the sum looks wrong, and knowing *why* it was dropped is the point. */}
          {line.suppressed.length > 0 && (
            <>
              <span className="stat__suppressed-title">{t("breakdown.suppressed")}</span>
              <ul className="stat__suppressed">
                {line.suppressed.map((entry, index) => (
                  <li key={`${entry.label}-${index}`}>
                    <span>{entry.label}</span>
                    <span className="stat__delta"> {signed(entry.value)}</span>
                    <span className="stat__reason"> — {entry.reason}</span>
                  </li>
                ))}
              </ul>
            </>
          )}
        </span>
      )}
    </span>
  );
}
