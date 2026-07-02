# Step 5: Content Sections + Deploy

## Caption cards tied to the scrub

The source workflow's "map scroll behavior to the video" instruction means more than just
the product spinning — copy should surface at specific rotation angles, echoing what
Apple product pages do (a headline appears once the product has turned to show its most
photogenic face, a spec callout appears pointing at a feature once it's rotated into
view).

Define caption cards as `{ fromProgress, toProgress, content }` ranges over the same
0–1 progress value driving the frame index (see Step 4). Fade each card in/out with a
plain CSS opacity transition keyed off whether `progress` is inside its range — don't
give captions their own separate scroll listener, derive them from the one already
computed for the frame index.

Keep captions **out of the canvas** — they're real DOM text overlaid on top (absolutely
positioned over the canvas), not baked into the frames. This keeps them accessible,
selectable, and independent of frame resolution.

## The rest of the page

Everything below the hero is a normal marketing page — build it from wow-maker's
directory (§3/§5) rather than hand-rolling generic sections:

- **Features/specs** — Tailark `features-*` blocks, or a bento grid (Magic UI
  `bento-grid`) if the product has several distinct callouts worth their own tile.
- **Numbers that matter** (battery life, weight saved, price) — `@number-flow/react`
  animated counters instead of static digits, per wow-maker's minimum wow bar.
- **Testimonials/social proof** — Tailark `testimonials-*` if the brief has real quotes;
  skip the section entirely rather than filling it with placeholder quotes.
- **CTA + footer** — Tailark `call-to-action-*` / `footer-*`.

Match the mood chosen in Step 3 (dark cinematic vs. warm frosted) across every section —
a scroll-scrub hero that's dark and dramatic followed by default light Tailark sections
reads as two different sites stitched together.

## Deploy

```
website_repo_access(website_id)   # clone, edit, commit, push — the deploy builds from the pushed repo
deploy_website(website_id, env: "preview")
```

Preview only, per the website-builder flow's own hard rule — never `env: "production"`
unless the user explicitly asks to publish. Before calling it done, run
`bun run qa:fill -- --strict` from `app/` to catch any surviving placeholder copy or
`lorem ipsum`. Don't reflexively `bun install && bun run build` locally first — the
platform CI build on deploy is the authoritative check; only build locally if you changed
dependencies or are actively debugging a build error.

Return the preview URL. Don't screenshot it yourself unless asked — let the user open it.
