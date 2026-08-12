import type { AttackDTO } from "@/api/types";
import { AttackLines } from "@/components/AttackLines";
import { t } from "@/i18n";

interface SectionProps {
  /** Derived attack lines from `/derive` — one entry per weapon per alternative
   * way of using it (Ataque poderoso, Puntería mortal, ...). Absent only while
   * the first derivation is still loading; empty once it lands and no weapon is
   * equipped yet. */
  attacks?: AttackDTO[];
}

/** Below Equipo, so the attacks a GM rolls sit right under the weapons that
 * produce them. */
export function AttacksSection({ attacks }: SectionProps): React.JSX.Element {
  const lines = attacks ?? [];
  return (
    <section aria-labelledby="section-attacks" className="editor__section">
      <h2 id="section-attacks">{t("editor.section.attacks")}</h2>
      {lines.length === 0 ? (
        <p>{t("attacks.none")}</p>
      ) : (
        <div className="attacks">
          <AttackLines attacks={lines} />
        </div>
      )}
    </section>
  );
}
