# Employee Portal — Design System

**Product:** Internal employee portal / employee management system
**Audience:** Employees and HR/admin staff, internal use only
**Aesthetic:** Black-and-white foundation with a tight, controlled band of red-orange accents. Flat by default, hard edges, thick black rule lines. No decorative rounding — the only softness in the whole system is a small hover-triggered radius on filled elements.

This file is the single source of truth for color, type, borders, icons, and layout. Every value a component needs should come from the `:root` variables defined here — no ad hoc hex codes, no ad hoc font names, no one-off border declarations anywhere else in the codebase.

---

## 1. Color System

Seven colors, total. No tints, no shades, no gradients, no drop shadows for depth — if something needs separation from its neighbor, give it a border, not a shadow.

| Token | Hex | Role |
|---|---|---|
| `--color-black` | `#1E1B1A` | Text, borders, icon fill on light backgrounds, black-background surfaces |
| `--color-white` | `#FFFDF9` | Base page background, text/icon fill on black or accent backgrounds |
| `--color-offwhite` | `#E1E6E1` | Secondary section background, dividers, disabled states, table stripe |
| `--color-primary` | `#F85A3E` | Primary actions (primary buttons, active nav state, links) |
| `--color-primary-hover` | `#E63B2E` | Hover/pressed state for primary actions |
| `--color-secondary` | `#FF7733` | Secondary emphasis (badges, highlights, secondary buttons, in-progress states) |
| `--color-secondary-hover` | `#E15634` | Hover/pressed state for secondary emphasis |

**Rules of use:**
- Default surface is `--color-white`. Use `--color-black` as a surface only for deliberate emphasis (top nav bar, a callout, a footer) — never as body copy background.
- `--color-offwhite` is the only other neutral surface. Use it to separate a section from the white sections around it without introducing a new color.
- The two accent pairs (`primary`/`primary-hover`, `secondary`/`secondary-hover`) are functionally interchangeable in hue family (red-orange) but carry distinct meaning: **primary = the one action you want taken** (Save, Submit, Approve, primary nav highlight). **Secondary = flags attention without demanding action** (status badges, "pending" tags, secondary buttons, in-review markers).
- Never place `--color-primary` text/icons on a `--color-secondary` surface or vice versa — the two accents don't mix directly. They each pair only with black, white, or off-white.
- Color is the exception, not the rule. Most of any given screen should read as black, white, and off-white, with accent color appearing only at points of action or status.

---

## 2. Typography

Three families, three fixed jobs. Do not use any of them outside its assigned job, and do not introduce a fourth family.

| Token | Family | Job |
|---|---|---|
| `--font-title` | `'Russo One', sans-serif` | Page-level titles / hero headings only (H1) |
| `--font-subtitle` | `'Fira Sans', sans-serif` | Section, module, and article headings (H2–H4), nav labels, table headers |
| `--font-body` | `'Overpass', sans-serif` | Body copy, form fields, buttons, table cells, everything else |

**Import (Google Fonts):**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Russo+One&family=Fira+Sans:wght@400;500;600;700&family=Overpass:wght@400;500;600;700&display=swap" rel="stylesheet">
```

**Type scale (starting point, adjust proportionally):**
- H1 (`--font-title`): 2.5rem / 1.15 line-height, only one per page
- H2 (`--font-subtitle`): 1.5rem / 1.25 line-height, weight 600
- H3 (`--font-subtitle`): 1.125rem / 1.3 line-height, weight 600
- Body (`--font-body`): 1rem / 1.5 line-height, weight 400
- Small / meta (`--font-body`): 0.875rem / 1.4 line-height, weight 400
- Button/label text (`--font-body`): 0.9375rem, weight 600

Keep body line length under ~80 characters. Russo One is a display face — never set it below 1.5rem or use it for more than a few words at a time (it does not read well in long strings). Do not use all-caps as a substitute for hierarchy; weight and family already carry that job.

---

## 3. Borders & Radius

Two rules govern the entire system:

1. **Flat by default, everywhere.** `border-radius: 0` is the baseline for every element in the system.
2. **Soft on hover, only if there's a fill.** An element transitions to a small radius on hover **only when that element has a background color** (buttons, filled badges, filled nav items, cards with a colored surface). Elements with no background fill (plain text links, unfilled outline items, table rows) never gain a hover radius, since there is no filled shape for the rounding to read on.

Border strokes are `2px solid var(--color-black)` by default across the whole system. Every element category has its own on/off switch (`--border-style` value: `solid` or `none`) living in `:root`, defaulted to **on**. A component is switched off by editing that one variable in `:root` — never by overriding `border: none` inside a component's own rule.

```css
transition: border-radius 0.18s ease;
```

---

## 4. `:root` — Full Variable Reference

This block is the only place colors, fonts, and border toggles are declared. Every component pulls from these tokens; nothing below this layer should hard-code a hex value, font name, or `border-radius`/`border-style` value directly.

```css
:root {
  /* ============ COLOR ============ */
  --color-black: #1E1B1A;
  --color-white: #FFFDF9;
  --color-offwhite: #E1E6E1;

  --color-primary: #F85A3E;
  --color-primary-hover: #E63B2E;
  --color-secondary: #FF7733;
  --color-secondary-hover: #E15634;

  /* Semantic aliases — reference these in components, not the raw colors above */
  --color-bg: var(--color-white);
  --color-bg-alt: var(--color-offwhite);
  --color-bg-inverse: var(--color-black);
  --color-text: var(--color-black);
  --color-text-inverse: var(--color-white);
  --color-action: var(--color-primary);
  --color-action-hover: var(--color-primary-hover);
  --color-flag: var(--color-secondary);
  --color-flag-hover: var(--color-secondary-hover);

  /* ============ TYPE ============ */
  --font-title: 'Russo One', sans-serif;
  --font-subtitle: 'Fira Sans', sans-serif;
  --font-body: 'Overpass', sans-serif;

  --fs-h1: 2.5rem;
  --fs-h2: 1.5rem;
  --fs-h3: 1.125rem;
  --fs-body: 1rem;
  --fs-small: 0.875rem;
  --fs-label: 0.9375rem;

  /* ============ BORDER — GLOBAL ============ */
  --border-width: 2px;
  --border-color: var(--color-black);

  /* Radius */
  --radius-flat: 0px;
  --radius-hover: 6px;
  --radius-transition: border-radius 0.18s ease;

  /* ============ BORDER — PER-COMPONENT TOGGLES ============ */
  /* Value is either `solid` (ON, default) or `none` (OFF).            */
  /* To disable a category site-wide, change its value here — do not   */
  /* override border in the component's own rule.                     */
  --border-buttons: solid;
  --border-inputs: solid;
  --border-cards: solid;
  --border-nav: solid;
  --border-tables: solid;
  --border-sections: solid;
  --border-modals: solid;
  --border-badges: solid;
  --border-dropdowns: solid;
  --border-avatars: solid;
  --border-tabs: solid;
  --border-tooltips: solid;

  /* ============ SPACING (8px base grid) ============ */
  --space-1: 0.5rem;
  --space-2: 1rem;
  --space-3: 1.5rem;
  --space-4: 2rem;
  --space-5: 3rem;
}
```

**Applying a toggle in component CSS:**
```css
.btn {
  border: var(--border-width) var(--border-buttons) var(--border-color);
}
.card {
  border: var(--border-width) var(--border-cards) var(--border-color);
}
```
If `--border-buttons` is changed to `none`, every button in the system loses its border in one edit, with no per-component overrides required.

---

## 5. Layout & Alignment

- **Flexbox is the default layout mechanism** for every component — nav bars, cards, form rows, list items, table toolbars, modal headers/footers, button groups. Use `display: flex` with explicit `flex-direction`, `align-items`, `justify-content`, and `gap` rather than margin-based spacing between flex children.
- **Alignment default is left-aligned.** Body text, form labels, table content, list content, card content — all left-aligned unless a component specifically calls for centering.
- **Center only where it aids focus**, specifically:
  - Empty states / zero-data placeholders (icon + message + action, centered as a column)
  - Modal/dialog action buttons on narrow modals
  - Loading states
  - The content of a badge or pill (text centered within its own shape)
- Use `flex-wrap: wrap` on any row-based layout that must respond to narrower viewports (toolbars, filter bars, tag rows) rather than switching to grid.
- Sections are full-width flex columns (`flex-direction: column`) with generous internal padding (`--space-4` / `--space-5`), and each section may take a different background token (`--color-bg`, `--color-bg-alt`, or `--color-bg-inverse`) to visually separate zones of the portal (e.g., a black header/nav band, a white content band, an off-white "team directory" band).

---

## 6. Component Patterns

### Buttons
- Flat rectangle, `border-radius: var(--radius-flat)`, `border: var(--border-width) var(--border-buttons) var(--border-color)`.
- Primary button: `background: var(--color-action)`, text `var(--color-white)`.
- Secondary button: `background: transparent`, text/border `var(--color-black)`.
- Flagged/tertiary button: `background: var(--color-flag)`, text `var(--color-black)`.
- On hover (any filled button): `border-radius: var(--radius-hover)` + swap background to its `-hover` token. Transition via `--radius-transition`.
- Internal layout: `display: flex; align-items: center; gap: var(--space-1);` for icon + label buttons, content left-aligned within the button unless the button is a standalone icon button (then centered).

### Cards / Modules
- `background: var(--color-white)` or `var(--color-bg-alt)`, `border: var(--border-width) var(--border-cards) var(--border-color)`, flat corners at rest.
- Hover radius (`--radius-hover`) only applies if the card itself is clickable/interactive **and** carries a background fill distinct from the page (e.g., a colored status card). A plain white card sitting on a white page does not gain a hover radius, since it has no fill to soften against — that card should instead show a border-color or background shift on hover.
- Header row inside a card: flex row, `justify-content: space-between`, title in `--font-subtitle`.

### Form Inputs
- Flat rectangle, 2px black border by default (`--border-inputs`). No inner shadow, no glow.
- Focus state: swap border color to `var(--color-action)`, keep radius flat (inputs are functional, not decorative — no hover-radius softening on inputs even though they have a white fill, since flattening/softening on focus would compete with the border-color focus cue).
- Label above field, left-aligned, `--font-body` weight 600, `--fs-small`.

### Navigation
- Top nav bar: `background: var(--color-bg-inverse)` (black band), flex row, `justify-content: space-between`, icons and active-state text in `--color-white`; active nav item accented with `--color-action` underline or left-border tick (flat, no radius).
- Nav items use `--border-nav` for any dividing rules between items (thin vertical rule, still using the 2px black stroke token unless intentionally thinned in a specific spot).
- Sidebar (if used): `background: var(--color-white)` or `--color-bg-alt`, flex column, left-aligned items, `border-right: var(--border-width) var(--border-nav) var(--border-color)`.

### Tables
- Header row: `--font-subtitle`, `background: var(--color-bg-alt)` or `var(--color-bg-inverse)` depending on section, `border-bottom: var(--border-width) var(--border-tables) var(--border-color)`.
- Row dividers: 1× `--border-width` hairline in `--border-color` via `--border-tables`, no vertical column rules (keeps it flat and quiet — horizontal-only ruling).
- Stripe alternate rows with `--color-offwhite`, not a tint of the accent.

### Badges / Status Pills
- Flat rectangle by default, `border: var(--border-width) var(--border-badges) var(--border-color)`, background per status:
  - Active/approved → `--color-action` fill, white text
  - Pending/in-review → `--color-flag` fill, black text
  - Neutral/inactive → `--color-bg-alt` fill, black text, black border
- Content centered (`justify-content: center`) within the pill, flex row, small internal gap if paired with an icon.
- Hover radius applies since these always carry a fill.

### Modals / Dialogs
- Flat corners, `border: var(--border-width) var(--border-modals) var(--border-color)`, `background: var(--color-white)`.
- Header: flex row, `justify-content: space-between`, title in `--font-subtitle`.
- Footer actions: flex row, `justify-content: flex-end`, gap `--space-2` (except single-action confirp modals, which may center the one button).

### Sections
- Full-bleed flex columns, `border-top`/`border-bottom: var(--border-width) var(--border-sections) var(--border-color)` where one section meets the next, so the page reads as a stack of clearly bounded zones rather than a continuous scroll.
- Vary background per section purpose (white for primary content, off-white for secondary/grouped content, black for a header/hero or footer band) — never more than one accent color introduced within a single section.

---

## 7. Icons

- Source: **Flaticon**, **"Straight"** style family, **solid** (filled) variant only — no outline/line icons, no duotone, no hand-drawn sets.
- Color logic is background-driven, not decorative:
  - Icon sits on `--color-white` or `--color-offwhite` → fill `--color-black`.
  - Icon sits on `--color-black` (or any filled black surface, e.g. the top nav) → fill `--color-white`.
  - Icon sits on an accent-filled surface (a primary button, a badge) → fill whichever of black/white has higher contrast against that specific accent (white on `--color-primary`/`--color-primary-hover`; black on `--color-secondary`/`--color-secondary-hover`).
- Never recolor an icon into the accent palette itself (no orange/red icons) — icons stay strictly black-or-white; color is reserved for surfaces and text emphasis, not iconography.
- Size icons to sit optically centered against adjacent `--font-body` or `--font-subtitle` text (typically 1–1.25× the line's font-size), and lay out icon + label pairs as `display: flex; align-items: center; gap: var(--space-1);`.

---

## 8. Motion

- The only recurring transition in the system is the border-radius softening on hover (`--radius-transition`, 0.18s ease) plus a simultaneous background-color swap to the element's `-hover` token. Keep both on the same duration so they read as one motion, not two.
- Do not add fade-ins, slide-ups, or scroll-triggered reveals to routine content (cards, list rows, table rows) — this is an internal tool used daily; motion should never slow down repeat use. Reserve any additional motion for a single deliberate moment (e.g., a save-confirmation toast) rather than scattering it across every component.

---

## 9. Accessibility Floor

- Maintain WCAG AA contrast: black-on-white and white-on-black pairs pass cleanly; verify `--color-primary`/`--color-secondary` fills against white text at typical button sizes and increase font-weight rather than lightening the fill if a pairing runs close.
- Every interactive element needs a visible keyboard focus state (a 2px offset outline in `--color-action` is consistent with the border language already in use).
- Respect `prefers-reduced-motion`: disable the radius/background transition for users who request it, snapping states instead of animating them.
