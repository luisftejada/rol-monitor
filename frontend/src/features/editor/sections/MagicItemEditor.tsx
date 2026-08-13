import type { MagicItemIn, MetaDTO } from "@/api/types";
import { Modal } from "@/components/Modal";
import { t } from "@/i18n";

interface MagicItemEditorProps {
  item: MagicItemIn;
  meta?: MetaDTO;
  onChange: (changes: Partial<MagicItemIn>) => void;
  onRemove: () => void;
  onClose: () => void;
}

/** Where an item sits when it is not being worn. Nothing here contributes. */
export const BACKPACK = "mochila";

/** Bonus types worth offering: the ones a worn item actually grants. The corpus lists
 * sixteen, and a picker that long would bury the five that matter. */
const AC_TYPES = ["deflexión", "armadura natural", "armadura", "escudo", "esquiva"] as const;
const WEAPON_TYPES = ["potenciador", "competencia", "moral", "suerte"] as const;

/** Every field of one magic item, in a dialog reached from its slot. */
export function MagicItemEditor({
  item,
  meta,
  onChange,
  onRemove,
  onClose,
}: MagicItemEditorProps): React.JSX.Element {
  return (
    <Modal title={item.name} onClose={onClose}>
      <div className="item-editor">
        <div className="item-editor__row">
          <label className="field">
            <span>{t("items.name")}</span>
            <input value={item.name} onChange={(e) => onChange({ name: e.target.value })} />
          </label>

          <label className="field">
            <span>{t("items.slot")}</span>
            <select value={item.slot} onChange={(e) => onChange({ slot: e.target.value })}>
              <option value={BACKPACK}>{t("items.slot.backpack")}</option>
              {(meta?.item_slots ?? []).map((slot) => (
                <option key={slot.slug} value={slot.slug}>
                  {slot.name}
                </option>
              ))}
            </select>
          </label>
        </div>

        {item.slot === BACKPACK && <p className="item-editor__note">{t("items.stowed")}</p>}

        <div className="item-editor__row">
          <label className="field">
            <span>{t("items.category")}</span>
            <select
              value={item.category ?? ""}
              onChange={(e) => onChange({ category: e.target.value || null })}
            >
              <option value="">{t("items.unset")}</option>
              {(meta?.item_categories ?? []).map((name) => (
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
              onChange={(e) => onChange({ activation: e.target.value || null })}
            >
              <option value="">{t("items.unset")}</option>
              {(meta?.item_activations ?? []).map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="item-editor__row">
          <NumberField
            label={t("items.acBonus")}
            value={item.ac_bonus ?? 0}
            onChange={(value) => onChange({ ac_bonus: value })}
          />
          {/* The type is what decides whether this adds to the armour you wear or is
              swallowed by it, so it sits beside the number rather than behind a menu. */}
          <label className="field">
            <span>{t("items.acBonusType")}</span>
            <select
              value={item.ac_bonus_type ?? ""}
              onChange={(e) => onChange({ ac_bonus_type: e.target.value || null })}
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

        <div className="item-editor__row">
          <NumberField
            label={t("items.attackBonus")}
            value={item.attack_bonus ?? 0}
            onChange={(value) => onChange({ attack_bonus: value })}
          />
          <NumberField
            label={t("items.damageBonus")}
            value={item.damage_bonus ?? 0}
            onChange={(value) => onChange({ damage_bonus: value })}
          />
          <label className="field">
            <span>{t("items.weaponBonusType")}</span>
            <select
              value={item.weapon_bonus_type ?? ""}
              onChange={(e) => onChange({ weapon_bonus_type: e.target.value || null })}
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

        <div className="item-editor__row">
          <NumberField
            label={t("items.checkPenalty")}
            value={item.armor_check_penalty ?? 0}
            onChange={(value) => onChange({ armor_check_penalty: value })}
          />
          <NumberField
            label={t("items.speedBonus")}
            value={item.speed_bonus ?? 0}
            onChange={(value) => onChange({ speed_bonus: value })}
          />
        </div>

        <div className="item-editor__row">
          <NumberField
            label={t("items.useDc")}
            value={item.use_device_dc ?? 0}
            onChange={(value) => onChange({ use_device_dc: value || null })}
          />
          <NumberField
            label={t("items.usesPerDay")}
            value={item.uses_per_day ?? 0}
            // A fresh item starts the day full, so setting the allowance fills it:
            // nobody wants to type the same number twice.
            onChange={(value) =>
              onChange({ uses_per_day: value || null, uses_remaining: value || null })
            }
          />
          <NumberField
            label={t("items.usesLeft")}
            value={item.uses_remaining ?? 0}
            onChange={(value) => onChange({ uses_remaining: value })}
          />
        </div>

        <label className="field">
          <span>{t("items.description")}</span>
          <textarea
            rows={3}
            value={item.description ?? ""}
            onChange={(e) => onChange({ description: e.target.value || null })}
          />
        </label>

        <button type="button" className="button button--danger" onClick={onRemove}>
          {t("items.remove", { item: item.name })}
        </button>
      </div>
    </Modal>
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
      <input type="number" value={value} onChange={(e) => onChange(Number(e.target.value))} />
    </label>
  );
}
