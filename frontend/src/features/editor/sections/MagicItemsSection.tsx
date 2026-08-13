import type { CharacterCreate, MagicItemIn } from "@/api/types";
import { useMeta } from "@/hooks/useRules";
import { t } from "@/i18n";

interface SectionProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
}

/** Where an item sits when it is not being worn. Nothing here contributes. */
const BACKPACK = "mochila";

/** Bonus types worth offering: the ones a worn item actually grants. The full list
 * lives in the corpus, but a picker of sixteen would bury the four that matter. */
const AC_TYPES = ["deflexión", "armadura natural", "armadura", "escudo", "esquiva"] as const;
const WEAPON_TYPES = ["potenciador", "competencia", "moral", "suerte"] as const;

export function MagicItemsSection({ draft, patch }: SectionProps): React.JSX.Element {
  const meta = useMeta();
  const slots = meta.data?.item_slots ?? [];
  const items = draft.magic_items ?? [];

  /** A default name that says what it is and does not collide: "Anillo-1". */
  const nextName = (slot: string): string => {
    const label = slots.find((entry) => entry.slug === slot)?.slug ?? slot;
    const stem = label.charAt(0).toUpperCase() + label.slice(1);
    const taken = items.filter((item) => item.name.startsWith(`${stem}-`)).length;
    return `${stem}-${taken + 1}`;
  };

  const addItem = (): void => {
    const item: MagicItemIn = {
      name: nextName(BACKPACK),
      slot: BACKPACK,
      attack_bonus: 0,
      damage_bonus: 0,
      weapon_bonus_type: "potenciador",
      ac_bonus: 0,
      ac_bonus_type: "deflexión",
      armor_check_penalty: 0,
      speed_bonus: 0,
    };
    patch({ magic_items: [...items, item] });
  };

  const update = (index: number, changes: Partial<MagicItemIn>): void => {
    patch({
      magic_items: items.map((item, i) => (i === index ? { ...item, ...changes } : item)),
    });
  };

  const remove = (index: number): void => {
    patch({ magic_items: items.filter((_, i) => i !== index) });
  };

  // How full each slot is, so going over shows where it happened rather than only in
  // the sheet's warnings. Stowed items never count.
  const worn = new Map<string, number>();
  for (const item of items) {
    if (item.slot !== BACKPACK) worn.set(item.slot, (worn.get(item.slot) ?? 0) + 1);
  }
  const overCapacity = (slot: string): boolean => {
    const capacity = slots.find((entry) => entry.slug === slot)?.capacity ?? 1;
    return slot !== BACKPACK && (worn.get(slot) ?? 0) > capacity;
  };

  return (
    <section aria-labelledby="section-items" className="editor__section">
      <h2 id="section-items">{t("editor.section.items")}</h2>

      {items.length === 0 && <p>{t("items.none")}</p>}

      <ul className="magic-items" aria-label={t("editor.section.items")}>
        {items.map((item, index) => (
          <li key={item.id ?? index} className={overCapacity(item.slot) ? "is-over" : undefined}>
            <div className="magic-items__row">
              <label className="field">
                <span>{t("items.name")}</span>
                <input
                  value={item.name}
                  onChange={(event) => update(index, { name: event.target.value })}
                />
              </label>

              <label className="field">
                <span>{t("items.slot")}</span>
                <select
                  value={item.slot}
                  onChange={(event) => update(index, { slot: event.target.value })}
                >
                  <option value={BACKPACK}>{t("items.slot.backpack")}</option>
                  {slots.map((slot) => (
                    <option key={slot.slug} value={slot.slug}>
                      {slot.name}
                    </option>
                  ))}
                </select>
              </label>

              <button
                type="button"
                aria-label={t("items.remove", { item: item.name })}
                onClick={() => remove(index)}
              >
                ×
              </button>
            </div>

            {/* Stated once, where the choice is made: an item you are not wearing is
                still yours, it just is not helping. */}
            {item.slot === BACKPACK && <p className="magic-items__note">{t("items.stowed")}</p>}
            {overCapacity(item.slot) && (
              <p className="magic-items__warn" role="alert">
                {t("items.overCapacity")}
              </p>
            )}

            <div className="magic-items__row">
              <label className="field">
                <span>{t("items.category")}</span>
                <select
                  value={item.category ?? ""}
                  onChange={(event) => update(index, { category: event.target.value || null })}
                >
                  <option value="">{t("items.unset")}</option>
                  {(meta.data?.item_categories ?? []).map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>

              <label className="field">
                <span>{t("items.activation")}</span>
                <select
                  value={item.activation ?? ""}
                  onChange={(event) => update(index, { activation: event.target.value || null })}
                >
                  <option value="">{t("items.unset")}</option>
                  {(meta.data?.item_activations ?? []).map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="magic-items__row">
              <NumberField
                label={t("items.acBonus")}
                value={item.ac_bonus ?? 0}
                onChange={(value) => update(index, { ac_bonus: value })}
              />
              <label className="field">
                {/* The type is what decides whether it adds to the armour you wear or
                    is swallowed by it, so it sits beside the number, not in a dialog. */}
                <span>{t("items.acBonusType")}</span>
                <select
                  value={item.ac_bonus_type ?? ""}
                  onChange={(event) => update(index, { ac_bonus_type: event.target.value || null })}
                >
                  <option value="">{t("breakdown.untyped")}</option>
                  {AC_TYPES.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="magic-items__row">
              <NumberField
                label={t("items.attackBonus")}
                value={item.attack_bonus ?? 0}
                onChange={(value) => update(index, { attack_bonus: value })}
              />
              <NumberField
                label={t("items.damageBonus")}
                value={item.damage_bonus ?? 0}
                onChange={(value) => update(index, { damage_bonus: value })}
              />
              <label className="field">
                <span>{t("items.weaponBonusType")}</span>
                <select
                  value={item.weapon_bonus_type ?? ""}
                  onChange={(event) =>
                    update(index, { weapon_bonus_type: event.target.value || null })
                  }
                >
                  <option value="">{t("breakdown.untyped")}</option>
                  {WEAPON_TYPES.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="magic-items__row">
              <NumberField
                label={t("items.checkPenalty")}
                value={item.armor_check_penalty ?? 0}
                onChange={(value) => update(index, { armor_check_penalty: value })}
              />
              <NumberField
                label={t("items.speedBonus")}
                value={item.speed_bonus ?? 0}
                onChange={(value) => update(index, { speed_bonus: value })}
              />
            </div>

            <div className="magic-items__row">
              <NumberField
                label={t("items.useDc")}
                value={item.use_device_dc ?? 0}
                onChange={(value) => update(index, { use_device_dc: value || null })}
              />
              <NumberField
                label={t("items.usesPerDay")}
                value={item.uses_per_day ?? 0}
                onChange={(value) =>
                  // A fresh item starts the day full, so setting the allowance also
                  // fills it: nobody wants to type the same number twice.
                  update(index, { uses_per_day: value || null, uses_remaining: value || null })
                }
              />
              <NumberField
                label={t("items.usesLeft")}
                value={item.uses_remaining ?? 0}
                onChange={(value) => update(index, { uses_remaining: value })}
              />
            </div>

            <label className="field">
              <span>{t("items.description")}</span>
              <textarea
                rows={2}
                value={item.description ?? ""}
                onChange={(event) => update(index, { description: event.target.value || null })}
              />
            </label>
          </li>
        ))}
      </ul>

      <button type="button" className="button" onClick={addItem}>
        {t("items.add")}
      </button>
    </section>
  );
}

interface NumberFieldProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
}

function NumberField({ label, value, onChange }: NumberFieldProps): React.JSX.Element {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        type="number"
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}
