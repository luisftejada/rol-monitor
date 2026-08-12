import type { AttackDTO } from "@/api/types";
import { StatBreakdown } from "@/components/StatBreakdown";
import { t } from "@/i18n";
import { signed } from "@/lib/format";

/**
 * One block per attack line. A weapon that can be used more than one way (Ataque
 * poderoso, Puntería mortal, ...) appears once per way, exactly as `/derive`
 * lists them — nothing here decides which alternatives exist, it only renders
 * whatever the backend already resolved. Shared by the read-only combat card and
 * the editor's own Ataques section so the two never drift apart.
 */
export function AttackLines({ attacks }: { attacks: AttackDTO[] }): React.JSX.Element {
  return (
    <>
      {attacks.map((attack, index) => (
        <div key={`${attack.weapon}-${index}`} className="attack">
          <p className="attack__name">
            {attack.weapon}
            {!attack.is_proficient && (
              <span className="attack__warn"> ({t("sheet.attack.notProficient")})</span>
            )}
          </p>
          <div className="attack__stats">
            <StatBreakdown
              label={attack.weapon}
              value={attack.attack_line}
              breakdown={attack.attack.breakdown}
              suppressed={attack.attack.suppressed}
            />
            {/* Manyshot rolls the first arrow's dice twice, so the first attack
                is shown separately: "2d8 then 1d8" is not one number. */}
            {attack.first_attack_damage_expression && (
              <StatBreakdown
                label={t("sheet.attack.firstDamage")}
                value={attack.first_attack_damage_expression}
                breakdown={attack.damage.breakdown}
                suppressed={attack.damage.suppressed}
              />
            )}
            {attack.damage_expression && (
              <StatBreakdown
                label={t("sheet.attack.damage")}
                value={attack.damage_expression}
                breakdown={attack.damage.breakdown}
                suppressed={attack.damage.suppressed}
              />
            )}
            <p className="attack__crit">
              {t("sheet.attack.crit")}: {attack.threat_range}-20/×{attack.crit_multiplier}
            </p>
          </div>
          {/* Power Attack's penalty applies to combat manoeuvres too, so a line
              that costs CMB shows the one to use while it is in play. */}
          {attack.cmb && (
            <StatBreakdown
              label={t("sheet.attack.cmb")}
              value={signed(attack.cmb.total)}
              breakdown={attack.cmb.breakdown}
              suppressed={attack.cmb.suppressed}
            />
          )}
          {/* What a feat does to the *target* — a critical feat has no number of
              yours to change, so it is shown where the GM confirms the crit. */}
          {attack.notes.length > 0 && (
            <ul className="attack__notes">
              {attack.notes.map((note, noteIndex) => (
                <li key={noteIndex}>{note}</li>
              ))}
            </ul>
          )}
        </div>
      ))}
    </>
  );
}
