# Step 4: Build the Scroll-Scrub Hero

## Prerequisite

Call `get_website_creation_instructions` before touching any website tool — it's a hard
requirement of that flow, not optional here. Then `create_website`. Everything below
assumes the standard template: React 19 + TanStack Start, SSR'd, `app/public/` served at
the Worker root.

This is the `[C]` **"Scroll-scrub film"** pattern from `wow-maker.md` §2 — client-only,
no WebGL, so it needs the `ClientOnly` gate but not the `React.lazy` code-split that `[W]`
(three.js) patterns require.

## Where things go

- Frames from Step 2 → `app/public/frames/<slug>/frame-0001.jpg`… + `manifest.json`.
  The Worker serves `public/` at the root, so the component fetches
  `/frames/<slug>/frame-0001.jpg` etc. — same-origin, no CDN needed.
- Component → `app/src/components/scroll-scrub-hero.tsx`, adapted from
  [assets/scroll-scrub-hero.tsx](../assets/scroll-scrub-hero.tsx) in this skill.
- Wire it into the hero route (usually `app/src/routes/index.tsx`).

## The scroll → frame mapping

The core idea: make the hero section **tall** (several viewport heights), pin the canvas
inside it, and drive frame index off scroll progress through that tall section — not off
raw `window.scrollY`, which breaks the moment the page layout changes above the hero.

```tsx
const frameIndex = Math.round(progress * (frameCount - 1));
```

Where `progress` is 0→1 across the pinned section's scroll range. Use GSAP ScrollTrigger
(`scrub: true`, no easing — scrub should track the scrollbar 1:1, not lag behind it) to
compute progress; the template component wires this for you. `lenis` smooth-scroll is
optional polish (wow-maker §4) — nice with ScrollTrigger, not required for correctness.

## Preload strategy (the part that actually determines whether this feels premium or janky)

Never scrub against an image that hasn't loaded yet — that's the single biggest way this
pattern fails in practice.

1. **Block on a small head window** — preload the first ~10 frames before mounting the
   scroll listener at all; show a lightweight loading state (or just the static first
   frame) until they're in.
2. **Stream the rest in the background** — kick off loading frames 11..N immediately
   after, in order, without blocking interaction.
3. **Guard the draw call** — if `frameIndex` points at a frame that hasn't finished
   loading yet, draw the nearest loaded frame instead of skipping the paint (a blank
   canvas frame reads as broken; a slightly-stale frame does not).

The template component implements all three — read it rather than re-deriving this from
scratch.

## Canvas sizing

Account for `devicePixelRatio` or the image will look soft on retina displays: size the
canvas backing store at `cssWidth * dpr` / `cssHeight * dpr`, then scale the drawing
context, not the CSS size.

## SSR + reduced motion (non-negotiable per wow-maker's hard rules)

- No `window`/`document`/canvas access at module top level or during the SSR render pass.
  Wrap the whole component in `ClientOnly` (see `wow-maker.md` §6) with a static fallback
  (e.g. a plain `<img>` of the middle frame) rendered server-side.
- Check `prefers-reduced-motion` and, when set, skip the scroll listener entirely: render
  one static frame (pick the "hero" angle — usually the middle frame, not frame 0) with
  no pin, no scrub. This is a hard SSR/motion rule for every `[C]`/`[W]` pattern in
  wow-maker, not specific to this skill.

## Verify

Scroll through the section at normal speed and at a fast flick. At normal speed the
rotation should track the scrollbar with no visible frame drop; at a fast flick it should
jump straight to the correct frame for wherever the scroll landed (no catch-up
animation — that's what makes video-seeking approaches feel laggy by comparison). Resize
the window and confirm the canvas stays crisp and centered.
