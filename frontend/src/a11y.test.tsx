import { screen } from "@testing-library/react";
import { axe } from "jest-axe";
import { describe, expect, it } from "vitest";

import { App } from "@/App";
import { CombatCard } from "@/components/CombatCard";
import { fighterSheet } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";

describe("accessibility (axe)", () => {
  it("the combat card has no violations", async () => {
    const { container } = renderWithProviders(<CombatCard name="Aldous" sheet={fighterSheet} />);
    expect(await axe(container)).toHaveNoViolations();
  });

  it("the roster has no violations", async () => {
    const { container } = renderWithProviders(<App />, { route: "/" });
    await screen.findByRole("link", { name: "Aldous" });
    expect(await axe(container)).toHaveNoViolations();
  });

  it("the character editor has no violations", async () => {
    const { container } = renderWithProviders(<App />, { route: "/new" });
    await screen.findByRole("heading", { name: "Nuevo personaje", level: 1 });
    // Wait for /derive's figures to land in the Equipo section so the whole
    // (post-derivation) page is evaluated, not just its initial skeleton.
    await screen.findByRole("button", { name: /Clase de armadura/ });
    expect(await axe(container)).toHaveNoViolations();
  });

  it("the combat tracking view has no violations", async () => {
    const { container } = renderWithProviders(<App />, { route: "/characters/char-1" });
    await screen.findByRole("article", { name: "Aldous" });
    expect(await axe(container)).toHaveNoViolations();
  });
});
