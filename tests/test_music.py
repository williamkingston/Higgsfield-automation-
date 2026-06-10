from src.empire_ops import music
from src.empire_ops.schema import ContentQueue, MusicCatalog
from tests.conftest import FakeAirtable


def _row(rec_id, status):
    return {"id": rec_id, "fields": {MusicCatalog.STATUS: status}}


def test_ready_to_build_filters_by_status():
    client = FakeAirtable(
        [
            _row("rec1", music.READY_TO_BUILD),
            _row("rec2", music.IDEA),
            _row("rec3", music.READY_TO_BUILD),
        ]
    )
    assert {r["id"] for r in music.ready_to_build(client)} == {"rec1", "rec3"}


def test_suno_scaffold_leaves_verses_open():
    text = music.build_suno_scaffold(
        "Midnight Velvet", style="dark R&B", bpm=92, key="F# minor"
    )
    assert "# Midnight Velvet" in text
    assert "Style: dark R&B, BPM 92, Key F# minor" in text
    assert "[Chorus]" in text
    # Every verse section is followed by the open-verse marker, never lyrics.
    lines = text.splitlines()
    verse_idxs = [i for i, ln in enumerate(lines) if ln.startswith("[Verse")]
    assert verse_idxs
    for i in verse_idxs:
        assert lines[i + 1] == "(open — left for writing)"


def test_log_scaffold_writes_metadata_and_open_verse():
    client = FakeAirtable()
    music.log_scaffold(
        client, "rec1", bpm=92, key="F# minor", direction="moody, sparse"
    )
    _, record_id, fields = client.updated[0]
    assert record_id == "rec1"
    assert fields[MusicCatalog.STATUS] == music.SCAFFOLDED
    assert fields[MusicCatalog.OPEN_VERSE] is True
    assert fields[MusicCatalog.BPM] == 92
    assert fields[MusicCatalog.KEY] == "F# minor"


def test_queue_cover_art_enqueues_and_flags_track():
    client = FakeAirtable()
    music.queue_cover_art(
        client,
        track_title="Midnight Velvet",
        brand="WrichSoundWavs",
        prompt="moody album cover, velvet textures, neon rim light",
        music_record_id="rec1",
    )
    # A Content Queue cover-art row was created…
    table_id, records = client.created[0]
    assert table_id == ContentQueue.TABLE_ID
    assert records[0][ContentQueue.ASSET_TYPE] == "Cover Art"
    assert records[0][ContentQueue.STATUS] == "Queued"
    # …and the track was flagged.
    _, record_id, fields = client.updated[0]
    assert record_id == "rec1"
    assert fields[MusicCatalog.COVER_ART_QUEUED] is True
