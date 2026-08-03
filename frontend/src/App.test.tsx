import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { App } from "@/App";
import { renderWithProviders } from "@/test/render";

describe("App routing", () => {
  it("lists characters and navigates to the combat card", async () => {
    const user = userEvent.setup();
    renderWithProviders(<App />, { route: "/" });

    // The roster shows the derived AC for the character.
    const row = await screen.findByRole("row", { name: /Aldous/ });
    expect(within(row).getByText("18")).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: "Aldous" }));

    // The combat card for that character appears.
    const card = await screen.findByRole("article", { name: "Aldous" });
    await waitFor(() => expect(card).toBeInTheDocument());
    expect(within(card).getByRole("heading", { name: "Aldous" })).toBeInTheDocument();
  });

  it("opens the creation editor from the roster", async () => {
    const user = userEvent.setup();
    renderWithProviders(<App />, { route: "/" });
    await user.click(await screen.findByRole("link", { name: "Nuevo personaje" }));
    expect(
      await screen.findByRole("heading", { name: "Nuevo personaje", level: 1 }),
    ).toBeInTheDocument();
  });

  it("opens the edit editor for an existing character", async () => {
    renderWithProviders(<App />, { route: "/characters/char-1/edit" });
    expect(
      await screen.findByRole("heading", { name: "Editar personaje", level: 1 }),
    ).toBeInTheDocument();
  });
});
