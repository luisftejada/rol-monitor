import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Combobox, type ComboboxOption } from "@/components/Combobox";
import { renderWithProviders } from "@/test/render";

const options: ComboboxOption[] = [
  { value: "espada-larga", label: "Espada larga" },
  { value: "espada-corta", label: "Espada corta" },
  { value: "introspeccion", label: "Introspección" },
  { value: "bloqueada", label: "Bloqueada", disabled: true, hint: "no disponible" },
];

describe("Combobox", () => {
  it("filters options by fuzzy, accent-insensitive search", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <Combobox label="Arma" options={options} value={null} onChange={vi.fn()} />,
    );
    const input = screen.getByRole("combobox", { name: "Arma" });

    await user.type(input, "espada lar");
    const list = screen.getByRole("listbox");
    expect(within(list).getByRole("option", { name: /Espada larga/ })).toBeInTheDocument();
    expect(within(list).queryByRole("option", { name: /Espada corta/ })).not.toBeInTheDocument();

    await user.clear(input);
    await user.type(input, "introspec"); // no accent typed, accented option matches
    expect(screen.getByRole("option", { name: /Introspección/ })).toBeInTheDocument();
  });

  it("selects an option on click", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <Combobox label="Arma" options={options} value={null} onChange={onChange} />,
    );
    await user.click(screen.getByRole("combobox", { name: "Arma" }));
    await user.click(screen.getByRole("option", { name: "Espada larga" }));
    expect(onChange).toHaveBeenCalledWith("espada-larga");
  });

  it("reopens on click after a selection, when the field still has focus", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <Combobox label="Arma" options={options} value="espada-larga" onChange={onChange} />,
    );
    const input = screen.getByRole("combobox", { name: "Arma" });

    await user.click(input);
    await user.click(screen.getByRole("option", { name: "Espada corta" }));
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();
    expect(input).toHaveFocus();

    // A second click emits no focus event, so opening must not depend on focus.
    await user.click(input);
    expect(screen.getByRole("listbox")).toBeInTheDocument();
  });

  it("reopens on click after dismissing the list with Escape", async () => {
    const user = userEvent.setup();
    renderWithProviders(
      <Combobox label="Arma" options={options} value={null} onChange={vi.fn()} />,
    );
    const input = screen.getByRole("combobox", { name: "Arma" });

    await user.click(input);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("listbox")).not.toBeInTheDocument();

    await user.click(input);
    expect(screen.getByRole("listbox")).toBeInTheDocument();
  });

  it("is keyboard operable (ArrowDown + Enter)", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <Combobox label="Arma" options={options} value={null} onChange={onChange} />,
    );
    await user.click(screen.getByRole("combobox", { name: "Arma" }));
    await user.keyboard("{ArrowDown}{Enter}");
    expect(onChange).toHaveBeenCalledWith("espada-larga");
  });

  it("does not select a disabled option", async () => {
    const onChange = vi.fn();
    const user = userEvent.setup();
    renderWithProviders(
      <Combobox label="Arma" options={options} value={null} onChange={onChange} />,
    );
    await user.click(screen.getByRole("combobox", { name: "Arma" }));
    const disabled = screen.getByRole("option", { name: /Bloqueada/ });
    expect(disabled).toHaveAttribute("aria-disabled", "true");
    await user.click(disabled);
    expect(onChange).not.toHaveBeenCalled();
  });
});
