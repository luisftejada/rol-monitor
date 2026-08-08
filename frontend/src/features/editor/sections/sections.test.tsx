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

  it("picks an alignment from the catalog and can clear it again", async () => {
    const user = userEvent.setup();
    function Host() {
      const { draft, patch } = useDraft();
      return (
        <>
          <IdentitySection draft={draft} patch={patch} />
          <output>{draft.alignment ?? "sin alineamiento"}</output>
        </>
      );
    }
    renderWithProviders(<Host />);

    const alignment = await screen.findByRole("combobox", { name: "Alineamiento" });
    await user.click(alignment);
    await user.click(await screen.findByRole("option", { name: /Legal neutral/ }));
    // The corpus code is what gets persisted; the Spanish name is what is shown.
    expect(screen.getByRole("status")).toHaveTextContent("LN");
    expect(alignment).toHaveValue("Legal neutral");

    await user.click(alignment);
    await user.click(await screen.findByRole("option", { name: "Sin definir" }));
    expect(screen.getByRole("status")).toHaveTextContent("sin alineamiento");
  });

  it("matches alignments ignoring accents", async () => {
    const user = userEvent.setup();
    function Host() {
      const { draft, patch } = useDraft();
      return (
        <>
          <IdentitySection draft={draft} patch={patch} />
          <output>{draft.alignment ?? "sin alineamiento"}</output>
        </>
      );
    }
    renderWithProviders(<Host />);

    const alignment = await screen.findByRole("combobox", { name: "Alineamiento" });
    await user.type(alignment, "caotico mal");
    await user.click(await screen.findByRole("option", { name: /Caótico maligno/ }));
    expect(screen.getByRole("status")).toHaveTextContent("CM");
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
  function EquipmentHost() {
    const { draft, patch } = useDraft();
    return <EquipmentSection draft={draft} patch={patch} />;
  }

  /** The browsable list of weapons matching the current filters. */
  function weaponList(): HTMLElement {
    return screen.getByRole("list", { name: "Añadir arma" });
  }

  it("equips a shield and manages weapons", async () => {
    const user = userEvent.setup();
    renderWithProviders(<EquipmentHost />);

    await user.click(await screen.findByRole("combobox", { name: "Escudo" }));
    await user.click(await screen.findByRole("option", { name: "Escudo pesado de acero" }));

    await user.click(await screen.findByRole("button", { name: "Añadir Espada larga" }));

    const weapons = screen.getByRole("list", { name: "Arma" });
    expect(
      within(weapons).getByRole("button", { name: "Ver detalles de Espada larga" }),
    ).toBeInTheDocument();

    await user.click(within(weapons).getByRole("button", { name: "Quitar Espada larga" }));
    await waitFor(() =>
      expect(within(weapons).queryByText("Espada larga")).not.toBeInTheDocument(),
    );
  });

  it("lists every weapon alphabetically when no type is selected", async () => {
    renderWithProviders(<EquipmentHost />);
    const names = within(await screen.findByRole("list", { name: "Añadir arma" }))
      .getAllByRole("button", { name: /^Ver detalles de/ })
      .map((button) => button.textContent);
    expect(names).toEqual(["Arco largo", "Daga", "Espada larga", "Lanza larga"]);
  });

  it("filters to a single weapon type", async () => {
    const user = userEvent.setup();
    renderWithProviders(<EquipmentHost />);
    await screen.findByRole("list", { name: "Añadir arma" });

    await user.selectOptions(screen.getByLabelText("Tipo de arma"), "Armas a distancia");
    expect(
      within(weaponList()).getByRole("button", { name: "Ver detalles de Arco largo" }),
    ).toBeInTheDocument();
    expect(
      within(weaponList()).queryByRole("button", { name: "Ver detalles de Espada larga" }),
    ).not.toBeInTheDocument();

    await user.selectOptions(screen.getByLabelText("Tipo de arma"), "Todas (alfabéticamente)");
    expect(
      within(weaponList()).getByRole("button", { name: "Ver detalles de Espada larga" }),
    ).toBeInTheDocument();
  });

  it("searches weapons by name, ignoring accents", async () => {
    const user = userEvent.setup();
    renderWithProviders(<EquipmentHost />);
    await screen.findByRole("list", { name: "Añadir arma" });

    await user.type(screen.getByLabelText("Buscar arma"), "lanza lar");
    const names = within(weaponList())
      .getAllByRole("button", { name: /^Ver detalles de/ })
      .map((button) => button.textContent);
    expect(names).toEqual(["Lanza larga"]);
  });

  it("shows the stat line as a hover tooltip", async () => {
    renderWithProviders(<EquipmentHost />);
    const espada = await screen.findByRole("button", { name: "Ver detalles de Espada larga" });
    expect(espada).toHaveAttribute("title", "1d8 — 19-20/×2 — Cor");

    // A weapon that always threatens on 20 shows only its multiplier.
    const arco = screen.getByRole("button", { name: "Ver detalles de Arco largo" });
    expect(arco).toHaveAttribute("title", "1d8 — ×3 — Per");
  });

  it("opens a details dialog with the weapon's stat block", async () => {
    const user = userEvent.setup();
    renderWithProviders(<EquipmentHost />);
    await user.click(await screen.findByRole("button", { name: "Ver detalles de Lanza larga" }));

    const dialog = screen.getByRole("dialog", { name: "Lanza larga" });
    expect(within(dialog).getByText("sencilla")).toBeInTheDocument();
    expect(within(dialog).getByText("1d6 / 1d8")).toBeInTheDocument();
    expect(within(dialog).getByText("×3")).toBeInTheDocument();
    expect(within(dialog).getByText("apuntalar, alcance")).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("equips a weapon from the details dialog", async () => {
    const user = userEvent.setup();
    renderWithProviders(<EquipmentHost />);
    await user.click(await screen.findByRole("button", { name: "Ver detalles de Daga" }));
    await user.click(
      within(screen.getByRole("dialog", { name: "Daga" })).getByRole("button", {
        name: "Añadir arma",
      }),
    );

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    const weapons = screen.getByRole("list", { name: "Arma" });
    expect(
      within(weapons).getByRole("button", { name: "Ver detalles de Daga" }),
    ).toBeInTheDocument();
  });

  it("gives equipped weapons the same tooltip and dialog", async () => {
    const user = userEvent.setup();
    renderWithProviders(<EquipmentHost />);
    await user.click(await screen.findByRole("button", { name: "Añadir Espada larga" }));

    const weapons = screen.getByRole("list", { name: "Arma" });
    const chip = within(weapons).getByRole("button", { name: "Ver detalles de Espada larga" });
    expect(chip).toHaveAttribute("title", "1d8 — 19-20/×2 — Cor");

    await user.click(chip);
    expect(screen.getByRole("dialog", { name: "Espada larga" })).toBeInTheDocument();
  });
});
