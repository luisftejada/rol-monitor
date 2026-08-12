import type { AttackDTO } from "@/api/types";
import { StatBreakdown } from "@/components/StatBreakdown";
import { t } from "@/i18n";
import { signed } from "@/lib/format";

/** The weapon's own name, without the "(<variant_label>)" suffix `weapon` folds
 * it into for anything that reads the whole line as one string — a renderer
 * showing the two apart already has `variant_label` on its own and does not need
 * to reconstruct it, only strip the exact substring the backend added. */
function baseWeaponName(attack: AttackDTO): string {
  return attack.variant_label
    ? attack.weapon.replace(` (${attack.variant_label})`, "")
    : attack.weapon;
}

/**
 * One block per attack line. A weapon that can be used more than one way (Ataque
 * poderoso, Puntería mortal, ...) appears once per way, exactly as `/derive`
 * lists them — nothing here decides which alternatives exist, it only renders
 * whatever the backend already resolved. Shared by the read-only combat card and
 * the editor's own Ataques section so the two never drift apart.
 *
 * Layout: the weapon name and its bonus/damage/crit share one row, so every
 * line's numbers land in the same three columns; what makes the line a variant
 * (Ataque poderoso, Disparo a bocajarro's range caveat, ...) is its own line right
 * below the name, and anything that effect changes elsewhere (the CMB Ataque
 * poderoso also charges) follows directly under that.
 */
export function AttackLines({ attacks }: { attacks: AttackDTO[] }): React.JSX.Element {
  return (
    <>
      {attacks.map((attack, index) => (
        <div key={`${attack.weapon}-${index}`} className="attack">
          <div className="attack__row">
            <p className="attack__name">
              {baseWeaponName(attack)}
              {!attack.is_proficient && (
                <span className="attack__warn"> ({t("sheet.attack.notProficient")})</span>
              )}
            </p>
            <StatBreakdown
              label={t("sheet.attack.bonus")}
              value={attack.attack_line}
              breakdown={attack.attack.breakdown}
              suppressed={attack.attack.suppressed}
            />
            {attack.damage_expression ? (
              <StatBreakdown
                label={t("sheet.attack.damage")}
                value={attack.damage_expression}
                breakdown={attack.damage.breakdown}
                suppressed={attack.damage.suppressed}
              />
            ) : (
              // Kept as an empty tile, not omitted, so the crit column after it
              // still lands in the same place as every other line's.
              <p className="attack__static">
                <span className="stat__label">{t("sheet.attack.damage")}</span>
              </p>
            )}
            <p className="attack__static">
              <span className="stat__label">{t("sheet.attack.crit")}</span>
              <span className="stat__value">
                {attack.threat_range}-20/×{attack.crit_multiplier}
              </span>
            </p>
          </div>

          {/* Manyshot rolls the first arrow's dice twice, so it is shown as its own
              extra line: "2d8 then 1d8" is not the one damage figure above. */}
          {attack.first_attack_damage_expression && (
            <StatBreakdown
              label={t("sheet.attack.firstDamage")}
              value={attack.first_attack_damage_expression}
              breakdown={attack.damage.breakdown}
              suppressed={attack.damage.suppressed}
            />
          )}

          {/* What makes this line a variant of the weapon's base one, right below
              the name it modifies rather than folded into it a second time. */}
          {attack.variant_label && <p className="attack__variant">{attack.variant_label}</p>}

          {/* Power Attack's penalty applies to combat manoeuvres too, so a line
              that costs CMB shows the one to use while it is in play — right below
              the variant that costs it. */}
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
