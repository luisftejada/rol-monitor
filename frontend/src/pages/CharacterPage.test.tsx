import { screen, waitFor } from "@testing-library/react";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { App } from "@/App";
import { server } from "@/test/server";
import { renderWithProviders } from "@/test/render";

describe("CharacterPage", () => {
  it("renders the combat card for a character", async () => {
    renderWithProviders(<App />, { route: "/characters/char-1" });
    const card = await screen.findByRole("article", { name: "Aldous" });
    expect(card).toHaveTextContent("Clase de armadura");
    expect(card).toHaveTextContent("Espada larga");
  });

  it("shows an error state when the combat sheet fails to load", async () => {
    server.use(
      http.get(
        "/api/v1/characters/:id/combat-sheet",
        () => new HttpResponse(null, { status: 500 }),
      ),
    );
    renderWithProviders(<App />, { route: "/characters/char-1" });
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
  });
});
