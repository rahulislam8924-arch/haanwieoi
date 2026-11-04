"""Tiny procedural music bed (soft pad) so the promo isn't bare voice-over.

Not a song — four slow chords that rise and fall under the narration. Written as
plain numpy synthesis so the whole video stays reproducible from source.
"""
from __future__ import annotations

import numpy as np
import wave

SR = 48000

# Am – F – C – G, two octaves spread, in Hz
CHORDS = [
    [110.00, 164.81, 261.63, 329.63],   # A2 E3 C4 E4
    [87.31, 174.61, 261.63, 349.23],    # F2 F3 C4 F4
    [130.81, 196.00, 329.63, 392.00],   # C3 G3 E4 G4
    [98.00, 196.00, 293.66, 392.00],    # G2 G3 D4 G4
]

BAR = 4.0  # seconds per chord


def _tone(freq: float, dur: float, detune: float = 0.0) -> np.ndarray:
    n = int(SR * dur)
    t = np.arange(n) / SR
    f = freq * (1.0 + detune)
    # soft saw-ish pad: few harmonics, 1/n amplitude
    sig = np.zeros(n)
    for h, amp in [(1, 1.0), (2, 0.32), (3, 0.14), (4, 0.07)]:
        sig += amp * np.sin(2 * np.pi * f * h * t + h * 0.7)
    return sig


def _envelope(dur: float, attack: float = 1.1, release: float = 1.4) -> np.ndarray:
    n = int(SR * dur)
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    r = np.clip((dur - t) / release, 0, 1)
    # smoothstep for a soft swell
    a = a * a * (3 - 2 * a)
    r = r * r * (3 - 2 * r)
    return a * r


def build(total: float, out_path: str, level: float = 0.14) -> str:
    n = int(SR * total)
    left = np.zeros(n)
    right = np.zeros(n)
    bar = 0
    pos = 0.0
    while pos < total:
        chord = CHORDS[bar % len(CHORDS)]
        dur = min(BAR + 1.2, total - pos + 1.2)  # overlap slightly for crossfade
        env = _envelope(dur)
        buf_l = np.zeros(int(SR * dur))
        buf_r = np.zeros(int(SR * dur))
        for i, f in enumerate(chord):
            pan = 0.5 + 0.16 * np.sin(i * 1.7 + bar)
            amp = 0.28 / (1 + 0.35 * i)
            buf_l += _tone(f, dur, detune=+0.0012) * amp * (1 - pan)
            buf_r += _tone(f, dur, detune=-0.0012) * amp * pan
        # octave shimmer, very low
        buf_l += _tone(chord[0] * 4, dur, detune=0.002) * 0.02
        buf_r += _tone(chord[1] * 4, dur, detune=-0.002) * 0.02
        start = int(SR * pos)
        seg = min(len(buf_l), n - start)
        if seg > 0:
            left[start:start + seg] += (buf_l * env)[:seg]
            right[start:start + seg] += (buf_r * env)[:seg]
        pos += BAR
        bar += 1

    # gentle overall shape: fade in / out across the whole spot
    t = np.arange(n) / SR
    master = np.clip(t / 2.0, 0, 1) * np.clip((total - t) / 2.5, 0, 1)
    stereo = np.stack([left * master, right * master], axis=1)
    peak = np.max(np.abs(stereo)) or 1.0
    stereo = stereo / peak * level
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2")
    with wave.open(out_path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())
    return out_path
