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
});
