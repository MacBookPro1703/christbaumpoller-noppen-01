"""Stille Nacht (Franz Xaver Gruber, 1818 – gemeinfrei) als Spieluhr, 23 s."""
import numpy as np, wave
SR = 44100
DUR = 23.0
E8 = 0.235  # Achtel in s
N = {"C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23, "G4": 392.0, "A4": 440.0, "B4": 493.88,
     "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46, "G5": 783.99, "C3": 130.81, "G3": 196.0, "F3": 174.61}
mel = [("G4", 3), ("A4", 1), ("G4", 2), ("E4", 6), ("G4", 3), ("A4", 1), ("G4", 2), ("E4", 6),
       ("D5", 4), ("D5", 2), ("B4", 6), ("C5", 4), ("C5", 2), ("G4", 6),
       ("A4", 4), ("A4", 2), ("C5", 3), ("B4", 1), ("A4", 2), ("G4", 3), ("A4", 1), ("G4", 2), ("E4", 6),
       ("A4", 4), ("A4", 2), ("C5", 3), ("B4", 1), ("A4", 2), ("G4", 3), ("A4", 1), ("G4", 2), ("E4", 6)]
bass = [("C3", 12), ("C3", 12), ("G3", 12), ("C3", 12), ("F3", 12), ("C3", 12), ("F3", 12), ("C3", 12)]
out = np.zeros(int(SR * (DUR + 2)))

def bell(f, t0, amp, dec=1.6):
    n = int(SR * 3.0)
    t = np.arange(n) / SR
    s = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 3)
         + 0.18 * np.sin(2 * np.pi * f * 3.01 * t) * np.exp(-t * 5) + 0.08 * np.sin(2 * np.pi * f * 4.2 * t) * np.exp(-t * 8))
    s *= np.exp(-t * dec) * np.minimum(1, t / 0.004)
    i = int(t0 * SR)
    j = min(len(out), i + n)
    out[i:j] += amp * s[: j - i]

t = 0.9
for nm, l in mel:
    bell(N[nm] * 2, t, 0.30)
    t += l * E8
t = 0.9
for nm, l in bass:
    bell(N[nm] * 2, t, 0.16, dec=1.0)
    bell(N[nm] * 3, t + 3 * E8, 0.07, dec=1.4)
    t += l * E8
# einfacher Hall
y = out.copy()
for d, g in ((0.031, .35), (0.047, .3), (0.083, .22), (0.121, .18), (0.173, .12), (0.241, .09)):
    k = int(d * SR)
    y[k:] += g * out[:-k]
y = y[: int(SR * DUR)]
fade = np.ones_like(y); fl = int(SR * 2.2)
fade[-fl:] = np.linspace(1, 0, fl)
y = y * fade
y = y / np.max(np.abs(y)) * 0.8
st = np.stack([y, np.roll(y, 220) * 0.96], 1)
with wave.open("musik.wav", "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print("ok", len(y) / SR)
