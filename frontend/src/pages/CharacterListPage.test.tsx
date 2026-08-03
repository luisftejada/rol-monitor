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
