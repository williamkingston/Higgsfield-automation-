# Step 2: Extract the Frame Sequence

Scroll-scrubbing draws still frames to a `<canvas>` and swaps the frame on scroll — it
never seeks a `<video>` element. Video seeking has real latency (a decode round-trip per
seek) and stutters at scroll speed; blitting a preloaded image to canvas is instant.

## How many frames

More frames = smoother scrub but more to download. Use:

```
frameCount = clamp(round(source_duration_seconds * 12), 60, 180)
```

12 "effective fps" reads as smooth for a scroll-driven reveal (the eye is tracking scroll
position, not judging frame-rate the way it would judge normal playback) while keeping
the asset count sane. 60–180 covers a 5–15s source clip. Don't extract at the source's
native fps (usually 24–30) — that's 2–3x the payload for no perceptible smoothness gain
in a scrubbed context.

## Run the extraction

```bash
./scripts/extract-frames.sh <input-video> <output-dir> [frameCount]
```

Example:

```bash
./scripts/extract-frames.sh turntable.mp4 app/public/frames/product 96
```

This writes `app/public/frames/product/frame-0001.jpg` … `frame-0096.jpg` plus a
`manifest.json` in the same directory:

```json
{
  "frameCount": 96,
  "width": 1600,
  "height": 1600,
  "pattern": "frame-%04d.jpg",
  "sourceDurationSeconds": 8
}
```

## Sizing and format

- **Downscale to the largest size the hero will ever render at** — typically 1200–1800px
  on the long edge is plenty for a hero that's at most viewport-width; extracting at
  source resolution (often 2-4K) bloats every frame for no visible gain.
- **JPEG quality ~80** is the right tradeoff for photographic product frames (WebP saves
  more but costs a bit of CPU on decode for older devices — JPEG is the safer default,
  switch to WebP if payload size becomes the bottleneck).
- **Square or the product's natural aspect ratio** — don't force 16:9 padding you'll just
  crop in CSS; crop once at extraction time instead (the script center-crops, see below).

## Spot-check before Step 4

Open frame 1, the middle frame, and the last frame directly:

- No JPEG banding/artifacts on the clean backdrop (a low `-q:v` value shows up as visible
  blocking on flat color first).
- Middle frame actually shows the "other side" of the rotation, confirming the extraction
  spacing is even across the full clip, not front-loaded.
- Last frame's product orientation, compared to frame 1, matches what the film's loop
  point should be (matters if Step 4 makes the scroll range loop rather than clamp).
