import type { EquippedWeaponIn } from "@/api/types";
import { t } from "@/i18n";
import { signed } from "@/lib/format";

interface WeaponBonusesProps {
  weapon: EquippedWeaponIn;
  onChange: (field: "attack_bonus" | "damage_bonus", value: number) => void;
}

/** The two sides of a weapon's enhancement bonus, side by side.
 *
 * A magic weapon has *one* bonus that applies to both, so these are normally set to
 * the same number — a +1 longsword is 1 and 1. They are separate because the sheet
 * has to express the cases where they differ: masterwork is +1 to attack and nothing
 * to damage, and a GM's own item is a GM's business.
 *
 * Shown in the equipped row and again in the weapon's dialog, since that is where
 * someone lands when they click the weapon to look at it.
 */
export function WeaponBonuses({ weapon, onChange }: WeaponBonusesProps): React.JSX.Element {
  const fields = [
    { key: "attack_bonus", label: t("equipment.bonus.attack") },
    { key: "damage_bonus", label: t("equipment.bonus.damage") },
  ] as const;

  return (
    <div className="weapon-bonuses">
      {fields.map(({ key, label }) => {
        // Falls back to the single stored bonus so a weapon saved before the split
        // shows the magic it already has instead of reading as mundane.
        const value = weapon[key] || weapon.enhancement_bonus || 0;
        return (
          <div key={key} className="weapon-bonuses__field">
            <span className="weapon-bonuses__label">{label}</span>
            <span className="stepper">
              <button
                type="button"
                aria-label={t("equipment.bonus.decrement", {
                  bonus: label,
                  weapon: weapon.catalog_name,
                })}
                onClick={() => onChange(key, value - 1)}
              >
                −
              </button>
              <output aria-label={`${label} — ${weapon.catalog_name}`}>{signed(value)}</output>
              <button
                type="button"
                aria-label={t("equipment.bonus.increment", {
                  bonus: label,
                  weapon: weapon.catalog_name,
                })}
                onClick={() => onChange(key, value + 1)}
              >
                +
              </button>
            </span>
          </div>
        );
      })}
    </div>
  );
}
