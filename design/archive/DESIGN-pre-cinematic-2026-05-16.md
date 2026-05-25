# Axylusion — Design Specification

**Last updated:** 2026-05-02
**Stack:** Static HTML + vanilla CSS/JS
**Source of truth:** `styles.css`

---

## 1. Visual Theme & Atmosphere

A premium, cinematic AI art portfolio. Pure black canvas. The hero image breathes via slow scale animation; ambient amber glow pools in two corners of the viewport. The mood is a **museum gallery after-hours** — intentionally dim, inviting attention to the work, not the chrome around it.

Tone words: cinematic, hushed, premium, deliberate.

---

## 2. Colour Palette & Roles

### Primary (warm amber)
- `--axyl-amber` `#c4851a` — sole accent, the gallery brass
- `--axyl-amber-light` `#d4a03a` — hover, focus
- `--axyl-amber-dark` `#8a5d12` — pressed
- `--axyl-amber-glow` `rgba(196, 133, 26, 0.4)` — used in radial overlays + text glow

### Neutrals (rich blacks)
- `--axyl-black` `#0a0a0a` — page
- `--axyl-dark` `#111111` — sections
- `--axyl-gray-900..300` — six-step scale for borders, secondary text, dividers
- `--axyl-cream` `#f5e6c8` — hero title only (warm off-white that complements the amber)
- `--axyl-white` `#fafafa` — body text where high contrast is needed

**Single-accent system.** No green, no blue. Status colours, links, buttons all map to amber.

---

## 3. Typography Rules

| Role | Family | Notes |
|------|--------|-------|
| Display | **Outfit** (or Inter fallback) | 800 weight, 0.15em tracking on hero, uppercase |
| Body | **Plus Jakarta Sans** (or Inter fallback) | 400/500, 1.6 line-height |
| Mono | **JetBrains Mono** | rare; metadata only |

- Hero title clamps `clamp(3rem, 10vw, 6rem)`
- Hero subtitle clamps `clamp(0.9rem, 2vw, 1.2rem)` with 0.3em tracking
- Section headings: 800, uppercase, amber

---

## 4. Component Stylings

- **Hero** — full-viewport image with quad-stop gradient overlay (top 30% subtle, bottom 70% to 100% near-opaque), radial amber glow at `50% 120%`, slow `scale(1.05) → 1` over 10s
- **Buttons** — pill (`--radius-full`), 1px amber border, transparent fill, fills on hover
- **Cards** — `--radius-lg` (12px), 1px gray-700 border, gray-900 fill, lift on hover with `--shadow-glow`
- **Spring transition** — `cubic-bezier(0.175, 0.885, 0.32, 1.275)` for emphatic moves only

### Spacing scale
`xs 4px · sm 8px · md 16px · lg 24px · xl 32px · 2xl 48px · 3xl 64px`

### Radius scale
`sm 4 · md 8 · lg 12 · xl 16 · full 9999`

---

## 5. Layout Principles

- Single hero per landing
- Showcase pages use a strict 1- or 2-column grid; never 3+ on desktop
- `--space-2xl` (48px) between major sections
- Generous outer padding on hero content (`--space-xl` = 32px)

---

## 6. Depth & Elevation

Five-step shadow scale, all near-black:
- `sm` `0 1px 2px rgba(0,0,0,0.3)`
- `md` `0 4px 12px rgba(0,0,0,0.4)`
- `lg` `0 8px 24px rgba(0,0,0,0.5)`
- `xl` `0 16px 48px rgba(0,0,0,0.6)`
- `glow` `0 0 40px var(--axyl-amber-glow)` — reserved for active/featured cards

---

## 7. Do's and Don'ts

**Do**
- Let images dominate — chrome is intentionally minimal
- Use amber once per viewport for a single signal
- Use the noise overlay (opacity 0.02) — adds film grain
- Animate hero scale slowly (10s)

**Don't**
- Introduce a second accent colour
- Use box-shadows lighter than `rgba(0,0,0,0.3)` — they vanish on near-black
- Add card hover lifts greater than 4px — it cheapens the gallery feel
- Use any sans-serif other than Outfit/Plus Jakarta Sans

---

## 8. Responsive Behaviour

- **≥ 1024px:** wide hero, 2-column showcase
- **640–1024px:** single-column showcase, full-bleed hero
- **≤ 640px:** hero subtitle hidden when vertical space is tight; CTA stacks below title

---

## 9. Agent Prompt Guide

> "Design for Axylusion. Pure black background `#0a0a0a`. Single accent: amber `#c4851a` with `0.4` glow. Outfit display 800 uppercase 0.15em tracking. Plus Jakarta Sans body. Hero is full-viewport image with bottom-heavy dark gradient and radial amber pool at 50% 120%. Cinematic, gallery-after-hours mood. No second accent colour. No glass-morphism."

---

## Files

- `styles.css` — main styles
- `news-controls.css` — news-specific styles
- `index.html`, `about.html`, `gallery.html`, etc.
- `assets/showcase/` — featured work
