import type { CharacterCreate, EquippedWeaponIn } from "@/api/types";
import { Combobox } from "@/components/Combobox";
import { useArmor, useWeapons } from "@/hooks/useRules";
import { t } from "@/i18n";

interface SectionProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
}

const NONE = "__none__";

export function EquipmentSection({ draft, patch }: SectionProps): React.JSX.Element {
  const armorQuery = useArmor();
  const weaponsQuery = useWeapons();

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
  const weaponOptions = (weaponsQuery.data ?? []).map((item) => ({
    value: item.name,
    label: item.name,
  }));

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

      <Combobox
        label={t("equipment.addWeapon")}
        options={weaponOptions}
        value={null}
        onChange={addWeapon}
        placeholder={t("equipment.addWeapon")}
      />

      <ul className="weapons" aria-label={t("equipment.weapon")}>
        {weapons.map((weapon, index) => (
          <li key={index}>
            {weapon.catalog_name}
            <button
              type="button"
              aria-label={t("equipment.removeWeapon", { weapon: weapon.catalog_name })}
              onClick={() => removeWeapon(index)}
            >
              ×
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}
