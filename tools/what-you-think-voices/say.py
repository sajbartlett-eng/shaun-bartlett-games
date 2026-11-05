"""Speak one line with Kokoro. Usage: say.py WORK OUT.wav VOICE SPEED "line"."""
import glob, os, sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

work, out, voice, speed, text = sys.argv[1], sys.argv[2], sys.argv[3], float(sys.argv[4]), sys.argv[5]

# kokoro-js ships each voice style as raw float32 (510 x 256); kokoro-onnx wants them in one .npz.
pack = os.path.join(work, "voices.npz")
if not os.path.exists(pack):
    styles = glob.glob(os.path.join(work, "node_modules/kokoro-js/voices/*.bin"))
    np.savez(pack, **{os.path.basename(p)[:-4]: np.fromfile(p, dtype=np.float32).reshape(510, 1, 256) for p in styles})

kokoro = Kokoro(os.path.join(work, "kokoro-q8.onnx"), pack)
lang = "en-gb" if voice.startswith("b") else "en-us"
samples, rate = kokoro.create(text, voice=voice, speed=speed, lang=lang)
sf.write(out, samples, rate)
