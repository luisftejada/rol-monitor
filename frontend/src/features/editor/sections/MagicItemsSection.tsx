import { useState } from "react";

import type { CharacterCreate, MagicItemIn } from "@/api/types";
import { BACKPACK, MagicItemEditor } from "@/features/editor/sections/MagicItemEditor";
import { useMeta } from "@/hooks/useRules";
import { t } from "@/i18n";

interface SectionProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
}

/** Categories that hang off no body slot. Listed on their own below the slots. */
const HELD_CATEGORIES = new Set(["bastones", "varitas"]);

/** One line of the slot grid: a place on the body and what is in it. */
interface SlotRow {
  slug: string;
  label: string;
  item: MagicItemIn | undefined;
  /** True when this line exists only because the slot is over-filled. */
  isOverflow: boolean;
}

export function MagicItemsSection({ draft, patch }: SectionProps): React.JSX.Element {
  const meta = useMeta();
  const items = draft.magic_items ?? [];
  const [editing, setEditing] = useState<string | null>(null);

  const update = (id: string, changes: Partial<MagicItemIn>): void => {
    patch({ magic_items: items.map((item) => (item.id === id ? { ...item, ...changes } : item)) });
  };

  const remove = (id: string): void => {
    patch({ magic_items: items.filter((item) => item.id !== id) });
    setEditing(null);
  };

  /** Create an item already in the slot that was clicked, and open it. */
  const addTo = (slot: string): void => {
    const stem = slot.charAt(0).toUpperCase() + slot.slice(1);
    const taken = items.filter((item) => item.name.startsWith(`${stem}-`)).length;
    const item: MagicItemIn = {
      id: crypto.randomUUID(),
      name: `${stem}-${taken + 1}`,
      slot,
      attack_bonus: 0,
      damage_bonus: 0,
      weapon_bonus_type: "potenciador",
      ac_bonus: 0,
      ac_bonus_type: "deflexión",
      armor_check_penalty: 0,
      speed_bonus: 0,
    };
    patch({ magic_items: [...items, item] });
    setEditing(item.id!);
  };

  // A staff or a wand is held, not worn, so it never occupies a body slot and is
  // listed on its own below. Everything else is placed by its slot.
  const held = items.filter((item) => HELD_CATEGORIES.has(item.category ?? ""));
  const worn = items.filter((item) => !HELD_CATEGORIES.has(item.category ?? ""));

  const rows: SlotRow[] = [];
  for (const slot of meta.data?.item_slots ?? []) {
    const inSlot = worn.filter((item) => item.slot === slot.slug);
    // One line per place the slot offers, so "anillo (×2)" reads as two rings and an
    // empty one is as visible as a filled one. Anything beyond capacity gets a line
    // of its own, flagged, rather than being hidden behind the ones that fit.
    for (let i = 0; i < Math.max(slot.capacity, inSlot.length); i += 1) {
      rows.push({
        slug: slot.slug,
        label: slot.name,
        item: inSlot[i],
        isOverflow: i >= slot.capacity,
      });
    }
  }

  const stowed = worn.filter((item) => item.slot === BACKPACK);
  const open = items.find((item) => item.id === editing);

  return (
    <section aria-labelledby="section-items" className="editor__section">
      <h2 id="section-items">{t("editor.section.items")}</h2>

      <table className="slots">
        <thead>
          <tr>
            <th scope="col">{t("items.slot")}</th>
            <th scope="col">{t("items.inSlot")}</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${row.slug}-${index}`} className={row.isOverflow ? "is-over" : undefined}>
              <th scope="row">{row.label}</th>
              <td>
                <SlotButton row={row} onOpen={setEditing} onAdd={addTo} />
                {row.isOverflow && (
                  <span className="slots__warn" role="alert">
                    {t("items.overCapacity")}
                  </span>
                )}
              </td>
            </tr>
          ))}

          {/* The backpack is a slot too: the item is owned, just not helping. */}
          <tr>
            <th scope="row">{t("items.slot.backpack")}</th>
            <td className="slots__stowed">
              {stowed.map((item) => (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => setEditing(item.id!)}
                  aria-label={t("items.edit", { item: item.name })}
                >
                  {item.name}
                </button>
              ))}
              <button
                type="button"
                className="slots__add"
                aria-label={t("items.addTo", { slot: t("items.slot.backpack") })}
                onClick={() => addTo(BACKPACK)}
              >
                +
              </button>
            </td>
          </tr>
        </tbody>
      </table>

      <h3>{t("items.held")}</h3>
      {held.length === 0 ? (
        <p>{t("items.noneHeld")}</p>
      ) : (
        <ul className="slots__held" aria-label={t("items.held")}>
          {held.map((item) => (
            <li key={item.id}>
              <button
                type="button"
                onClick={() => setEditing(item.id!)}
                aria-label={t("items.edit", { item: item.name })}
              >
                {item.name}
              </button>
              <span className="slots__category">{item.category}</span>
            </li>
          ))}
        </ul>
      )}

      {open && (
        <MagicItemEditor
          item={open}
          meta={meta.data}
          onChange={(changes) => update(open.id!, changes)}
          onRemove={() => remove(open.id!)}
          onClose={() => setEditing(null)}
        />
      )}
    </section>
  );
}

interface SlotButtonProps {
  row: SlotRow;
  onOpen: (id: string) => void;
  onAdd: (slot: string) => void;
}

/** A filled slot opens its item; an empty one creates one already in that slot,
 * which is the only thing anybody wants from clicking an empty row. */
function SlotButton({ row, onOpen, onAdd }: SlotButtonProps): React.JSX.Element {
  if (row.item) {
    return (
      <button
        type="button"
        onClick={() => onOpen(row.item!.id!)}
        aria-label={t("items.edit", { item: row.item.name })}
      >
        {row.item.name}
      </button>
    );
  }
  return (
    <button
      type="button"
      className="slots__add"
      aria-label={t("items.addTo", { slot: row.label })}
      onClick={() => onAdd(row.slug)}
    >
      {t("items.empty")}
    </button>
  );
}
