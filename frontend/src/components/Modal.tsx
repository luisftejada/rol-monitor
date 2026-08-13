import { useEffect, useId, useRef } from "react";

import { t } from "@/i18n";

interface ModalProps {
  title: string;
  onClose: () => void;
  children: React.ReactNode;
}

/**
 * A minimal accessible dialog: labelled by its heading, dismissed with Escape, the
 * backdrop, or the close button, and it returns focus to whatever opened it.
 *
 * Implemented over a plain element rather than `<dialog>` because `showModal` is
 * not implemented in the jsdom version the test suite runs on.
 */
export function Modal({ title, onClose, children }: ModalProps): React.JSX.Element {
  const titleId = useId();
  const closeRef = useRef<HTMLButtonElement>(null);
  const openerRef = useRef<Element | null>(null);

  // Focus moves on open and back on close — once each. This used to share an effect
  // with the Escape listener, whose dependency is `onClose`; callers pass an inline
  // arrow, so it changed identity every render and the effect re-ran, pulling focus
  // back to the close button. A dialog with only buttons never showed it, but typing
  // in one with a text field lost every character after the first.
  useEffect(() => {
    openerRef.current = document.activeElement;
    closeRef.current?.focus();
    return () => {
      // Returning focus keeps keyboard users where they were in the list.
      if (openerRef.current instanceof HTMLElement) openerRef.current.focus();
    };
  }, []);

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent): void => {
      if (event.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div
      className="modal__backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby={titleId}>
        <div className="modal__head">
          <h3 id={titleId}>{title}</h3>
          <button type="button" ref={closeRef} onClick={onClose}>
            {t("modal.close")}
          </button>
        </div>
        <div className="modal__body">{children}</div>
      </div>
    </div>
  );
}
