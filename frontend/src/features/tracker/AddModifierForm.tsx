import { useState } from "react";

import { useMeta } from "@/hooks/useRules";
import { t } from "@/i18n";
import type { CombatMutations } from "@/features/tracker/useCombatMutations";

interface AddModifierFormProps {
  mutations: CombatMutations;
}

const TARGETS = [
  "AC",
  "ATTACK_MELEE",
  "ATTACK_RANGED",
  "ALL_ATTACKS",
  "DAMAGE_MELEE",
  "ALL_SAVES",
  "SAVE_FORT",
  "SAVE_REF",
  "SAVE_WILL",
  "INITIATIVE",
  "CMB",
  "CMD",
  "SPEED",
];

export function AddModifierForm({ mutations }: AddModifierFormProps): React.JSX.Element {
  const meta = useMeta();
  const [source, setSource] = useState("");
  const [target, setTarget] = useState("AC");
  const [value, setValue] = useState(1);
  const [bonusType, setBonusType] = useState("");
  const [expires, setExpires] = useState("");

  const bonusTypes = [
    ...(meta.data?.bonus_types.do_not_stack ?? []),
    ...(meta.data?.bonus_types.always_stack ?? []),
  ].filter((label) => !label.includes("("));

  const submit = (event: React.FormEvent): void => {
    event.preventDefault();
    if (!source.trim()) return;
    mutations.addModifier.mutate({
      source: source.trim(),
      target,
      value,
      bonus_type: bonusType || null,
      source_kind: "manual",
      is_active: true,
      expires_in_rounds: expires ? Number(expires) : null,
    });
    setSource("");
    setValue(1);
    setExpires("");
  };

  return (
    <form
      className="tracker__block add-modifier"
      onSubmit={submit}
      aria-label={t("tracker.addModifier")}
    >
      <h3>{t("tracker.addModifier")}</h3>
      <label className="field">
        <span>{t("tracker.mod.source")}</span>
        <input value={source} onChange={(event) => setSource(event.target.value)} />
      </label>
      <label className="field">
        <span>{t("tracker.mod.target")}</span>
        <select value={target} onChange={(event) => setTarget(event.target.value)}>
          {TARGETS.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
      <label className="field field--narrow">
        <span>{t("tracker.mod.value")}</span>
        <input
          type="number"
          value={value}
          onChange={(event) => setValue(Number(event.target.value))}
        />
      </label>
      <label className="field">
        <span>{t("tracker.mod.type")}</span>
        <select value={bonusType} onChange={(event) => setBonusType(event.target.value)}>
          <option value="">{t("tracker.mod.untyped")}</option>
          {bonusTypes.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </label>
      <label className="field field--narrow">
        <span>{t("tracker.mod.expires")}</span>
        <input
          type="number"
          min={1}
          value={expires}
          onChange={(event) => setExpires(event.target.value)}
        />
      </label>
      <button type="submit">{t("tracker.mod.add")}</button>
    </form>
  );
}
