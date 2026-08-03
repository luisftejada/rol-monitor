import { screen, waitFor, within } from "@testing-library/react";
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

describe("FeatsSection", () => {
  it("adds and removes a feat", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await user.click(await screen.findByRole("combobox", { name: "Añadir dote" }));
    await user.click(await screen.findByRole("option", { name: /Esquiva/ }));

    const owned = screen.getByRole("list", { name: "Dotes seleccionadas" });
    expect(within(owned).getByText("Esquiva")).toBeInTheDocument();

    await user.click(within(owned).getByRole("button", { name: "Quitar Esquiva" }));
    expect(within(owned).queryByText("Esquiva")).not.toBeInTheDocument();
  });

  it("surfaces the unmet prerequisite for ineligible feats (never hidden)", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Host />);
    await user.click(await screen.findByRole("combobox", { name: "Añadir dote" }));
    const acometer = await screen.findByRole("option", { name: /Acometer/ });
    await waitFor(() => expect(acometer).toHaveTextContent("ataque base +6"));
  });
});
