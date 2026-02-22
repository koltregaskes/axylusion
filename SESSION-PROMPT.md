# axylusiondotcom — Session Handoff Prompt

Use the prompt below to start a new Claude Code session pointed at this repo.

---

Read the HANDOFF.md file in this repo root first — it has the full project overview, current state, technical details, schema, pending tasks, and notes for next session.

Also read ROADMAP.md for the phased feature plan, and SPEC.md for the original specification.

This is axylusion.com (currently live at https://koltregaskes.github.io/axylusiondotcom). It is an AI art portfolio website for Kol Tregaskes, showcasing Midjourney images, videos, and Suno music.

Tech stack: Pure vanilla HTML/CSS/JS — no frameworks, no npm, no build tools. Data lives in data/gallery.json. Dark theme with amber/cream accents (#c4851a amber, #0a0a0a background). Fonts: Inter (display/body), JetBrains Mono (mono). GitHub Pages deployment.

Current state: The gallery works with 4 sample images, search, filtering by type/date/model, modal viewer with keyboard navigation, URL history, pagination, social links. Videos are hidden (Midjourney CDN returns 403). Music schema is ready but no Suno tracks added yet.

There is a detailed Gemini Deep Think prompt at W:\Agent Workspace 2\prompts\12-axy-lusion-website.md that covers the full architecture, bugs to fix, news page design, and image hosting strategy. No response has been generated for it yet.

The HANDOFF.md lists these priority tasks:
1. Image grouping/bundling feature for similar prompts.
2. Model info pages documenting each AI model.
3. AI news page (expand beyond gallery).
4. Video hosting solution (Midjourney CDN returns 403 on videos).
5. DNS migration from Notion redirect to GitHub Pages.

Rules:
- UK English always
- Dark mode only — the premium black gallery aesthetic is the brand
- Amber accent (#c4851a) only — no new accent colours
- No frameworks, no npm, no bundlers — pure static files
- Performance first — site will have 6,000+ items eventually
- Mobile-first responsive
- All images must have alt text
- Social links order: X, Instagram, YouTube, TikTok, Midjourney, Suno
- Test locally before committing
- Commit and push when done
