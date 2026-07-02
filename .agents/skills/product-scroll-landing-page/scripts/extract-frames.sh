#!/usr/bin/env bash
# extract-frames.sh — turn a turntable video into a numbered frame sequence
# for a scroll-scrub canvas hero, plus a manifest.json the component reads.
#
# Usage:
#   extract-frames.sh <input-video> <output-dir> [frameCount] [maxLongEdge]
#
# Example:
#   extract-frames.sh turntable.mp4 app/public/frames/product 96 1600

set -euo pipefail

if [ $# -lt 2 ]; then
  echo "Usage: $0 <input-video> <output-dir> [frameCount] [maxLongEdge]" >&2
  exit 1
fi

INPUT="$1"
OUTDIR="$2"
FRAME_COUNT="${3:-96}"
MAX_EDGE="${4:-1600}"

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required but not found on PATH" >&2
  exit 1
fi
if ! command -v ffprobe >/dev/null 2>&1; then
  echo "ffprobe is required but not found on PATH" >&2
  exit 1
fi
if [ ! -f "$INPUT" ]; then
  echo "Input video not found: $INPUT" >&2
  exit 1
fi

mkdir -p "$OUTDIR"

DURATION=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$INPUT")
FPS=$(awk -v d="$DURATION" -v n="$FRAME_COUNT" 'BEGIN { printf "%.6f", n / d }')

# Center-crop to square on the shorter edge, then scale so the long edge caps at
# MAX_EDGE — keeps every frame the same aspect ratio regardless of source framing.
FILTER="fps=${FPS},crop='min(iw,ih)':'min(iw,ih)',scale=${MAX_EDGE}:${MAX_EDGE}:flags=lanczos"

ffmpeg -y -i "$INPUT" \
  -vf "$FILTER" \
  -frames:v "$FRAME_COUNT" \
  -q:v 3 \
  "${OUTDIR}/frame-%04d.jpg"

ACTUAL_COUNT=$(find "$OUTDIR" -maxdepth 1 -name 'frame-*.jpg' | wc -l | tr -d ' ')

cat > "${OUTDIR}/manifest.json" <<EOF
{
  "frameCount": ${ACTUAL_COUNT},
  "width": ${MAX_EDGE},
  "height": ${MAX_EDGE},
  "pattern": "frame-%04d.jpg",
  "sourceDurationSeconds": ${DURATION}
}
EOF

echo "Extracted ${ACTUAL_COUNT} frames to ${OUTDIR} (requested ${FRAME_COUNT})"
