import { fireEvent, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import type { CharacterCreate, SkillLineDTO } from "@/api/types";
import { SkillsSection } from "@/features/editor/sections/SkillsSection";
import { defaultDraft } from "@/features/editor/draft";
import { fighterSheet } from "@/test/fixtures";
import { renderWithProviders } from "@/test/render";

function Host({ derived }: { derived?: SkillLineDTO[] } = {}): React.JSX.Element {
  const [draft, setDraft] = useState<CharacterCreate>(defaultDraft());
  return (
    <SkillsSection
      draft={draft}
      patch={(p) => setDraft((c) => ({ ...c, ...p }))}
      intModifier={1}
      derived={derived}
    />
  );
}

describe("SkillsSection", () => {
  it("shows the ranks spent/available counter", async () => {
    renderWithProviders(<Host />);
    // guerrero L1: max(1, 2 + Int 1) = 3, + human +1 = 4 available; 0 spent.
    await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Rangos: 0 / 4"));
  });

  it("marks class skills and increments ranks", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    const row = await screen.findByRole("row", { name: /Intimidar/ });
    expect(row).toHaveTextContent("★");

    await user.click(within(row).getByRole("button", { name: "Subir rango de Intimidar" }));
    expect(screen.getByRole("status")).toHaveTextContent("Rangos: 1 / 4");
  });

  it("shows the key characteristic in its own column, not beside the skill name", async () => {
    renderWithProviders(<Host />);
    const row = await screen.findByRole("row", { name: /Intimidar/ });
    const nameCell = within(row).getByRole("rowheader");
    expect(nameCell).toHaveTextContent("Intimidar");
    expect(nameCell).not.toHaveTextContent("Car");

    const cells = within(row).getAllByRole("cell");
    expect(cells[1]).toHaveTextContent("Car"); // the new characteristic column
  });

  it("drops a skill back to zero (only non-zero ranks persist)", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    const row = await screen.findByRole("row", { name: /Intimidar/ });
    await user.click(within(row).getByRole("button", { name: "Subir rango de Intimidar" }));
    await user.click(within(row).getByRole("button", { name: "Bajar rango de Intimidar" }));
    expect(screen.getByRole("status")).toHaveTextContent("Rangos: 0 / 4");
    expect(within(row).getByLabelText("Intimidar")).toHaveValue(0);
  });

  it("shows the ability, others and total columns from /derive", async () => {
    renderWithProviders(<Host derived={fighterSheet.skills} />);
    const row = await screen.findByRole("row", { name: /Intimidar/ });
    // 1 rank − 1 Charisma + 3 class skill = +3, as the fixture states it.
    expect(row).toHaveTextContent("-1");
    expect(row).toHaveTextContent("+3");
  });

  it("explains the others figure on hover and on keyboard focus", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host derived={fighterSheet.skills} />);
    const row = await screen.findByRole("row", { name: /Intimidar/ });
    const others = within(row).getByRole("button", { name: "Ver los bonificadores de Intimidar" });

    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();

    await user.hover(others);
    const tip = await screen.findByRole("tooltip");
    expect(tip).toHaveTextContent("Habilidad de clase");
    // Ranks and the ability modifier have their own columns, so the tooltip behind
    // "others" leaves them out rather than repeating what those columns already show.
    expect(tip).not.toHaveTextContent("Carisma");
    expect(tip).not.toHaveTextContent("Rangos");

    await user.unhover(others);
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();

    // Hover alone would leave this unreachable by keyboard and dead on touch.
    fireEvent.focus(others);
    expect(await screen.findByRole("tooltip")).toBeInTheDocument();
  });

  it("renders a placeholder until the first derivation arrives", async () => {
    renderWithProviders(<Host />);
    const row = await screen.findByRole("row", { name: /Intimidar/ });
    expect(row).toHaveTextContent("—");
    expect(within(row).queryByRole("button", { name: /Ver los bonificadores/ })).toBeNull();
  });
});
