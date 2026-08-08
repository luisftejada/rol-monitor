import { useQuery } from "@tanstack/react-query";

import {
  getAlignments,
  getArmor,
  getClasses,
  getConditions,
  getFeats,
  getMeta,
  getRaces,
  getSkills,
  getWeapons,
  type FeatParams,
} from "@/api/rules";

// The rules catalog is immutable per corpus version, so cache it aggressively.
const CATALOG = { staleTime: Infinity, gcTime: Infinity } as const;

export function useMeta() {
  return useQuery({ queryKey: ["rules", "meta"], queryFn: getMeta, ...CATALOG });
}

export function useAlignments() {
  return useQuery({ queryKey: ["rules", "alignments"], queryFn: getAlignments, ...CATALOG });
}

export function useRaces() {
  return useQuery({ queryKey: ["rules", "races"], queryFn: getRaces, ...CATALOG });
}

export function useClasses(includePrestige = false) {
  return useQuery({
    queryKey: ["rules", "classes", includePrestige],
    queryFn: () => getClasses(includePrestige),
    ...CATALOG,
  });
}

export function useSkills() {
  return useQuery({ queryKey: ["rules", "skills"], queryFn: getSkills, ...CATALOG });
}

export function useWeapons() {
  return useQuery({ queryKey: ["rules", "weapons"], queryFn: getWeapons, ...CATALOG });
}

export function useArmor() {
  return useQuery({ queryKey: ["rules", "armor"], queryFn: getArmor, ...CATALOG });
}

export function useConditions() {
  return useQuery({ queryKey: ["rules", "conditions"], queryFn: getConditions, ...CATALOG });
}

export function useFeats(params: FeatParams) {
  return useQuery({
    queryKey: ["rules", "feats", params],
    queryFn: () => getFeats(params),
    ...CATALOG,
  });
}
