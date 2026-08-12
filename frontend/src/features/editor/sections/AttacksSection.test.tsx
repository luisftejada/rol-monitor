import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import type { AttackDTO } from "@/api/types";
import { AttacksSection } from "@/features/editor/sections/AttacksSection";
import { fighterSheet } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";

/** The `.attack` block a given "Bono" toggle belongs to. */
function attackBlockOf(bonusToggle: HTMLElement): HTMLElement {
  const block = bonusToggle.closest(".attack");
  if (!(block instanceof HTMLElement)) throw new Error("no .attack ancestor");
  return block;
}

describe("AttacksSection", () => {
  it("shows a placeholder while derivation is still loading", () => {
    renderWithProviders(<AttacksSection />);
    expect(screen.getByText(/Añade un arma en Equipo/)).toBeInTheDocument();
  });

  it("shows a placeholder once derived but no weapon is equipped", () => {
    renderWithProviders(<AttacksSection attacks={[]} />);
    expect(screen.getByText(/Añade un arma en Equipo/)).toBeInTheDocument();
  });

  it("shows each equipped weapon's attack and damage lines", () => {
    renderWithProviders(<AttacksSection attacks={fighterSheet.attacks} />);
    expect(screen.getByText("Espada larga")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Bono/ })).toHaveTextContent("+4");
    expect(screen.getByRole("button", { name: /^Daño/ })).toHaveTextContent("1d8+3");
    expect(screen.getByText(/19-20\/×2/, { selector: ".stat__value" })).toBeInTheDocument();
  });

  // A weapon that can be used more than one way (Ataque poderoso, Puntería
  // mortal, ...) is one row per way in `/derive`'s response, not one row with a
  // toggle — the frontend renders whatever it is given, one block per entry. Both
  // lines share the bare weapon name; only the second names what makes it an
  // alternative, right below that name rather than folded into it again.
  it("lists each way of using a weapon as its own line", () => {
    const base = fighterSheet.attacks[0]!;
    const attacks: AttackDTO[] = [
      base,
      {
        ...base,
        weapon: "Espada larga (Ataque poderoso)",
        variant_label: "Ataque poderoso",
        attack_line: "+2",
        damage_expression: "1d8+9",
        cmb: {
          total: 2,
          breakdown: [{ label: "Ataque poderoso", value: -2, type: null, source: "feat" }],
          suppressed: [],
        },
      },
    ];
    renderWithProviders(<AttacksSection attacks={attacks} />);

    const bonusToggles = screen.getAllByRole("button", { name: /^Bono/ });
    expect(bonusToggles).toHaveLength(2);
    const [plain, powered] = bonusToggles.map(attackBlockOf);

    expect(within(plain!).getByRole("button", { name: /^Bono/ })).toHaveTextContent("+4");
    expect(within(plain!).queryByText("Ataque poderoso")).not.toBeInTheDocument();
    expect(
      within(plain!).queryByRole("button", { name: /BMC con esta línea/ }),
    ).not.toBeInTheDocument();

    expect(within(powered!).getByRole("button", { name: /^Bono/ })).toHaveTextContent("+2");
    expect(within(powered!).getByText("Ataque poderoso")).toBeInTheDocument();
    // Only the alternative line costs a CMB of its own.
    expect(within(powered!).getByRole("button", { name: /BMC con esta línea/ })).toHaveTextContent(
      "+2",
    );
  });

  it("flags a weapon the character is not proficient with", () => {
    const attacks: AttackDTO[] = [{ ...fighterSheet.attacks[0]!, is_proficient: false }];
    renderWithProviders(<AttacksSection attacks={attacks} />);
    expect(screen.getByText(/No competente/)).toBeInTheDocument();
  });

  it("shows what a critical feat does to the target", () => {
    renderWithProviders(<AttacksSection attacks={fighterSheet.attacks} />);
    expect(screen.getByText(/queda exhausto/)).toBeInTheDocument();
  });

  it("expands an attack line to show its breakdown", async () => {
    const user = userEvent.setup();
    renderWithProviders(<AttacksSection attacks={fighterSheet.attacks} />);
    await user.click(screen.getByRole("button", { name: /^Bono/ }));
    expect(screen.getByRole("region", { name: /Bono/ })).toHaveTextContent("Fue");
  });
});
