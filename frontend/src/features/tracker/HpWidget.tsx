import { useState } from "react";

import type { CharacterRead } from "@/api/types";
import { t } from "@/i18n";
import type { CombatMutations } from "@/features/tracker/useCombatMutations";

interface HpWidgetProps {
  character: CharacterRead;
  mutations: CombatMutations;
}

export function HpWidget({ character, mutations }: HpWidgetProps): React.JSX.Element {
  const [amount, setAmount] = useState(1);
  const [temp, setTemp] = useState(0);

  const current = character.current_hp ?? 0;
  const max = character.max_hp ?? 0;
  const temporary = character.temporary_hp ?? 0;

  const applyDamage = (): void => {
    const absorbed = Math.min(temporary, amount);
    mutations.patch.mutate({
      temporary_hp: temporary - absorbed,
      current_hp: current - (amount - absorbed), // negative HP allowed
    });
  };

  const applyHeal = (): void => {
    mutations.patch.mutate({ current_hp: Math.min(max, current + amount) });
  };

  return (
    <section aria-labelledby="hp-heading" className="tracker__block">
      <h3 id="hp-heading">{t("tracker.hp")}</h3>
      <p className="hp__total">
        {t("tracker.hp.current", { current, max })}
        {temporary > 0 && ` (+${temporary})`}
      </p>

      <div className="hp__controls">
        <label className="field field--narrow">
          <span>{t("tracker.hp.amount")}</span>
          <input
            type="number"
            min={0}
            value={amount}
            onChange={(event) => setAmount(Math.max(0, Number(event.target.value)))}
          />
        </label>
        <button type="button" onClick={applyDamage}>
          {t("tracker.hp.damage")}
        </button>
        <button type="button" onClick={applyHeal}>
          {t("tracker.hp.heal")}
        </button>
      </div>

      <div className="hp__controls">
        <label className="field field--narrow">
          <span>{t("tracker.hp.temp")}</span>
          <input
            type="number"
            min={0}
            value={temp}
            onChange={(event) => setTemp(Math.max(0, Number(event.target.value)))}
          />
        </label>
        <button type="button" onClick={() => mutations.patch.mutate({ temporary_hp: temp })}>
          {t("tracker.hp.setTemp")}
        </button>
      </div>
    </section>
  );
}
