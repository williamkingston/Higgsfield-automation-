---
name: product-scroll-landing-page
description: |
  Turn product photos/video into an Apple-style, scroll-driven 3D landing page — a
  clean-backdrop turntable film of the product, extracted to a frame sequence, scrubbed
  by scroll position on a canvas, shipped as a real Higgsfield website. Use when: (1) a
  user uploads or references product photos/video and asks for a landing page, "3D
  website", or "site like apple.com", (2) someone asks to replicate a scroll-triggered
  product reveal / hero animation, (3) a request mentions "spinning product", "turntable
  video into a website", "scroll-scrub", or pairs a product asset with an "inspo" /
  reference site URL. Even a bare "make me a landing page for this product" with an
  attached photo is this skill if the product itself should be the hero.
---

# Product → Scroll-Driven Landing Page

Reproduce the high-end, scroll-triggered 3D product reveal that agencies charge for —
without hand-rolling WebGL. The trick: generate a clean-backdrop turntable video of the
product, extract it to still frames, and blit frames to a `<canvas>` keyed to scroll
progress instead of seeking a `<video>` element (video `currentTime` seeking is laggy and
never feels frame-accurate; frame-blitting is what Apple's own product pages do).

This skill is a specific playbook layered on top of two things this repo/platform already
provide — it does not reinvent them:

- **`mcp__Higgsfield__*` generation tools** — for the turntable film itself.
- **The Higgsfield website-builder flow** (`get_website_creation_instructions` →
  `create_website` → `website_repo_access` → `deploy_website`) — for the actual site. Its
  `references/wow-maker.md` already names this exact technique as the **"Scroll-scrub
  film"** signature effect (§2). This skill fills in the missing specifics: how to shoot
  the source film, how to extract and preload frames without jank, and a ready component.

The workflow has 6 steps. Steps marked 💬 stop and ask the user; skip them only if the
user has already signaled autonomous mode ("just build it", "surprise me").

---

## Step 0: Gather Inputs 💬

You need, at minimum, **one clear product photo or video** (packaging, hero shot, or a
short handheld clip — doesn't need to already be a turntable). Optional but valuable:

- **Inspiration URL** (e.g. `apple.com`, a competitor's PDP) — used in Step 3 to pull a
  real palette/type/grid instead of guessing.
- **Master brief** — any styling instructions, copy, or a target mood ("dark and
  cinematic" vs "warm boutique frosted glass" — these map to different wow-maker
  variants in Step 4).

If no product asset has been shared: for Apps UI-capable clients call
`media_upload_widget` so the user picks the local file directly — never ask them to paste
it into chat, remote tools can't read chat attachments. For a URL, call `media_import_url`.

**Gate:** a usable product image/video is uploaded (have a `media_id`), and you know
whether an inspo URL / brief exists.

---

## Step 1: Generate the Turntable Film

**Read:** [references/step-1-generate-video.md](references/step-1-generate-video.md)

Turn the product photo into a short (~5-15s), clean-backdrop, slowly-rotating or
orbiting-camera video using Higgsfield's video generation tools. This is the raw material
the whole scroll effect is built from — get the backdrop and motion right here, not later.

**Gate:** a completed, downloaded video file, backdrop genuinely clean (no seams, no
warped logos), rotation reads as one continuous cycle.

---

## Step 2: Extract the Frame Sequence

**Read:** [references/step-2-extract-frames.md](references/step-2-extract-frames.md)
**Script:** [scripts/extract-frames.sh](scripts/extract-frames.sh)

Extract the film to a numbered JPEG/WebP sequence at the frame count the scroll effect
actually needs (not the source fps) and write a `manifest.json` the component reads.

**Gate:** `frames/` has `frameCount` sequential files, `manifest.json` matches them, and a
spot-check of first/middle/last frames confirms no encoding artifacts.

---

## Step 3: Pull Design Inspiration (optional)

**Read:** [references/step-3-inspiration.md](references/step-3-inspiration.md)

If an inspo URL was given, capture it for real color/font/grid tokens instead of
eyeballing it. If not, pick a wow-maker variant from Step 4's table by mood and skip
straight there.

**Gate:** either real tokens extracted, or a deliberate mood chosen and stated to the user.

---

## Step 4: Build the Scroll-Scrub Hero

**Read:** [references/step-4-build-scroll-scrub.md](references/step-4-build-scroll-scrub.md)
**Component template:** [assets/scroll-scrub-hero.tsx](assets/scroll-scrub-hero.tsx)

Call `get_website_creation_instructions` (required by that flow before any website edit),
then `create_website`. Drop the frames into `app/public/frames/`, adapt
`scroll-scrub-hero.tsx` as the hero, and wire scroll progress → frame index. This is the
`[C]` "Scroll-scrub film" pattern from `wow-maker.md` §2 — follow its SSR pattern
(`ClientOnly` + no `window` at module top) exactly.

**Gate:** scrolling the hero section visibly steps through the product's rotation with no
stutter, and a `prefers-reduced-motion` fallback renders a static frame.

---

## Step 5: Content Sections + Deploy

**Read:** [references/step-5-content-sections.md](references/step-5-content-sections.md)

Build the rest of the page (features, specs, CTA) around the hero using wow-maker's
component directory (§5) rather than hand-rolling generic sections. Caption cards fade in
at frame milestones as the user scrolls, echoing the "map scroll behavior to the video"
brief from the source workflow. Then commit, push, and `deploy_website(env='preview')`.

**Gate:** preview URL returned; every section scroll-reveals; no placeholder copy/`lorem`
survives `bun run qa:fill -- --strict`.

---

## Quick Reference

| File | When to read |
|---|---|
| [step-1-generate-video.md](references/step-1-generate-video.md) | Step 1 — model choice, prompt shape, backdrop/rotation checks |
| [step-2-extract-frames.md](references/step-2-extract-frames.md) | Step 2 — frame count formula, ffmpeg flags, manifest schema |
| [scripts/extract-frames.sh](scripts/extract-frames.sh) | Step 2 — run directly, don't retype the ffmpeg command |
| [step-3-inspiration.md](references/step-3-inspiration.md) | Step 3 — reusing the `hyperframes capture` pipeline for tokens |
| [step-4-build-scroll-scrub.md](references/step-4-build-scroll-scrub.md) | Step 4 — scroll math, preload strategy, SSR gotchas |
| [assets/scroll-scrub-hero.tsx](assets/scroll-scrub-hero.tsx) | Step 4 — starting component, adapt don't rewrite |
| [step-5-content-sections.md](references/step-5-content-sections.md) | Step 5 — caption-card timing, section directory picks, deploy |

## Related Skills

- **`gsap`** — tween/timeline syntax used for caption-card reveals. Note: its
  `window.__timelines` contract is for HyperFrames video *rendering*, not this — a live
  website registers GSAP/ScrollTrigger normally.
- **`emil-design-eng`** — polish pass on the non-scroll-bound motion (buttons, cards,
  reduced-motion fallbacks) once the hero works.
- **`website-to-hyperframes`** — the inverse direction (site → video). Its capture
  pipeline (`npx hyperframes capture`) is what Step 3 reuses for inspo tokens.
