import type { CharacterRead } from "@/api/types";
import { t } from "@/i18n";
import { AddModifierForm } from "@/features/tracker/AddModifierForm";
import { ConditionChips } from "@/features/tracker/ConditionChips";
import { HpWidget } from "@/features/tracker/HpWidget";
import { StanceToggles } from "@/features/tracker/StanceToggles";
import { TimedEffects } from "@/features/tracker/TimedEffects";
import { useCombatMutations } from "@/features/tracker/useCombatMutations";

interface CombatTrackerProps {
  character: CharacterRead;
}

/** Live combat tracking: HP, conditions, stances, timed effects, ad-hoc modifiers.
 * Each action mutates the persisted character; the combat card refreshes in turn. */
export function CombatTracker({ character }: CombatTrackerProps): React.JSX.Element {
  const mutations = useCombatMutations(character.id);

  return (
    <div className="tracker" aria-label={t("tracker.title")}>
      <HpWidget character={character} mutations={mutations} />
      <ConditionChips character={character} mutations={mutations} />
      <StanceToggles character={character} mutations={mutations} />
      <TimedEffects character={character} mutations={mutations} />
      <AddModifierForm mutations={mutations} />
    </div>
  );
}
