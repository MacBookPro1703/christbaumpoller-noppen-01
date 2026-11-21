"""Christbaumpoller – Hintergrundmusik „Feierliche Zufahrt“, Fassung 3 „Engelschor“ (eigene Komposition, Ebbing Project 2026).
Ruhig, meditativ: Chorflächen (Ooh/Aah), schwebender Sopran, tiefes Summen, vereinzelte leise Celesta, Kathedralen-Hall.
Zitat: „Macht hoch die Tür“ (Melodie Halle 1704, gemeinfrei), erste zwei Zeilen im Sopran.
Nahtlose Schleife: 16 Takte à 4,0 s (60 BPM) = 64 s, Nachhall wird an den Anfang gefaltet.
Fassungen: 1 = 96 BPM mit Bläsern (weihnacht_v1.py) · 2 = 80 BPM, Chor führt (weihnacht_v2.py) · 3 = diese (Jörg 20.11. 23:41: „meditativer, engelsgleich“)."""
import numpy as np, wave, sys
from scipy.signal import fftconvolve, butter, sosfiltfilt

SR = 44100
BPM = 60
BEAT = 60 / BPM            # 1,0 s
BAR = 4 * BEAT             # 4,0 s
BARS = 16
LOOP = BARS * BAR          # 64 s
TAIL = 8.0
N = int(SR * (LOOP + TAIL))
L = np.zeros(N); R = np.zeros(N)
rng = np.random.default_rng(11)
NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}


def hz(n):
    return 440 * 2 ** ((NOTE[n[:-1]] + 12 * (int(n[-1]) + 1) - 69) / 12)


def sh(n, o):
    return n[:-1] + str(int(n[-1]) + o)


def add(sig, t0, pan=0.0, gain=1.0):
    i = int(t0 * SR)
    if i < 0:
        sig, i = sig[-i:], 0
    j = min(N, i + len(sig))
    if j <= i:
        return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    L[i:j] += sig[: j - i] * gain * l * 1.41
    R[i:j] += sig[: j - i] * gain * r * 1.41


def swell(n, a, rel, dur):
    """Weiche Hüllkurve: Sinus-Einblendung, Halten, langes Ausklingen – keine Kanten."""
    t = np.arange(n) / SR
    up = np.where(t < a, 0.5 - 0.5 * np.cos(np.pi * np.minimum(t / a, 1)), 1.0)
    down = np.where(t > dur, np.exp(-(t - dur) / rel), 1.0)
    return up * down


def formant(f, vowel):
    # ooh: 350/800 · aah: 680/1100 – Mischung je nach vowel (0 = ooh, 1 = aah)
    g = 0.0
    for fc, bw, a in ((350 + 330 * vowel, 0.22, 1.0), (800 + 300 * vowel, 0.20, 0.5), (2700, 0.12, 0.06)):
        g += a * np.exp(-((np.log(f / fc)) / bw) ** 2)
    return 0.05 + g


def voice(note, dur, vel=1.0, voices=6, vowel=0.4, att=1.6, rel=2.2, fmax=3200):
    f0 = hz(note)
    n = int(SR * (dur + rel * 3))
    t = np.arange(n) / SR
    out = np.zeros(n)
    for v in range(voices):
        det = 1 + rng.normal(0, 0.0035)
        vib = 1 + 0.004 * np.sin(2 * np.pi * (4.2 + 0.8 * rng.random()) * t + rng.random() * 6) * np.minimum(1, t / 1.5)
        drift = 1 + 0.0015 * np.sin(2 * np.pi * 0.13 * t + rng.random() * 6)
        ph = 2 * np.pi * f0 * det * np.cumsum(vib * drift) / SR + rng.random() * 6
        k = 1
        while k * f0 < fmax:
            out += formant(k * f0, vowel) / k ** 1.1 * np.sin(k * ph)
            k += 1
    return out * swell(n, att, rel, dur) * vel / voices * 0.10


def celesta(note, vel=1.0):
    f = hz(note)
    n = int(SR * 4.0)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * f * t) + 0.12 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 4)
    return s * np.exp(-t * 0.9) * (0.5 - 0.5 * np.cos(np.pi * np.minimum(t / 0.02, 1))) * vel * 0.035


# ---------------- Satz ----------------
CH = ["C", "Am", "F", "G", "C", "Am", "F", "G", "C/E", "F", "Dm7", "C", "C", "Am", "F", "Gsus"]
VO = {"C": ["C4", "E4", "G4"], "Am": ["A3", "E4", "A4"], "F": ["F3", "C4", "A4"], "G": ["G3", "D4", "B4"],
      "C/E": ["E3", "C4", "G4"], "Dm7": ["D4", "F4", "C5"], "Gsus": ["G3", "C4", "D4"]}
LOW = {"C": "C3", "Am": "A2", "F": "F2", "G": "G2", "C/E": "E2", "Dm7": "D3", "Gsus": "G2"}
# Sopran-Melodie (eigene Erfindung), (Note, Start in Schlägen ab Taktbeginn, Dauer in Schlägen) – breit und gebunden
MEL = {4: [("G4", 0, 1), ("C5", 1, 1), ("E5", 2, 2)],
       5: [("D5", 0, 1), ("C5", 1, 1), ("A4", 2, 2)],
       6: [("A4", 0, 1), ("C5", 1, 1), ("F5", 2, 2)],
       7: [("E5", 0, 1), ("D5", 1, 3)],
       8: [("E5", 0, 2), ("G5", 2, 2)],
       9: [("F5", 0, 1), ("E5", 1, 1), ("C5", 2, 2)],
       10: [("D5", 0, 2), ("A4", 2, 2)],
       11: [("C5", 0, 4)]}
# Zitat „Macht hoch die Tür …“ (Halle 1704), C-Dur, Stufen 3 5 4 3 2 1 2 3 | 2 5 4 4 3 3 2 1 – je Ton ein Schlag, Schluss lang
ZITAT = [("E5", 0, 1), ("G5", 1, 1), ("F5", 2, 1), ("E5", 3, 1), ("D5", 4, 1), ("C5", 5, 1), ("D5", 6, 1), ("E5", 7, 1),
         ("D5", 8, 1), ("G5", 9, 1), ("F5", 10, 1), ("F5", 11, 1), ("E5", 12, 1), ("E5", 13, 1), ("D5", 14, 2)]

for b, ch in enumerate(CH):
    t0 = b * BAR
    vel = 0.55 + 0.45 * min(1, b / 3)
    for i, nt in enumerate(VO[ch]):                                   # Chorfläche
        add(voice(nt, BAR * 1.05, vel * 0.9, voices=6, vowel=0.25), t0 - 0.3, pan=(-0.5 + i / 2) * 0.7)
    add(voice(LOW[ch], BAR * 1.05, vel * 0.55, voices=4, vowel=0.0, fmax=1500), t0 - 0.3, pan=0.0)   # tiefes Summen
    add(voice(sh(VO[ch][-1], 1), BAR * 1.05, vel * 0.18, voices=4, vowel=0.6, att=2.5), t0 - 0.3, pan=0.35)  # schwebende Höhe
    if b < 4 or b >= 12:                                              # vereinzelte Celesta, sehr leise
        arp = [sh(x, 1) for x in VO[ch]]
        for i, nt in enumerate(arp[:2] if b % 2 else arp[1:]):
            add(celesta(nt, 0.8), t0 + BEAT * (1 + 2 * i) + 0.02 * rng.random(), pan=-0.35 + 0.7 * i)
for b, notes in MEL.items():
    for nt, st, du in notes:
        add(voice(nt, du * BEAT * 1.08, 0.75, voices=7, vowel=0.55, att=0.55, rel=1.4, fmax=3600), b * BAR + st * BEAT - 0.08, pan=-0.05)
for nt, st, du in ZITAT:
    add(voice(nt, du * BEAT * 1.08, 0.7, voices=7, vowel=0.5, att=0.5, rel=1.4, fmax=3600), 12 * BAR + st * BEAT - 0.08, pan=0.05)
    if st % 4 == 0:
        add(celesta(sh(nt, 1), 0.5), 12 * BAR + st * BEAT, pan=0.3)

# ---------------- Kathedralen-Hall ----------------
rt = np.arange(int(SR * 6.0)) / SR
irs = []
for _ in range(2):
    ir = rng.normal(0, 1, len(rt)) * np.exp(-rt / 1.45)
    ir[: int(0.025 * SR)] = 0
    ir = sosfiltfilt(butter(2, 5000, fs=SR, output="sos"), ir)       # dunkler Hall
    irs.append(ir / np.sqrt(np.sum(ir ** 2)))
wet = 0.55
L2 = L * 0.8 + wet * fftconvolve(L, irs[0])[:N]
R2 = R * 0.8 + wet * fftconvolve(R, irs[1])[:N]
n = int(LOOP * SR)
outL, outR = L2[:n].copy(), R2[:n].copy()
outL[: N - n] += L2[n:]
outR[: N - n] += R2[n:]
sos = butter(2, 4500, fs=SR, output="sos")
outL, outR = sosfiltfilt(sos, outL), sosfiltfilt(sos, outR)
st = np.stack([outL, outR], 1)
st = st / np.max(np.abs(st)) * 0.7
out = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/cbp/render/weihnacht.wav"
with wave.open(out, "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((st * 32767).astype(np.int16).tobytes())
print("ok", out, len(st) / SR, "s")
