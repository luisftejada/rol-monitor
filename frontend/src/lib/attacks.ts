import type { AttackDTO } from "@/api/types";

/**
 * The attack lines a character has chosen to see.
 *
 * Every way of using a weapon is derived — each grip crossed with each declared
 * feat — which is the truth but also eight rows for one longsword. The player picks
 * per weapon which ones stay; the preference is stored as what to *hide*, so a line
 * that appears later (a new feat, a new weapon) shows up on its own.
 */
export function visibleAttacks(attacks: AttackDTO[], hidden: string[] = []): AttackDTO[] {
  if (hidden.length === 0) return attacks;
  const dropped = new Set(hidden);
  return attacks.filter((attack) => !attack.variant_key || !dropped.has(attack.variant_key));
}

/** Every line belonging to one weapon, in derivation order. */
export function linesForWeapon(attacks: AttackDTO[], weaponName: string): AttackDTO[] {
  // Matching on the key's first field rather than on the display name: the name has
  // the variant folded into it, so "Espada larga" would also match "Espada larga +1".
  const prefix = `${weaponName}|`;
  return attacks.filter((attack) => attack.variant_key?.startsWith(prefix));
}
