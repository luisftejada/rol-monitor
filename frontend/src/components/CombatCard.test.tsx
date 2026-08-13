import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { CombatCard } from "@/components/CombatCard";
import { fighterSheet } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";

describe("CombatCard", () => {
  it("renders the headline combat numbers", () => {
    renderWithProviders(<CombatCard name="Aldous" sheet={fighterSheet} />);
    expect(screen.getByRole("heading", { name: "Aldous" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Clase de armadura/ })).toHaveTextContent("18");
    expect(screen.getByText(/CA de tacto/)).toHaveTextContent("11");
    expect(screen.getByText("Espada larga")).toBeInTheDocument();
    // The attack routine's breakdown toggle shows the attack line.
    expect(screen.getByRole("button", { name: /^Bono/ })).toHaveTextContent("+4");
  });

  it("expands the AC to show its breakdown and the suppressed bonus", async () => {
    const user = userEvent.setup();
    renderWithProviders(<CombatCard name="Aldous" sheet={fighterSheet} />);

    await user.click(screen.getByRole("button", { name: /Clase de armadura/ }));
    const region = screen.getByRole("region", { name: /Clase de armadura/ });
    expect(region).toHaveTextContent("Cota de escamas");
    expect(region).toHaveTextContent("Escudo de fe"); // suppressed
  });

  it("does not render a warnings section when there are none", () => {
    renderWithProviders(<CombatCard name="Aldous" sheet={fighterSheet} />);
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("shows warnings when present", () => {
    const sheet = { ...fighterSheet, warnings: ["Carga por encima del máximo pesado"] };
    renderWithProviders(<CombatCard name="Aldous" sheet={sheet} />);
    const alert = screen.getByRole("alert");
    expect(within(alert).getByText("Carga por encima del máximo pesado")).toBeInTheDocument();
  });

  it("shows a line's own CMB only when that line changes it", async () => {
    const user = userEvent.setup();
    const base = fighterSheet.attacks[0]!;
    const sheet = {
      ...fighterSheet,
      attacks: [
        base,
        {
          ...base,
          weapon: "Espada larga (Ataque poderoso)",
          variant_label: "Ataque poderoso",
          cmb: {
            total: 2,
            breakdown: [{ label: "Ataque poderoso", value: -2, type: null, source: "feat" }],
            suppressed: [],
          },
        },
      ],
    };
    renderWithProviders(<CombatCard name="Aldous" sheet={sheet} />);

    const toggles = screen.getAllByRole("button", { name: /BMC con esta línea/ });
    expect(toggles).toHaveLength(1);
    expect(toggles[0]!).toHaveTextContent("+2");

    await user.click(toggles[0]!);
    expect(screen.getByRole("region", { name: /BMC con esta línea/ })).toHaveTextContent(
      "Ataque poderoso",
    );
  });

  it("hides the attack lines the player trimmed", () => {
    const sample = fighterSheet.attacks[0]!;
    const sheet = {
      ...fighterSheet,
      attacks: [
        { ...sample, weapon: "Espada larga", variant_key: "Espada larga|one_handed|" },
        {
          ...sample,
          weapon: "Espada larga (a dos manos)",
          variant_label: "a dos manos",
          variant_key: "Espada larga|two_handed|",
        },
      ],
    };
    renderWithProviders(
      <CombatCard name="Aldous" sheet={sheet} hiddenAttackLines={["Espada larga|two_handed|"]} />,
    );

    expect(screen.getByText("Espada larga")).toBeInTheDocument();
    expect(screen.queryByText("Espada larga (a dos manos)")).not.toBeInTheDocument();
  });

  it("says which skills have ranks in them", async () => {
    const trained = fighterSheet.skills[0]!;
    const sheet = {
      ...fighterSheet,
      skills: [
        trained,
        { ...trained, slug: "acrobacias", name: "Acrobacias", ranks: 0, total: 1 },
        { ...trained, slug: "montar", name: "Montar", ranks: 1, total: 4 },
      ],
    };
    renderWithProviders(<CombatCard name="Aldous" sheet={sheet} />);

    // The count is part of the row's accessible name, not a colour or a weight.
    expect(screen.getByRole("button", { name: /Intimidar.*1 rango\b/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Montar.*1 rango\b/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Acrobacias/ })).not.toHaveTextContent("rango");
  });

  it("pluralises the rank count", () => {
    const base = fighterSheet.skills[0]!;
    const sheet = { ...fighterSheet, skills: [{ ...base, ranks: 3 }] };
    renderWithProviders(<CombatCard name="Aldous" sheet={sheet} />);
    expect(screen.getByRole("button", { name: /3 rangos/ })).toBeInTheDocument();
  });

  it("shows what a critical feat does to the target on the weapon line", () => {
    renderWithProviders(<CombatCard name="Aldous" sheet={fighterSheet} />);
    // The feat changes no number of yours, so the line carries the prose instead.
    expect(screen.getByText(/queda exhausto/)).toBeInTheDocument();
  });
});
