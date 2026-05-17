# Axy Lusion — Design System (Cinematic)

**Source of truth:** `cinematic.css` (single stylesheet, scoped under `.cn-page`).
**Reference render:** `Axy Lusion - Cinematic.html` (open locally to inspect).
**Last updated:** 16 May 2026.

This document is the design contract. Anything not in this document is unspecified — ask before inventing.

---

## 1. Mood and tone

A premium, cinematic AI-art portfolio. Pure black canvas. Hero imagery breathes slowly (14s). Amber pools live at the corners. **Gallery-after-hours.** The chrome stays quiet so the work can speak; when there is no work yet, the chrome stays *honest* — gradient placeholders, not stretched-thin marketing copy.

Tone words: cinematic · hushed · premium · deliberate · honest.

---

## 2. Palette

### Brand

| Token | Value | Use |
| --- | --- | --- |
| `--axyl-amber` | `#c4851a` | Single accent. Active states, kickers, leader card, CTAs. |
| `--axyl-amber-light` | `#d4a03a` | Hover / gradient end-stop. |
| `--axyl-amber-glow` | `rgba(196,133,26,0.4)` | Glow shadows, text shadow on hero display, hero atmosphere radial. |

**Strict single-accent rule.** No green, no blue, no red except the live-broadcast tick on the news lead. Status, links, buttons, focus rings — all amber.

### Neutrals

| Token | Value | Use |
| --- | --- | --- |
| `--axl-black` | `#060606` | Hero & footer base. |
| `--axl-page` | `#0a0a0a` | Page surface. |
| `--axl-dark` | `#111` | Section dividers. |
| `--axl-g900..g300` | `#1a → #aaa` | Borders, secondary text, dividers. |
| `--axl-cream` | `#f5e6c8` | Hero title + section headings. Warm off-white. |
| `--axl-white` | `#fafafa` | High-contrast body text where needed. |

---

## 3. Typography

| Role | Family | Weights | Notes |
| --- | --- | --- | --- |
| Display | **Outfit** | 300, 500, 700, 800 | H1/H2/H3, CTA labels, logo, large numerals. Uppercase with 0.04em+ tracking. Italic 300/400 reserved for pull quotes + prompt captions only. |
| Body | **Plus Jakarta Sans** | 400, 500, 700 | Paragraphs, UI labels, lede. Line-height 1.6 for body, 1.5 for UI. |
| Mono | **JetBrains Mono** | 400, 500, 600 | Kickers, frame refs, dates, code, search-keyboard hint. |

Type scale (clamped):

```
H1  clamp(48px, 7vw,  88px)   line 0.95   letter 0.04em   uppercase Outfit 800
H2  clamp(32px, 4vw,  48px)   line 1.05   letter 0.03em   uppercase Outfit 800
H3  18px                        letter 0.12em             uppercase Outfit 700
Display  clamp(72px, 11vw, 128px)  line 0.92  letter 0.14em  uppercase Outfit 800
Body  16px                      line 1.6                    Plus Jakarta 400
Lede  18px                      line 1.6                    Plus Jakarta 400
Kicker  11px                    letter 0.24em   uppercase   JetBrains 500
```

Display headlines never wrap below 0.92 line-height. Body text never wraps below 1.55.

---

## 4. Spacing

```
--space-xs   4px
--space-sm   8px
--space-md   16px
--space-lg   24px
--space-xl   32px
--space-2xl  48px
--space-3xl  64px
```

- Outer page padding: 48px desktop, 24px mobile.
- Inter-section padding: 96px desktop, 56px mobile.
- Inner gutters: 32px (most grids), 24px (filter rows).

---

## 5. The image primitive: `<Frame>`

**Every image on the site goes through `<Frame>`.** This is the design contract for visual consistency and for graceful handling of pending media.

### Signature

```tsx
<Frame
  item={item}              // { id, prompt?, created, tones, src?, ref }
  index={i}                // numeric index in the listing
  ratio="3/4"              // CSS aspect-ratio
  mode="plate" | "full"    // 12px radius vs 4px radius
  caption={false}          // show prompt-as-caption overlay (default: false)
/>
```

### Layered structure

1. `cn-frame__bg` — either a deterministic 3-stop gradient (built from `item.tones`) or `<img src={item.src}>` once durable hosting is online. The gradient stays under any `<img>` as a load shim and a no-src fallback.
2. `cn-frame__grain` — SVG fractal noise data-URI, 18% opacity, overlay blend mode. Gives gradients film-grain texture so they don't read as flat CSS.
3. `cn-frame__vignette` — radial dark from bottom + linear dark gradient. Subtle.
4. `cn-frame__corner` — top-left pill with `F0042 · 13 Dec 2025`. Always present.
5. `cn-frame__cap` — bottom italic prompt caption, two-line clamp. **Off by default.** Only on when explicitly enabled (see §6).

### Border-radius modes

- `mode="plate"` → 12px. Default for grid cards.
- `mode="full"` → 4px. Use for hero / reel / cover images where the frame is large.

---

## 6. The "no titles" decision

**There are no titles on the site.** Images are identified by:

1. **Frame ref** — `F` + 4-digit padded index. Assigned at ingestion, stable forever, never renumbered.
2. **Date** — from `item.created`.
3. **Prompt** — the original prompt where logged; surfaced as italic caption *only* on detail views and *only* when the user opts in.

The reasoning is in `HANDOFF.md §1.1`. The design surfaces this fact, calmly, via the `<UntitledNote>` chip on listing pages.

**One opt-in lever:** the Tweaks panel exposes `Show captions on grid` (default `false`). When `true`, the gallery grid shows the prompt as a 2-line caption under each frame. Use this to preview what AI-generated titles would look like before committing to a titling pipeline. If they don't read well, flip back to `false` — no migration cost.

---

## 7. Page layouts

All page-level CSS lives in `cinematic.css` under `.cn-page` and below. Each page is a top-level component in `cinematic.jsx`.

### 7.1 Header (`Header`)

Sticky, 18px×48px padding. 3-column grid: logo · centered nav · social icons. Active nav item carries an amber underline (`.cn-nav a.is-active::after`). Blurred backdrop.

### 7.2 Hero (Homepage)

Full-bleed featured frame as background, 14s breathe animation, dark gradient overlay + amber radial pool at `50% 110%`. Content stack: kicker → display → display-sub → pull-quote → CTA row. **8-cell contact strip** along the bottom — clicking a cell swaps the hero target.

### 7.3 Reel (Homepage)

Vertical list of N frames (default 8). Each row: `[index 80px] [frame 16:9] [meta 300px]`. Meta sidebar: kicker (frame ref + date) → italic prompt → migration-status microcopy.

### 7.4 Gallery grid

4-column grid of `<Frame mode="plate" ratio="3/4">`. Captions off by default. Filters above: search input (with `/` keyboard hint), type chips, sort chips, model `<select>`. Pager footer.

### 7.5 News

**Lead story** — full-width frame card at the top, headline + topic + date overlaid. No side rail.

**Filter bar** — search + 3 range buttons (Issue day / 7-day / All) + topic chips (All / Image / Video / Audio / 3D / Tools / Benchmarks) + Clear-all. State is local; filters apply live to the digest list below.

**Digest list** — `[date column] [headline ul w/ topic chips] [Open button]`. Empty state when filters return no matches.

### 7.6 Blog

Featured post card (1.2fr / 1fr split: cover frame · copy + CTA), then archive list (date · body · arrow), then a `coming soon` empty-state card.

### 7.7 A-List

Method chips on the page head. Category tab nav. Per category: one full-width leader card (amber border, glow shadow, AA/LM Arena/Expert breakdown) + 2-column grid of runner-up cards.

### 7.8 About

Sticky-portrait split. Left = `<Frame>` portrait + name card (sticky on scroll). Right = long-form copy with H3 sections: Practice / Why no titles? / Elsewhere. **Keep the "Why no titles?" section** — it explains the design choice on the artist's page itself.

### 7.9 Footer

3-column: brand · large social icons · copyright. 56px top padding, 48px bottom.

---

## 8. Components glossary

| Component | File | Notes |
| --- | --- | --- |
| `<Frame>` | `src/components/Frame.tsx` | The image primitive. §5. |
| `<Header active={page} />` | `src/components/Header.tsx` | Sticky chrome. |
| `<Footer />` | `src/components/Footer.tsx` | Three-column footer. |
| `<UntitledNote compact?>` | `src/components/UntitledNote.tsx` | Amber-tinted explainer chip. |
| `frameRef(i)` | `src/lib/frame-ref.ts` | `F0042` formatter. |
| `fmtDate(iso)` / `fmtDateLong(iso)` | `src/lib/format-date.ts` | British English date formats. |

---

## 9. Motion

| Element | Animation | Duration | Easing |
| --- | --- | --- | --- |
| Hero bg | scale 1.05 → 1.0 (alternating) | 14s | ease-out |
| Live tick | opacity 1 → 0.4 | 2s loop | ease-out |
| Card hover | translateY(-4px) + shadow | 350ms | ease |
| CTA hover | translateY(-2px) | 250ms | cubic-bezier(0.175, 0.885, 0.32, 1.275) — overshoot spring |
| Underline reveal | scaleX 0 → 1 | 280ms | cubic-bezier(0.22, 1, 0.36, 1) |

Do not introduce new keyframe animations without good reason. The system is **slow and deliberate** — fast/bouncy moves cheapen the gallery feel.

---

## 10. Do's and Don'ts

**Do**

- Use `<Frame>` for every image, every time.
- Let images dominate. The chrome is intentionally minimal.
- Stay on amber. One signal per viewport.
- Use italic Outfit only for prompt captions / pull quotes.
- Treat the corner pill (`F0042 · date`) as load-bearing — it's the system's commitment to the no-titles decision.

**Don't**

- Add a second accent colour.
- Render `item.name` anywhere. The field is preserved in JSON for backwards-compat with the existing data file, but it is not part of the design.
- Generate, fabricate, or auto-title images without it being opt-in behind the `showCaptions` lever.
- Use box-shadows lighter than `rgba(0,0,0,0.3)` — they vanish on near-black.
- Use any sans-serif other than Outfit / Plus Jakarta Sans.
- Let card hover-lifts exceed 4px — it cheapens the gallery feel.
- Add titles to news side rails or stats panels — `News` lead is now full-width by design.

---

## 11. Responsive breakpoints

- **≥ 1100px** — desktop. 4-col gallery, 2-col leader/runners, sticky portrait.
- **640 – 1100px** — tablet. 2-col gallery, single-col runners, footer stacks.
- **≤ 640px** — mobile. Single-col everywhere. Hero contact-strip becomes a 4×2 grid. Header social row collapses to icons-only.

The breakpoint logic is in `cinematic.css` near the bottom — keep the same query thresholds when refactoring.

---

## 12. Where to extend

When a new page is needed, build it as a top-level component in `src/pages/`, reuse `<Header>` and `<Footer>` verbatim, and start from the closest existing layout:

- Listing pages → Gallery
- Editorial pages → News
- Long-form copy → About
- Featured-item pages → Blog

If a new image treatment is needed, **extend `<Frame>`** rather than creating a new primitive. The contract is what makes the design coherent.
