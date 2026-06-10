# Routine — Music Pipeline (Phase 2)

**Trigger:** nightly cron (shares slot logic with the content engine).
**Guardrail:** Tier B — scaffolds and drafts only. **Release decisions are
yours.** Spotify is research/reference only — no distribution.
**Tools:** Claude Code + Splice connector + Suno skill (Suno Bible) + Google
Drive connector + the `empire_ops` helpers.

A scheduled Claude session runs these steps using the connectors and the
deterministic `music` / `content` / `approvals` helpers.

## Steps

1. **Select work.** `music.ready_to_build(client)` → Music Catalog rows marked
   `Ready to Build`. If none, log and stop.

2. **Source beds/loops.** Use the Splice connector to find beds/loops matching
   the row's `Direction`. Note BPM and key.

3. **Assemble the scaffold.** `music.build_suno_scaffold(title, style=…, bpm=…,
   key=…)` produces a Suno-formatted scaffold with **verses left open** per the
   standing rule. Apply the Suno Bible skill for style tags and arrangement.

4. **Log back to the catalog.** `music.log_scaffold(client, id, bpm=…, key=…,
   direction=…, open_verse=True, drive_link=…, status=music.SCAFFOLDED)`.

5. **Queue cover art.** `music.queue_cover_art(client, track_title=…, brand=…,
   prompt=…, music_record_id=id)` — drops a Cover Art brief into the Content
   Queue (generated + approved through the Phase 1 path) and flags the track.

6. **Drop drafts + queue for approval.** Save stems/scaffold to Google Drive,
   then `approvals.submit_for_approval(client, item=<track title>,
   type_=approvals.MUSIC, summary=<one line>, brand=<brand>,
   preview_link=<drive link>, tier="B", source_table="Music Catalog",
   source_record=id)`.

7. **Summarize the run:** tracks scaffolded, cover art queued, drafts dropped.

## Guardrails

- Tier B throughout. The routine never releases or distributes — it produces
  scaffolds + art and files them for your approval.
- Verses stay open. The scaffold builder never fills verse lyrics.
- Spotify (if used) is reference/research only — never a distribution target.
