import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import type { CharacterCreate } from "@/api/types";
import { ClassesSection } from "@/features/editor/sections/ClassesSection";
import { EquipmentSection } from "@/features/editor/sections/EquipmentSection";
import { IdentitySection } from "@/features/editor/sections/IdentitySection";
import { defaultDraft } from "@/features/editor/draft";
import { renderWithProviders } from "@/test/render";

function useDraft() {
  const [draft, setDraft] = useState<CharacterCreate>(defaultDraft());
  return { draft, patch: (p: Partial<CharacterCreate>) => setDraft((c) => ({ ...c, ...p })) };
}

describe("IdentitySection", () => {
  it("edits the name and picks a race", async () => {
    const user = userEvent.setup();
    function Host() {
      const { draft, patch } = useDraft();
      return (
        <>
          <IdentitySection draft={draft} patch={patch} />
          <output>{draft.race}</output>
        </>
      );
    }
    renderWithProviders(<Host />);

    const name = screen.getByLabelText("Nombre");
    await user.clear(name);
    await user.type(name, "Seoni");
    expect(name).toHaveValue("Seoni");

    await user.click(await screen.findByRole("combobox", { name: "Raza" }));
    await user.click(await screen.findByRole("option", { name: "Mediano" }));
    expect(screen.getByRole("status")).toHaveTextContent("mediano");
  });
});

describe("ClassesSection", () => {
  it("adds, edits, and removes class levels", async () => {
    const user = userEvent.setup();
    function Host() {
      const { draft, patch } = useDraft();
      return (
        <>
          <ClassesSection draft={draft} patch={patch} />
          <output>{draft.class_levels?.length}</output>
        </>
      );
    }
    renderWithProviders(<Host />);
    await screen.findByRole("combobox", { name: "Clase" });

    await user.click(screen.getByRole("button", { name: "Añadir clase" }));
    expect(screen.getByRole("status")).toHaveTextContent("2");

    await user.click(screen.getAllByRole("button", { name: "Quitar" })[0]!);
    expect(screen.getByRole("status")).toHaveTextContent("1");
  });
});

describe("EquipmentSection", () => {
  it("equips a shield and manages weapons", async () => {
    const user = userEvent.setup();
    function Host() {
      const { draft, patch } = useDraft();
      return <EquipmentSection draft={draft} patch={patch} />;
    }
    renderWithProviders(<Host />);

    await user.click(await screen.findByRole("combobox", { name: "Escudo" }));
    await user.click(await screen.findByRole("option", { name: "Escudo pesado de acero" }));

    await user.click(screen.getByRole("combobox", { name: "Añadir arma" }));
    await user.click(await screen.findByRole("option", { name: "Espada larga" }));

    const weapons = screen.getByRole("list", { name: "Arma" });
    expect(within(weapons).getByText("Espada larga")).toBeInTheDocument();

    await user.click(within(weapons).getByRole("button", { name: "Quitar Espada larga" }));
    await waitFor(() =>
      expect(within(weapons).queryByText("Espada larga")).not.toBeInTheDocument(),
    );
  });
});
