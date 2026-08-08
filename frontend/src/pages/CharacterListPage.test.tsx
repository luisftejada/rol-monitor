import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, describe, expect, it, vi } from "vitest";

import { CharacterListPage } from "@/pages/CharacterListPage";
import { server } from "@/test/server";
import { renderWithProviders } from "@/test/render";

describe("CharacterListPage", () => {
  afterEach(() => vi.restoreAllMocks());

  it("shows a loading state then the roster", async () => {
    renderWithProviders(<CharacterListPage />);
    expect(screen.getByRole("status")).toHaveTextContent("Cargando…");
    expect(await screen.findByRole("link", { name: "Aldous" })).toBeInTheDocument();
    // Derived numbers from the summary are shown.
    const row = screen.getByRole("row", { name: /Aldous/ });
    expect(row).toHaveTextContent("18");
  });

  it("has an accessible search field", async () => {
    renderWithProviders(<CharacterListPage />);
    await screen.findByRole("link", { name: "Aldous" });
    expect(screen.getByRole("searchbox", { name: "Buscar por nombre" })).toBeInTheDocument();
  });

  it("exposes the row actions as buttons, not links", async () => {
    renderWithProviders(<CharacterListPage />);
    await screen.findByRole("link", { name: "Aldous" });

    // Actions are buttons; links are reserved for navigating to a section.
    expect(screen.getByRole("button", { name: "Duplicar" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Eliminar" })).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Duplicar" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Eliminar" })).not.toBeInTheDocument();
  });

  it("labels the icon actions for hover and for screen readers", async () => {
    renderWithProviders(<CharacterListPage />);
    await screen.findByRole("link", { name: "Aldous" });

    // The glyph alone would be a guess: `title` shows the word on hover, and the
    // accessible name says the same thing.
    for (const [role, name] of [
      ["link", "Editar"],
      ["button", "Duplicar"],
      ["button", "Eliminar"],
    ] as const) {
      const action = screen.getByRole(role, { name });
      expect(action).toHaveAttribute("title", name);
    }
  });

  it("links the edit action to the character's editor", async () => {
    renderWithProviders(<CharacterListPage />);
    await screen.findByRole("link", { name: "Aldous" });
    expect(screen.getByRole("link", { name: "Editar" })).toHaveAttribute(
      "href",
      "/characters/char-1/edit",
    );
  });

  it("confirms before deleting", async () => {
    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(true);
    const user = userEvent.setup();
    renderWithProviders(<CharacterListPage />);
    await screen.findByRole("link", { name: "Aldous" });

    await user.click(screen.getByRole("button", { name: "Eliminar" }));
    expect(confirmSpy).toHaveBeenCalledWith("¿Eliminar «Aldous»?");
  });

  it("shows an error state with retry", async () => {
    server.use(http.get("/api/v1/characters", () => new HttpResponse(null, { status: 500 })));
    renderWithProviders(<CharacterListPage />);
    await waitFor(() => expect(screen.getByRole("alert")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Reintentar" })).toBeInTheDocument();
  });

  it("shows an empty state when there are no characters", async () => {
    server.use(
      http.get("/api/v1/characters", () =>
        HttpResponse.json({ items: [], total: 0, limit: 50, offset: 0 }),
      ),
    );
    renderWithProviders(<CharacterListPage />);
    expect(await screen.findByText("Aún no hay personajes.")).toBeInTheDocument();
  });
});
