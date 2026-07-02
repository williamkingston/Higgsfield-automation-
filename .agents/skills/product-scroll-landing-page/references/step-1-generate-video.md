# Step 1: Generate the Turntable Film

## Pick a model

Don't hardcode a model id — call `models_explore` first, since available models change:

```
models_explore(action:'recommend', type:'video', input:'image',
  query:'clean studio backdrop turntable rotation of a product from a single reference photo')
```

Starting points, per `wow-maker.md` §1 and the `generate_video` tool defaults:

- **`seedance_2_0`** — the wow-maker default for seamless loops/short films; good first
  choice for a clean rotating-product clip.
- **`kling3_0_turbo`** — fast text-to-video / single-start-frame animation; use when you
  only have one photo and want a quick single-shot rotation.
- **`kling3_0`** — better for multi-shot or when you need explicit motion transfer /
  audio; overkill for a plain turntable but fine if the brief wants a multi-angle reveal.

If `models_explore` recommends something else, use that — the goal is the result
described below, not a specific model name.

## Prompt shape

The prompt needs three things every time:

1. **Clean backdrop** — "seamless white/neutral studio backdrop, soft even studio
   lighting, no props, no reflections that break continuity."
2. **Continuous rotation** — "slow full 360° turntable rotation, constant angular
   speed, camera locked, product centered" (or "orbiting camera" if the product itself
   should stay still — pick one, don't mix, or the extracted frames won't scrub cleanly).
3. **No text/logos added** — "no added text, no watermark, no logo overlays" (same
   IP-safety rule as wow-maker §1) so captions can be composited in HTML afterward.

Call shape:

```
generate_video(params: {
  model: "<from models_explore>",
  prompt: "<backdrop + rotation + no-text, as above>",
  medias: [{ value: "<media_id from Step 0>", role: "start_image" }], // role per the chosen model's medias[].roles
  duration: 8, // 5-15s is the useful range; longer just means more frames to extract later
})
```

Poll the job to completion, then download the result (do not pass the `https://` result
URL back into another Higgsfield tool as a media value — those expect a `media_id` or a
prior `job_id`; download it directly for Step 2's ffmpeg pass).

## Verify before moving on

Before extracting frames, actually watch the clip:

- **Rotation is one continuous cycle**, not a back-and-forth wobble or a jump-cut. Scroll
  scrubbing will replay any jump or reversal every time the user scrolls past it, so it
  reads as a glitch, not a stylistic choice.
- **Backdrop has no seams** — a visible horizon line or gradient shift will "pop" as
  frames step forward, which is very noticeable at scrub speed even if invisible at
  normal playback speed.
- **No warped text/logos** on the product — generation artifacts on branding read as
  broken immediately, more than on a plain surface.

If any of these fail, regenerate with a tighter prompt (or try the model
`models_explore` ranked second) before spending time on frame extraction — fixing it
after extraction means redoing Step 2 anyway.

## Alternative: real interactive 3D instead of a pre-rendered film

The scroll-scrub technique (this skill's default) trades true interactivity for zero
WebGL code — it's a video, so the user can only "spin" it by scrolling, not drag it.
If the brief specifically wants drag-to-rotate, use `generate_3d` (image → textured
`.glb`) and wow-maker §2's **"Hold-to-spin 3D showroom"** pattern instead
(`three` + `@react-three/fiber` + `@react-three/drei`). That's a materially bigger
build — real WebGL, real assets — so only switch to it if scroll-only rotation is
explicitly not enough for the brief.
