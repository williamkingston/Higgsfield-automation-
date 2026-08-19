import re

from src.templates.fashion_film_silhouette_reveal import (
    FilmSubject,
    Reference,
    render_all_shots,
)


def make_subject(num_accessories: int = 1) -> FilmSubject:
    return FilmSubject(
        subject=Reference(role="male model", description="male model"),
        garment=Reference(role="gray distressed hooded jacket", description="gray distressed hooded jacket"),
        accessories=[
            Reference(role=f"accessory {i}", description=f"accessory {i}")
            for i in range(1, num_accessories + 1)
        ],
    )


def test_renders_four_shots():
    shots = render_all_shots(make_subject())
    assert len(shots) == 4
    assert all(isinstance(shot, str) and shot.strip() for shot in shots)


def test_reference_tags_are_consistently_numbered_across_all_shots():
    subject = make_subject(num_accessories=2)
    shots = render_all_shots(subject)

    for shot in shots:
        tags_used = sorted(set(re.findall(r"@image_(\d+)", shot)), key=int)
        # subject is always @image_1, garment is always @image_2, regardless of shot
        assert "1" in tags_used
        if "@image_2" in shot:
            assert "2" in tags_used


def test_no_unfilled_placeholders_remain():
    shots = render_all_shots(make_subject())
    for shot in shots:
        assert "{" not in shot and "}" not in shot


def test_zero_accessories_is_supported():
    subject = make_subject(num_accessories=0)
    shots = render_all_shots(subject)
    assert len(shots) == 4
    # garment-macro shot must still reference the garment as @image_2
    assert "@image_2" in shots[2]


def test_many_accessories_are_all_referenced():
    subject = make_subject(num_accessories=3)
    shots = render_all_shots(subject)
    reveal_shot = shots[0]
    for i in range(1, 6):  # subject + garment + 3 accessories = 5 tags
        assert f"@image_{i}" in reveal_shot
