import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import type { CharacterCreate } from "@/api/types";
import { FeatsSection } from "@/features/editor/sections/FeatsSection";
import { defaultDraft } from "@/features/editor/draft";
import { renderWithProviders } from "@/test/render";

function Host(): React.JSX.Element {
  const [draft, setDraft] = useState<CharacterCreate>(defaultDraft());
  return (
    <FeatsSection
      draft={draft}
      patch={(p) => setDraft((c) => ({ ...c, ...p }))}
      bab={1}
      abilities={{ Fue: 15 }}
    />
  );
}

/** The browsable list of feats matching the current filters. */
function featList(): HTMLElement {
  return screen.getByRole("list", { name: "Añadir dote" });
}

describe("FeatsSection", () => {
  it("lists every feat alphabetically when no type is selected", async () => {
    renderWithProviders(<Host />);
    const names = within(await screen.findByRole("list", { name: "Añadir dote" }))
      .getAllByRole("button", { name: /^Ver detalles de/ })
      .map((button) => button.textContent);
    expect(names).toEqual([
      "Abstención de materiales",
      "Acometer ⚠",
      "Esquiva",
      "Hendedura",
      "Soltura con un arma",
    ]);
  });

  it("filters to a single feat type", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await screen.findByRole("list", { name: "Añadir dote" });

    await user.selectOptions(screen.getByLabelText("Tipo de dote"), "General");
    expect(
      within(featList()).getByRole("button", { name: "Ver detalles de Abstención de materiales" }),
    ).toBeInTheDocument();
    expect(
      within(featList()).queryByRole("button", { name: "Ver detalles de Esquiva" }),
    ).not.toBeInTheDocument();

    // Back to the unfiltered, alphabetical listing.
    await user.selectOptions(screen.getByLabelText("Tipo de dote"), "Todas (alfabéticamente)");
    expect(
      within(featList()).getByRole("button", { name: "Ver detalles de Esquiva" }),
    ).toBeInTheDocument();
  });

  it("hides feats whose prerequisites are unmet when the filter is on", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await screen.findByRole("list", { name: "Añadir dote" });

    // Acometer requires BAB +6 and the character has +1.
    expect(
      within(featList()).getByRole("button", { name: "Ver detalles de Acometer" }),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("checkbox", { name: "Solo dotes cuyos requisitos cumplo" }));
    expect(
      within(featList()).queryByRole("button", { name: "Ver detalles de Acometer" }),
    ).not.toBeInTheDocument();
    expect(
      within(featList()).getByRole("button", { name: "Ver detalles de Esquiva" }),
    ).toBeInTheDocument();
  });

  it("searches by name, ignoring accents", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await screen.findByRole("list", { name: "Añadir dote" });

    await user.type(screen.getByLabelText("Buscar dote"), "abstencion");
    const names = within(featList())
      .getAllByRole("button", { name: /^Ver detalles de/ })
      .map((button) => button.textContent);
    expect(names).toEqual(["Abstención de materiales"]);
  });

  it("shows the benefit as a hover tooltip on each feat", async () => {
    renderWithProviders(<Host />);
    const esquiva = await screen.findByRole("button", { name: "Ver detalles de Esquiva" });
    expect(esquiva).toHaveAttribute("title", "+1 CA");

    // An ineligible feat also spells out the prerequisite it fails.
    const acometer = screen.getByRole("button", { name: "Ver detalles de Acometer" });
    expect(acometer.getAttribute("title")).toContain("ataque base +6");
  });

  it("opens a details dialog with the feat's information", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await user.click(await screen.findByRole("button", { name: "Ver detalles de Acometer" }));

    const dialog = screen.getByRole("dialog", { name: "Acometer" });
    expect(within(dialog).getByText("ataque base +6")).toBeInTheDocument();
    expect(within(dialog).getByText(/arma de alcance/)).toBeInTheDocument();
    expect(within(dialog).getByText("No cumples los requisitos")).toBeInTheDocument();

    await user.keyboard("{Escape}");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("adds a feat from the details dialog", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await user.click(await screen.findByRole("button", { name: "Ver detalles de Esquiva" }));
    await user.click(
      within(screen.getByRole("dialog", { name: "Esquiva" })).getByRole("button", {
        name: "Añadir dote",
      }),
    );

    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    const owned = screen.getByRole("list", { name: "Dotes seleccionadas" });
    expect(within(owned).getByText("Esquiva")).toBeInTheDocument();
  });

  it("adds and removes a feat without opening the dialog", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await user.click(await screen.findByRole("button", { name: "Añadir Esquiva" }));
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();

    const owned = screen.getByRole("list", { name: "Dotes seleccionadas" });
    expect(within(owned).getByText("Esquiva")).toBeInTheDocument();
    // Already owned: the add button is disabled rather than duplicating it.
    expect(screen.getByRole("button", { name: "Añadir Esquiva" })).toBeDisabled();

    await user.click(within(owned).getByRole("button", { name: "Quitar Esquiva" }));
    expect(within(owned).queryByText("Esquiva")).not.toBeInTheDocument();
  });

  it("gives selected feats the same tooltip and details dialog", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await user.click(await screen.findByRole("button", { name: "Añadir Esquiva" }));

    const owned = screen.getByRole("list", { name: "Dotes seleccionadas" });
    const chip = within(owned).getByRole("button", { name: "Ver detalles de Esquiva" });
    expect(chip).toHaveAttribute("title", "+1 CA");

    await user.click(chip);
    const dialog = screen.getByRole("dialog", { name: "Esquiva" });
    expect(within(dialog).getByText("+1 CA")).toBeInTheDocument();
    // Already selected, so the dialog offers no second add.
    expect(within(dialog).getByRole("button", { name: "Ya seleccionada" })).toBeDisabled();
  });

  it("leaves a feat that is not in the catalog as plain text", async () => {
    function CustomHost(): React.JSX.Element {
      const [draft, setDraft] = useState<CharacterCreate>({
        ...defaultDraft(),
        feats: ["Dote de la casa"],
      });
      return (
        <FeatsSection
          draft={draft}
          patch={(p) => setDraft((c) => ({ ...c, ...p }))}
          bab={1}
          abilities={{ Fue: 15 }}
        />
      );
    }
    renderWithProviders(<CustomHost />);

    const owned = await screen.findByRole("list", { name: "Dotes seleccionadas" });
    expect(within(owned).getByText("Dote de la casa")).toBeInTheDocument();
    // Nothing to show, so it is not offered as a details control.
    expect(
      within(owned).queryByRole("button", { name: "Ver detalles de Dote de la casa" }),
    ).not.toBeInTheDocument();
    // It can still be removed.
    expect(
      within(owned).getByRole("button", { name: "Quitar Dote de la casa" }),
    ).toBeInTheDocument();
  });

  it("asks which weapon a weapon-scoped feat was taken for", async () => {
    const user = userEvent.setup();
    function Host2(): React.JSX.Element {
      const [draft, setDraft] = useState<CharacterCreate>(defaultDraft());
      return (
        <>
          <FeatsSection
            draft={draft}
            patch={(p) => setDraft((c) => ({ ...c, ...p }))}
            bab={1}
            abilities={{ Fue: 15 }}
          />
          <output aria-label="opciones">{JSON.stringify(draft.feat_options)}</output>
        </>
      );
    }
    renderWithProviders(<Host2 />);
    await user.click(await screen.findByRole("button", { name: "Añadir Soltura con un arma" }));

    const choice = screen.getByRole("combobox", {
      name: "Arma elegida para Soltura con un arma",
    });
    await user.selectOptions(choice, "Espada larga");
    expect(screen.getByRole("status", { name: "opciones" })).toHaveTextContent(
      '{"Soltura con un arma":"Espada larga"}',
    );

    // Clearing it removes the entry rather than storing an empty string.
    await user.selectOptions(choice, "Sin elegir");
    expect(screen.getByRole("status", { name: "opciones" })).toHaveTextContent("{}");
  });

  it("offers no weapon choice for a feat that takes none", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await user.click(await screen.findByRole("button", { name: "Añadir Esquiva" }));
    expect(screen.queryByRole("combobox", { name: /Arma elegida/ })).not.toBeInTheDocument();
  });

  it("drops the weapon choice when the feat is removed", async () => {
    const user = userEvent.setup();
    function Host3(): React.JSX.Element {
      const [draft, setDraft] = useState<CharacterCreate>(defaultDraft());
      return (
        <>
          <FeatsSection
            draft={draft}
            patch={(p) => setDraft((c) => ({ ...c, ...p }))}
            bab={1}
            abilities={{ Fue: 15 }}
          />
          <output aria-label="opciones">{JSON.stringify(draft.feat_options)}</output>
        </>
      );
    }
    renderWithProviders(<Host3 />);
    await user.click(await screen.findByRole("button", { name: "Añadir Soltura con un arma" }));
    await user.selectOptions(
      screen.getByRole("combobox", { name: "Arma elegida para Soltura con un arma" }),
      "Espada larga",
    );

    const owned = screen.getByRole("list", { name: "Dotes seleccionadas" });
    await user.click(within(owned).getByRole("button", { name: "Quitar Soltura con un arma" }));
    // A stale option would silently reappear if the feat were taken again.
    expect(screen.getByRole("status", { name: "opciones" })).toHaveTextContent("{}");
  });

  it("shows the feat budget and where it comes from", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <FeatsSection
        draft={defaultDraft()}
        patch={() => {}}
        bab={1}
        abilities={{ Fue: 15 }}
        budget={{
          available: 2,
          spent: 1,
          granted: ["Impacto sin arma mejorado"],
          slots: [
            { level: 1, source: "base", choice: "libre", types: [] },
            { level: 1, source: "Humano", choice: "libre", types: [] },
          ],
          lists: {},
          list_notes: {},
        }}
      />,
    );

    expect(await screen.findByText("Dotes: 1 / 2")).toBeInTheDocument();
    // A granted feat costs no slot, so it is listed apart from the budget.
    expect(screen.getByText(/Impacto sin arma mejorado/)).toBeInTheDocument();

    await user.click(screen.getByText("Ver de dónde salen"));
    expect(screen.getByText(/por nivel · nivel 1/)).toBeInTheDocument();
    expect(screen.getByText(/Humano · nivel 1/)).toBeInTheDocument();
  });

  it("warns when over the feat budget without blocking", async () => {
    renderWithProviders(
      <FeatsSection
        draft={defaultDraft()}
        patch={() => {}}
        bab={1}
        abilities={{ Fue: 15 }}
        budget={{ available: 1, spent: 3, granted: [], slots: [], lists: {}, list_notes: {} }}
      />,
    );
    expect(await screen.findByText("Dotes: 3 / 1")).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("Te has pasado");
    // Still fully usable: house rules are real.
    expect(await screen.findByRole("button", { name: "Añadir Esquiva" })).toBeEnabled();
  });

  it("shows no budget until the backend has derived one", async () => {
    renderWithProviders(<Host />);
    await screen.findByRole("list", { name: "Añadir dote" });
    expect(screen.queryByText(/^Dotes: /)).not.toBeInTheDocument();
  });

  it("offers a filter per kind of slot, and applies what that slot accepts", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <FeatsSection
        draft={defaultDraft()}
        patch={() => {}}
        bab={1}
        abilities={{ Fue: 15 }}
        budget={{
          available: 2,
          spent: 0,
          granted: [],
          slots: [
            { level: 1, source: "Guerrero", choice: "tipos", types: ["Combate"] },
            {
              level: 1,
              source: "Monje",
              choice: "lista",
              types: [],
              list_key: "dotes_adicionales_monje",
            },
          ],
          lists: { dotes_adicionales_monje: ["Esquiva"] },
          list_notes: { dotes_adicionales_monje: "no necesita cumplir los prerrequisitos" },
        }}
      />,
    );
    const filter = await screen.findByLabelText("Tipo de dote");

    // The class slot filters by category…
    await user.selectOptions(filter, "Combate — Guerrero");
    let names = within(featList())
      .getAllByRole("button", { name: /^Ver detalles de/ })
      .map((b) => b.textContent);
    expect(names).toEqual(["Acometer ⚠", "Esquiva", "Hendedura", "Soltura con un arma"]);

    // …and the restricted list by its resolved names, showing the corpus caveat.
    await user.selectOptions(filter, "Lista de Monje");
    names = within(featList())
      .getAllByRole("button", { name: /^Ver detalles de/ })
      .map((b) => b.textContent);
    expect(names).toEqual(["Esquiva"]);
    expect(screen.getByText(/no necesita cumplir los prerrequisitos/)).toBeInTheDocument();
  });

  it("offers no slot filters when there is no budget yet", async () => {
    renderWithProviders(<Host />);
    const filter = await screen.findByLabelText("Tipo de dote");
    expect(within(filter).queryByRole("group", { name: "Lo que puedes elegir" })).toBeNull();
  });

  it("reports when nothing matches the filters", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await screen.findByRole("list", { name: "Añadir dote" });

    await user.type(screen.getByLabelText("Buscar dote"), "no existe");
    expect(screen.getByText("Ninguna dote coincide con el filtro.")).toBeInTheDocument();
  });
});
