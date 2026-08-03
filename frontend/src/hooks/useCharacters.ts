import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  deleteCharacter,
  duplicateCharacter,
  getCharacter,
  getCharacters,
  getCombatSheet,
  type ListParams,
} from "@/api/characters";

export const characterKeys = {
  all: ["characters"] as const,
  list: (params: ListParams) => ["characters", "list", params] as const,
  detail: (id: string) => ["characters", "detail", id] as const,
  combatSheet: (id: string) => ["characters", "combat-sheet", id] as const,
};

export function useCharacters(params: ListParams = {}) {
  return useQuery({
    queryKey: characterKeys.list(params),
    queryFn: () => getCharacters(params),
  });
}

export function useCharacter(id: string) {
  return useQuery({
    queryKey: characterKeys.detail(id),
    queryFn: () => getCharacter(id),
  });
}

export function useCombatSheet(id: string) {
  return useQuery({
    queryKey: characterKeys.combatSheet(id),
    queryFn: () => getCombatSheet(id),
  });
}

export function useDuplicateCharacter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => duplicateCharacter(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: characterKeys.all }),
  });
}

export function useDeleteCharacter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteCharacter(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: characterKeys.all }),
  });
}
