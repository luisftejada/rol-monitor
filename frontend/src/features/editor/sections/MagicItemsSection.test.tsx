import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import type { CharacterCreate } from "@/api/types";
import { defaultDraft } from "@/features/editor/draft";
import { MagicItemsSection } from "@/features/editor/sections/MagicItemsSection";
import { renderWithProviders } from "@/test/render";

function renderSection(): { draft: () => CharacterCreate } {
  const seen = { current: defaultDraft() };
  function Host() {
    const [draft, setDraft] = useState<CharacterCreate>(defaultDraft());
    seen.current = draft;
    return (
      <MagicItemsSection
        draft={draft}
        patch={(p) => setDraft((current) => ({ ...current, ...p }))}
      />
    );
  }
  renderWithProviders(<Host />);
  return { draft: () => seen.current };
}

describe("MagicItemsSection", () => {
  it("lists every place on the body, empty ones included", async () => {
    renderSection();
    // The test catalog has anillo (×2), cuello and manos.
    const rings = await screen.findAllByRole("row", { name: /anillo/ });
    expect(rings).toHaveLength(2); // one line per place the slot offers
    expect(screen.getByRole("row", { name: /cuello/ })).toBeInTheDocument();
  });

  it("creates an item already in the slot that was clicked", async () => {
    const user = userEvent.setup();
    const { draft } = renderSection();

    await user.click(
      (await screen.findAllByRole("button", { name: /Añadir objeto en cuello/ }))[0]!,
    );

    // The item lands in that slot, not in the backpack, and its editor opens.
    expect(draft().magic_items?.[0]).toMatchObject({ slot: "cuello" });
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });

  it("opens an existing item from its slot", async () => {
    const user = userEvent.setup();
    renderSection();

    await user.click(
      (await screen.findAllByRole("button", { name: /Añadir objeto en cuello/ }))[0]!,
    );
    await user.click(
      within(await screen.findByRole("dialog")).getByRole("button", { name: "Cerrar" }),
    );

    await user.click(screen.getByRole("button", { name: /^Editar Cuello-1/ }));
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
  });

  it("edits a field from the dialog and keeps the slot grid in step", async () => {
    const user = userEvent.setup();
    const { draft } = renderSection();
    await user.click(
      (await screen.findAllByRole("button", { name: /Añadir objeto en cuello/ }))[0]!,
    );

    const dialog = await screen.findByRole("dialog");
    const name = within(dialog).getByLabelText("Nombre");
    await user.clear(name);
    await user.type(name, "Amuleto");
    await user.selectOptions(
      within(dialog).getByLabelText("Tipo del bono de CA"),
      "armadura natural",
    );

    expect(draft().magic_items?.[0]).toMatchObject({
      name: "Amuleto",
      ac_bonus_type: "armadura natural",
    });
    expect(screen.getByRole("button", { name: /^Editar Amuleto/ })).toBeInTheDocument();
  });

  it("gives an over-filled slot a line of its own, flagged", async () => {
    const user = userEvent.setup();
    renderSection();

    // Fill both ring places, then move a third item into the slot from its dialog —
    // which is the only way to over-fill, since the grid offers no empty line once
    // the slot is full.
    for (let n = 0; n < 2; n += 1) {
      const empty = await screen.findAllByRole("button", { name: /Añadir objeto en anillo/ });
      await user.click(empty[0]!);
      await user.click(
        within(await screen.findByRole("dialog")).getByRole("button", { name: "Cerrar" }),
      );
    }
    await user.click(await screen.findByRole("button", { name: /Añadir objeto en Mochila/ }));
    const third = await screen.findByRole("dialog");
    await user.selectOptions(within(third).getByLabelText("Ranura"), "anillo");
    await user.click(within(third).getByRole("button", { name: "Cerrar" }));

    expect(await screen.findAllByRole("row", { name: /anillo/ })).toHaveLength(3);
    expect(screen.getByRole("alert")).toBeInTheDocument();
  });

  it("keeps staves and wands out of the body slots", async () => {
    const user = userEvent.setup();
    renderSection();
    await user.click(
      (await screen.findAllByRole("button", { name: /Añadir objeto en cuello/ }))[0]!,
    );

    const dialog = await screen.findByRole("dialog");
    await user.selectOptions(within(dialog).getByLabelText("Categoría"), "varitas");
    await user.click(within(dialog).getByRole("button", { name: "Cerrar" }));

    // A wand is held, not worn, so the neck is free again and it is listed below.
    const held = screen.getByRole("list", { name: "Bastones y varitas" });
    expect(within(held).getByRole("button", { name: /^Editar Cuello-1/ })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: /Añadir objeto en cuello/ })).toHaveLength(1);
  });

  it("removes an item from its dialog", async () => {
    const user = userEvent.setup();
    const { draft } = renderSection();
    await user.click(
      (await screen.findAllByRole("button", { name: /Añadir objeto en cuello/ }))[0]!,
    );

    const dialog = await screen.findByRole("dialog");
    await user.click(within(dialog).getByRole("button", { name: /^Quitar/ }));

    expect(draft().magic_items).toEqual([]);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("stows an item in the backpack, where several fit", async () => {
    const user = userEvent.setup();
    const { draft } = renderSection();

    await user.click(await screen.findByRole("button", { name: /Añadir objeto en Mochila/ }));
    await user.click(
      within(await screen.findByRole("dialog")).getByRole("button", { name: "Cerrar" }),
    );
    await user.click(screen.getByRole("button", { name: /Añadir objeto en Mochila/ }));

    expect(draft().magic_items).toHaveLength(2);
    expect(draft().magic_items?.every((item) => item.slot === "mochila")).toBe(true);
    // Stowed items never trip the capacity warning: they are owned, not worn.
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
