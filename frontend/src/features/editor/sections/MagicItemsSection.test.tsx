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
  it("adds an item stowed, with a name that says what it is", async () => {
    const user = userEvent.setup();
    const { draft } = renderSection();

    await user.click(screen.getByRole("button", { name: "Añadir objeto" }));

    const [item] = draft().magic_items ?? [];
    // Stowed by default: an item you have just written down is not yet being worn.
    expect(item).toMatchObject({ slot: "mochila" });
    expect(item?.name).toMatch(/-1$/);
    expect(screen.getByText(/no se aplican/)).toBeInTheDocument();
  });

  it("warns when a slot carries more than it holds", async () => {
    const user = userEvent.setup();
    const { draft } = renderSection();

    // The ring slot takes two, per the corpus' own "anillo (×2)".
    for (let n = 0; n < 3; n += 1) {
      await user.click(screen.getByRole("button", { name: "Añadir objeto" }));
    }
    for (const select of await screen.findAllByLabelText("Ranura")) {
      await user.selectOptions(select, "anillo");
    }

    expect(screen.getAllByRole("alert")).not.toHaveLength(0);
    expect(draft().magic_items?.every((item) => item.slot === "anillo")).toBe(true);
  });

  it("keeps two rings quiet, and a third stowed one too", async () => {
    const user = userEvent.setup();
    renderSection();

    for (let n = 0; n < 3; n += 1) {
      await user.click(screen.getByRole("button", { name: "Añadir objeto" }));
    }
    const slots = await screen.findAllByLabelText("Ranura");
    await user.selectOptions(slots[0]!, "anillo");
    await user.selectOptions(slots[1]!, "anillo");
    // The third stays in the backpack, so it does not count against the slot.

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("records the bonus with its type, which is what decides the stacking", async () => {
    const user = userEvent.setup();
    const { draft } = renderSection();
    await user.click(screen.getByRole("button", { name: "Añadir objeto" }));

    const list = screen.getByRole("list", { name: "Objetos mágicos" });
    await user.selectOptions(within(list).getByLabelText("Ranura"), "anillo");
    const ac = within(list).getByLabelText("Bono de CA");
    await user.clear(ac);
    await user.type(ac, "2");
    await user.selectOptions(within(list).getByLabelText("Tipo del bono de CA"), "deflexión");

    expect(draft().magic_items?.[0]).toMatchObject({
      slot: "anillo",
      ac_bonus: 2,
      ac_bonus_type: "deflexión",
    });
  });

  it("fills the day's uses when the allowance is set", async () => {
    const user = userEvent.setup();
    const { draft } = renderSection();
    await user.click(screen.getByRole("button", { name: "Añadir objeto" }));

    const perDay = screen.getByLabelText("Usos por día");
    await user.clear(perDay);
    await user.type(perDay, "3");

    // Typing the same number twice is a chore nobody should have to do.
    expect(draft().magic_items?.[0]).toMatchObject({ uses_per_day: 3, uses_remaining: 3 });
  });

  it("removes an item", async () => {
    const user = userEvent.setup();
    const { draft } = renderSection();
    await user.click(screen.getByRole("button", { name: "Añadir objeto" }));
    const name = draft().magic_items?.[0]?.name ?? "";

    await user.click(screen.getByRole("button", { name: `Quitar ${name}` }));
    expect(draft().magic_items).toEqual([]);
  });
});
