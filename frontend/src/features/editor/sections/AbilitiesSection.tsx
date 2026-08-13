import { useState } from "react";

import type { BabDTO, CharacterCreate, ValueBreakdown } from "@/api/types";
import { StatBreakdown } from "@/components/StatBreakdown";
import { ABILITY_ORDER, POINT_BUY_BUDGET, STANDARD_ARRAY } from "@/features/editor/draft";
import { HitPointsPerLevel } from "@/features/editor/sections/HitPointsPerLevel";
import { useMeta, useRaces } from "@/hooks/useRules";
import { t } from "@/i18n";
import { signed } from "@/lib/format";

interface SectionProps {
  draft: CharacterCreate;
  patch: (partial: Partial<CharacterCreate>) => void;
  /**
   * Ability modifiers keyed by abbreviation, as derived by the backend. The
   * modifier is a Pathfinder formula, so it is never recomputed here — the
   * column renders what ``/derive`` returned, and stays blank until it has.
   */
  modifiers?: Record<string, number>;
  /** The rest of `/derive`'s tactical numbers, shown here rather than only in the
   * live preview: they read off the same ability scores this card edits. */
  bab?: BabDTO;
  initiative?: ValueBreakdown;
  cmb?: ValueBreakdown;
  cmd?: ValueBreakdown;
}

type Method = "point-buy" | "manual" | "standard";

const FLEXIBLE_KEY = "cualquiera";

export function AbilitiesSection({
  draft,
  patch,
  modifiers = {},
  bab,
  initiative,
  cmb,
  cmd,
}: SectionProps): React.JSX.Element {
  const meta = useMeta();
  const races = useRaces();
  const [method, setMethod] = useState<Method>("point-buy");
  // The budget is a table convention, not character data, so it lives in the
  // editor rather than on the character. It only drives the over-budget warning.
  const [budget, setBudget] = useState(POINT_BUY_BUDGET);

  const costs = meta.data?.point_buy_costs ?? {};
  const baseScores = draft.base_scores ?? {};
  const racialChoices = draft.racial_bonus_choices ?? {};
  const race = (races.data ?? []).find((r) => r.slug === draft.race);
  const raceMods = race?.ability_modifiers ?? {};
  const flexibleAmount = raceMods[FLEXIBLE_KEY];

  const racialFor = (abbr: string): number => (raceMods[abbr] ?? 0) + (racialChoices[abbr] ?? 0);

  const setScore = (abbr: string, score: number): void => {
    patch({ base_scores: { ...baseScores, [abbr]: score } });
  };

  const pointsSpent = ABILITY_ORDER.reduce(
    (sum, abbr) => sum + (costs[String(baseScores[abbr] ?? 10)] ?? 0),
    0,
  );

  const applyStandardArray = (): void => {
    const scores: Record<string, number> = {};
    ABILITY_ORDER.forEach((abbr, index) => {
      scores[abbr] = STANDARD_ARRAY[index] ?? 10;
    });
    patch({ base_scores: scores });
  };

  const chooseMethod = (next: Method): void => {
    setMethod(next);
    if (next === "standard") applyStandardArray();
  };

  return (
    <section aria-labelledby="section-abilities" className="editor__section">
      <h2 id="section-abilities">{t("editor.section.abilities")}</h2>

      <div className="ability-method-row">
        <fieldset className="ability-method">
          <legend>{t("abilities.method")}</legend>
          {(["point-buy", "manual", "standard"] as const).map((option) => (
            <label key={option}>
              <input
                type="radio"
                name="ability-method"
                checked={method === option}
                onChange={() => chooseMethod(option)}
              />
              {t(`abilities.method.${option === "point-buy" ? "pointBuy" : option}` as const)}
            </label>
          ))}
        </fieldset>

        {method === "point-buy" && (
          <div className="point-budget">
            <label htmlFor="point-budget">{t("abilities.budget")}</label>
            <span className="stepper">
              <button
                type="button"
                aria-label={t("abilities.budget.decrement")}
                onClick={() => setBudget(Math.max(0, budget - 1))}
              >
                −
              </button>
              <input
                id="point-budget"
                type="number"
                min={0}
                value={budget}
                onChange={(event) => setBudget(Math.max(0, Number(event.target.value)))}
              />
              <button
                type="button"
                aria-label={t("abilities.budget.increment")}
                onClick={() => setBudget(budget + 1)}
              >
                +
              </button>
            </span>
          </div>
        )}
      </div>

      {flexibleAmount !== undefined && (
        <label className="field">
          <span>{`+${flexibleAmount} racial`}</span>
          <select
            value={Object.keys(racialChoices)[0] ?? ""}
            onChange={(event) =>
              patch({
                racial_bonus_choices: event.target.value
                  ? { [event.target.value]: flexibleAmount }
                  : {},
              })
            }
          >
            <option value="">—</option>
            {ABILITY_ORDER.map((abbr) => (
              <option key={abbr} value={abbr}>
                {abbr}
              </option>
            ))}
          </select>
        </label>
      )}

      {method === "point-buy" && (
        <p className={pointsSpent > budget ? "points points--over" : "points"}>
          {t("abilities.points", { spent: pointsSpent, budget })}
          {pointsSpent > budget && <span role="alert"> {t("abilities.pointsOver")}</span>}
        </p>
      )}

      <table className="abilities">
        <thead>
          <tr>
            <th scope="col">·</th>
            <th scope="col">{t("abilities.col.base")}</th>
            <th scope="col">{t("abilities.col.racial")}</th>
            <th scope="col">{t("abilities.col.final")}</th>
            <th scope="col">{t("abilities.col.modifier")}</th>
          </tr>
        </thead>
        <tbody>
          {ABILITY_ORDER.map((abbr) => {
            const base = baseScores[abbr] ?? 10;
            const racial = racialFor(abbr);
            const modifier = modifiers[abbr];
            return (
              <tr key={abbr}>
                <th scope="row">{abbr}</th>
                <td>
                  {method === "standard" ? (
                    <StandardArraySelect abbr={abbr} scores={baseScores} onPick={setScore} />
                  ) : method === "point-buy" ? (
                    <PointBuyStepper abbr={abbr} value={base} onChange={setScore} />
                  ) : (
                    <input
                      type="number"
                      aria-label={abbr}
                      value={base}
                      onChange={(event) => setScore(abbr, Number(event.target.value))}
                    />
                  )}
                </td>
                <td>{racial >= 0 ? `+${racial}` : racial}</td>
                <td>{base + racial}</td>
                <td className="abilities__modifier">
                  {modifier === undefined ? "—" : signed(modifier)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Expandable like every other derived figure: on a multiclass sheet the total
          is the one a player is most likely to doubt, and the breakdown names the
          class that cost the points. */}
      <StatBreakdown
        label={t("sheet.bab")}
        value={
          bab
            ? `${signed(bab.total)}${
                bab.iteratives.length > 1 ? ` (${bab.iteratives.map(signed).join(" / ")})` : ""
              }`
            : "—"
        }
        breakdown={bab?.breakdown ?? []}
      />

      {/* Hit points live here because they are read off Constitution, which this card
          edits. Max is derived per level elsewhere; these two are the running state a
          GM changes mid-fight. */}
      <div className="field-grid">
        <label className="field field--narrow">
          <span>{t("sheet.hp.current")}</span>
          <input
            type="number"
            value={draft.current_hp ?? 0}
            onChange={(event) => patch({ current_hp: Number(event.target.value) })}
          />
        </label>
        <label className="field field--narrow">
          <span>{t("sheet.hp.temp")}</span>
          <input
            type="number"
            min={0}
            value={draft.temporary_hp ?? 0}
            onChange={(event) => patch({ temporary_hp: Math.max(0, Number(event.target.value)) })}
          />
        </label>
      </div>

      <HitPointsPerLevel draft={draft} patch={patch} />

      <div className="card__tactics">
        <StatBreakdown
          label={t("sheet.initiative")}
          value={initiative ? signed(initiative.total) : "—"}
          breakdown={initiative?.breakdown ?? []}
          suppressed={initiative?.suppressed}
        />
        <StatBreakdown
          label={t("sheet.cmb")}
          value={cmb ? signed(cmb.total) : "—"}
          breakdown={cmb?.breakdown ?? []}
          suppressed={cmb?.suppressed}
        />
        <StatBreakdown
          label={t("sheet.cmd")}
          value={cmd ? String(cmd.total) : "—"}
          breakdown={cmd?.breakdown ?? []}
          suppressed={cmd?.suppressed}
        />
      </div>
    </section>
  );
}

function PointBuyStepper({
  abbr,
  value,
  onChange,
}: {
  abbr: string;
  value: number;
  onChange: (abbr: string, score: number) => void;
}): React.JSX.Element {
  return (
    <span className="stepper">
      <button
        type="button"
        aria-label={`− ${abbr}`}
        onClick={() => onChange(abbr, Math.max(7, value - 1))}
      >
        −
      </button>
      <span aria-label={abbr}>{value}</span>
      <button
        type="button"
        aria-label={`+ ${abbr}`}
        onClick={() => onChange(abbr, Math.min(18, value + 1))}
      >
        +
      </button>
    </span>
  );
}

function StandardArraySelect({
  abbr,
  scores,
  onPick,
}: {
  abbr: string;
  scores: Record<string, number>;
  onPick: (abbr: string, score: number) => void;
}): React.JSX.Element {
  const usedElsewhere = new Set(
    ABILITY_ORDER.filter((other) => other !== abbr).map((other) => scores[other]),
  );
  return (
    <select
      aria-label={abbr}
      value={scores[abbr] ?? ""}
      onChange={(event) => onPick(abbr, Number(event.target.value))}
    >
      {STANDARD_ARRAY.map((score) => (
        <option key={score} value={score} disabled={usedElsewhere.has(score)}>
          {score}
        </option>
      ))}
    </select>
  );
}
