import { useState } from "react";

import type { CharacterCreate, FeatBudgetDTO, FeatDTO } from "@/api/types";
import { Modal } from "@/components/Modal";
import { useFeats, useMeta, useWeapons } from "@/hooks/useRules";
import { t } from "@/i18n";
import { fuzzyMatch } from "@/lib/normalize";

interface SectionProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
  bab: number;
  abilities: Record<string, number>;
  /** The feat budget as derived by the backend; the frontend counts nothing itself. */
  budget?: FeatBudgetDTO;
}

/** Sentinel for "no type filter"; feat types themselves come from the corpus. */
const ALL_TYPES = "*";

export function FeatsSection({
  draft,
  patch,
  bab,
  abilities,
  budget,
}: SectionProps): React.JSX.Element {
  const ownedFeats = draft.feats ?? [];
  const feats = useFeats({ bab, abilities, owned: ownedFeats });
  const meta = useMeta();
  const weapons = useWeapons();

  const [type, setType] = useState<string>(ALL_TYPES);
  const [onlyEligible, setOnlyEligible] = useState(false);
  const [query, setQuery] = useState("");
  const [detailed, setDetailed] = useState<FeatDTO | null>(null);

  const owned = new Set(ownedFeats);
  const featTypes = meta.data?.feat_types ?? [];
  const featOptions = draft.feat_options ?? {};
  // The full catalog, not just what is equipped: a feat can be taken for a weapon
  // the character does not carry yet.
  const weaponNames = (weapons.data ?? []).map((weapon) => weapon.name);
  // Selected feats are stored as names; the catalog entry carries what to show.
  const byName = new Map((feats.data ?? []).map((feat) => [feat.name, feat]));

  // What each remaining kind of slot accepts, offered as filters before the raw
  // type list: these are the feats the character can actually spend a slot on. The
  // backend decides what fills a slot; this only groups the answers.
  const slotFilters = new Map<string, { label: string; allows: (feat: FeatDTO) => boolean }>();
  for (const slot of budget?.slots ?? []) {
    if (slot.choice === "tipos" && slot.types.length > 0) {
      const key = `tipos:${slot.types.join(",")}`;
      slotFilters.set(key, {
        label: t("feats.filter.slotTypes", {
          types: slot.types.join(", "),
          source: slot.source,
        }),
        allows: (feat) => slot.types.some((type) => feat.types.includes(type)),
      });
    } else if (slot.choice === "lista" && slot.list_key) {
      const allowed = new Set(budget?.lists?.[slot.list_key] ?? []);
      slotFilters.set(`lista:${slot.list_key}`, {
        label: t("feats.filter.slotList", { source: slot.source }),
        allows: (feat) => allowed.has(feat.name),
      });
    }
  }
  const activeSlot = slotFilters.get(type);
  const slotNote = type.startsWith("lista:")
    ? budget?.list_notes?.[type.slice("lista:".length)]
    : undefined;

  const visible = (feats.data ?? [])
    .filter((feat) =>
      type === ALL_TYPES ? true : activeSlot ? activeSlot.allows(feat) : feat.types.includes(type),
    )
    .filter((feat) => !onlyEligible || feat.is_eligible)
    .filter((feat) => !query.trim() || fuzzyMatch(feat.name, query))
    .sort((a, b) => a.name.localeCompare(b.name));

  const add = (name: string): void => {
    if (!owned.has(name)) patch({ feats: [...ownedFeats, name] });
  };

  const remove = (name: string): void => {
    // Drop any option with it, or a stale weapon choice would reappear if the same
    // feat were taken again later.
    const options = { ...featOptions };
    delete options[name];
    patch({ feats: ownedFeats.filter((feat) => feat !== name), feat_options: options });
  };

  const chooseWeapon = (feat: string, weapon: string): void => {
    const next = { ...featOptions };
    if (weapon) {
      next[feat] = weapon;
    } else {
      delete next[feat];
    }
    patch({ feat_options: next });
  };

  return (
    <section aria-labelledby="section-feats" className="editor__section">
      <h2 id="section-feats">{t("editor.section.feats")}</h2>

      {budget && (
        <div className="feats__budget">
          <p className={budget.spent > budget.available ? "points points--over" : "points"}>
            {t("feats.count.budget", { spent: budget.spent, available: budget.available })}
            {budget.spent > budget.available && <span role="alert"> {t("feats.count.over")}</span>}
          </p>

          {/* Where the number comes from, the same way every other figure on the
              sheet can be opened up. */}
          <details>
            <summary>{t("feats.count.detail")}</summary>
            <ul className="feats__slots">
              {budget.slots.map((slot, index) => (
                <li key={index}>
                  {slot.source === "base" ? t("feats.slot.base") : slot.source} · nivel {slot.level}
                  {slot.feat ? ` · ${slot.feat}` : ""}
                  {slot.types.length > 0 ? ` · ${slot.types.join(", ")}` : ""}
                </li>
              ))}
            </ul>
          </details>

          {budget.granted.length > 0 && (
            <p className="feats__granted">
              {t("feats.granted")}: {budget.granted.join(", ")}
            </p>
          )}
        </div>
      )}

      <div className="picker-filters">
        <div className="field">
          <label htmlFor="feat-type">{t("feats.type")}</label>
          <select id="feat-type" value={type} onChange={(event) => setType(event.target.value)}>
            <option value={ALL_TYPES}>{t("feats.type.all")}</option>
            {slotFilters.size > 0 && (
              <optgroup label={t("feats.filter.slots")}>
                {[...slotFilters].map(([key, filter]) => (
                  <option key={key} value={key}>
                    {filter.label}
                  </option>
                ))}
              </optgroup>
            )}
            <optgroup label={t("feats.filter.types")}>
              {featTypes.map((featType) => (
                <option key={featType} value={featType}>
                  {featType}
                </option>
              ))}
            </optgroup>
          </select>
        </div>

        <div className="field">
          <label htmlFor="feat-search">{t("feats.search")}</label>
          <input
            id="feat-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>

        <label className="feats__eligible">
          <input
            type="checkbox"
            checked={onlyEligible}
            onChange={(event) => setOnlyEligible(event.target.checked)}
          />
          {t("feats.onlyEligible")}
        </label>
      </div>

      <p className="counter" role="status">
        {t("feats.count", { count: visible.length })}
      </p>
      {activeSlot && slotNote && <p className="feats__granted">{slotNote}</p>}

      {visible.length === 0 ? (
        <p>{t("feats.none")}</p>
      ) : (
        <ul className="picker-list" aria-label={t("feats.add")}>
          {visible.map((feat) => (
            <li key={feat.slug} className={feat.is_eligible ? undefined : "is-ineligible"}>
              {/* The name opens the details dialog; hovering shows the same summary
                  as a tooltip, so scanning the list never needs a click. */}
              <button
                type="button"
                className="picker-list__name"
                title={summaryOf(feat)}
                aria-label={t("feats.details", { feat: feat.name })}
                onClick={() => setDetailed(feat)}
              >
                {feat.name}
                {!feat.is_eligible && <span aria-hidden="true"> ⚠</span>}
              </button>
              {/* Adding never requires opening the dialog, so bulk entry stays fast. */}
              <button
                type="button"
                aria-label={t("feats.addNamed", { feat: feat.name })}
                disabled={owned.has(feat.name)}
                onClick={() => add(feat.name)}
              >
                +
              </button>
            </li>
          ))}
        </ul>
      )}

      <ul className="owned-feats" aria-label={t("feats.owned")}>
        {ownedFeats.map((feat) => {
          const known = byName.get(feat);
          return (
            <li key={feat}>
              {/* Selected feats get the same tooltip and details dialog as the ones
                  in the list. A feat absent from the catalog (an imported or
                  house-ruled one) has nothing to show, so it stays plain text. */}
              {known ? (
                <button
                  type="button"
                  className="chip__name"
                  title={summaryOf(known)}
                  aria-label={t("feats.details", { feat })}
                  onClick={() => setDetailed(known)}
                >
                  {feat}
                </button>
              ) : (
                feat
              )}
              <button
                type="button"
                aria-label={t("feats.remove", { feat })}
                onClick={() => remove(feat)}
              >
                ×
              </button>

              {/* Feats taken "for a weapon" do nothing until one is picked, so the
                  choice sits on the chip rather than hidden behind the dialog. */}
              {known?.choice_kind === "weapon" && (
                <select
                  aria-label={t("feats.choice.weapon", { feat })}
                  value={featOptions[feat] ?? ""}
                  onChange={(event) => chooseWeapon(feat, event.target.value)}
                >
                  <option value="">{t("feats.choice.none")}</option>
                  {weaponNames.map((name) => (
                    <option key={name} value={name}>
                      {name}
                    </option>
                  ))}
                </select>
              )}
            </li>
          );
        })}
      </ul>

      {detailed && (
        <Modal title={detailed.name} onClose={() => setDetailed(null)}>
          <dl className="details-grid">
            <dt>{t("feats.dialog.types")}</dt>
            <dd>{detailed.types.join(", ")}</dd>

            <dt>{t("feats.dialog.prerequisites")}</dt>
            <dd>{detailed.prerequisites ?? t("feats.dialog.none")}</dd>

            <dt>{t("feats.dialog.benefit")}</dt>
            <dd>{detailed.benefit ?? t("feats.dialog.none")}</dd>
          </dl>

          <p className={detailed.is_eligible ? "details-grid__ok" : "details-grid__warn"}>
            {detailed.is_eligible ? t("feats.dialog.eligible") : t("feats.dialog.notEligible")}
          </p>

          <button
            type="button"
            className="button"
            disabled={owned.has(detailed.name)}
            onClick={() => {
              add(detailed.name);
              setDetailed(null);
            }}
          >
            {owned.has(detailed.name) ? t("feats.alreadyOwned") : t("feats.add")}
          </button>
        </Modal>
      )}
    </section>
  );
}

/** Tooltip text: the benefit summary, with the unmet prerequisite when relevant. */
function summaryOf(feat: FeatDTO): string {
  const parts = [feat.benefit ?? ""];
  if (!feat.is_eligible) {
    parts.push(t("feats.ineligible", { prereq: feat.prerequisites ?? "?" }));
  }
  return parts.filter(Boolean).join(" — ");
}
