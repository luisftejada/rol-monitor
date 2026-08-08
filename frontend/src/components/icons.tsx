/**
 * Inline SVG icons. Drawn here rather than pulled from an icon package: three
 * glyphs do not justify a dependency, and inlining keeps them styleable with
 * `currentColor` so they follow the button they sit in, in either theme.
 *
 * Each is `aria-hidden`: the button around it carries the accessible name, so a
 * screen reader announces the action once, not twice.
 */

const BASE = {
  width: 16,
  height: 16,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 2,
  strokeLinecap: "round",
  strokeLinejoin: "round",
  "aria-hidden": true,
  focusable: false,
} as const;

/** Two overlapping sheets: the conventional "copy" glyph. */
export function CopyIcon(): React.JSX.Element {
  return (
    <svg {...BASE}>
      <rect x="9" y="9" width="11" height="11" rx="2" />
      <path d="M5 15V5a2 2 0 0 1 2-2h10" />
    </svg>
  );
}

/** A waste bin, for destructive actions. */
export function TrashIcon(): React.JSX.Element {
  return (
    <svg {...BASE}>
      <path d="M3 6h18" />
      <path d="M8 6V4a1 1 0 0 1 1-1h6a1 1 0 0 1 1 1v2" />
      <path d="M6 6v14a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V6" />
      <path d="M10 11v6M14 11v6" />
    </svg>
  );
}

/** A pencil, for editing. */
export function PencilIcon(): React.JSX.Element {
  return (
    <svg {...BASE}>
      <path d="M12 20h9" />
      <path d="M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z" />
    </svg>
  );
}
