# Unlimited local rendering with LTX-Video

The `ltx` backend renders video on **your own GPU** using Lightricks' open-source
[LTX-Video](https://github.com/Lightricks/LTX-Video) model. No per-clip credits, no
paywall, no approval gates — the only cost is electricity (or a rented GPU). This is
the genuine "unlimited" path.

## What you need (hardware)

LTX-Video needs an **NVIDIA CUDA GPU**. Pick a model variant to match your VRAM:

| Your GPU / VRAM | Recommended model | Notes |
|---|---|---|
| 24 GB+ (RTX 3090/4090, A100, L40S) | 13B `ltxv-13b-0.9.7-dev` | Best quality; what `example-series-ltx.yaml` uses |
| 12–16 GB (RTX 4070 Ti/4080, 3060 12GB) | 13B **quantized** (`fp8`) or the **2B** model | Lower VRAM; slightly lower fidelity |
| 8–12 GB | 2B distilled model | Fastest, lowest VRAM |
| No NVIDIA GPU | **Rent one** (below) | Mac/AMD can't run CUDA inference |

CPU-only or Apple Silicon won't run it — LTX inference is CUDA-only.

### No GPU? Rent one (still no per-clip fees)
Spin up a cloud GPU by the hour and run the same setup:
- **RunPod**, **Vast.ai**, **Lambda** — an RTX 4090 runs roughly **$0.3–0.7/hr**, an
  A100 ~$1–2/hr. You pay for *time*, not per video, so a long render batch is cheap.

## One-time setup

```bash
# Clones LTX-Video into vendor/LTX-Video and installs it in a venv.
./setup-ltx.sh

# Tell the project where it lives (or set repo_dir in the series YAML):
export LTX_VIDEO_DIR="$(pwd)/vendor/LTX-Video"
```

Model **weights download automatically from Hugging Face on the first generation**
(several GB) — the first clip is slow, subsequent ones are fast.

## Render Mythrealm locally

A ready-to-run series file is provided: **`series/mythrealm-ltx.yaml`** (same
Episode 1 as `mythrealm.yaml`, switched to the local backend, with your
`assets/` reference images wired in as conditioning frames).

```bash
# Activate the LTX venv so inference.py runs with the right Python, or set
# backend_options.python_bin in the YAML to vendor/LTX-Video/.venv/bin/python
source vendor/LTX-Video/.venv/bin/activate

python scripts/generate_episode.py series/mythrealm-ltx.yaml --episode 1
# → output/mythrealm/ep01/episode.mp4
```

Everything else is identical to the hosted path: resume from `jobs.json`, retry on
failure, auto-assembly. To convert any existing series to local rendering, just set:

```yaml
backend: ltx
backend_options:
  pipeline_config: configs/ltxv-13b-0.9.7-dev.yaml
  # python_bin: vendor/LTX-Video/.venv/bin/python   # skip activating the venv
```

## Hosted vs local — when to use which

| | Higgsfield (hosted) | LTX-Video (local) |
|---|---|---|
| Cost | Per-clip credits | Free (your GPU) / hourly rental |
| Setup | API key only | Clone + GPU + weights |
| Speed | Fast (their GPUs) | Depends on your GPU |
| "Unlimited" | Needs Unlimited plan | Inherently uncapped |
| Best for | Quick iterations, no GPU | High volume, full episodes, full control |
