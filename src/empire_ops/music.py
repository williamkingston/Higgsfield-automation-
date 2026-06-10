"""Music Catalog helpers for the Phase 2 music pipeline.

Deterministic glue: pick tracks marked ready, build a Suno-formatted scaffold
(verses left open per the standing rule), log musical metadata back to the
catalog, and queue cover art into the content engine. Sourcing beds/loops
(Splice) and the creative direction are done by the routine via connectors/skills.
"""

from __future__ import annotations

from . import content
from .airtable import AirtableClient
from .schema import MusicCatalog

# Music Catalog status values (match the "Status" field choices).
IDEA = "Idea"
READY_TO_BUILD = "Ready to Build"
SCAFFOLDED = "Scaffolded"
STEMS_READY = "Stems Ready"
RELEASED_HOLD = "Released-Hold"

# Default song structure. Verses are intentionally left open.
DEFAULT_SECTIONS = ("Intro", "Verse 1", "Chorus", "Verse 2", "Chorus", "Bridge", "Outro")
_OPEN_VERSE_MARK = "(open — left for writing)"


def ready_to_build(client: AirtableClient) -> list[dict]:
    """Return Music Catalog rows marked 'Ready to Build'."""
    return [
        record
        for record in client.list_records(MusicCatalog.TABLE_ID)
        if record["fields"].get(MusicCatalog.STATUS) == READY_TO_BUILD
    ]


def build_suno_scaffold(
    title: str,
    *,
    style: str,
    bpm: int | None = None,
    key: str | None = None,
    sections: tuple[str, ...] = DEFAULT_SECTIONS,
) -> str:
    """Build a Suno-formatted track scaffold with verses left open.

    Verse sections carry an open-verse marker (no lyrics) so they stay yours to
    write; other sections are left as empty tagged blocks for arrangement.
    """
    descriptor = f"Style: {style}"
    if bpm:
        descriptor += f", BPM {bpm}"
    if key:
        descriptor += f", Key {key}"

    lines = [f"# {title}", f"[{descriptor}]", ""]
    for section in sections:
        lines.append(f"[{section}]")
        if section.lower().startswith("verse"):
            lines.append(_OPEN_VERSE_MARK)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def log_scaffold(
    client: AirtableClient,
    record_id: str,
    *,
    bpm: int | None = None,
    key: str | None = None,
    direction: str | None = None,
    open_verse: bool = True,
    drive_link: str | None = None,
    status: str = SCAFFOLDED,
) -> dict:
    """Write musical metadata and open-verse status back to the catalog."""
    fields: dict[str, object] = {
        MusicCatalog.STATUS: status,
        MusicCatalog.OPEN_VERSE: open_verse,
    }
    if bpm is not None:
        fields[MusicCatalog.BPM] = bpm
    if key:
        fields[MusicCatalog.KEY] = key
    if direction:
        fields[MusicCatalog.DIRECTION] = direction
    if drive_link:
        fields[MusicCatalog.DRIVE_LINK] = drive_link
    return client.update_record(MusicCatalog.TABLE_ID, record_id, fields)


def queue_cover_art(
    client: AirtableClient,
    *,
    track_title: str,
    brand: str,
    prompt: str,
    music_record_id: str | None = None,
) -> dict:
    """Queue a cover-art brief into the Content Queue and flag the track.

    Reuses the content engine: the cover art is generated and approved through
    the same Tier-B path as everything else.
    """
    created = content.enqueue(
        client,
        title=f"Cover art — {track_title}",
        prompt=prompt,
        brand=brand,
        asset_type="Cover Art",
    )
    if music_record_id:
        client.update_record(
            MusicCatalog.TABLE_ID,
            music_record_id,
            {MusicCatalog.COVER_ART_QUEUED: True},
        )
    return created
