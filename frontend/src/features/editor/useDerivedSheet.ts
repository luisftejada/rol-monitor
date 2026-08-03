import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";

import { deriveCharacter } from "@/api/characters";
import type { CharacterCreate } from "@/api/types";

function useDebounced<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delayMs);
    return () => clearTimeout(timer);
  }, [value, delayMs]);
  return debounced;
}

/**
 * Live combat sheet for the editor: debounces the draft (250 ms) and recomputes via
 * the stateless `/derive` endpoint. Previous data is kept while recomputing so the
 * card never flashes empty.
 */
export function useDerivedSheet(draft: CharacterCreate) {
  const debounced = useDebounced(draft, 250);
  return useQuery({
    queryKey: ["derive", debounced],
    queryFn: () => deriveCharacter(debounced),
    placeholderData: keepPreviousData,
  });
}
