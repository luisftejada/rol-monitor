import type { CharacterRead, StancesIn } from "@/api/types";
import { t, type MessageKey } from "@/i18n";
import type { CombatMutations } from "@/features/tracker/useCombatMutations";

interface StanceTogglesProps {
  character: CharacterRead;
  mutations: CombatMutations;
}

const STANCE_KEYS: (keyof StancesIn)[] = [
  "charge",
  "fighting_defensively",
  "total_defense",
  "power_attack",
  "combat_expertise",
  "flanking",
  "higher_ground",
];

const EMPTY_STANCES: StancesIn = {
  charge: false,
  fighting_defensively: false,
  total_defense: false,
  power_attack: false,
  combat_expertise: false,
  flanking: false,
  higher_ground: false,
};

export function StanceToggles({ character, mutations }: StanceTogglesProps): React.JSX.Element {
  const stances = { ...EMPTY_STANCES, ...(character.stances ?? {}) };

  const toggle = (key: keyof StancesIn, checked: boolean): void => {
    mutations.patch.mutate({ stances: { ...stances, [key]: checked } });
  };

  return (
    <section aria-labelledby="stances-heading" className="tracker__block">
      <h3 id="stances-heading">{t("tracker.stances")}</h3>
      <ul className="stances">
        {STANCE_KEYS.map((key) => (
          <li key={key}>
            <label>
              <input
                type="checkbox"
                checked={stances[key]}
                onChange={(event) => toggle(key, event.target.checked)}
              />
              {t(`tracker.stance.${key}` as MessageKey)}
            </label>
          </li>
        ))}
      </ul>
    </section>
  );
}
