import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ExportButton } from "@/features/io/ExportButton";
import { ImportButton } from "@/features/io/ImportButton";
import { fighterCharacter } from "@/test/fixtures";
import { server } from "@/test/server";
import { renderWithProviders } from "@/test/render";

describe("ExportButton", () => {
  beforeEach(() => {
    globalThis.URL.createObjectURL = vi.fn(() => "blob:test");
    globalThis.URL.revokeObjectURL = vi.fn();
    vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  });
  afterEach(() => vi.restoreAllMocks());

  it("downloads the exported character as JSON", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ExportButton id="char-1" name="Aldous" />);
    await user.click(screen.getByRole("button", { name: "Exportar" }));
    await waitFor(() => expect(globalThis.URL.createObjectURL).toHaveBeenCalled());
  });
});

describe("ImportButton", () => {
  it("imports a valid character file", async () => {
    const user = userEvent.setup();
    let importedBody: unknown;
    server.use(
      http.post("/api/v1/characters/import", async ({ request }) => {
        importedBody = await request.json();
        return HttpResponse.json(fighterCharacter, { status: 201 });
      }),
    );
    renderWithProviders(<ImportButton />);

    const file = new File([JSON.stringify(fighterCharacter)], "aldous.json", {
      type: "application/json",
    });
    await user.upload(screen.getByLabelText("Importar personaje"), file);

    await waitFor(() => expect(importedBody).toMatchObject({ name: "Aldous" }));
  });

  it("shows an error for an invalid file", async () => {
    const user = userEvent.setup();
    renderWithProviders(<ImportButton />);
    const file = new File(["{ not json"], "broken.json", { type: "application/json" });
    await user.upload(screen.getByLabelText("Importar personaje"), file);
    expect(await screen.findByRole("alert")).toHaveTextContent("no es un personaje válido");
  });
});
