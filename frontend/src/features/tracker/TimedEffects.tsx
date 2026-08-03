import type { CharacterRead } from "@/api/types";
import { t } from "@/i18n";
import { signed } from "@/lib/format";
import type { CombatMutations } from "@/features/tracker/useCombatMutations";

interface TimedEffectsProps {
  character: CharacterRead;
  mutations: CombatMutations;
}

export function TimedEffects({ character, mutations }: TimedEffectsProps): React.JSX.Element {
  const modifiers = character.modifiers ?? [];

  return (
    <section aria-labelledby="effects-heading" className="tracker__block">
      <div className="tracker__block-head">
        <h3 id="effects-heading">{t("tracker.effects")}</h3>
        <button type="button" onClick={() => mutations.tick.mutate(1)}>
          {t("tracker.nextRound")}
        </button>
      </div>

      {modifiers.length === 0 ? (
        <p>{t("tracker.effects.none")}</p>
      ) : (
        <ul className="effects" aria-label={t("tracker.effects")}>
          {modifiers.map((modifier) => (
            <li key={modifier.id} className={modifier.is_active ? undefined : "is-inactive"}>
              <label>
                <input
                  type="checkbox"
                  checked={modifier.is_active ?? true}
                  aria-label={modifier.source}
                  onChange={(event) =>
                    mutations.patchModifier.mutate({
                      modifierId: modifier.id ?? "",
                      body: { is_active: event.target.checked },
                    })
                  }
                />
                {modifier.source} ({signed(modifier.value)} {modifier.target})
              </label>
              <span className="effects__rounds">
                {modifier.expires_in_rounds == null
                  ? t("tracker.effects.permanent")
                  : t("tracker.effects.rounds", { rounds: modifier.expires_in_rounds })}
              </span>
              <button
                type="button"
                aria-label={t("feats.remove", { feat: modifier.source })}
                onClick={() => mutations.removeModifier.mutate(modifier.id ?? "")}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
