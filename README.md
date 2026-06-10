# Higgsfield Automation — Episodic AI Video Series

Generate episodic AI video "shows" with the [Higgsfield AI](https://higgsfield.ai)
platform. Describe a series once — its style, characters, and per-scene prompts —
and the pipeline turns each episode into video-generation jobs, polls them to
completion, downloads the clips, and writes a manifest.

## How it works

```
series.yaml  ──►  Series ─► Episode ─► Scene ─┐
                                              ▼
                              HiggsfieldClient.create_video_job()
                                              │   (async job)
                                              ▼
                              wait_for_job()  ─►  download clip
                                              ▼
                              output/<series>/<epNN>/manifest.json
```

- **Pluggable backends** (`src/higgsfield/backends.py`) — generate scenes with the
  hosted **Higgsfield** API or a local **LTX-Video** model, chosen per series.
- **One client module** (`src/higgsfield/client.py`) for all Higgsfield API calls —
  bearer auth, exponential backoff on `429`/`5xx`, and async job polling.
- **Crash-recoverable**: each scene's job id is persisted to `jobs.json`, so a
  re-run skips already-completed scenes instead of regenerating (and paying) again.
- **Auto-assembled**: once an episode's scenes are generated, the clips are
  stitched into a single `episode.mp4` with ffmpeg (lossless stream copy).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env      # then add your HIGGSFIELD_API_KEY
```

## Generate an episode

```bash
python scripts/generate_episode.py series/example-series.yaml --episode 1
```

Scene clips, the stitched `episode.mp4`, and a `manifest.json` land in
`output/<series>/ep01/`. Assembly needs [`ffmpeg`](https://ffmpeg.org) on your
PATH; without it, the individual clips are still produced and the step is skipped.

## Define your own show

Copy `series/example-series.yaml` and edit it. `style` and `character_bible` are
prepended to every scene prompt so the look and cast stay consistent across
episodes. Each scene becomes one generation job:

```yaml
title: "My Show"
style: "Cinematic, neon-noir, rain-soaked streets"
character_bible: "REN, a courier with a chrome arm and a red umbrella"
aspect_ratio: "16:9"
episodes:
  - number: 1
    title: "Pilot"
    scenes:
      - id: scene-01
        prompt: "Wide shot of Ren stepping off a maglev train into the rain"
        duration_seconds: 6
        motion: slow push-in
```

## Backends

Each series picks how its scenes are generated via a `backend:` field.

### Higgsfield (hosted API — default)

```yaml
backend: higgsfield
```

Needs `HIGGSFIELD_API_KEY`. Scenes are submitted as async jobs and downloaded
when complete.

### LTX-Video (local, open-source)

Runs [Lightricks/LTX-Video](https://github.com/Lightricks/LTX-Video) on your own
GPU — no per-clip API cost. Install it with the helper script:

```bash
./setup-ltx.sh                 # clones LTX-Video into vendor/ and installs it
export LTX_VIDEO_DIR="$PWD/vendor/LTX-Video"
```

Then point a series at it:

```yaml
backend: ltx
backend_options:
  repo_dir: vendor/LTX-Video            # or set LTX_VIDEO_DIR
  pipeline_config: configs/ltxv-13b-0.9.7-dev.yaml
```

A ready-made example lives at `series/example-series-ltx.yaml`:

```bash
python scripts/generate_episode.py series/example-series-ltx.yaml --episode 1
```

The backend shells out to LTX-Video's `inference.py`, mapping each scene's
`aspect_ratio` → height/width, `duration_seconds` × `fps` → `num_frames`
(rounded to LTX's required `8k+1`), and `image_reference` → image conditioning.
The rendered clip is moved into `output/<series>/<epNN>/`, so assembly and the
rest of the pipeline work identically regardless of backend.

## Tests

```bash
pytest
```

The suite stubs the network, so it runs without an API key.

## Notes on the API

The endpoint paths and request/response field names live as constants at the top
of `src/higgsfield/client.py` (`PATH_CREATE_VIDEO`, `PATH_JOB_STATUS`, etc.).
Adjust them there to match your Higgsfield API account's exact surface — every
call site reads from those constants, so nothing else needs to change.
