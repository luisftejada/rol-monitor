import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { SavesSection } from "@/features/editor/sections/SavesSection";
import { value } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";

describe("SavesSection", () => {
  it("shows the three saves from the derived values", () => {
    renderWithProviders(
      <SavesSection saves={{ Fortaleza: value(5), Reflejos: value(2), Voluntad: value(-1) }} />,
    );
    // The toggle's accessible name is its label plus its value, hence the regexes.
    expect(screen.getByRole("button", { name: /^Fortaleza/ })).toHaveTextContent("+5");
    expect(screen.getByRole("button", { name: /^Reflejos/ })).toHaveTextContent("+2");
    expect(screen.getByRole("button", { name: /^Voluntad/ })).toHaveTextContent("-1");
  });

  it("shows a placeholder for each save until derivation arrives", () => {
    renderWithProviders(<SavesSection />);
    expect(screen.getByRole("button", { name: /^Fortaleza/ })).toHaveTextContent("—");
  });

  it("expands a save to show its breakdown", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <SavesSection
        saves={{
          Fortaleza: value(5, [{ label: "Constitución", value: 1, type: null, source: "ability" }]),
        }}
      />,
    );
    await user.click(screen.getByRole("button", { name: /^Fortaleza/ }));
    expect(screen.getByRole("region", { name: /Fortaleza/ })).toHaveTextContent("Constitución");
  });
});
