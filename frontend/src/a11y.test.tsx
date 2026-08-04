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
    // Wait for the live card to render so the whole page is evaluated.
    await screen.findByRole("article", { name: "Nuevo personaje" });
    expect(await axe(container)).toHaveNoViolations();
  });

  it("the combat tracking view has no violations", async () => {
    const { container } = renderWithProviders(<App />, { route: "/characters/char-1" });
    await screen.findByRole("article", { name: "Aldous" });
    expect(await axe(container)).toHaveNoViolations();
  });
});
