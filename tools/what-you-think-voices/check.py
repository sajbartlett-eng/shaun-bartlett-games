"""Transcribe each clip back and measure its pitch, so a garbled take is caught."""
import sys, json, wave, subprocess, numpy as np
from vosk import Model, KaldiRecognizer, SetLogLevel
SetLogLevel(-1)
model = Model(sys.argv[1])
for path in sys.argv[2:]:
    pcm = subprocess.run(["ffmpeg","-v","quiet","-i",path,"-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout
    rec = KaldiRecognizer(model, 16000); rec.AcceptWaveform(pcm)
    heard = json.loads(rec.FinalResult())["text"]
    x = np.frombuffer(pcm, np.int16).astype(float)/32768
    # median F0 by autocorrelation over voiced frames
    f0s=[]
    for i in range(0, len(x)-1024, 320):
        fr = x[i:i+1024]*np.hanning(1024)
        if np.sqrt((fr**2).mean()) < 0.02: continue
        ac = np.correlate(fr, fr, 'full')[1023:]
        lo, hi = 16000//500, 16000//80
        lag = lo + np.argmax(ac[lo:hi])
        if ac[lag] > 0.3*ac[0]: f0s.append(16000/lag)
    dur = len(x)/16000
    print(f"{path.split('/')[-1]:34s} {dur:4.2f}s  F0~{int(np.median(f0s)) if f0s else 0:3d}Hz  heard: '{heard}'")
