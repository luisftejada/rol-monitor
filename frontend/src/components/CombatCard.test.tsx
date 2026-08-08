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
    // The attack routine's breakdown toggle shows the attack line.
    expect(screen.getByRole("button", { name: /Espada larga/ })).toHaveTextContent("+4");
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

  it("shows what a critical feat does to the target on the weapon line", () => {
    renderWithProviders(<CombatCard name="Aldous" sheet={fighterSheet} />);
    // The feat changes no number of yours, so the line carries the prose instead.
    expect(screen.getByText(/queda exhausto/)).toBeInTheDocument();
  });
});
