"""Parametrized 4-shot "Silhouette Reveal" fashion film template.

Structure (fixed across any subject): a full-body silhouette reveal in a
light beam, a noir face close-up, a macro pass over the hero garment, and a
closing silhouette that dissolves into lens flare. The shot skeleton is
generic — only the subject, hero garment, and optional accessories change
between generations, so the same four beats can drive any character/product
set rather than one specific jacket-and-sunglasses shoot.

Reference tags are always assigned in a fixed order (subject, garment, then
accessories) so every rendered prompt numbers its @image_N references
consistently — the source brief for this template had the tags swapped in
one of its four shots, which this generator avoids by construction.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Reference:
    """One reference image: what it's a picture of, and how to describe it."""

    role: str  # short label, e.g. "male model", "silver sunglasses"
    description: str  # full descriptive clause used in the prompt


@dataclass(frozen=True)
class FilmSubject:
    subject: Reference  # the person/character — must be a 100% identity match
    garment: Reference  # the hero wearable that shot 3 macros over
    accessories: list[Reference] = field(default_factory=list)  # worn throughout, optional

    def all_references(self) -> list[Reference]:
        return [self.subject, self.garment, *self.accessories]


def _tag(index: int) -> str:
    return f"@image_{index}"


def _reference_block(subject: FilmSubject) -> str:
    refs = subject.all_references()
    lines = [f"{_tag(i)} is the {ref.description}." for i, ref in enumerate(refs, start=1)]
    return "\n".join(lines)


def _worn_clause(subject: FilmSubject) -> str:
    items = [subject.garment, *subject.accessories]
    tags = [_tag(i) for i in range(2, len(items) + 2)]
    parts = [f"{tag} ({item.role})" for tag, item in zip(tags, items, strict=True)]
    if len(parts) == 1:
        return f"wearing {parts[0]}"
    return "wearing " + ", ".join(parts[:-1]) + f", and {parts[-1]}"


def render_shot_1_silhouette_reveal(subject: FilmSubject) -> str:
    return f"""SCENE CONTEXT
A tall figure stands motionless against a single blinding vertical light beam in a pitch-black studio, revealed first as a pure silhouette.
ACTIVE REFERENCES
{_reference_block(subject)}
FIRST FRAME AND SPATIAL BLOCKING
The first visible frame already contains {_tag(1)} full-height, centered, back three-quarter to camera, standing within the vertical beam. No empty establishing shot. Subject is {_worn_clause(subject)}.
OPTICS
47 degrees diagonal field of view, standard normal lens, camera 4 meters from subject, natural proportions, no distortion.
CAMERA
Static locked-off camera at chest height. A faint haze drifts across the beam. Single continuous take.
ACTION TIMING
BEAT 1 — Subject holds dead still, chest barely rising. BEAT 2 — A brief beat later, subject slowly rolls their head one degree toward camera, a rim of light catching {_tag(2)}.
PHYSICS
Subject is grounded, weight even on both feet; garment settles and holds still; cloth obeys gravity.
LIGHTING
Contre-jour: subject stands between camera and the vertical beam. Camera is on the shadow side. The silhouette and the rim outline carry the image; subject stays in crushed near-black, only a thin edge of light reveals them. Faces stay in shadow.
AUDIO
Low cinematic drone bed, a soft electronic pulse. No dialogue."""


def render_shot_2_face_reveal(subject: FilmSubject) -> str:
    return f"""SCENE CONTEXT: Close-up of the subject's face, slowly lifting toward a hidden light source with quiet awe.
REFERENCE: face and identity 100% match {_tag(1)}; subject is {_worn_clause(subject)}.
FIRST FRAME: Subject's face fills the frame, deep top shadow.
LIGHTING: hard directional light from directly above, crushed shadow under nose and chin, lit brow and cheekbones, noir chiaroscuro, no soft fill.
OPTICS / CAMERA: intimate close-up, 84° field of view, camera about one meter away, slow subtle dolly-in as subject tilts their head up; shallow focus on the eyes.
ACTION: subject lifts their chin and eyes slowly across the shot, one held introspective expression, slow-motion feel, natural hair settling.
POSITIVE LOCK: black-and-white, high-contrast noir, 35mm film grain, futuristic fashion campaign, moody low-key light; no text, no logo, no watermarks, no UI."""


def render_shot_3_garment_macro(subject: FilmSubject) -> str:
    garment_tag = _tag(2)
    return f"""SCENE CONTEXT
The camera closes in on the subject's chest, caressing the {subject.garment.description} — every seam, hardware detail, and fastener catches the light.
ACTIVE REFERENCES
{_tag(1)} is the subject — 100% matches the reference.
{garment_tag} is the {subject.garment.description} — the hero of this shot.
FIRST FRAME AND SPATIAL BLOCKING
First frame is an extreme close-up of the garment's chest: its central closure running down the center of frame, flanking details on either side, and any trim or hardware along the seams. {_tag(1)}'s collared neck and jaw appear only at the very top edge.
OPTICS
29 degrees diagonal field of view, short telephoto macro character, camera 0.5 meters from the fabric. Shallow focus: the current seam is razor sharp, surrounding material melts into soft bokeh.
CAMERA
A slow vertical tracking move, starting at the collar and gliding down over the chest and hardware before settling on a cuff or hem detail.
ACTION TIMING
BEAT 1 — Frame opens on the collar. BEAT 2 — The camera slides down over the central closure; hardware glitters as it passes. BEAT 3 — It settles on a cuff or hem detail catching a hard glint, while the chest rises in a slow breath.
PHYSICS
The fabric holds its structure; folds hold their shape, and each glint responds to the same single moving light source. Any pull or clasp stays weighted and still.
LIGHTING
One hard raking key from high camera-left slides across the textured weave and hardware in a moving band of specular highlights, over deep crushed shadows. High-contrast, near-monochrome.
AUDIO
Low drone cushions the shot with a soft metallic clink as the frame rests. No dialogue."""


def render_shot_4_closing_silhouette(subject: FilmSubject) -> str:
    return f"""SCENE CONTEXT
The closing shot: a profile silhouette of the subject, as a hazy light washes past them and the frame drifts into soft-lens flare.
ACTIVE REFERENCES
{_reference_block(subject)}
FIRST FRAME AND SPATIAL BLOCKING
First frame shows subject's full profile in near-total silhouette, chest-high framing, centered against a light-gray halo of haze.
OPTICS
47 degrees diagonal field of view, standard normal lens, camera 3 meters from the profile; soft atmospheric diffusion.
CAMERA
A slow, subtle zoom-out while the operator drifts one hand-width to the side; the focus eases from the temple into blurred haze over the last beat.
ACTION TIMING
BEAT 1 — Subject holds perfectly still in profile. BEAT 2 — A wave of hazy light travels across the frame, briefly silvering any hardware on {_worn_clause(subject)}. BEAT 3 — The edges bloom into lens flare and the image dissolves to light.
PHYSICS
The body is static; motion is purely the camera retreat and light moving through haze.
LIGHTING
Backlit and overexposed: subject sits between camera and a bright diffused source, kept as a black silhouette; only the light passing around them is visible. Muted, hazy, monochrome with flare.
AUDIO
The drone sustains and softens, ending on a single sustained tone. No dialogue."""


SHOT_RENDERERS = [
    render_shot_1_silhouette_reveal,
    render_shot_2_face_reveal,
    render_shot_3_garment_macro,
    render_shot_4_closing_silhouette,
]


def render_all_shots(subject: FilmSubject) -> list[str]:
    return [renderer(subject) for renderer in SHOT_RENDERERS]
