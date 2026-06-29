#!/usr/bin/env bash
# Mythrealm — Episode 2: download the 8 clips and stitch into one MP4.
set -euo pipefail
B="https://d8j0ntlcm91z4.cloudfront.net/user_328KrQzY8FXxc5VLqo8nbfTnCna"
urls=(
  "$B/hf_20260629_125146_54edb941-13ab-4ea2-84aa-69c07c15d916.mp4"
  "$B/hf_20260629_125129_8553bcd8-1dbf-4815-a703-b40d7a9cb91c.mp4"
  "$B/hf_20260629_125132_aa7b7e04-d4f5-4279-9c42-dad69a2e65bd.mp4"
  "$B/hf_20260629_125134_f9037ea7-992a-40c7-950d-6203c1bf8b4b.mp4"
  "$B/hf_20260629_125505_41c0fe5f-4215-4a72-9b26-197d587df608.mp4"
  "$B/hf_20260629_125518_98939c36-8fa4-440d-926e-13309af2094d.mp4"
  "$B/hf_20260629_125832_21946a08-e8d0-4453-976f-aa70cde6f44e.mp4"
  "$B/hf_20260629_125835_90c2a942-a4a4-4479-b07f-eedc6f7086ba.mp4"
)
mkdir -p clips_ep02; : > list_ep02.txt; i=1
for u in "${urls[@]}"; do
  f=$(printf "clips_ep02/scene-%02d.mp4" $i)
  echo "Downloading scene $i..."; curl -fsSL -o "$f" "$u"
  echo "file '$PWD/$f'" >> list_ep02.txt; i=$((i+1))
done
echo "Stitching -> episode02.mp4"
ffmpeg -y -f concat -safe 0 -i list_ep02.txt -c:v libx264 -c:a aac -movflags +faststart episode02.mp4
echo "Done: episode02.mp4"
