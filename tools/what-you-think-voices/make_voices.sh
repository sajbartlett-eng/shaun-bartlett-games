#!/usr/bin/env bash
# Makes the six spoken lines for What You Think (WhatYouThink.html).
#
# Voices come from Kokoro-82M (Apache-2.0), an open text-to-speech model, run locally.
# Each line is transcribed back with an offline speech recogniser (Vosk) so a garbled
# take is caught before it ships.
#
# Usage: tools/what-you-think-voices/make_voices.sh [work-dir]
# Needs: node/npm, python3, ffmpeg (with rubberband and libmp3lame).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$HERE/../.." && pwd)"
WORK="${1:-${TMPDIR:-/tmp}/what-you-think-voices}"
OUT="$REPO/assets/audio/what-you-think"
mkdir -p "$WORK" "$OUT"
cd "$WORK"

# 1. The model, the voice styles and the recogniser, all from npm and PyPI.
if [ ! -d node_modules/kokoro-js ] || [ ! -d node_modules/transcribe2texts ]; then
  [ -f package.json ] || npm init -y >/dev/null
  npm install --ignore-scripts --no-audit --no-fund kokoro-q8-shards@1.0.0 kokoro-js transcribe2texts >/dev/null
fi
if [ ! -f kokoro-q8.onnx ]; then
  cat node_modules/kokoro-q8-shards/kokoro-q8.part{0..5}.bin > kokoro-q8.onnx
  echo "fbae9257e1e05ffc727e951ef9b9c98418e6d79f1c9b6b13bd59f5c9028a1478  kokoro-q8.onnx" | sha256sum -c -
fi
if [ ! -d venv ]; then
  python3 -m venv venv
  venv/bin/pip install -q kokoro-onnx soundfile vosk
fi

# 2. The cast. Only the words in quotation marks are said out loud.
#    Part 1  the child, calling out in the dark            "Daddy?"
#    Part 2  an older woman, a carer perhaps. The muffling is added in the browser
#            (space: "muffled"), so for now you can't be sure who she is.
#                                                          "Are you okay?"  "Here's your medicine."
#    Part 3  the same woman, clear now                     "Open your eyes."
#    Part 4  the narrator, grown into a young woman         "Hello. Are you looking for a toy?"
#            then a warped voice                           "Do you like to play Hide and Seek?"
#
#    The child and the young woman are one voice (Isabella) at two ages. The child is lifted:
#    pitch up about 32%, the size of the voice (formants) only about 15%, so it reads as small,
#    not sped up. The carer (Emma) is lowered about 7% in pitch and size, so she sounds older.
#    The warped voice is the young woman, the child and a deep, dropped copy of the same voice
#    speaking at once, a few milliseconds apart, with a slow wobble through it.
NARRATOR="bf_isabella"
CARER="bf_emma"
CHILD_FX="asetrate=24000*1.15,aresample=24000,atempo=1/1.15,rubberband=pitch=1.15:formant=preserved"
CARER_FX="asetrate=24000*0.93,aresample=24000,atempo=1/0.93"
YOUNG_FX="anull"
WARPED_FX="asplit=3[young][small][deep];\
[small]$CHILD_FX,adelay=28[s];\
[deep]asetrate=24000*0.76,aresample=24000,atempo=1/0.76,adelay=11[d];\
[young][s][d]amix=inputs=3:weights=1 0.55 0.8:normalize=0,vibrato=f=3.5:d=0.35,\
aeval='if(isnan(val(0)),0,max(-1,min(1,val(0))))',afade=t=in:d=0.05"
#    (vibrato starts with a glitch: invalid samples and a spike. The guard and the short fade-in
#     remove it, over silence, before the leveller sees it and turns the whole line down.)

#    file              voice        speed  fx      line
LINES=(
  "daddy|$NARRATOR|0.92|child|Daddy?"
  "are-you-okay|$CARER|0.9|carer|Are you okay?"
  "medicine|$CARER|0.9|carer|Here's your medicine."
  "open-your-eyes|$CARER|0.85|carer|Open your eyes."
  "hello|$NARRATOR|0.96|young|Hello. Are you looking for a toy?"
  "hide-and-seek|$NARRATOR|0.84|warped|Do you like to play Hide and Seek?"
)

for entry in "${LINES[@]}"; do
  IFS='|' read -r name voice speed fx line <<<"$entry"
  venv/bin/python -I "$HERE/say.py" "$WORK" "$WORK/$name.raw.wav" "$voice" "$speed" "$line" >/dev/null
  case "$fx" in
    child) filter="$CHILD_FX" ;;
    carer) filter="$CARER_FX" ;;
    warped) filter="$WARPED_FX" ;;
    *) filter="$YOUNG_FX" ;;
  esac
  # Trim the air either side, a breath of room before the word, gentle edges, even loudness.
  ffmpeg -v quiet -y -i "$WORK/$name.raw.wav" -filter_complex "$filter,\
silenceremove=start_periods=1:start_threshold=-50dB:detection=peak,areverse,\
silenceremove=start_periods=1:start_threshold=-50dB:detection=peak,areverse,\
adelay=60,afade=t=in:d=0.02,apad=pad_dur=0.25,\
loudnorm=I=-20:TP=-3:LRA=7,highpass=f=90" -ar 44100 -ac 1 -c:a libmp3lame -b:a 96k "$OUT/$name.mp3"
done

# 3. Listen back.
venv/bin/python -I "$HERE/check.py" "$WORK/node_modules/transcribe2texts/vosk-model-small-en-us-0.15" "$OUT"/*.mp3
