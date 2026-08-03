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
    await user.click(screen.getByRole("checkbox", { name: "Ataque poderoso" }));
    await waitFor(() =>
      expect((patch.body as { stances: { power_attack: boolean } }).stances.power_attack).toBe(
        true,
      ),
    );
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
