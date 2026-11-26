"""Original tropical/soca track for the Colony Food Market ads (no samples, no copyright issues).
Usage: python3 music.py out.wav [seconds]   (needs numpy + scipy)"""
import numpy as np, wave, sys
from scipy.signal import lfilter, fftconvolve

sr = 44100
total = float(sys.argv[2]) if len(sys.argv) > 2 else 36.0
bpm = 116; beat = 60 / bpm; bar = 4 * beat; s16 = beat / 4
N = int(sr * (total + 2))
rng = np.random.default_rng(7)

def bus(): return np.zeros((N, 2))
dry, verb = bus(), bus()

def add(sig, t, pan=0.5, g=1.0, send=0.0):
    i = int(t * sr)
    if i >= N or t < 0: return
    j = min(N, i + len(sig)); s = sig[:j - i] * g
    l, r = np.cos(pan * np.pi / 2), np.sin(pan * np.pi / 2)
    dry[i:j, 0] += s * l; dry[i:j, 1] += s * r
    if send: verb[i:j, 0] += s * l * send; verb[i:j, 1] += s * r * send

def hz(n): return 440 * 2 ** ((n - 69) / 12)
def tt(d): return np.arange(int(sr * d)) / sr
def lp(x, fc):  # one-pole low-pass
    a = np.exp(-2 * np.pi * fc / sr); return lfilter([1 - a], [1, -a], x)
def hp(x, fc): return x - lp(x, fc)

# ---------- instruments ----------
def steelpan(f, d=1.1):
    t = tt(d); env = np.exp(-t * 3.2) * (1 - np.exp(-t * 600))
    s = (np.sin(2*np.pi*f*t) + .55*np.sin(2*np.pi*2*f*t)*np.exp(-t*2.5)
         + .3*np.sin(2*np.pi*2.98*f*t)*np.exp(-t*6) + .18*np.sin(2*np.pi*4.1*f*t)*np.exp(-t*10)
         + .08*np.sin(2*np.pi*5.4*f*t)*np.exp(-t*16))
    return s * env * .30

def pluck(f, d=.28):  # short guitar-like skank (Karplus-Strong)
    n = int(sr / f); buf = rng.uniform(-1, 1, n); out = np.zeros(int(sr * d))
    for i in range(len(out)):
        out[i] = buf[i % n]; buf[i % n] = .5 * (buf[i % n] + buf[(i + 1) % n]) * .996
    return lp(out, 3500) * np.exp(-tt(d) * 6) * .35

def pad(fs, d):
    t = tt(d); s = np.zeros_like(t)
    for f in fs:
        for det in (-.12, .12):
            ph = (f * (1 + det / 100) * t) % 1; s += 2 * ph - 1
    env = np.minimum(1, t / .4) * np.minimum(1, (d - t) / .3)
    return lp(lp(s, 1400), 1800) * env * .045

def bass(f, d):
    t = tt(d); env = np.minimum(1, t * 400) * np.exp(-t * 2.2)
    s = np.sin(2*np.pi*f*t) + .35*np.tanh(3*np.sin(2*np.pi*f*t))
    return lp(s, 700) * env * .55

def kick():
    t = tt(.35); f = 48 + 110 * np.exp(-t * 28)
    return np.sin(2*np.pi*np.cumsum(f)/sr) * np.exp(-t * 8) * .95 + rng.standard_normal(len(t)) * np.exp(-t*300)*.1

def clap():
    t = tt(.25); n = hp(rng.standard_normal(len(t)), 900)
    env = sum(np.exp(-np.maximum(t - o, 0) * 60) * (t >= o) for o in (0, .011, .022)) * .6 + np.exp(-t * 18) * .4
    return lp(n, 6000) * env * .32

def hat(open_=False):
    d = .22 if open_ else .05; t = tt(d)
    return hp(rng.standard_normal(len(t)), 7000) * np.exp(-t * (14 if open_ else 70)) * .10

def shaker():
    t = tt(.06); return hp(rng.standard_normal(len(t)), 5000) * np.exp(-t * 55) * .05

def conga(high=True):
    t = tt(.3); f0 = 330 if high else 220; f = f0 * (1 + .25 * np.exp(-t * 40))
    s = np.sin(2*np.pi*np.cumsum(f)/sr) * np.exp(-t * (14 if high else 10))
    return (s + hp(rng.standard_normal(len(t)), 2000) * np.exp(-t*120) * .3) * .32

def snare():
    t = tt(.18); return (hp(rng.standard_normal(len(t)), 1500) * .6 + np.sin(2*np.pi*200*t)) * np.exp(-t * 20) * .2

def riser(d):
    t = tt(d); n = rng.standard_normal(len(t)); out = np.zeros_like(n); a = 0.0; st = 0.0
    fc = 300 + 7000 * (t / d) ** 2
    for i in range(0, len(n), 256):
        a = np.exp(-2*np.pi*fc[i]/sr); seg = n[i:i+256]
        y, zf = lfilter([1-a], [1, -a], seg, zi=[st]); out[i:i+256] = y; st = zf[0]
    return (n - out) * (t / d) ** 2 * .12

def crash():
    t = tt(2.0); return hp(rng.standard_normal(len(t)), 4000) * np.exp(-t * 2.2) * .10

# ---------- song ----------
prog = [(48, [60, 64, 67]), (43, [59, 62, 67]), (45, [60, 64, 69]), (41, [60, 65, 69])]  # C G Am F
melA = [[76,None,79,76,74,72,74,76],[74,None,71,74,79,None,None,None],
        [72,None,76,72,81,79,76,72],[74,None,72,69,72,None,None,None]]
melB = [[79,None,79,81,79,76,74,76],[74,None,74,76,74,71,67,None],
        [72,None,76,79,84,None,81,79],[77,None,76,74,72,None,None,None]]
nbars = int(np.ceil(total / bar))
groove_from = 1          # bar 0 is the intro
for b in range(nbars):
    t0 = b * bar; root, ch = prog[b % 4]; full = b >= groove_from
    mel = (melA if (b // 4) % 2 == 0 else melB)[b % 4]
    add(pad([hz(n) for n in ch], bar + .1), t0, .5, 1.0 if full else 1.4, .35)
    for k, n in enumerate(mel):                      # steel pan hook (+ echo)
        if n is None: continue
        sig = steelpan(hz(n)); tk = t0 + k * beat / 2
        add(sig, tk, .58, .95, .35); add(sig, tk + 3 * s16, .25, .30, .3)
    if not full:
        add(riser(bar * .9), t0 + bar * .1, .5, 1.0); continue
    if b == groove_from: add(crash(), t0, .5, 1, .2)
    for k in range(4): add(kick(), t0 + k * beat)
    for k in (1, 3): add(clap(), t0 + k * beat, .5, 1, .3)
    for k in range(8): add(hat(open_=(k % 2 == 1)), t0 + k * beat / 2, .7, 1 if k % 2 else .6)
    for k in range(16): add(shaker(), t0 + k * s16, .3, 1.2 if k % 4 == 2 else .6)
    for k, hi in ((3, True), (6, False), (7, True), (10, True), (11, False), (14, True)):
        add(conga(hi), t0 + k * s16, .2 if hi else .8, 1, .15)
    for o, d, iv in ((0, .7, 0), (1.5, .45, 0), (2.5, .5, 7), (3.5, .4, 12)):   # soca bass
        add(bass(hz(root - 12 + iv), d * beat * 1.6), t0 + o * beat)
    for k in range(4):                                                          # offbeat skank
        for n in ch: add(pluck(hz(n + 12)), t0 + (k + .5) * beat, .35, .55, .1)
    if b % 8 == 7 and b < nbars - 1:                                            # drum fill
        for k in range(8): add(snare(), t0 + 3 * beat + k * s16 / 2, .5, .5 + k * .08, .2)

# final hit
end_t = nbars * bar
if end_t > total - 1:
    pass
add(crash(), max(0, total - 2.6), .5, .8, .3)

# reverb
ir_t = tt(1.8); ir = rng.standard_normal((len(ir_t), 2)) * np.exp(-ir_t * 3.2)[:, None]
ir[:, 0] = lp(ir[:, 0], 5000); ir[:, 1] = lp(ir[:, 1], 5000)
wet = np.stack([fftconvolve(verb[:, c], ir[:, c])[:N] for c in range(2)], 1) * .06
mix = (dry + wet)[:int(sr * total)]

# master: gentle low-end tidy, fades, soft clip, normalise
fi, fo = int(sr * .05), int(sr * 2.8)
mix[:fi] *= np.linspace(0, 1, fi)[:, None]; mix[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
mix /= np.abs(mix).max(); mix = np.tanh(mix * 1.8) / np.tanh(1.8) * .92
with wave.open(sys.argv[1], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr)
    w.writeframes((mix * 32767).astype('<i2').tobytes())
