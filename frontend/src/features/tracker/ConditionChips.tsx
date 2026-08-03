import type { CharacterRead } from "@/api/types";
import { Combobox } from "@/components/Combobox";
import { useConditions } from "@/hooks/useRules";
import { t } from "@/i18n";
import type { CombatMutations } from "@/features/tracker/useCombatMutations";

interface ConditionChipsProps {
  character: CharacterRead;
  mutations: CombatMutations;
}

export function ConditionChips({ character, mutations }: ConditionChipsProps): React.JSX.Element {
  const conditions = useConditions();
  const active = character.active_conditions ?? [];
  const catalog = conditions.data ?? [];
  const nameFor = (slug: string): string =>
    catalog.find((condition) => condition.slug === slug)?.name ?? slug;

  const options = catalog
    .filter((condition) => !active.includes(condition.slug))
    .map((condition) => ({ value: condition.slug, label: condition.name, hint: condition.effect }));

  return (
    <section aria-labelledby="conditions-heading" className="tracker__block">
      <h3 id="conditions-heading">{t("tracker.conditions")}</h3>

      {active.length === 0 ? (
        <p>{t("tracker.conditions.none")}</p>
      ) : (
        <ul className="chips" aria-label={t("tracker.conditions")}>
          {active.map((slug) => (
            <li key={slug} className="chip">
              {nameFor(slug)}
              <button
                type="button"
                aria-label={t("tracker.conditions.remove", { condition: nameFor(slug) })}
                onClick={() => mutations.setCondition.mutate({ condition: slug, active: false })}
              >
                ×
              </button>
            </li>
          ))}
        </ul>
      )}

      <Combobox
        label={t("tracker.conditions.add")}
        options={options}
        value={null}
        onChange={(slug) => mutations.setCondition.mutate({ condition: slug, active: true })}
        placeholder={t("tracker.conditions.add")}
      />
    </section>
  );
}
