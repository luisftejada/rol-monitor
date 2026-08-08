import type { CharacterRead, StancesIn } from "@/api/types";
import { useFeats } from "@/hooks/useRules";
import { t, type MessageKey } from "@/i18n";
import type { CombatMutations } from "@/features/tracker/useCombatMutations";

interface StanceTogglesProps {
  character: CharacterRead;
  mutations: CombatMutations;
}

/** The always-available stances; `feat_stances` is a list, handled separately. */
type BooleanStance = Exclude<keyof StancesIn, "feat_stances">;

const STANCE_KEYS: BooleanStance[] = [
  "charge",
  "fighting_defensively",
  "total_defense",
  "flanking",
  "higher_ground",
];

const EMPTY_STANCES: StancesIn = {
  charge: false,
  fighting_defensively: false,
  total_defense: false,
  flanking: false,
  higher_ground: false,
};

export function StanceToggles({ character, mutations }: StanceTogglesProps): React.JSX.Element {
  const stances = { ...EMPTY_STANCES, ...(character.stances ?? {}) };
  const feats = useFeats({ owned: character.feats ?? [] });

  // Only feats the character actually has, and only those the backend classifies as
  // a round-long choice — the frontend never decides that on rules grounds.
  const owned = new Set(character.feats ?? []);
  const featStances = (feats.data ?? []).filter((feat) => feat.is_stance && owned.has(feat.name));
  const active = stances.feat_stances ?? [];

  const toggle = (key: BooleanStance, checked: boolean): void => {
    mutations.patch.mutate({ stances: { ...stances, [key]: checked } });
  };

  const toggleFeat = (name: string, checked: boolean): void => {
    const next = checked ? [...active, name] : active.filter((feat) => feat !== name);
    mutations.patch.mutate({ stances: { ...stances, feat_stances: next } });
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

      {featStances.length > 0 && (
        <>
          <h4>{t("tracker.stances.fromFeats")}</h4>
          {/* Combat Expertise raises AC here and penalises attacks on its weapon
              line; without saying so, half of it looks missing. */}
          <p className="stances__note">{t("tracker.stances.fromFeats.note")}</p>
          <ul className="stances">
            {featStances.map((feat) => (
              <li key={feat.slug}>
                <label title={feat.benefit ?? undefined}>
                  <input
                    type="checkbox"
                    checked={active.includes(feat.name)}
                    onChange={(event) => toggleFeat(feat.name, event.target.checked)}
                  />
                  {feat.name}
                </label>
                {/* While it is on, spell out what it does: a bleed the GM must apply
                    each round is only useful if the number is in front of them. */}
                {active.includes(feat.name) && feat.benefit && (
                  <p className="stances__effect">{feat.benefit}</p>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
