import type { LevelUpResponse } from "@/api/types";
import { Modal } from "@/components/Modal";
import { t } from "@/i18n";
import { signed } from "@/lib/format";

interface LevelUpDialogProps {
  report: LevelUpResponse;
  onClose: () => void;
}

/**
 * What the next level buys, as a report. It applies nothing by design: the owner
 * enters the result in the cards that already exist, so this is a checklist to work
 * through rather than a wizard that decides.
 *
 * Everything is shown as before → after where it is a number, because "Fortaleza +4"
 * leaves you wondering whether that is the gain or the total.
 */
export function LevelUpDialog({ report, onClose }: LevelUpDialogProps): React.JSX.Element {
  const saves = Object.keys(report.saves_after);

  return (
    <Modal
      title={t("levelUp.title", {
        class: report.class_name,
        from: report.class_level_before,
        to: report.class_level_after,
      })}
      onClose={onClose}
    >
      <div className="level-up">
        <p className="level-up__total">
          {t("levelUp.total", {
            from: report.total_level_before,
            to: report.total_level_after,
          })}
        </p>

        <dl className="level-up__figures">
          <dt>{t("sheet.hp")}</dt>
          <dd>
            {t("levelUp.hitPoints", {
              die: report.hit_die,
              con: signed(report.constitution_modifier),
            })}
          </dd>

          <dt>{t("sheet.bab")}</dt>
          <dd>
            {signed(report.base_attack_before)} →{" "}
            <strong>{signed(report.base_attack_after)}</strong>
          </dd>

          {saves.map((save) => (
            <Fragment key={save}>
              <dt>{save}</dt>
              <dd>
                {signed(report.saves_before[save] ?? 0)} →{" "}
                <strong>{signed(report.saves_after[save] ?? 0)}</strong>
              </dd>
            </Fragment>
          ))}

          <dt>{t("skills.column.ranks")}</dt>
          <dd>{signed(report.skill_ranks)}</dd>
        </dl>

        {/* The choices, kept apart from the figures: these are the ones that need a
            decision rather than a number copied across. */}
        <ul className="level-up__choices">
          {report.grants_feat && <li>{t("levelUp.feat")}</li>}
          {report.grants_ability_increment && <li>{t("levelUp.abilityIncrement")}</li>}
          {report.bonus_feat_slots.map((slot, index) => (
            <li key={index}>
              {t("levelUp.bonusFeat", {
                what: slot.types.length > 0 ? slot.types.join(", ") : (slot.feat ?? slot.choice),
              })}
            </li>
          ))}
          {report.class_features.map((feature) => (
            <li key={feature}>{t("levelUp.classFeature", { feature })}</li>
          ))}
          {report.favored_class_note && <li>{report.favored_class_note}</li>}
          {report.spells_per_day && (
            <li>{t("levelUp.spells", { spells: report.spells_per_day })}</li>
          )}
        </ul>

        {report.warnings.length > 0 && (
          <ul className="level-up__warnings" role="alert">
            {report.warnings.map((warning) => (
              <li key={warning}>{warning}</li>
            ))}
          </ul>
        )}

        <p className="level-up__note">{t("levelUp.applyByHand")}</p>
      </div>
    </Modal>
  );
}

/** Local alias so the save rows stay a flat definition list. */
function Fragment({ children }: { children: React.ReactNode }): React.JSX.Element {
  return <>{children}</>;
}
