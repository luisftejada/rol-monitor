import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import type { CharacterCreate } from "@/api/types";
import { SkillsSection } from "@/features/editor/sections/SkillsSection";
import { defaultDraft } from "@/features/editor/draft";
import { renderWithProviders } from "@/test/render";

function Host(): React.JSX.Element {
  const [draft, setDraft] = useState<CharacterCreate>(defaultDraft());
  return (
    <SkillsSection draft={draft} patch={(p) => setDraft((c) => ({ ...c, ...p }))} intModifier={1} />
  );
}

describe("SkillsSection", () => {
  it("shows the ranks spent/available counter", async () => {
    renderWithProviders(<Host />);
    // guerrero L1: max(1, 2 + Int 1) = 3, + human +1 = 4 available; 0 spent.
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Rangos: 0 / 4"));
  });

  it("marks class skills and increments ranks", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    const row = await screen.findByRole("row", { name: /Intimidar/ });
    expect(row).toHaveTextContent("★");

    await user.click(within(row).getByRole("button", { name: "Subir rango de Intimidar" }));
    expect(screen.getByRole("status")).toHaveTextContent("Rangos: 1 / 4");
  });

  it("drops a skill back to zero (only non-zero ranks persist)", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    const row = await screen.findByRole("row", { name: /Intimidar/ });
    await user.click(within(row).getByRole("button", { name: "Subir rango de Intimidar" }));
    await user.click(within(row).getByRole("button", { name: "Bajar rango de Intimidar" }));
    expect(screen.getByRole("status")).toHaveTextContent("Rangos: 0 / 4");
    expect(within(row).getByLabelText("Intimidar")).toHaveValue(0);
  });
});
