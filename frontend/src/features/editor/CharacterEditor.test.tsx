import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it, vi } from "vitest";

import type { CharacterCreate } from "@/api/types";
import { CharacterEditor } from "@/features/editor/CharacterEditor";
import { defaultDraft } from "@/features/editor/draft";
import { fighterSheet } from "@/test/fixtures";
import { server } from "@/test/server";
import { renderWithProviders } from "@/test/render";

// A /derive handler whose AC reflects whether armor is equipped, so we can observe
// the live card refreshing in response to a form change.
function armorAwareDerive() {
  server.use(
    http.post("/api/v1/derive", async ({ request }) => {
      const body = (await request.json()) as CharacterCreate;
      return HttpResponse.json({
        ...fighterSheet,
        ac: { ...fighterSheet.ac, total: body.armor ? 18 : 12 },
      });
    }),
  );
}

describe("CharacterEditor", () => {
  it("renders the live combat card from /derive", async () => {
    renderWithProviders(<CharacterEditor initialDraft={defaultDraft()} mode="create" />);
    const card = await screen.findByRole("article", { name: "Nuevo personaje" });
    expect(card).toBeInTheDocument();
  });

  it("recomputes the card when equipment changes (autofill via /derive)", async () => {
    armorAwareDerive();
    const user = userEvent.setup();
    renderWithProviders(<CharacterEditor initialDraft={defaultDraft()} mode="create" />);

    // Starts with no armor -> AC 12.
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /Clase de armadura/ })).toHaveTextContent("12"),
    );

    await user.click(screen.getByRole("combobox", { name: "Armadura" }));
    await user.click(await screen.findByRole("option", { name: "Cota de escamas" }));

    // After the debounced re-derive, the card reflects the equipped armor.
    await waitFor(
      () =>
        expect(screen.getByRole("button", { name: /Clase de armadura/ })).toHaveTextContent("18"),
      { timeout: 3000 },
    );
  });

  it("saves and reports the save state", async () => {
    const onSaved = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <CharacterEditor initialDraft={defaultDraft()} mode="create" onSaved={onSaved} />,
    );
    await user.click(screen.getByRole("button", { name: "Guardar" }));

    await waitFor(() => expect(onSaved).toHaveBeenCalled());
    expect(await screen.findByText("Guardado")).toBeInTheDocument();
  });

  it("saves with Ctrl+S (keyboard-first)", async () => {
    const onSaved = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <CharacterEditor initialDraft={defaultDraft()} mode="create" onSaved={onSaved} />,
    );
    await user.keyboard("{Control>}s{/Control}");
    await waitFor(() => expect(onSaved).toHaveBeenCalled());
  });
});
