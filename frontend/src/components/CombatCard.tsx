import type { CombatSheetResponse } from "@/api/types";
import { StatBreakdown } from "@/components/StatBreakdown";
import { t, type MessageKey } from "@/i18n";
import { signed } from "@/lib/format";

const ABILITY_ORDER = ["Fue", "Des", "Con", "Int", "Sab", "Car"] as const;
const SAVE_ORDER = ["Fortaleza", "Reflejos", "Voluntad"] as const;

interface CombatCardProps {
  name: string;
  sheet: CombatSheetResponse;
}

export function CombatCard({ name, sheet }: CombatCardProps): React.JSX.Element {
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
          {sheet.attacks.map((attack, index) => (
            <div key={`${attack.weapon}-${index}`} className="attack">
              <p className="attack__name">
                {attack.weapon}
                {!attack.is_proficient && (
                  <span className="attack__warn"> ({t("sheet.attack.notProficient")})</span>
                )}
              </p>
              <StatBreakdown
                label={attack.weapon}
                value={attack.attack_line}
                breakdown={attack.attack.breakdown}
                suppressed={attack.attack.suppressed}
              />
              {/* Manyshot rolls the first arrow's dice twice, so the first attack
                  is shown separately: "2d8 then 1d8" is not one number. */}
              {attack.first_attack_damage_expression && (
                <StatBreakdown
                  label={t("sheet.attack.firstDamage")}
                  value={attack.first_attack_damage_expression}
                  breakdown={attack.damage.breakdown}
                  suppressed={attack.damage.suppressed}
                />
              )}
              {attack.damage_expression && (
                <StatBreakdown
                  label={t("sheet.attack.damage")}
                  value={attack.damage_expression}
                  breakdown={attack.damage.breakdown}
                  suppressed={attack.damage.suppressed}
                />
              )}
              <p className="attack__crit">
                {t("sheet.attack.crit")}: {attack.threat_range}-20/×{attack.crit_multiplier}
              </p>
              {/* What a feat does to the *target* — a critical feat has no number of
                  yours to change, so it is shown where the GM confirms the crit. */}
              {attack.notes.length > 0 && (
                <ul className="attack__notes">
                  {attack.notes.map((note, noteIndex) => (
                    <li key={noteIndex}>{note}</li>
                  ))}
                </ul>
              )}
            </div>
          ))}
        </section>
      )}

      {sheet.skills.length > 0 && (
        <section className="card__skills">
          <h3>{t("sheet.skills")}</h3>
          {sheet.skills.map((skill) => (
            <StatBreakdown
              key={skill.slug}
              label={`${skill.name}${skill.is_class_skill ? " ★" : ""}`}
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
