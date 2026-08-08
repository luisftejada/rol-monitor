import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vitest";

import { CombatTracker } from "@/features/tracker/CombatTracker";
import { fighterCharacter, trackedCharacter } from "@/test/fixtures";
import { server } from "@/test/server";
import { renderWithProviders } from "@/test/render";

/** Capture the JSON body of the next request to `method path`. */
function capture(method: "post" | "patch" | "delete", path: string): { body: unknown } {
  const box: { body: unknown } = { body: undefined };
  server.use(
    http[method](path, async ({ request }) => {
      try {
        box.body = await request.json();
      } catch {
        box.body = null;
      }
      return HttpResponse.json(fighterCharacter);
    }),
  );
  return box;
}

describe("CombatTracker", () => {
  it("applies HP damage (temp-first, negative allowed)", async () => {
    const user = userEvent.setup();
    const patch = capture("patch", "/api/v1/characters/:id");
    renderWithProviders(<CombatTracker character={trackedCharacter} />);

    const amount = screen.getByLabelText("Cantidad");
    await user.clear(amount);
    await user.type(amount, "5");
    await user.click(screen.getByRole("button", { name: "Daño" }));

    await waitFor(() => expect(patch.body).toEqual({ temporary_hp: 0, current_hp: 7 }));
  });

  it("heals (capped at max) and sets temporary HP", async () => {
    const user = userEvent.setup();
    renderWithProviders(<CombatTracker character={trackedCharacter} />);

    const heal = capture("patch", "/api/v1/characters/:id");
    await user.click(screen.getByRole("button", { name: "Curar" }));
    await waitFor(() => expect(heal.body).toEqual({ current_hp: 12 })); // already at max

    const temp = capture("patch", "/api/v1/characters/:id");
    const tempInput = screen.getByLabelText("PG temporales");
    await user.clear(tempInput);
    await user.type(tempInput, "5");
    await user.click(screen.getByRole("button", { name: "Fijar temporales" }));
    await waitFor(() => expect(temp.body).toEqual({ temporary_hp: 5 }));
  });

  it("toggles and removes a timed effect", async () => {
    const user = userEvent.setup();
    renderWithProviders(<CombatTracker character={trackedCharacter} />);
    const effects = await screen.findByRole("list", { name: "Efectos temporales" });

    const toggle = capture("patch", "/api/v1/characters/:id/modifiers/:mid");
    await user.click(within(effects).getByRole("checkbox", { name: "Bendecir" }));
    await waitFor(() => expect(toggle.body).toEqual({ is_active: false }));

    const remove = capture("delete", "/api/v1/characters/:id/modifiers/:mid");
    await user.click(within(effects).getByRole("button", { name: "Quitar Bendecir" }));
    await waitFor(() => expect(remove.body).toBeNull());
  });

  it("adds and removes conditions", async () => {
    const user = userEvent.setup();
    renderWithProviders(<CombatTracker character={trackedCharacter} />);

    // Active condition chip is shown (with its catalog name) and removable.
    await screen.findByText("Fatigado");
    const chips = screen.getByRole("list", { name: "Estados" });
    const post = capture("post", "/api/v1/characters/:id/conditions");
    await user.click(within(chips).getByRole("button", { name: "Quitar Fatigado" }));
    await waitFor(() => expect(post.body).toEqual({ condition: "fatigado", active: false }));

    // Adding a new condition.
    const add = capture("post", "/api/v1/characters/:id/conditions");
    await user.click(screen.getByRole("combobox", { name: "Añadir estado" }));
    await user.click(await screen.findByRole("option", { name: /Cegado/ }));
    await waitFor(() => expect(add.body).toEqual({ condition: "cegado", active: true }));
  });

  it("toggles a stance", async () => {
    const user = userEvent.setup();
    const patch = capture("patch", "/api/v1/characters/:id");
    renderWithProviders(<CombatTracker character={trackedCharacter} />);
    await user.click(screen.getByRole("checkbox", { name: "Cargar" }));
    await waitFor(() =>
      expect((patch.body as { stances: { charge: boolean } }).stances.charge).toBe(true),
    );
  });

  it("offers only the situational stances", async () => {
    renderWithProviders(<CombatTracker character={trackedCharacter} />);
    const stances = await screen.findByRole("region", { name: "Posturas" });

    for (const name of [
      "Cargar",
      "Luchar a la defensiva",
      "Defensa total",
      "Flanqueo",
      "Superioridad de altura",
    ]) {
      expect(within(stances).getByRole("checkbox", { name })).toBeInTheDocument();
    }
    expect(within(stances).getAllByRole("checkbox")).toHaveLength(5);

    // Power Attack and Combat Expertise belong to a weapon: they are attack lines,
    // not round-long choices, and a toggle here would double-count them.
    expect(screen.queryByRole("checkbox", { name: "Ataque poderoso" })).not.toBeInTheDocument();
    expect(screen.queryByRole("checkbox", { name: "Pericia en combate" })).not.toBeInTheDocument();
  });

  it("offers a stance for a feat the character has, and toggles it", async () => {
    const user = userEvent.setup();
    const patch = capture("patch", "/api/v1/characters/:id");
    renderWithProviders(
      <CombatTracker character={{ ...trackedCharacter, feats: ["Hendedura"] }} />,
    );

    const toggle = await screen.findByRole("checkbox", { name: "Hendedura" });
    await user.click(toggle);
    await waitFor(() =>
      expect((patch.body as { stances: { feat_stances: string[] } }).stances.feat_stances).toEqual([
        "Hendedura",
      ]),
    );
  });

  it("explains where each half of a stance feat is applied", async () => {
    renderWithProviders(
      <CombatTracker character={{ ...trackedCharacter, feats: ["Hendedura"] }} />,
    );
    await screen.findByRole("checkbox", { name: "Hendedura" });
    expect(screen.getByText(/aparece en su línea de arma/)).toBeInTheDocument();
  });

  it("spells out what a stance does while it is switched on", async () => {
    const withFeat = { ...trackedCharacter, feats: ["Hendedura"] };

    // Off: the benefit stays a tooltip.
    const { unmount } = renderWithProviders(<CombatTracker character={withFeat} />);
    await screen.findByRole("checkbox", { name: "Hendedura" });
    expect(screen.queryByText(/Atacas a un segundo enemigo/)).not.toBeInTheDocument();
    unmount();

    // On: it is on screen, because a number the GM must keep applying each round is
    // useless hidden behind a hover.
    renderWithProviders(
      <CombatTracker
        character={{
          ...withFeat,
          stances: {
            charge: false,
            fighting_defensively: false,
            total_defense: false,
            flanking: false,
            higher_ground: false,
            feat_stances: ["Hendedura"],
          },
        }}
      />,
    );
    expect(await screen.findByText(/Atacas a un segundo enemigo/)).toBeInTheDocument();
  });

  it("does not offer a stance for a feat the character lacks", async () => {
    renderWithProviders(<CombatTracker character={trackedCharacter} />);
    await screen.findByRole("region", { name: "Posturas" });
    expect(screen.queryByRole("checkbox", { name: "Hendedura" })).not.toBeInTheDocument();
  });

  it("lists timed effects and advances the round", async () => {
    const user = userEvent.setup();
    renderWithProviders(<CombatTracker character={trackedCharacter} />);
    const effects = await screen.findByRole("list", { name: "Efectos temporales" });
    expect(within(effects).getByText(/Bendecir/)).toBeInTheDocument();
    expect(within(effects).getByText("3 asaltos")).toBeInTheDocument();

    const tick = capture("post", "/api/v1/characters/:id/tick");
    await user.click(screen.getByRole("button", { name: "Siguiente asalto" }));
    await waitFor(() => expect(tick.body).toEqual({ rounds: 1 }));
  });

  it("adds an ad-hoc modifier", async () => {
    const user = userEvent.setup();
    const post = capture("post", "/api/v1/characters/:id/modifiers");
    renderWithProviders(<CombatTracker character={trackedCharacter} />);

    const form = screen.getByRole("form", { name: "Añadir modificador" });
    await user.type(within(form).getByLabelText("Fuente"), "Ira");
    await user.selectOptions(within(form).getByLabelText("Objetivo"), "ALL_SAVES");
    await user.click(within(form).getByRole("button", { name: "Añadir" }));

    await waitFor(() =>
      expect((post.body as { source: string; target: string }).source).toBe("Ira"),
    );
    expect((post.body as { target: string }).target).toBe("ALL_SAVES");
  });
});
