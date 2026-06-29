# Rent a 4090 and test-render Mythrealm (before buying anything)

Goal: render Episode 1 on a rented RTX 4090 for **~$1–2 total**, driven from your
MacBook Air's browser/terminal — so you see real speed + quality before spending
money on a desktop. Uses the free local **LTX-Video** backend (no Higgsfield credits).

Estimated time: ~10 min setup + first render (weights download once), then ~2–3
min/clip. A short episode is well under an hour.

---

## 1. Sign up + add a few dollars
- Create an account at **runpod.io** (Vast.ai works the same way; RunPod is simpler).
- Add **$5–10** of credit. That's plenty for a test.

## 2. Deploy a GPU pod
- **Deploy → Pods → GPU Cloud**.
- GPU: pick **RTX 4090** (Community Cloud is cheapest, ~$0.34–0.69/hr).
- Template: choose a **"RunPod PyTorch 2.x"** template (CUDA + PyTorch preinstalled).
- **Storage: set the Volume disk to 100 GB** (default is often 20 GB — the model
  weights won't fit; this is the #1 mistake). Volume mounts at `/workspace`.
- Deploy. Wait ~1 min for it to start.

## 3. Connect (any of these, from your Mac browser)
- **Web Terminal** or **Jupyter Lab** from the pod's "Connect" button — no install.
- (Optional) SSH from the MacBook Air terminal using the command RunPod shows.

## 4. Set up the project + LTX on the pod
Run these in the pod's terminal. Work under `/workspace` so it lands on the 100 GB volume:

```bash
cd /workspace

# Your repo. If it's private, use a GitHub token in the URL:
#   git clone https://<TOKEN>@github.com/williamkingston/Higgsfield-automation-.git
git clone https://github.com/williamkingston/Higgsfield-automation-.git
cd Higgsfield-automation-

# Clone + install LTX-Video (downloads several GB of code/deps)
./setup-ltx.sh
source vendor/LTX-Video/.venv/bin/activate
export LTX_VIDEO_DIR="$(pwd)/vendor/LTX-Video"

# Pipeline deps in the same venv (so inference + orchestration share one Python)
pip install -q pyyaml python-dotenv httpx imageio-ffmpeg
```

## 5. Render Episode 1
```bash
python scripts/generate_episode.py series/mythrealm-ltx.yaml --episode 1
```
- The **first** generation downloads the model weights (~25–40 GB) — that's the
  slow part, once. Subsequent clips are fast.
- Output lands in `output/mythrealm/ep01/` — `scene-XX.mp4` clips + `episode.mp4`.
- If it stops partway (e.g. a pod hiccup), just re-run the same command — it
  **resumes** from where it left off.

## 6. Get the video onto your Mac
- Easiest: open **Jupyter Lab** (from the pod's Connect button), browse to
  `output/mythrealm/ep01/episode.mp4`, right-click → **Download**.
- Or from your Mac terminal: `scp` it down using the pod's SSH details.

## 7. ⚠️ Stop the billing
- When done, **Terminate** the pod (Pods → ⋮ → Terminate). Stopping alone still
  charges a small storage fee; terminating ends all charges (and deletes the pod).
- Download anything you want to keep **before** terminating.

---

## What this tells you before you buy
- **Render speed per clip** on a 4090 → how long a full episode really takes.
- **Quality** of LTX on your actual prompts/characters vs the hosted look.
- Whether 24 GB VRAM is enough for the clip length/resolution you want (it is for
  the 13B model at these settings).

If you love it → buy a **24 GB (RTX 3090/4090) desktop** and run the identical
commands locally, free forever. If render speed matters more than upfront cost →
just keep renting per session. Either way you'll *know*, not guess.

> Tip: a rented pod is also a perfectly good permanent render box — spin it up for a
> render session, terminate when done. No purchase required to make full episodes.
