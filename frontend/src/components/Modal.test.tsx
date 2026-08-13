import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { describe, expect, it, vi } from "vitest";

import { Modal } from "@/components/Modal";
import { renderWithProviders } from "@/test/render";

describe("Modal", () => {
  it("keeps focus in a field while typing", async () => {
    const user = userEvent.setup();
    // A caller passing an inline `onClose` is the normal case, and it used to make
    // the mount effect re-run on every render — which pulled focus back to the close
    // button after each keystroke, so only the first character survived.
    function Host() {
      const [value, setValue] = useState("");
      const [open, setOpen] = useState(true);
      return open ? (
        <Modal title="Objeto" onClose={() => setOpen(false)}>
          <label>
            Nombre
            <input value={value} onChange={(event) => setValue(event.target.value)} />
          </label>
        </Modal>
      ) : null;
    }
    renderWithProviders(<Host />);

    await user.type(screen.getByLabelText("Nombre"), "Amuleto");
    expect(screen.getByLabelText("Nombre")).toHaveValue("Amuleto");
  });

  it("opens with the close button focused", () => {
    renderWithProviders(
      <Modal title="Objeto" onClose={vi.fn()}>
        <p>contenido</p>
      </Modal>,
    );
    expect(screen.getByRole("button", { name: "Cerrar" })).toHaveFocus();
  });

  it("closes on Escape and on the close button", async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    renderWithProviders(
      <Modal title="Objeto" onClose={onClose}>
        <p>contenido</p>
      </Modal>,
    );

    await user.keyboard("{Escape}");
    expect(onClose).toHaveBeenCalledTimes(1);

    await user.click(within(screen.getByRole("dialog")).getByRole("button", { name: "Cerrar" }));
    expect(onClose).toHaveBeenCalledTimes(2);
  });
});
