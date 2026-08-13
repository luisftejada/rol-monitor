import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import type { BabDTO, CharacterCreate, ValueBreakdown } from "@/api/types";
import { AbilitiesSection } from "@/features/editor/sections/AbilitiesSection";
import { defaultDraft } from "@/features/editor/draft";
import { renderWithProviders } from "@/test/render";
import { value } from "@/test/fixtures";

function Host({
  modifiers,
  bab,
  initiative,
  cmb,
  cmd,
}: {
  modifiers?: Record<string, number>;
  bab?: BabDTO;
  initiative?: ValueBreakdown;
  cmb?: ValueBreakdown;
  cmd?: ValueBreakdown;
} = {}): React.JSX.Element {
  const [draft, setDraft] = useState<CharacterCreate>(defaultDraft());
  return (
    <AbilitiesSection
      draft={draft}
      patch={(p) => setDraft((c) => ({ ...c, ...p }))}
      modifiers={modifiers}
      bab={bab}
      initiative={initiative}
      cmb={cmb}
      cmd={cmd}
    />
  );
}

/** Last cell of a row is the "Bonif" column. */
function modifierCell(ability: string): HTMLElement {
  const cells = within(screen.getByRole("row", { name: new RegExp(ability) })).getAllByRole("cell");
  const last = cells.at(-1);
  if (!last) throw new Error(`no cells in row ${ability}`);
  return last;
}

describe("AbilitiesSection", () => {
  it("shows the point-buy counter against the default budget of 20", async () => {
    renderWithProviders(<Host />);
    // 7+5+3+2+0-2 = 15 for {15,14,13,12,10,8}
    await waitFor(() => expect(screen.getByText("Puntos: 15 / 20")).toBeInTheDocument());
    expect(screen.getByLabelText("Puntos disponibles")).toHaveValue(20);
  });

  it("adjusts the budget with the steppers and direct entry", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await waitFor(() => expect(screen.getByText("Puntos: 15 / 20")).toBeInTheDocument());

    await user.click(screen.getByRole("button", { name: "Subir puntos disponibles" }));
    expect(screen.getByText("Puntos: 15 / 21")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Bajar puntos disponibles" }));
    expect(screen.getByText("Puntos: 15 / 20")).toBeInTheDocument();

    const budget = screen.getByLabelText("Puntos disponibles");
    await user.clear(budget);
    await user.type(budget, "25");
    expect(screen.getByText("Puntos: 15 / 25")).toBeInTheDocument();
  });

  it("flags going over the budget, and clears once the budget is raised", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await waitFor(() => expect(screen.getByText(/Puntos: 15/)).toBeInTheDocument());

    // Drop the budget below what the standard array already spends.
    const budget = screen.getByLabelText("Puntos disponibles");
    await user.clear(budget);
    await user.type(budget, "10");
    expect(screen.getByText(/Puntos: 15 \/ 10/)).toBeInTheDocument();
    expect(screen.getByRole("alert")).toHaveTextContent("presupuesto");

    // Raising it past the spend clears the warning.
    await user.clear(budget);
    await user.type(budget, "20");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("counts a raised score against the budget", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await waitFor(() => expect(screen.getByText(/Puntos: 15/)).toBeInTheDocument());
    await user.click(screen.getByRole("button", { name: "+ Fue" }));
    // 15 -> 16 costs 10 instead of 7: total 18, still inside the default 20.
    expect(screen.getByText(/Puntos: 18 \/ 20/)).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders the modifier column from the derived values", async () => {
    // Values stand in for what /derive returned; the modifier is a Pathfinder
    // formula and is never recomputed in the frontend.
    renderWithProviders(<Host modifiers={{ Fue: 2, Des: 2, Con: 1, Int: 1, Sab: 0, Car: -1 }} />);
    await screen.findByRole("columnheader", { name: "Bonif" });

    expect(modifierCell("Fue")).toHaveTextContent("+2");
    expect(modifierCell("Sab")).toHaveTextContent("+0");
    expect(modifierCell("Car")).toHaveTextContent("-1");
  });

  it("shows a placeholder in the modifier column until derivation arrives", async () => {
    renderWithProviders(<Host />);
    await screen.findByRole("columnheader", { name: "Bonif" });
    expect(modifierCell("Fue")).toHaveTextContent("—");
  });

  it("shows base attack, initiative, BMC and DMC from the derived values", async () => {
    renderWithProviders(
      <Host
        bab={{ total: 6, iteratives: [6, 1], breakdown: [] }}
        initiative={value(3)}
        cmb={value(7)}
        cmd={value(19)}
      />,
    );
    // The toggle's accessible name is its label plus its value, hence the regexes.
    expect(screen.getByRole("button", { name: /Ataque base/ })).toHaveTextContent("+6 (+6 / +1)");
    // The toggle's accessible name is its label plus its value, hence the regexes.
    expect(screen.getByRole("button", { name: /Iniciativa/ })).toHaveTextContent("+3");
    expect(screen.getByRole("button", { name: /^BMC/ })).toHaveTextContent("+7");
    expect(screen.getByRole("button", { name: /^DMC/ })).toHaveTextContent("19");
  });

  it("shows placeholders for the tactical figures until derivation arrives", async () => {
    renderWithProviders(<Host />);
    expect(screen.getByRole("button", { name: /Ataque base/ })).toHaveTextContent("—");
    expect(screen.getByRole("button", { name: /Iniciativa/ })).toHaveTextContent("—");
  });

  it("expands base attack to show which class earned it", async () => {
    const user = userEvent.setup();
    // A fighter 4 / wizard 4 has +6, not the +8 a pure fighter has: the breakdown is
    // what answers "why is this lower than I expected?".
    renderWithProviders(
      <Host
        bab={{
          total: 6,
          iteratives: [6, 1],
          breakdown: [
            { label: "Guerrero 4", value: 4, type: null, source: "class" },
            { label: "Mago 4", value: 2, type: null, source: "class" },
          ],
        }}
      />,
    );

    await user.click(screen.getByRole("button", { name: /Ataque base/ }));
    const region = screen.getByRole("region", { name: /Ataque base/ });
    expect(region).toHaveTextContent("Guerrero 4");
    expect(region).toHaveTextContent("Mago 4");
  });

  it("edits current and temporary hit points", async () => {
    const user = userEvent.setup();
    const seen: { draft: CharacterCreate } = { draft: defaultDraft() };
    function HpHost() {
      const [draft, setDraft] = useState<CharacterCreate>(defaultDraft());
      seen.draft = draft;
      return <AbilitiesSection draft={draft} patch={(p) => setDraft((c) => ({ ...c, ...p }))} />;
    }
    renderWithProviders(<HpHost />);

    const current = screen.getByLabelText("Actuales");
    await user.clear(current);
    await user.type(current, "17");
    expect(seen.draft.current_hp).toBe(17);

    // Temporary hit points are a pool you are given, never a debt.
    const temporary = screen.getByLabelText("Temporales");
    await user.clear(temporary);
    await user.type(temporary, "-3");
    expect(seen.draft.temporary_hp).toBe(3);
  });

  it("fixes level 1 at the die's maximum and lets later levels be entered", async () => {
    const user = userEvent.setup();
    const seen: { draft: CharacterCreate } = { draft: defaultDraft() };
    function HpHost() {
      const [draft, setDraft] = useState<CharacterCreate>({
        ...defaultDraft(),
        class_levels: [{ class_slug: "guerrero", level: 2, is_prestige: false, is_favored: false }],
      });
      seen.draft = draft;
      return <AbilitiesSection draft={draft} patch={(p) => setDraft((c) => ({ ...c, ...p }))} />;
    }
    renderWithProviders(<HpHost />);

    // Level 1 is the die's maximum by rule, so it is shown rather than asked for.
    // The row exists before the class catalog lands, so the die is what to wait on.
    await waitFor(() => expect(screen.getByLabelText("PG del nivel 1")).toHaveValue(10));
    expect(screen.getByLabelText("PG del nivel 1")).toBeDisabled();

    const second = screen.getByLabelText("PG del nivel 2");
    expect(second).toBeEnabled();
    // Select and overwrite, the way one edits a number that is already there:
    // the field is clamped to 1..die, so clearing it writes the minimum back.
    await user.tripleClick(second);
    await user.keyboard("7");
    expect(seen.draft.hp_per_level?.find((e) => e.level === 2)).toMatchObject({
      value: 7,
      mode: "manual",
    });
  });

  it("rolls a level, and rolls it with the floor the backend gave", async () => {
    const user = userEvent.setup();
    const seen: { draft: CharacterCreate } = { draft: defaultDraft() };
    function HpHost() {
      const [draft, setDraft] = useState<CharacterCreate>({
        ...defaultDraft(),
        class_levels: [{ class_slug: "guerrero", level: 2, is_prestige: false, is_favored: false }],
      });
      seen.draft = draft;
      return <AbilitiesSection draft={draft} patch={(p) => setDraft((c) => ({ ...c, ...p }))} />;
    }
    renderWithProviders(<HpHost />);

    await user.click(await screen.findByLabelText("Tirar los PG del nivel 2"));
    const rolled = seen.draft.hp_per_level?.find((e) => e.level === 2);
    expect(rolled?.mode).toBe("roll");
    expect(rolled!.value).toBeGreaterThanOrEqual(1);
    expect(rolled!.value).toBeLessThanOrEqual(10);

    // The floored roll can never come out under the class' floor, whatever the die
    // does — that is the whole point of the option.
    await user.click(screen.getByLabelText("Tirar con mínimo los PG del nivel 2"));
    const floored = seen.draft.hp_per_level?.find((e) => e.level === 2);
    expect(floored?.mode).toBe("floored");
    expect(floored!.value).toBeGreaterThanOrEqual(6); // d10 floors at 6
  });

  it("clamps point-buy scores to a minimum of 7", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    const minus = await screen.findByRole("button", { name: "− Fue" });
    for (let i = 0; i < 12; i += 1) await user.click(minus);
    const row = screen.getByRole("row", { name: /Fue/ });
    expect(within(row).getByLabelText("Fue")).toHaveTextContent("7");
  });

  it("assigns the flexible racial bonus (human +2)", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    const select = await screen.findByRole("combobox", { name: "+2 racial" });
    await user.selectOptions(select, "Fue");
    const row = screen.getByRole("row", { name: /Fue/ });
    // Racial column becomes +2.
    expect(within(row).getByText("+2")).toBeInTheDocument();
  });

  it("allows free manual entry", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await user.click(await screen.findByRole("radio", { name: "Manual" }));
    const row = screen.getByRole("row", { name: /Fue/ });
    const input = within(row).getByLabelText("Fue");
    await user.clear(input);
    await user.type(input, "20");
    expect(input).toHaveValue(20);
  });

  it("prevents duplicate values in the standard-array method", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await user.click(await screen.findByRole("radio", { name: "Matriz estándar" }));
    const row = screen.getByRole("row", { name: /Fue/ });
    const select = within(row).getByRole("combobox", { name: "Fue" });
    // 14 is taken by Des, so it is disabled in Fue's select.
    const option14 = within(select).getByRole("option", { name: "14" }) as HTMLOptionElement;
    expect(option14.disabled).toBe(true);
  });
});
