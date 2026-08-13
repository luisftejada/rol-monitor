import type { CombatSheetResponse } from "@/api/types";
import { AttackLines } from "@/components/AttackLines";
import { StatBreakdown } from "@/components/StatBreakdown";
import { t, type MessageKey } from "@/i18n";
import { visibleAttacks } from "@/lib/attacks";
import { signed } from "@/lib/format";

const ABILITY_ORDER = ["Fue", "Des", "Con", "Int", "Sab", "Car"] as const;
const SAVE_ORDER = ["Fortaleza", "Reflejos", "Voluntad"] as const;

interface CombatCardProps {
  name: string;
  sheet: CombatSheetResponse;
  /** Lines the player trimmed in each weapon's dialog. The read-only sheet honours
   * the same choice the editor does; a line hidden in one is hidden in both. */
  hiddenAttackLines?: string[];
}

export function CombatCard({ name, sheet, hiddenAttackLines }: CombatCardProps): React.JSX.Element {
  return (
    <article className="card" aria-label={name} aria-live="polite">
      <header className="card__header">
        <h2>{name}</h2>
        <p className="card__bab">
          {t("sheet.bab")} {signed(sheet.bab.total)}{" "}
          <span className="card__iteratives">({sheet.bab.iteratives.map(signed).join(" / ")})</span>
        </p>
      </header>

      <section className="card__abilities">
        {ABILITY_ORDER.map((abbr) => {
          const ability = sheet.abilities[abbr];
          if (!ability) return null;
          return (
            <div key={abbr} className="ability">
              <span className="ability__name">{abbr}</span>
              <span className="ability__score">{ability.score}</span>
              <span className="ability__mod">{signed(ability.modifier)}</span>
            </div>
          );
        })}
      </section>

      <section className="card__defense">
        <StatBreakdown
          label={t("sheet.ac")}
          value={String(sheet.ac.total)}
          breakdown={sheet.ac.breakdown}
          suppressed={sheet.ac.suppressed}
        />
        <p className="card__secondary">
          <span>
            {t("sheet.ac.touch")}: {sheet.ac.touch}
          </span>
          <span>
            {t("sheet.ac.flat")}: {sheet.ac.flat_footed}
          </span>
        </p>
      </section>

      <section className="card__saves">
        {SAVE_ORDER.map((kind) => {
          const save = sheet.saves[kind];
          if (!save) return null;
          return (
            <StatBreakdown
              key={kind}
              label={t(`sheet.save.${kind}` as MessageKey)}
              value={signed(save.total)}
              breakdown={save.breakdown}
              suppressed={save.suppressed}
            />
          );
        })}
      </section>

      <section className="card__tactics">
        <StatBreakdown
          label={t("sheet.initiative")}
          value={signed(sheet.initiative.total)}
          breakdown={sheet.initiative.breakdown}
          suppressed={sheet.initiative.suppressed}
        />
        <StatBreakdown
          label={t("sheet.cmb")}
          value={signed(sheet.cmb.total)}
          breakdown={sheet.cmb.breakdown}
          suppressed={sheet.cmb.suppressed}
        />
        <StatBreakdown
          label={t("sheet.cmd")}
          value={String(sheet.cmd.total)}
          breakdown={sheet.cmd.breakdown}
          suppressed={sheet.cmd.suppressed}
        />
      </section>

      {sheet.attacks.length > 0 && (
        <section className="card__attacks">
          <h3>{t("sheet.attacks")}</h3>
          <AttackLines attacks={visibleAttacks(sheet.attacks, hiddenAttackLines)} />
        </section>
      )}

      {sheet.skills.length > 0 && (
        <section className="card__skills">
          <h3>{t("sheet.skills")}</h3>
          {/* Every skill is listed, so the ones actually trained have to say so:
              among 35 rows, a bonus alone does not tell you where the ranks went. */}
          {sheet.skills.map((skill) => (
            <StatBreakdown
              key={skill.slug}
              label={`${skill.name}${skill.is_class_skill ? " ★" : ""}`}
              note={skill.ranks > 0 ? t("sheet.skill.ranks", { count: skill.ranks }) : undefined}
              value={signed(skill.total)}
              breakdown={skill.breakdown}
              suppressed={skill.suppressed}
            />
          ))}
        </section>
      )}

      <section className="card__vitals">
        <p>
          {t("sheet.hp")}: {sheet.hp.current}/{sheet.hp.max}
          {sheet.hp.temporary > 0 && ` (+${sheet.hp.temporary} ${t("sheet.hp.temp")})`}
        </p>
        <p>
          {t("sheet.speed")}: {t("sheet.speed.feet", { value: sheet.speed.final_ft })}
        </p>
        <p>
          {t("sheet.acp")}: {sheet.armor_check_penalty} · {t("sheet.asf")}:{" "}
          {sheet.arcane_spell_failure}%
        </p>
      </section>

      {sheet.warnings.length > 0 && (
        <section aria-label={t("sheet.warnings")} className="card__warnings" role="alert">
          <h3>{t("sheet.warnings")}</h3>
          <ul>
            {sheet.warnings.map((warning, index) => (
              <li key={index}>{warning}</li>
            ))}
          </ul>
        </section>
      )}
    </article>
  );
}
