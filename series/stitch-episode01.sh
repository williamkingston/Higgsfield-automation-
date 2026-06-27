#!/usr/bin/env bash
# Mythrealm — Episode 1: download the 8 clips and stitch into one MP4.
# Requires ffmpeg + curl. Run:  bash series/stitch-episode01.sh
set -euo pipefail
B="https://d8j0ntlcm91z4.cloudfront.net/user_328KrQzY8FXxc5VLqo8nbfTnCna"
urls=(
  "$B/hf_20260626_114129_3deedae6-1934-4195-b5b7-54a7179cb748.mp4"
  "$B/hf_20260627_054654_f33f4dc5-5dce-400d-8bdb-c79e29390155.mp4"
  "$B/hf_20260627_052309_e1b352cd-ac34-4640-b74e-4e4a02db26ea.mp4"
  "$B/hf_20260627_054659_dcfac15b-ad39-464e-a49e-9214e104e174.mp4"
  "$B/hf_20260627_054705_9f795e22-5698-48d7-b12b-533f9dc69346.mp4"
  "$B/hf_20260627_054711_dd2163f2-23ca-48ef-b26f-06c3a10c3c34.mp4"
  "$B/hf_20260627_055310_8d125bff-fb40-4ae6-bde4-7855cb407b0f.mp4"
  "$B/hf_20260627_055321_9324c63c-f641-406c-af56-c2d95df0a859.mp4"
)
mkdir -p clips
: > list.txt
i=1
for u in "${urls[@]}"; do
  f=$(printf "clips/scene-%02d.mp4" $i)
  echo "Downloading scene $i..."
  curl -fsSL -o "$f" "$u"
  echo "file '$PWD/$f'" >> list.txt
  i=$((i+1))
done
echo "Stitching -> episode01.mp4"
# Re-encode for safe concat (uniform timebase/audio); use -c copy if all clips match exactly.
ffmpeg -y -f concat -safe 0 -i list.txt -c:v libx264 -c:a aac -movflags +faststart episode01.mp4
echo "Done: episode01.mp4"
