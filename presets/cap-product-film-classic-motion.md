# Cap Product Film — Classic Motion

Universal image-to-video prompt for a cap/hat product film. Animates a single
reference frame (the product photo) into a 10-second photoreal product film.
Designed to preserve the exact product from the reference image — no
redrawing, restyling, or invented logo/embroidery detail.

## Placeholders

Fill these in before submitting the prompt:

| Placeholder | Description | Example |
|---|---|---|
| `[ASPECT RATIO]` | Output aspect ratio | `16:9`, `9:16`, or `1:1` |
| `[ACCENT]` | The one saturated color present in the reference image | `papaya orange`, `powder blue`, `chocolate brown` |

## Positive prompt

```
CLASSIC MOTION — universal cap product film. Image-to-video from the attached
reference frame. Photoreal. No text of any kind in frame.
ASPECT RATIO: [16:9 / 9:16 / 1:1]
ACCENT: [name the one saturated color in the reference image — e.g. papaya orange,
powder blue, chocolate brown]
SUBJECT LOCK: animate the exact cap in the reference image. Preserve its crown shape,
panel count, brim curve, fabric type and weave, every color and the exact front-panel
graphic as they appear in the reference. Do not redraw, restyle, recolor, simplify or
embellish the logo or embroidery. Do not add lettering, tags, patches or emblems that
are not already in the reference. If the front graphic is text-based, treat it as a
fixed texture that moves with the panel — never regenerate it.
LOOK LOCK: match the reference frame's background exactly — same tone, same gradient,
same seamless sweep with no floor line, no props, no hands, no environment. Match its
key light direction and softness; keep the shadow under the cap soft and consistent.
Palette limited to the colors already present in the reference plus the named ACCENT.
Camera moves slowly and deliberately. Transitions are clean hard cuts on a calm rhythm,
never crossfades. Continuity anchor: the ACCENT is the only saturated hue in frame and
stays lit and unbroken through every beat.
0.0–1.5s — Extreme macro on the crown fabric, its weave or nap filling frame. Camera
drifts across the surface as a raking highlight travels with it, texture resolving in
and out of a razor-thin focus plane.
1.5–3.2s — Hard cut to a low three-quarter view, cap upright, brim angled toward camera
left. Camera arcs slowly left to right while the cap rotates a few degrees the opposite
way; the key reflection sweeps across the panels, the brim shifting from matte shadow
into soft sheen as it turns into the light.
3.2–4.8s — Match-cut into the front panel: macro on the graphic and the fabric around it,
holding its exact form from the reference. Camera pushes in a few centimetres and settles;
the key rakes across the surface so raised stitching, print edge or weave catches a soft
specular edge.
4.8–6.3s — Hard cut to a tight raking angle along the brim, the ACCENT detail filling the
lower third. Camera slides right as a soft specular band travels the length of it,
brightening to a warm core then narrowing away; the brim's face stays sharp above it.
6.3–8.0s — Hard cut to a dead-on front hero: cap perfectly symmetrical, brim level, graphic
centred, camera easing to a rest. A tiny settle in the fabric, then completely still.
8.0–10.0s — Locked-off, zero-drift static hold on the same dead-on hero framing. No camera
movement, no product movement, no light animation. Cap centred with clean empty negative
space across the lower third and even background tone, as a plate for a brand lock-up to be
composited in post. Hard stop on the last frame — no fade.
TECHNICAL: photoreal product cinematography, shallow depth of field on the three macro beats
opening to a fully sharp product on the hero, natural motion blur only on the arc and the
brim slide, soft studio contrast with open shadow detail, no grain, no lens dirt, no flare.
Absolutely no text, captions, frame labels, subtitles, numbers, typography or watermarks
generated anywhere at any point. [ASPECT RATIO], 10 seconds.
```

## Negative prompt (universal)

```
generated text, captions, burned-in labels, frame numbers, subtitles, typography,
wordmarks, garbled or invented lettering, watermark; redrawn, distorted, duplicated,
recolored or mirrored logo; added patches, tags, emblems or sponsor marks; humans,
skin, faces, hands, head or mannequin wearing the cap; environment, props, furniture,
table, horizon line; background change mid-clip, color shift, palette drift; plastic,
wet-look or patent sheen on matte fabric; asymmetric panels, warped brim curve,
changing crown shape, morphing between shots; dust, lint, fibers, fingerprints,
scuffs; handheld shake, crossfades, fade to black; heavy grain.
```
