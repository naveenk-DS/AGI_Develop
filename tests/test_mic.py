import sounddevice as sd
import numpy as np

devices = sd.query_devices()
print(f"{'ID':<4} {'Channels':>8}  Name")
print("-" * 60)

for i, d in enumerate(devices):
    ch = d["max_input_channels"]
    if ch < 1:
        continue
    name = d["name"]
    print(f"[{i:<3}] ch={ch}  {name}")
    try:
        audio = sd.rec(
            int(1 * 16000),
            samplerate=16000,
            channels=ch,
            dtype="float32",
            device=i,
        )
        sd.wait()
        audio = audio.mean(axis=1) if ch > 1 else audio.flatten()
        energy = float(np.sqrt(np.mean(audio**2)))
        print(f"       OK — energy={energy:.5f}")
    except Exception as e:
        print(f"       FAILED — {e}")
