# FIRM FLOW

**Vibe:** A crisp floor plan on a sunlit drafting table, with one deep-orange redline showing the new hire exactly where to walk.

**Theme:** Light only. Warm white canvas, white paper surfaces, warm ink text, deep orange for action.

---

## Style summary

FIRM FLOW looks like a well-run architecture studio: warm, precise, and quietly confident. Pages sit on a warm white canvas (`#FAF7F2`). Content lives on sharp-cornered white sheets with hairline warm-gray borders, like drawings pinned to a board, and only overlays that float above the page (menus, modals, the chat panel) get a single soft shadow. The one friendly exception to the sharp geometry is controls: every button and badge is a pill, so anything you can click reads as distinct from the architecture around it. Typography is one geometric sans (Plus Jakarta Sans) with tight, confident headings and calm, readable body text. Deep orange (`#C2410C`) is used sparingly, for primary actions, numbered section eyebrows, and one accent shape per illustration, never as a large fill. Illustration is abstract architecture: flat facade blocks, stepped massing, arches, window grids, and floor-plan outlines built from rectangles and quarter circles on an 8px grid, with no gradients, no 3D, and no people. Like Spine and Ben, the product itself is the hero: sections show real, working UI (contact cards, side-by-side manual review, quiz feedback) rather than decorative art. Density is balanced: medium spacing everywhere, generous enough to feel editorial on the marketing site but tight enough that app dashboards stay scannable.

---

## Tokens: Colors

Every color below has exactly one job. If a design needs a color not in this table, it doesn't get one.

| Name | Hex | CSS token | Role |
| --- | --- | --- | --- |
| Canvas | `#FAF7F2` | `--color-canvas` | Page background for every marketing and app page |
| Surface | `#FFFFFF` | `--color-surface` | Cards, inputs, sidebar, table body, modals, dropdowns, chat panel |
| Sunken | `#F3EEE7` | `--color-sunken` | Inset areas: table header rows, secondary button hover, neutral badge fill, code blocks, the "original manual" pane in side-by-side review |
| Border | `#E6DFD5` | `--color-border` | Card borders, dividers, table row lines, nav bottom border |
| Border strong | `#8F857A` | `--color-border-strong` | Input borders, secondary button border, checkbox and radio outlines (meets 3:1 non-text contrast) |
| Grid line | `#EFE8DE` | `--color-grid-line` | The faint 1px drafting grid behind hero and empty-state illustrations. Nothing else |
| Ink | `#1C1917` | `--color-ink` | Primary text, headings, icons at rest, footer background |
| Ink secondary | `#57534E` | `--color-ink-secondary` | Body copy under headings, nav links at rest, input hover border, table cell text |
| Ink tertiary | `#736B63` | `--color-ink-tertiary` | Captions, timestamps, placeholders, source citations ("From Handbook p. 12"), helper text |
| Primary | `#C2410C` | `--color-primary` | Primary button fill, links, numbered eyebrows, focus rings, active tab text, progress bar fill |
| Primary hover | `#9A3412` | `--color-primary-hover` | Primary button hover and pressed fill, link hover, text on primary tint |
| Primary tint | `#FDEBDD` | `--color-primary-tint` | Active sidebar item fill, brand badge fill, icon tile fill, input focus halo, selected row fill |
| Primary bright | `#E8590C` | `--color-primary-bright` | Exactly one accent shape per architecture illustration. Never text, never buttons |
| Shape sand | `#EADCCB` | `--color-shape-sand` | Large flat facade and massing blocks in architecture illustrations |
| Shape line | `#D6C4AE` | `--color-shape-line` | 1.5px floor-plan outlines, window mullions, and arch strokes in illustrations |
| Success | `#1E6B41` | `--color-success` | Text and icons for approved, completed, correct answer, "In today" |
| Success tint | `#E3F1E8` | `--color-success-tint` | Fill behind success badges and correct-answer feedback |
| Warning | `#92400E` | `--color-warning` | Text and icons for draft, flagged issue, out of office, needs review |
| Warning tint | `#FDF0D5` | `--color-warning-tint` | Fill behind warning badges and flagged-issue rows |
| Danger | `#B42318` | `--color-danger` | Errors, unsupported (ungrounded) AI text, wrong answer, destructive actions |
| Danger tint | `#FDE8E6` | `--color-danger-tint` | Fill behind danger badges, unsupported-text highlights, wrong-answer feedback |
| On dark | `#F5F0E8` | `--color-on-dark` | Headings and links on the ink footer and the single allowed dark band |
| On dark muted | `#A8A29E` | `--color-on-dark-muted` | Secondary text and legal copy on dark surfaces |
| Border on dark | `#3A332E` | `--color-border-on-dark` | Dividers inside the footer and dark band |

Verified contrast: white on Primary 5.2:1, Ink on Canvas 16.4:1, Ink secondary on Canvas 7.1:1, Ink tertiary on Canvas 4.9:1, Primary hover on Primary tint 6.3:1, each status color on its tint above 5.5:1.

```css
:root {
  --color-canvas: #FAF7F2;
  --color-surface: #FFFFFF;
  --color-sunken: #F3EEE7;
  --color-border: #E6DFD5;
  --color-border-strong: #8F857A;
  --color-grid-line: #EFE8DE;
  --color-ink: #1C1917;
  --color-ink-secondary: #57534E;
  --color-ink-tertiary: #736B63;
  --color-primary: #C2410C;
  --color-primary-hover: #9A3412;
  --color-primary-tint: #FDEBDD;
  --color-primary-bright: #E8590C;
  --color-shape-sand: #EADCCB;
  --color-shape-line: #D6C4AE;
  --color-success: #1E6B41;
  --color-success-tint: #E3F1E8;
  --color-warning: #92400E;
  --color-warning-tint: #FDF0D5;
  --color-danger: #B42318;
  --color-danger-tint: #FDE8E6;
  --color-on-dark: #F5F0E8;
  --color-on-dark-muted: #A8A29E;
  --color-border-on-dark: #3A332E;
}
```

---

## Tokens: Typography

**One family: Plus Jakarta Sans** (Google Fonts, free, SIL Open Font License). A geometric sans with precise, slightly architectural letterforms. No licensed font is used, so no substitute is needed. If it fails to load, fall back to the stack below.

```css
--font-sans: "Plus Jakarta Sans", ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
```

Load weights **400, 500, 600, 700** only. Never use 300 or 800.

| Weight | Use |
| --- | --- |
| 400 Regular | Body copy, table cells, input text |
| 500 Medium | Nav links, captions, labels, badges on neutral |
| 600 Semibold | Buttons, h3/h4, eyebrows, card titles, badges |
| 700 Bold | Display, h1, h2, big stat numbers |

**Type scale**

| Role | Size / line height | Weight | Letter spacing | Use |
| --- | --- | --- | --- | --- |
| Display | 56px / 60px (mobile 40 / 44) | 700 | -0.025em | Marketing hero headline only, once per page |
| Stat | 48px / 52px (mobile 36 / 40) | 700 | -0.02em | Big numbers in stat strips. Always `font-variant-numeric: tabular-nums` |
| H1 | 40px / 48px (mobile 32 / 40) | 700 | -0.02em | App page titles, marketing sub-page titles |
| H2 | 32px / 40px (mobile 26 / 34) | 700 | -0.015em | Section headings |
| H3 | 22px / 30px | 600 | -0.01em | Card titles on marketing, modal titles |
| H4 | 18px / 26px | 600 | -0.005em | Card titles in app, sidebar group titles |
| Body large | 18px / 28px | 400 | 0 | Section lead paragraphs, hero subhead |
| Body | 16px / 24px | 400 | 0 | Default text, module reading content |
| Body small | 14px / 20px | 400 | 0 | App tables, dense lists, chat messages, helper text |
| Label | 14px / 20px | 500 | 0 | Input labels, nav links, tab labels |
| Button | 15px / 20px (small: 14 / 20) | 600 | 0 | All button text |
| Caption | 12px / 16px | 500 | 0.01em | Timestamps, source citations, footnotes, badge text |
| Eyebrow | 12px / 16px | 600 | 0.08em, UPPERCASE | Numbered section labels like `01 · MANUAL ENHANCER` |

Rules: headings use `--color-ink`; body uses `--color-ink-secondary` on marketing and `--color-ink` in the app reader; paragraphs never exceed 68 characters (`max-width: 680px`).

---

## Tokens: Spacing and Shapes

**Spacing scale (4px base).** Only these values are allowed for margin, padding, and gap.

| Token | Value |
| --- | --- |
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-5` | 20px |
| `--space-6` | 24px |
| `--space-8` | 32px |
| `--space-10` | 40px |
| `--space-12` | 48px |
| `--space-16` | 64px |
| `--space-24` | 96px |
| `--space-30` | 120px |

**Border radius by element**

| Element | Radius | Token |
| --- | --- | --- |
| Buttons (all sizes and variants) | 9999px (pill) | `--radius-pill` |
| Badges and tags | 9999px (pill) | `--radius-pill` |
| Avatars, toggles, radio buttons | 50% / pill | `--radius-pill` |
| Cards, panels, modals, dropdowns, popovers, toasts, chat panel | 0 | `--radius-none` |
| Inputs, textareas, selects, search fields | 0 | `--radius-none` |
| Tables, images, icon tiles, progress bars, architecture shapes | 0 | `--radius-none` |
| Checkboxes | 2px | `--radius-hair` |

**Shadows.** There is exactly one shadow in the system.

```css
--shadow-raised: 0 8px 24px -8px rgba(28, 25, 23, 0.16);
```

Focus is a ring, not a shadow, and is allowed on every focusable element:

```css
--ring-focus: 0 0 0 2px var(--color-canvas), 0 0 0 4px var(--color-primary);   /* buttons, links, cards */
--ring-input: 0 0 0 3px var(--color-primary-tint);                             /* inputs, paired with primary border */
```

**Layout constants**

| Token | Value | Use |
| --- | --- | --- |
| `--max-width` | 1200px | Marketing content container |
| `--max-width-app` | 1120px | App content area to the right of the sidebar |
| `--max-width-prose` | 680px | Paragraphs, module reader column |
| `--page-gutter` | 32px desktop, 20px mobile | Horizontal padding inside the container |
| `--section-gap` | 96px desktop, 64px mobile | Vertical padding between marketing sections |
| `--hero-top` | 120px desktop, 72px mobile | Space above the hero headline |
| `--card-padding` | 24px (marketing feature cards 32px) | Inside every card |
| `--grid-gutter` | 24px | Gap between grid columns and cards |
| `--nav-height` | 72px marketing, 64px app top bar | Top navigation |
| `--sidebar-width` | 248px | App sidebar |
| `--motion-fast` | 150ms ease-out | Hovers, color changes |
| `--motion-base` | 200ms ease-out | Overlays opening, card lift |

---

## Components

### Primary button

- Fill `--color-primary`, text `#FFFFFF` (white on primary is the only place pure white text appears), font Button (15px/600).
- Height 44px, padding `0 22px`, radius `--radius-pill`, no border, no shadow.
- Small size: height 36px, padding `0 16px`, 14px text. Large (hero only): height 52px, padding `0 28px`, 16px text.
- Optional trailing icon: 16px lucide arrow-right, 8px gap.
- Hover: fill `--color-primary-hover`, trailing arrow translates 2px right, `--motion-fast`.
- Active: fill `--color-primary-hover`, `transform: translateY(1px)`.
- Focus-visible: `--ring-focus`.
- Disabled: fill `--color-sunken`, text `--color-ink-tertiary`, cursor not-allowed.
- One primary button per section or card, maximum.

### Secondary button

- Fill transparent, 1px border `--color-border-strong`, text `--color-ink`, font Button.
- Same sizes, padding, and radius as primary.
- Hover: fill `--color-sunken`, border `--color-ink`.
- Active: `transform: translateY(1px)`.
- Focus-visible: `--ring-focus`.
- Disabled: border `--color-border`, text `--color-ink-tertiary`.
- Text-only variant (tertiary): no border, text `--color-primary`, padding `0 4px`, hover text `--color-primary-hover` with underline offset 4px.

### Nav bar

**Marketing nav**

- Height 72px, background `--color-canvas`, full-width; inner content in the 1200px container.
- Left: wordmark "FIRM FLOW" in 18px/700, letter spacing 0.04em, `--color-ink`, preceded by a 24px geometric mark (a square with a quarter-circle cut, in `--color-primary`).
- Center: links in Label style (14px/500), `--color-ink-secondary`, 32px apart. Hover `--color-ink`. Active page: `--color-ink` with a 2px `--color-primary` underline, 8px below the text baseline.
- Right: "Log in" as a text-only button in `--color-ink`, then a small primary button "Book a demo", 16px gap.
- On scroll past 8px: add 1px bottom border `--color-border`. Never a shadow, never blur.
- Mobile (<768px): wordmark left, 40px menu icon button right; the menu opens as a full-width `--color-surface` sheet with 1px bottom border and `--shadow-raised`.

**App nav**

- Left sidebar, 248px wide, background `--color-surface`, 1px right border `--color-border`, padding 16px.
- Items: height 40px, padding `0 12px`, radius 0, Label style, icon 18px at 12px gap. Rest: text `--color-ink-secondary`. Hover: fill `--color-sunken`, text `--color-ink`. Active: fill `--color-primary-tint`, text and icon `--color-primary-hover`.
- Group titles: Eyebrow style in `--color-ink-tertiary`, 24px above each group.
- Bottom of sidebar: user avatar (32px circle) + name (14px/600) + role caption.

### Card

- Background `--color-surface`, 1px border `--color-border`, radius 0, padding `--card-padding`, no shadow at rest.
- Structure top to bottom: optional icon tile (40px square, `--color-primary-tint` fill, 20px lucide icon in `--color-primary`, 1.5px stroke), 16px gap, title (H4 in app, H3 on marketing), 8px gap, body (Body small in app, Body on marketing, `--color-ink-secondary`), optional footer row with 16px top border `--color-border` and caption or action.
- Interactive cards (the whole card is a link): hover border `--color-border-strong`, `--shadow-raised`, `transform: translateY(-2px)`, `--motion-base`. Focus-visible: `--ring-focus`.
- Selected state: border `--color-primary`, fill stays white.
- Cards in a row share equal height; align content to the top.

### Input

- Height 44px, background `--color-surface`, 1px border `--color-border-strong`, radius 0, padding `0 14px`, text Body (16px) in `--color-ink`. Textareas: padding 12px 14px, min-height 96px.
- Placeholder: `--color-ink-tertiary`.
- Label above: Label style, `--color-ink`, 8px gap. Helper text below: Caption, `--color-ink-tertiary`, 6px gap.
- Hover: border `--color-ink-secondary`.
- Focus: border `--color-primary` plus `--ring-input`.
- Error: border `--color-danger`, helper text `--color-danger` with 14px alert icon.
- Disabled: fill `--color-sunken`, text `--color-ink-tertiary`.
- Chat composer variant: same input, 52px tall, with a small primary pill "Ask" button inset 6px from the right edge.

### Badge

- Height 24px, padding `0 10px`, radius `--radius-pill`, Caption text at 600 weight, no border.
- Optional 6px leading dot in the text color.
- Variants (fill / text):
  - Neutral: `--color-sunken` / `--color-ink-secondary` (Week 1, Later, Not started)
  - Brand: `--color-primary-tint` / `--color-primary-hover` (Day 1, Critical, New)
  - Success: `--color-success-tint` / `--color-success` (Approved, Completed, In today, Correct)
  - Warning: `--color-warning-tint` / `--color-warning` (Draft, Flagged, Out of office)
  - Danger: `--color-danger-tint` / `--color-danger` (Unsupported, Broken link, Incorrect)
- Badges are not interactive and have no hover state. Filter chips that are clickable use the secondary button spec at small size.

### Section header

- Left-aligned block, max-width 720px.
- Eyebrow: `NN · SECTION NAME` in Eyebrow style, `--color-primary`. Numbering restarts on each page and counts sections in order (`01 · MANUAL ENHANCER`, `02 · FINAL CHECK`).
- 12px gap, then H2 in `--color-ink`.
- 16px gap, then optional lead paragraph in Body large, `--color-ink-secondary`, max-width 680px.
- 48px gap before section content.
- Optional right-side action (secondary button or text link) aligned to the H2 baseline on desktop; stacks under the lead on mobile.
- In the app, the page header uses H1 with no eyebrow, a Body small subtitle, and primary actions right-aligned; 32px below it.

### Footer

- Background `--color-ink`, padding 64px top, 32px bottom, full-width; content in the 1200px container.
- Top row: wordmark in `--color-on-dark` and a one-line description in Body small `--color-on-dark-muted` (col span 4), then three link columns (col span 2 each) with Eyebrow titles in `--color-on-dark-muted` and Body small links in `--color-on-dark`, 12px apart.
- Link hover: underline with 4px offset; color stays `--color-on-dark`.
- Optional: a 48px-tall facade strip of architecture shapes directly above the bottom row. On the dark footer, shapes use `--color-border-on-dark` fills plus exactly one `--color-primary-bright` block; sand and shape-line colors are not used on dark.
- Bottom row: 1px top border `--color-border-on-dark`, 24px padding top, Caption text `--color-on-dark-muted`: copyright left, legal links right.

---

## Do's and Don'ts

### Do

1. **Do** use `--color-canvas` (`#FAF7F2`) as the background of every page, and `--color-surface` (`#FFFFFF`) for anything that sits on it.
2. **Do** make every button and badge a pill (`border-radius: 9999px`), and make every card, input, table, modal, dropdown, image, and icon tile sharp (`border-radius: 0`).
3. **Do** separate cards from the canvas with a 1px `--color-border` hairline. Elevation at rest is always a border, never a shadow.
4. **Do** start every marketing section with a numbered orange eyebrow (`01 · MANUAL ENHANCER`) followed by an H2.
5. **Do** show the product with real HTML UI mockups (contact cards, side-by-side review panes, quiz feedback, progress bars) as the main visual of feature sections, built from these same components.
6. **Do** draw architecture illustrations as inline SVG using only rectangles, stepped blocks, quarter-circle arches, window grids, and 1.5px plan lines, snapped to an 8px grid, using only `--color-shape-sand`, `--color-shape-line`, `--color-ink`, and exactly one `--color-primary-bright` shape.
7. **Do** place a faint drafting grid (1px `--color-grid-line` lines every 48px) behind hero and empty-state illustrations only.
8. **Do** show a source citation in Caption style (`From Onboarding Handbook, p. 12`) under every piece of AI-generated or AI-enhanced content, since grounding is the product's promise.
9. **Do** use lucide icons at 1.5px stroke; 20px in cards and nav, 16px inside buttons and badges.
10. **Do** use `font-variant-numeric: tabular-nums` on every number in stats, tables, progress, and timestamps.
11. **Do** keep status colors fixed: green means approved/completed/available, amber means draft/flagged/out of office, red means error/unsupported/incorrect. Never reuse them decoratively.
12. **Do** use only spacing values from the 4px scale in this file.

### Don't

1. **Don't** use any purple, violet, indigo, blue, or teal anywhere: not in gradients, links, focus rings, charts, illustrations, badges, or hover states. No hue between 170° and 300° may appear in the UI.
2. **Don't** use gradients of any kind: no gradient backgrounds, gradient text, gradient borders, mesh blobs, glows, or glassmorphism.
3. **Don't** use sparkle, star, magic-wand, or "✨" icons (including lucide `Sparkles`, `WandSparkles`, `Stars`) or the words "magic" or "AI-powered" as decoration. Label AI features by what they did: "Enhanced from 3 sections", "Checked against source".
4. **Don't** put a shadow on cards at rest, buttons, inputs, badges, the nav bar, sections, or images. `--shadow-raised` is only for the elements listed in Surfaces and Elevation.
5. **Don't** round anything that isn't a button, badge, avatar, toggle, or radio. No `rounded-md`, `rounded-lg`, or `rounded-xl` on cards, inputs, or images, ever.
6. **Don't** fill any section, hero, or card background with orange. `--color-primary` covers at most 10% of any viewport, and full-bleed orange bands are banned.
7. **Don't** use pure black `#000000` for text or pure white `#FFFFFF` as a page background.
8. **Don't** center-align paragraphs, card content, lists, or section headers. The only centered block allowed is the closing call-to-action band at the bottom of a marketing page.
9. **Don't** use any font other than Plus Jakarta Sans, and don't use weights below 400 or above 700.
10. **Don't** add colored accent stripes or single-side borders to cards, callouts, or sidebar items (no `border-left: 4px solid orange`). Use a tinted fill or a badge instead.
11. **Don't** use isometric illustrations, 3D renders, photos of buildings, cartoon people, or stock office photos. Architecture appears only as the flat geometric shapes described above.
12. **Don't** round the corners of architecture shapes or add strokes thicker than 1.5px; buildings in this system are precise, not bubbly.
13. **Don't** place more than one architecture illustration per viewport, and never put one behind text.
14. **Don't** use emoji anywhere in the interface.

---

## Surfaces and Elevation

From the bottom up:

| Level | Surface | Token | What lives here | Separation |
| --- | --- | --- | --- | --- |
| 0 | Canvas | `--color-canvas` | Page background, section backgrounds, hero | None |
| 0 (inset) | Sunken | `--color-sunken` | Table headers, code blocks, original-manual pane, neutral badge fill | Tint only, no border |
| 1 | Surface | `--color-surface` | Cards, inputs, app sidebar, tables, app top bar | 1px `--color-border` |
| 2 | Raised | `--color-surface` + `--shadow-raised` | Dropdown menus, popovers, tooltips, modals, toasts, the floating chat assistant panel, mobile nav sheet, and interactive cards **while hovered** | Shadow plus 1px `--color-border` |
| Inverse | Ink | `--color-ink` | Footer, and at most one dark band per marketing page (for example, the stat strip or closing CTA) | Color change |

**Elements allowed to use `--shadow-raised`:** dropdown menus, popovers, tooltips, modals and dialogs, toasts, the floating chat assistant panel, the mobile nav sheet, and interactive cards on hover only. Nothing else receives a shadow. Modals also get a scrim of `rgba(28, 25, 23, 0.4)` behind them.

---

## Layout

**Marketing pages**

- Container: `max-width: 1200px`, centered, `--page-gutter` side padding.
- Grid: 12 columns, 24px gutter. Everything aligns to the container's left edge; headings, eyebrows, and body text share one left line.
- Section rhythm: every section has `--section-gap` (96px) top and bottom padding. Section order on the home page: nav → hero → logo or trust strip → problem → three numbered feature sections → guardrails → stat strip → closing CTA → footer.
- Hero: 7/5 split. Left 7 columns: eyebrow, Display headline, Body large subhead (max 560px), primary + secondary button row with 12px gap. Right 5 columns: one architecture composition over the drafting grid, top-aligned with the eyebrow.
- Feature sections: 5/7 split, text left and a product UI mockup right. Alternate the side each section (text left, then right, then left) while keeping the section header left-aligned above.
- Card grids: 3 columns on desktop (4 columns each), 2 at 768–1023px, 1 below 768px. Always 24px gaps.
- Stat strip: 4 equal columns separated by 1px vertical `--color-border` rules; Stat number above a Body small label.
- Closing CTA: the only centered block, H2 plus one primary button, max-width 720px.

**App pages**

- Shell: fixed 248px sidebar on the left, 64px top bar across the content area (page title breadcrumb left, search and avatar right), content area `max-width: 1120px` with 32px padding.
- Page structure: page header (H1, subtitle, right-aligned actions), 32px gap, then content.
- Dashboard: 12-column grid; progress summary card spans 8 columns with a 4-column "Ask the assistant" card beside it; module list below at full width.
- Module reader: single centered column of `--max-width-prose` (680px) inside the content area, with a 240px sticky "On this page" outline on the right at ≥1280px.
- Admin side-by-side review: two equal columns with a 1px `--color-border` divider; left pane `--color-sunken` (original), right pane `--color-surface` (enhanced), with passages aligned row by row.
- Chat assistant: 400px-wide floating panel anchored 24px from the bottom-right corner, raised level; full-screen sheet below 768px.

**Breakpoints:** 480px, 768px, 1024px, 1280px. Below 768px, all splits stack with the text block first.

---

## Agent Quick Reference

```
font:            "Plus Jakarta Sans", weights 400/500/600/700
text:            #1C1917  (--color-ink)
text-secondary:  #57534E  (--color-ink-secondary)
background:      #FAF7F2  (--color-canvas)
card-surface:    #FFFFFF  (--color-surface) + 1px border, radius 0, no shadow
border:          #E6DFD5  (--color-border)
input-border:    #8F857A  (--color-border-strong)
accent:          #FDEBDD  (--color-primary-tint)
primary-action:  #C2410C  (--color-primary), hover #9A3412, pill radius, white text
radius:          buttons/badges pill; everything else 0
shadow:          0 8px 24px -8px rgba(28,25,23,0.16), overlays and hovered cards only
banned:          purple/blue/teal, gradients, sparkle icons, emoji, rounded cards
```

**Example prompts for Claude Code**

1. *"Following Design.md, build the marketing hero: 7/5 split in the 1200px container. Left: eyebrow `AEC ONBOARDING`, Display headline 'Onboarding your firm already wrote, finally usable.', Body large subhead, a large primary button 'Book a demo' and a secondary button 'See how it works'. Right: an inline SVG facade composition (stepped sand blocks, a window grid in shape-line strokes, one primary-bright arch) over a 48px drafting grid. No gradients, no rounded corners on shapes."*

2. *"Following Design.md, build the Who Do I Ask? contact card as a sharp white card with a 1px border: eyebrow `PAYROLL`, the primary contact (name in H4, title in Body small) with a warning badge 'Out until Oct 2', a divider, then the backup contact with a success badge 'In today', working hours, and email in Ink tertiary, plus a small primary pill button 'Contact Laura' and a caption citation line. No shadow at rest."*

3. *"Following Design.md, build the admin side-by-side review screen in the app shell: page header 'Review: Onboarding Handbook' with a primary 'Approve module' button. Two equal columns: left sunken pane 'Original' showing source sections with page numbers, right white pane 'Enhanced' with matching passages. Mark ungrounded text with a danger-tint highlight and a danger badge 'Unsupported', and list flagged issues (broken links, outdated references) in a table below with warning badges."*
