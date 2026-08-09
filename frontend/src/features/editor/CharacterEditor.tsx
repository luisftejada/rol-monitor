import { useMutation } from "@tanstack/react-query";
import { useCallback, useEffect, useState } from "react";

import { createCharacter, updateCharacter } from "@/api/characters";
import type { CharacterCreate, CharacterRead } from "@/api/types";
import { CombatCard } from "@/components/CombatCard";
import { useDerivedSheet } from "@/features/editor/useDerivedSheet";
import { AbilitiesSection } from "@/features/editor/sections/AbilitiesSection";
import { ClassesSection } from "@/features/editor/sections/ClassesSection";
import { EquipmentSection } from "@/features/editor/sections/EquipmentSection";
import { FeatsSection } from "@/features/editor/sections/FeatsSection";
import { IdentitySection } from "@/features/editor/sections/IdentitySection";
import { SkillsSection } from "@/features/editor/sections/SkillsSection";
import { t, type MessageKey } from "@/i18n";

type SaveState = "idle" | "dirty" | "saving" | "saved" | "error";

interface CharacterEditorProps {
  initialDraft: CharacterCreate;
  mode: "create" | "edit";
  characterId?: string;
  onSaved?: (character: CharacterRead) => void;
}

const SECTIONS: { id: string; key: MessageKey }[] = [
  { id: "section-identity", key: "editor.section.identity" },
  { id: "section-abilities", key: "editor.section.abilities" },
  { id: "section-classes", key: "editor.section.classes" },
  { id: "section-skills", key: "editor.section.skills" },
  { id: "section-feats", key: "editor.section.feats" },
  { id: "section-equipment", key: "editor.section.equipment" },
];

export function CharacterEditor({
  initialDraft,
  mode,
  characterId,
  onSaved,
}: CharacterEditorProps): React.JSX.Element {
  const [draft, setDraft] = useState<CharacterCreate>(initialDraft);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const derived = useDerivedSheet(draft);

  const patch = useCallback((partial: Partial<CharacterCreate>): void => {
    setDraft((current) => ({ ...current, ...partial }));
    setSaveState("dirty");
  }, []);

  const save = useMutation({
    mutationFn: (body: CharacterCreate) =>
      mode === "edit" && characterId ? updateCharacter(characterId, body) : createCharacter(body),
    onMutate: () => setSaveState("saving"),
    onSuccess: (character) => {
      setSaveState("saved");
      onSaved?.(character);
    },
    onError: () => setSaveState("error"),
  });

  const triggerSave = useCallback(() => save.mutate(draft), [save, draft]);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent): void => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "s") {
        event.preventDefault();
        triggerSave();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [triggerSave]);

  const sheet = derived.data;
  const intModifier = sheet?.abilities.Int?.modifier ?? 0;
  const bab = sheet?.bab.total ?? 0;
  const abilityScores: Record<string, number> = {};
  const abilityModifiers: Record<string, number> = {};
  for (const [abbr, ability] of Object.entries(sheet?.abilities ?? {})) {
    abilityScores[abbr] = ability.score;
    abilityModifiers[abbr] = ability.modifier;
  }

  return (
    <div className="editor">
      <header className="editor__toolbar">
        <h1>{mode === "create" ? t("editor.new") : t("editor.edit")}</h1>
        <nav aria-label="secciones" className="editor__nav">
          {SECTIONS.map((section) => (
            <a key={section.id} href={`#${section.id}`}>
              {t(section.key)}
            </a>
          ))}
        </nav>
        <div className="editor__save">
          <span role="status">{t(`editor.saveState.${saveState}` as MessageKey)}</span>
          <button type="button" onClick={triggerSave} disabled={saveState === "saving"}>
            {t("editor.save")}
          </button>
        </div>
      </header>

      <div className="editor__panes">
        <form
          className="editor__form"
          onSubmit={(event) => {
            event.preventDefault();
            triggerSave();
          }}
        >
          <IdentitySection draft={draft} patch={patch} />
          <AbilitiesSection draft={draft} patch={patch} modifiers={abilityModifiers} />
          <ClassesSection draft={draft} patch={patch} />
          <SkillsSection
            draft={draft}
            patch={patch}
            intModifier={intModifier}
            derived={sheet?.skills}
          />
          <FeatsSection
            draft={draft}
            patch={patch}
            bab={bab}
            abilities={abilityScores}
            budget={sheet?.feats}
          />
          <EquipmentSection draft={draft} patch={patch} />
        </form>

        <aside className="editor__preview" aria-label={t("editor.livePreview")}>
          {sheet ? (
            <CombatCard name={draft.name} sheet={sheet} />
          ) : (
            <p role="status">{t("common.loading")}</p>
          )}
        </aside>
      </div>
    </div>
  );
}
