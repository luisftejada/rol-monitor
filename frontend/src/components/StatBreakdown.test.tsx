import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { StatBreakdown } from "@/components/StatBreakdown";
import { renderWithProviders } from "@/test/render";

const breakdown = [
  { label: "base", value: 10, type: null, source: "base" },
  { label: "Cota de escamas", value: 5, type: "armadura", source: "armor" },
];
const suppressed = [
  { label: "Escudo de fe", value: 1, type: "deflexión", reason: "superado por Anillo +2" },
];

describe("StatBreakdown", () => {
  it("starts collapsed and shows the total", () => {
    renderWithProviders(
      <StatBreakdown label="CA" value="18" breakdown={breakdown} suppressed={suppressed} />,
    );
    const toggle = screen.getByRole("button", { name: /CA/ });
    expect(toggle).toHaveAttribute("aria-expanded", "false");
    expect(toggle).toHaveTextContent("18");
    expect(screen.queryByText("Cota de escamas")).not.toBeInTheDocument();
  });

  it("expands to reveal applied and suppressed modifiers", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <StatBreakdown label="CA" value="18" breakdown={breakdown} suppressed={suppressed} />,
    );
    await user.click(screen.getByRole("button", { name: /CA/ }));

    expect(screen.getByRole("button", { name: /CA/ })).toHaveAttribute("aria-expanded", "true");
    const region = screen.getByRole("region");
    expect(region).toHaveTextContent("Cota de escamas");
    expect(region).toHaveTextContent("+5");
    // Suppressed bonus is surfaced with its reason.
    expect(region).toHaveTextContent("Escudo de fe");
    expect(region).toHaveTextContent("superado por Anillo +2");
  });

  it("collapses again on a second activation", async () => {
    const user = userEvent.setup();
    renderWithProviders(<StatBreakdown label="CA" value="18" breakdown={breakdown} />);
    const toggle = screen.getByRole("button", { name: /CA/ });
    await user.click(toggle);
    await user.click(toggle);
    expect(toggle).toHaveAttribute("aria-expanded", "false");
  });

  it("shows an empty-state when there are no modifiers", async () => {
    const user = userEvent.setup();
    renderWithProviders(<StatBreakdown label="CMD" value="15" breakdown={[]} />);
    await user.click(screen.getByRole("button", { name: /CMD/ }));
    expect(screen.getByText("Sin bonificadores.")).toBeInTheDocument();
  });
});
