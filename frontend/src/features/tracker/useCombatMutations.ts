import { useMutation, useQueryClient } from "@tanstack/react-query";

import {
  addModifier,
  patchCharacter,
  patchModifier,
  removeModifier,
  setCondition,
  tickRounds,
} from "@/api/characters";
import type { CharacterPatch, ConditionUpdate, ModifierCreate, ModifierPatch } from "@/api/types";
import { characterKeys } from "@/hooks/useCharacters";

/** Combat-tracking mutations that refresh the character and its combat sheet. */
export function useCombatMutations(id: string) {
  const queryClient = useQueryClient();
  const onSuccess = (): void => {
    void queryClient.invalidateQueries({ queryKey: characterKeys.detail(id) });
    void queryClient.invalidateQueries({ queryKey: characterKeys.combatSheet(id) });
    void queryClient.invalidateQueries({ queryKey: characterKeys.all });
  };

  return {
    addModifier: useMutation({
      mutationFn: (body: ModifierCreate) => addModifier(id, body),
      onSuccess,
    }),
    removeModifier: useMutation({
      mutationFn: (modifierId: string) => removeModifier(id, modifierId),
      onSuccess,
    }),
    patchModifier: useMutation({
      mutationFn: (vars: { modifierId: string; body: ModifierPatch }) =>
        patchModifier(id, vars.modifierId, vars.body),
      onSuccess,
    }),
    setCondition: useMutation({
      mutationFn: (body: ConditionUpdate) => setCondition(id, body),
      onSuccess,
    }),
    tick: useMutation({ mutationFn: (rounds: number) => tickRounds(id, rounds), onSuccess }),
    patch: useMutation({
      mutationFn: (body: CharacterPatch) => patchCharacter(id, body),
      onSuccess,
    }),
  };
}

export type CombatMutations = ReturnType<typeof useCombatMutations>;
