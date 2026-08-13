import { useState } from "react";

import type {
  ACDTO,
  ArmorDTO,
  AttackDTO,
  CharacterCreate,
  EquippedWeaponIn,
  WeaponDTO,
} from "@/api/types";
import { Combobox } from "@/components/Combobox";
import { Modal } from "@/components/Modal";
import { StatBreakdown } from "@/components/StatBreakdown";
import { WeaponBonuses } from "@/features/editor/sections/WeaponBonuses";
import { useArmor, useWeapons } from "@/hooks/useRules";
import { t } from "@/i18n";
import { linesForWeapon } from "@/lib/attacks";
import { signed } from "@/lib/format";

interface SectionProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
  /** The character's total AC from `/derive`, shown beside the armor that earns
   * it rather than only in the live preview. Absent only while it first loads. */
  ac?: ACDTO;
  /** Every derived way of using each equipped weapon, so its dialog can offer them
   * as a checklist. Absent only while the first derivation loads. */
  attacks?: AttackDTO[];
}

const NONE = "__none__";
/** Sentinel for "no category filter". */
const ALL_CATEGORIES = "*";

export function EquipmentSection({
  draft,
  patch,
  ac,
  attacks = [],
}: SectionProps): React.JSX.Element {
  const armorQuery = useArmor();
  const weaponsQuery = useWeapons();

  const [category, setCategory] = useState<string>(ALL_CATEGORIES);
  const [detailed, setDetailed] = useState<WeaponDTO | null>(null);

  const armor = armorQuery.data ?? [];
  const byArmorName = new Map(armor.map((item) => [item.name, item]));
  const armorOptions = [
    { value: NONE, label: t("equipment.none") },
    ...armor
      .filter((item) => item.category !== "escudo")
      .map((item) => ({ value: item.name, label: item.name, hint: armorSummary(item) })),
  ];
  const shieldOptions = [
    { value: NONE, label: t("equipment.none") },
    ...armor
      .filter((item) => item.category === "escudo")
      .map((item) => ({ value: item.name, label: item.name, hint: armorSummary(item) })),
  ];
  const selectedArmor = draft.armor && byArmorName.get(draft.armor.catalog_name);
  const selectedShield = draft.shield && byArmorName.get(draft.shield.catalog_name);
  const catalog = weaponsQuery.data ?? [];
  // The corpus declares no canonical list of weapon categories, so they are taken
  // from the catalog itself; first-appearance order matches the rulebook table.
  const categories = [...new Set(catalog.map((item) => item.category))];
  const byName = new Map(catalog.map((item) => [item.name, item]));

  const visible = catalog
    .filter((item) => category === ALL_CATEGORIES || item.category === category)
    .sort((a, b) => a.name.localeCompare(b.name));

  const weapons = draft.weapons ?? [];
  // Adding the same weapon twice does nothing today: every copy is equipped the same
  // way, so the second is an identical line on the sheet. It stops being a duplicate
  // the day the equipped row can set a wielding — two short swords, one per hand, is
  // a real build — so this is a guard on a UI that cannot express that yet, not a
  // rule of the game.
  const equipped = new Set(weapons.map((weapon) => weapon.catalog_name));

  const addWeapon = (name: string): void => {
    if (equipped.has(name)) return;
    const weapon: EquippedWeaponIn = {
      catalog_name: name,
      wielding: "one_handed",
      enhancement_bonus: 0,
      attack_bonus: 0,
      damage_bonus: 0,
      is_masterwork: false,
    };
    patch({ weapons: [...weapons, weapon] });
  };

  const removeWeapon = (index: number): void => {
    patch({ weapons: weapons.filter((_, i) => i !== index) });
  };

  const setBonus = (index: number, field: "attack_bonus" | "damage_bonus", value: number): void => {
    const next = weapons.map((weapon, i) =>
      i === index ? { ...weapon, [field]: Math.max(0, value) } : weapon,
    );
    patch({ weapons: next });
  };

  // -1 when the dialog is showing a weapon that is not carried, where there is no
  // magic to edit yet — the "add" button is what that case offers instead.
  const equippedIndex = detailed
    ? weapons.findIndex((weapon) => weapon.catalog_name === detailed.name)
    : -1;

  const hidden = draft.hidden_attack_lines ?? [];
  const toggleLine = (key: string, show: boolean): void => {
    patch({
      hidden_attack_lines: show ? hidden.filter((k) => k !== key) : [...hidden, key],
    });
  };

  return (
    <section aria-labelledby="section-equipment" className="editor__section">
      <h2 id="section-equipment">{t("editor.section.equipment")}</h2>

      <div className="equipment__armor-row">
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
        <StatBreakdown
          label={t("sheet.ac")}
          value={ac ? String(ac.total) : "—"}
          breakdown={ac?.breakdown ?? []}
          suppressed={ac?.suppressed}
        />
      </div>
      {selectedArmor && <p className="equipment__stats">{armorSummary(selectedArmor)}</p>}

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
      {selectedShield && <p className="equipment__stats">{armorSummary(selectedShield)}</p>}

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
                disabled={equipped.has(item.name)}
                aria-label={
                  equipped.has(item.name)
                    ? t("equipment.alreadyEquipped", { weapon: item.name })
                    : t("equipment.addNamed", { weapon: item.name })
                }
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
              <WeaponBonuses
                weapon={weapon}
                onChange={(field, value) => setBonus(index, field, value)}
              />
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

          {/* The same steppers as the equipped row: this dialog is where someone
              lands when they click a weapon to look at it, so the magic it carries
              has to be editable from here too. */}
          {equippedIndex >= 0 && (
            <WeaponBonuses
              weapon={weapons[equippedIndex]!}
              onChange={(field, value) => setBonus(equippedIndex, field, value)}
            />
          )}

          {/* Every derived way of using this weapon, each grip crossed with each
              declared feat. All are shown on the sheet by default; this is where a
              player trims the ones they will never roll. */}
          {linesForWeapon(attacks, detailed.name).length > 0 && (
            <fieldset className="attack-picker">
              <legend>{t("attacks.pick")}</legend>
              {linesForWeapon(attacks, detailed.name).map((line) => {
                const key = line.variant_key!;
                const label = line.variant_label ?? t("attacks.baseLine");
                return (
                  <label key={key} className="attack-picker__line">
                    <input
                      type="checkbox"
                      checked={!hidden.includes(key)}
                      onChange={(event) => toggleLine(key, event.target.checked)}
                    />
                    <span className="attack-picker__label">{label}</span>
                    <span className="attack-picker__numbers">
                      {line.attack_line}
                      {line.damage_expression ? ` · ${line.damage_expression}` : ""}
                    </span>
                  </label>
                );
              })}
            </fieldset>
          )}

          {/* The dialog is reached from the equipped list too, so it is the likeliest
              place to press "add" on something already carried. Say why it is off
              rather than leaving a dead button. */}
          <button
            type="button"
            className="button"
            disabled={equipped.has(detailed.name)}
            onClick={() => {
              addWeapon(detailed.name);
              setDetailed(null);
            }}
          >
            {equipped.has(detailed.name)
              ? t("equipment.alreadyEquipped.short")
              : t("equipment.addWeapon")}
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

/**
 * The stat line for a piece of armor: what it gives (the AC bonus) and what it
 * costs (the Dex cap and the check penalty). These are catalog values read
 * verbatim — nothing here is derived, so it stays clear of the rule that combat
 * arithmetic lives in the backend.
 */
function armorSummary(item: ArmorDTO): string {
  return [
    t("equipment.stats.ac", { value: signed(item.armor_bonus) }),
    item.max_dex != null ? t("equipment.stats.maxDex", { value: signed(item.max_dex) }) : null,
    t("equipment.stats.checkPenalty", { value: signed(item.armor_check_penalty) }),
  ]
    .filter(Boolean)
    .join(" · ");
}
