# Step 3: Pull Design Inspiration (optional)

The source workflow this skill is based on pastes a reference URL (e.g.
`apple.com`) into an "Inspo" field and lets the agent infer style from it. Don't
eyeball a live site by memory — capture it for real tokens, the same way the
`website-to-hyperframes` skill does for its brand step:

```bash
npx hyperframes capture <inspo-url> -o captures/<slug>
```

This needs no API key for the base capture (an optional `GEMINI_API_KEY` improves asset
descriptions, not relevant here since you're only pulling colors/fonts/layout, not
picking assets from the captured site).

Read only what Step 4 needs:

| File | Use for |
|---|---|
| `captures/<slug>/extracted/tokens.json` | color palette |
| `captures/<slug>/extracted/design-styles.json` | typography scale, spacing, component shapes |
| `captures/<slug>/extracted/fonts-manifest.json` | font families to source (Google Fonts / self-host) |
| `captures/<slug>/screenshots/contact-sheet-*.jpg` | grid layout and text-placement reference — how much whitespace around the hero, where captions sit relative to the product |

Do not copy the reference site's copy, imagery, or component code — only its systemic
choices (palette, type scale, spacing rhythm, hero-to-viewport ratio). The result should
feel like it belongs in the same design language, not like a clone.

## No inspo URL given

Pick a mood from wow-maker §2's two scroll-scrub variants and say which one you're using
before building:

- **"Scroll-scrub film"** (dark, cinematic) — for launches, premium tech, anything
  wanting drama. Near-black background, high-contrast type, captions as minimal white
  text.
- **"Frosted-card scrubber"** (warm, light) — for boutiques, lifestyle products. Light
  background, the film scrubs behind translucent frosted serif cards instead of plain
  text overlays.

Either way, state the choice to the user in one line before Step 4 — it changes the
component's color tokens and card treatment, and is cheap to redirect now versus after
building.
