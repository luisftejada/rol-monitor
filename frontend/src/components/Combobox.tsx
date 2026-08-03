import { useId, useRef, useState } from "react";

import { t } from "@/i18n";
import { fuzzyMatch } from "@/lib/normalize";

export interface ComboboxOption {
  value: string;
  label: string;
  disabled?: boolean;
  hint?: string;
}

interface ComboboxProps {
  label: string;
  options: ComboboxOption[];
  value: string | null;
  onChange: (value: string) => void;
  placeholder?: string;
}

/**
 * ARIA 1.2 combobox with a listbox popup and accent-insensitive fuzzy search.
 * Keyboard-complete: ArrowUp/Down move the active option, Enter commits, Escape
 * closes and reverts the query. Ineligible options are shown (never hidden) but
 * cannot be selected.
 */
export function Combobox({
  label,
  options,
  value,
  onChange,
  placeholder,
}: ComboboxProps): React.JSX.Element {
  const autoId = useId();
  const listId = `${autoId}-list`;
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const containerRef = useRef<HTMLDivElement>(null);

  const selected = options.find((option) => option.value === value) ?? null;
  const filtered = query.trim()
    ? options.filter((option) => fuzzyMatch(`${option.label} ${option.hint ?? ""}`, query))
    : options;
  const displayValue = open ? query : (selected?.label ?? "");

  const commit = (option: ComboboxOption): void => {
    if (option.disabled) return;
    onChange(option.value);
    setQuery("");
    setOpen(false);
    setActiveIndex(-1);
  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>): void => {
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setOpen(true);
      setActiveIndex((index) => Math.min(filtered.length - 1, index + 1));
    } else if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex((index) => Math.max(0, index - 1));
    } else if (event.key === "Enter") {
      const option = filtered[activeIndex];
      if (open && option) {
        event.preventDefault();
        commit(option);
      }
    } else if (event.key === "Escape") {
      setOpen(false);
      setQuery("");
      setActiveIndex(-1);
    }
  };

  const activeId =
    open && activeIndex >= 0 && filtered[activeIndex] ? `${listId}-opt-${activeIndex}` : undefined;

  return (
    <div
      className="combobox"
      ref={containerRef}
      onBlur={(event) => {
        if (!containerRef.current?.contains(event.relatedTarget as Node | null)) {
          setOpen(false);
        }
      }}
    >
      <label htmlFor={autoId}>{label}</label>
      <input
        id={autoId}
        role="combobox"
        aria-expanded={open}
        aria-controls={listId}
        aria-autocomplete="list"
        aria-activedescendant={activeId}
        value={displayValue}
        placeholder={placeholder}
        onChange={(event) => {
          setQuery(event.target.value);
          setOpen(true);
          setActiveIndex(-1);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={handleKeyDown}
      />
      {open && (
        <ul role="listbox" id={listId} aria-label={label} className="combobox__list">
          {filtered.length === 0 ? (
            <li className="combobox__empty" role="presentation">
              {t("combobox.noResults")}
            </li>
          ) : (
            filtered.map((option, index) => (
              <li
                key={option.value}
                id={`${listId}-opt-${index}`}
                role="option"
                aria-selected={option.value === value}
                aria-disabled={option.disabled || undefined}
                className={`combobox__option${index === activeIndex ? " is-active" : ""}${
                  option.disabled ? " is-disabled" : ""
                }`}
                onMouseDown={(event) => {
                  event.preventDefault();
                  commit(option);
                }}
              >
                <span>{option.label}</span>
                {option.hint && <span className="combobox__hint"> — {option.hint}</span>}
              </li>
            ))
          )}
        </ul>
      )}
    </div>
  );
}
