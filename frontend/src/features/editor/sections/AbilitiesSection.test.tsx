import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import type { CharacterCreate } from "@/api/types";
import { AbilitiesSection } from "@/features/editor/sections/AbilitiesSection";
import { defaultDraft } from "@/features/editor/draft";
import { renderWithProviders } from "@/test/render";

function Host(): React.JSX.Element {
  const [draft, setDraft] = useState<CharacterCreate>(defaultDraft());
  return <AbilitiesSection draft={draft} patch={(p) => setDraft((c) => ({ ...c, ...p }))} />;
}

describe("AbilitiesSection", () => {
  it("shows the point-buy counter for the standard array (15/15)", async () => {
    renderWithProviders(<Host />);
    // 7+5+3+2+0-2 = 15 for {15,14,13,12,10,8}
    await waitFor(() => expect(screen.getByText("Puntos: 15 / 15")).toBeInTheDocument());
  });

  it("flags going over the point budget", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await waitFor(() => expect(screen.getByText(/Puntos: 15/)).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "+ Fue" }));
    // 15 -> 16 costs 10 instead of 7: total 18 > 15.
    expect(screen.getByText(/Puntos: 18 \/ 15/)).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("presupuesto");
  });

  it("clamps point-buy scores to a minimum of 7", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    const minus = await screen.findByRole("button", { name: "− Fue" });
    for (let i = 0; i < 12; i += 1) await user.click(minus);
    const row = screen.getByRole("row", { name: /Fue/ });
    expect(within(row).getByLabelText("Fue")).toHaveTextContent("7");
  });

  it("assigns the flexible racial bonus (human +2)", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    const select = await screen.findByRole("combobox", { name: "+2 racial" });
    await user.selectOptions(select, "Fue");
    const row = screen.getByRole("row", { name: /Fue/ });
    // Racial column becomes +2.
    expect(within(row).getByText("+2")).toBeInTheDocument();
  });

  it("allows free manual entry", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await user.click(await screen.findByRole("radio", { name: "Manual" }));
    const row = screen.getByRole("row", { name: /Fue/ });
    const input = within(row).getByLabelText("Fue");
    await user.clear(input);
    await user.type(input, "20");
    expect(input).toHaveValue(20);
  });

  it("prevents duplicate values in the standard-array method", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await user.click(await screen.findByRole("radio", { name: "Matriz estándar" }));
    const row = screen.getByRole("row", { name: /Fue/ });
    const select = within(row).getByRole("combobox", { name: "Fue" });
    // 14 is taken by Des, so it is disabled in Fue's select.
    const option14 = within(select).getByRole("option", { name: "14" }) as HTMLOptionElement;
    expect(option14.disabled).toBe(true);
  });
});
