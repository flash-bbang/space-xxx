"""Synthesize the promo sound track from out/events.json -> out/music.wav (44.1 kHz stereo)."""
import json, os, wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, 'out', 'events.json')))
DUR, EVENTS = data['duration'], data['events']
SR = 44100
N = int(SR * (DUR + 0.5))
mix = np.zeros(N)

def at(name, default=None):
    for e in EVENTS:
        if e[0] == name: return e[1]
    return default

T_COLLAPSE = at('collapse', DUR)
T_LAUNCH = at('launch', DUR)
T_BOOM = at('boom', DUR)
T_END = at('endcard', DUR)
mtof = lambda n: 440.0 * 2 ** ((n - 69) / 12)

def env(n, a=0.005, r=None):
    t = np.arange(n) / SR
    e = np.minimum(1, t / a) if a > 0 else np.ones(n)
    return e * np.exp(-t / (r if r else n / SR / 3))

def osc(kind, f, n, f2=None):
    t = np.arange(n) / SR
    freq = f if f2 is None else f * (f2 / f) ** (t / (n / SR))
    ph = 2 * np.pi * np.cumsum(freq) / SR
    if kind == 'sine': return np.sin(ph)
    if kind == 'square': return np.sign(np.sin(ph)) * 0.6
    if kind == 'saw': return ((ph / np.pi) % 2 - 1) * 0.6
    if kind == 'tri': return 2 / np.pi * np.arcsin(np.sin(ph))
    return np.random.uniform(-1, 1, n)

def add(t0, sig, gain=1.0):
    i = int(t0 * SR)
    if i >= N or i + len(sig) <= 0: return
    j = min(N, i + len(sig))
    mix[max(0, i):j] += sig[max(0, -i):j - i] * gain

def tone(t0, kind, f, dur, gain, r=None, f2=None):
    n = int(dur * SR); add(t0, osc(kind, f, n, f2) * env(n, r=r), gain)

# ---------- background music: C - G - Am - F chiptune (game's own BGM) ----------
BPM = 112; STEP = 60 / BPM / 4
PROG = [[48, 52, 55], [43, 47, 50], [45, 48, 52], [41, 45, 48]]
ARP = [0, 1, 2, 1, 0, 2, 1, 2]
def bgm(t_start, t_stop, space=False):
    step = 0; t = t_start
    while t < t_stop - 0.05:
        bar = (step // 16) % 4; s = step % 16; ch = PROG[bar]
        if s % 4 == 0: tone(t, 'tri', mtof(ch[0] - 12), STEP * 3.2, 0.22 if not space else 0.16)
        if not space:
            if s % 4 == 2: tone(t, 'tri', mtof(ch[0]), STEP * 1.4, 0.10)
            if s % 8 == 0: tone(t, 'sine', 130, 0.16, 0.45, r=0.05, f2=40)
            if s % 4 == 2 or s % 2 == 1: add(t, osc('noise', 0, int(0.04 * SR)) * env(int(0.04 * SR), r=0.01), 0.035)
        if s % 2 == 0:
            n = ch[ARP[s // 2]] + (24 if space else 12)
            tone(t, 'sine' if space else 'square', mtof(n), STEP * (3 if space else 1.6), 0.07 if space else 0.045)
            if space: tone(t + 0.32, 'sine', mtof(n), STEP * 3, 0.03)
        step += 1; t += STEP

bgm(0.0, T_COLLAPSE)
bgm(T_LAUNCH, T_BOOM, space=True)
bgm(T_END, DUR + 0.4)

# ---------- collapse: Schubert "Erlkönig" opening motif (public domain) ----------
tc, tr = T_COLLAPSE, 0.125
tone(tc, 'sine', 80, 1.4, 0.7, r=0.4, f2=25)
for i in range(26):
    tone(tc + 0.15 + i * tr, 'square', mtof(67), 0.1, 0.05); tone(tc + 0.15 + i * tr, 'square', mtof(79), 0.1, 0.03)
for st in (0.15, 2.1):
    for i, n in enumerate([43, 45, 46, 48, 50, 51]): tone(tc + st + i * tr, 'saw', mtof(n), 0.2, 0.12)
    tone(tc + st + 6 * tr, 'saw', mtof(50), 0.7, 0.13)
    tone(tc + st + 6 * tr + 0.75, 'saw', mtof(46), 0.3, 0.12)
    tone(tc + st + 6 * tr + 1.05, 'saw', mtof(43), 0.6, 0.13)

# ---------- effects ----------
for e in EVENTS:
    name, t = e[0], e[1]
    if name == 'floor':
        combo = e[2] if len(e) > 2 else 0
        tone(t, 'square', 440 * 2 ** (min(combo, 12) / 12), 0.09, 0.10 if combo else 0.0)
        if not combo: tone(t, 'tri', 180, 0.07, 0.10)
    elif name == 'start': [tone(t + i * 0.07, 'square', f, 0.09, 0.06) for i, f in enumerate([523, 659, 784])]
    elif name == 'pigeon': tone(t, 'sine', 320, 0.12, 0.15); tone(t + 0.15, 'sine', 270, 0.16, 0.15)
    elif name == 'cutin_pigeon': tone(t, 'square', 90, 0.22, 0.2); add(t, osc('noise', 0, int(.15 * SR)) * env(int(.15 * SR), r=.04), 0.12)
    elif name == 'ajussi': tone(t + 1.0, 'square', 220, 0.25, 0.10); tone(t + 1.2, 'square', 196, 0.3, 0.10)
    elif name == 'cutin_ajussi':
        tone(t, 'tri', 700, 0.15, 0.12, f2=950); tone(t + 0.15, 'tri', 950, 0.3, 0.12, f2=520)   # meow
        tone(t, 'square', 110, 0.15, 0.12)
    elif name == 'cutin_dev': tone(t, 'square', 1046, 0.1, 0.08); tone(t + 0.1, 'square', 1318, 0.15, 0.08)
    elif name == 'cutin_mine': tone(t, 'saw', 220, 0.5, 0.18, f2=40); add(t, osc('noise', 0, int(.4 * SR)) * env(int(.4 * SR), r=.12), 0.25)
    elif name == 'launch': tone(t + 1.3, 'saw', 80, 1.6, 0.12, f2=300)
    elif name == 'boom':
        tone(t, 'sine', 90, 1.4, 0.8, r=0.45, f2=25); add(t, osc('noise', 0, int(1.0 * SR)) * env(int(1.0 * SR), r=0.3), 0.3)
        for i in range(1, 4): tone(t + i * 0.42, 'tri', 700 + i * 180, 0.25, 0.10)
    elif name == 'endcard': [tone(t + i * 0.09, 'square', f, 0.16, 0.07) for i, f in enumerate([523, 659, 784, 1047, 1319])]

# ---------- master: soft limiter, fade out, slight stereo ----------
mix = np.tanh(mix * 1.6) * 0.85
fade = int(0.6 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
d = int(0.012 * SR)
left, right = mix, np.concatenate([np.zeros(d), mix[:-d]]) * 0.95 + mix * 0.05
st = (np.stack([left, right], 1) * 32767).astype(np.int16)
with wave.open(os.path.join(HERE, 'out', 'music.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
print('music.wav', round(N / SR, 2), 's')
