import { useState } from "react";

import type { CharacterCreate, EquippedWeaponIn, WeaponDTO } from "@/api/types";
import { Combobox } from "@/components/Combobox";
import { Modal } from "@/components/Modal";
import { useArmor, useWeapons } from "@/hooks/useRules";
import { t } from "@/i18n";
import { fuzzyMatch } from "@/lib/normalize";

interface SectionProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
}

const NONE = "__none__";
/** Sentinel for "no category filter". */
const ALL_CATEGORIES = "*";

export function EquipmentSection({ draft, patch }: SectionProps): React.JSX.Element {
  const armorQuery = useArmor();
  const weaponsQuery = useWeapons();

  const [category, setCategory] = useState<string>(ALL_CATEGORIES);
  const [query, setQuery] = useState("");
  const [detailed, setDetailed] = useState<WeaponDTO | null>(null);

  const armor = armorQuery.data ?? [];
  const armorOptions = [
    { value: NONE, label: t("equipment.none") },
    ...armor
      .filter((item) => item.category !== "escudo")
      .map((item) => ({ value: item.name, label: item.name })),
  ];
  const shieldOptions = [
    { value: NONE, label: t("equipment.none") },
    ...armor
      .filter((item) => item.category === "escudo")
      .map((item) => ({ value: item.name, label: item.name })),
  ];
  const catalog = weaponsQuery.data ?? [];
  // The corpus declares no canonical list of weapon categories, so they are taken
  // from the catalog itself; first-appearance order matches the rulebook table.
  const categories = [...new Set(catalog.map((item) => item.category))];
  const byName = new Map(catalog.map((item) => [item.name, item]));

  const visible = catalog
    .filter((item) => category === ALL_CATEGORIES || item.category === category)
    .filter((item) => !query.trim() || fuzzyMatch(item.name, query))
    .sort((a, b) => a.name.localeCompare(b.name));

  const weapons = draft.weapons ?? [];

  const addWeapon = (name: string): void => {
    const weapon: EquippedWeaponIn = {
      catalog_name: name,
      wielding: "one_handed",
      enhancement_bonus: 0,
      is_masterwork: false,
    };
    patch({ weapons: [...weapons, weapon] });
  };

  const removeWeapon = (index: number): void => {
    patch({ weapons: weapons.filter((_, i) => i !== index) });
  };

  return (
    <section aria-labelledby="section-equipment" className="editor__section">
      <h2 id="section-equipment">{t("editor.section.equipment")}</h2>

      <Combobox
        label={t("equipment.armor")}
        options={armorOptions}
        value={draft.armor?.catalog_name ?? NONE}
        onChange={(name) =>
          patch({
            armor:
              name === NONE
                ? null
                : { catalog_name: name, enhancement_bonus: 0, is_masterwork: false },
          })
        }
      />

      <Combobox
        label={t("equipment.shield")}
        options={shieldOptions}
        value={draft.shield?.catalog_name ?? NONE}
        onChange={(name) =>
          patch({
            shield:
              name === NONE
                ? null
                : { catalog_name: name, enhancement_bonus: 0, is_masterwork: false },
          })
        }
      />

      <div className="picker-filters">
        <div className="field">
          <label htmlFor="weapon-category">{t("equipment.weaponType")}</label>
          <select
            id="weapon-category"
            value={category}
            onChange={(event) => setCategory(event.target.value)}
          >
            <option value={ALL_CATEGORIES}>{t("equipment.weaponType.all")}</option>
            {categories.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>

        <div className="field">
          <label htmlFor="weapon-search">{t("equipment.searchWeapon")}</label>
          <input
            id="weapon-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
      </div>

      <p className="counter" role="status">
        {t("equipment.weaponCount", { count: visible.length })}
      </p>

      {visible.length === 0 ? (
        <p>{t("equipment.noWeapons")}</p>
      ) : (
        <ul className="picker-list" aria-label={t("equipment.addWeapon")}>
          {visible.map((item) => (
            <li key={item.slug}>
              {/* Same affordances as the feat picker: hover for the stat line,
                  click for the full card, and a separate button to equip. */}
              <button
                type="button"
                className="picker-list__name"
                title={summaryOf(item)}
                aria-label={t("equipment.weaponDetails", { weapon: item.name })}
                onClick={() => setDetailed(item)}
              >
                {item.name}
              </button>
              <button
                type="button"
                aria-label={t("equipment.addNamed", { weapon: item.name })}
                onClick={() => addWeapon(item.name)}
              >
                +
              </button>
            </li>
          ))}
        </ul>
      )}

      <ul className="weapons" aria-label={t("equipment.weapon")}>
        {weapons.map((weapon, index) => {
          const known = byName.get(weapon.catalog_name);
          return (
            <li key={index}>
              {/* Equipped weapons carry the same tooltip and dialog. One that is not
                  in the catalog (imported or custom) stays plain text. */}
              {known ? (
                <button
                  type="button"
                  className="chip__name"
                  title={summaryOf(known)}
                  aria-label={t("equipment.weaponDetails", { weapon: weapon.catalog_name })}
                  onClick={() => setDetailed(known)}
                >
                  {weapon.catalog_name}
                </button>
              ) : (
                weapon.catalog_name
              )}
              <button
                type="button"
                aria-label={t("equipment.removeWeapon", { weapon: weapon.catalog_name })}
                onClick={() => removeWeapon(index)}
              >
                ×
              </button>
            </li>
          );
        })}
      </ul>

      {detailed && (
        <Modal title={detailed.name} onClose={() => setDetailed(null)}>
          <dl className="details-grid">
            <dt>{t("weapon.proficiency")}</dt>
            <dd>{detailed.proficiency}</dd>

            <dt>{t("weapon.category")}</dt>
            <dd>{detailed.category}</dd>

            <dt>{t("weapon.damage")}</dt>
            <dd>
              {detailed.damage_small ?? t("weapon.unknown")} /{" "}
              {detailed.damage_medium ?? t("weapon.unknown")}
            </dd>

            <dt>{t("weapon.critical")}</dt>
            <dd>{criticalOf(detailed)}</dd>

            <dt>{t("weapon.damageType")}</dt>
            <dd>{detailed.damage_type ?? t("weapon.unknown")}</dd>

            <dt>{t("weapon.range")}</dt>
            <dd>{detailed.range_increment ?? t("weapon.unknown")}</dd>

            <dt>{t("weapon.weight")}</dt>
            <dd>{detailed.weight ?? t("weapon.unknown")}</dd>

            <dt>{t("weapon.cost")}</dt>
            <dd>{detailed.cost ?? t("weapon.unknown")}</dd>

            <dt>{t("weapon.special")}</dt>
            <dd>{detailed.special ?? t("weapon.unknown")}</dd>
          </dl>

          <button
            type="button"
            className="button"
            onClick={() => {
              addWeapon(detailed.name);
              setDetailed(null);
            }}
          >
            {t("equipment.addWeapon")}
          </button>
        </Modal>
      )}
    </section>
  );
}

/** Threat range and multiplier, as the corpus renders them (e.g. "19-20/×2"). */
function criticalOf(weapon: WeaponDTO): string {
  if (weapon.critical.length === 0) return t("weapon.unknown");
  return weapon.critical
    .map((crit) =>
      crit.threat_range >= 20
        ? `×${crit.multiplier}`
        : `${crit.threat_range}-20/×${crit.multiplier}`,
    )
    .join(" / ");
}

/** Tooltip text: the stat line a GM scans for when picking a weapon. */
function summaryOf(weapon: WeaponDTO): string {
  return [weapon.damage_medium, criticalOf(weapon), weapon.damage_type, weapon.special]
    .filter(Boolean)
    .join(" — ");
}
