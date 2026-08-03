/** Format an integer as a signed modifier: 3 -> "+3", -2 -> "-2", 0 -> "+0". */
export function signed(value: number): string {
  return value >= 0 ? `+${value}` : `${value}`;
}
