#!/usr/bin/env python3
"""Render the Pace promo to MP4.

Usage:
  python3 video/render.py --out out/pace-promo-bn.mp4 [--fps 30] [--quick]
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from multiprocessing import Pool

import imageio_ffmpeg
import resvg_py

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kit  # noqa: E402
from scenes import SCENES  # noqa: E402

ROOT = kit.ROOT
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
VO_DIR = os.path.join(ROOT, "assets", "vo")
FPS = 30
LEAD = 0.55
TAIL = 0.75

FONTS = [os.path.join(kit.FONT_DIR, f) for f in sorted(os.listdir(kit.FONT_DIR))
         if f.endswith(".ttf")]

# NOTE: resvg takes one doc at a time; fonts passed explicitly each call.
def render_svg(svg: str) -> bytes:
    return resvg_py.svg_to_bytes(svg_string=svg, font_files=FONTS, skip_system_fonts=True)


_PLATE = None


def plate():
    """baked static background (gradient + glow blobs + grid), 1920x1080"""
    global _PLATE
    if _PLATE is None:
        kit._ensure_sprites()
        from PIL import Image
        _PLATE = Image.open(os.path.join(kit.SPRITE_DIR, "plate.png")).convert("RGB")
        _PLATE.load()
    return _PLATE


def media_duration(path: str) -> float:
    out = subprocess.run([FFMPEG, "-i", path, "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    times = re.findall(r"time=(\d+):(\d+):(\d+\.\d+)", out)
    if not times:
        raise RuntimeError("cannot read duration of %s" % path)
    h, m, s = times[-1]
    return int(h) * 3600 + int(m) * 60 + float(s)


def build_timeline():
    vo_files = sorted(f for f in os.listdir(VO_DIR) if f.endswith(".mp3"))
    assert len(vo_files) == len(SCENES), (vo_files, len(SCENES))
    tl = []
    t = 0.0
    for (name, fn), vf in zip(SCENES, vo_files):
        vo = media_duration(os.path.join(VO_DIR, vf))
        dur = LEAD + vo + TAIL
        tl.append({"name": name, "fn": fn, "vo": os.path.join(VO_DIR, vf),
                   "start": t, "dur": dur})
        t += dur
    return tl, t


def build_music(total: float, out_wav: str) -> str:
    from music import build
    return build(total, out_wav)


def build_audio(tl, out_wav: str):
    """one padded segment per scene, concatenated, so VO lands on the right beat"""
    parts = []
    for i, sc in enumerate(tl):
        part = "/tmp/vo_part_%02d.wav" % i
        cmd = [FFMPEG, "-y", "-v", "error",
               "-f", "lavfi", "-t", "%.3f" % sc["dur"],
               "-i", "anullsrc=r=48000:cl=stereo",
               "-i", sc["vo"],
               "-filter_complex",
               "[1:a]adelay=%d|%d,aformat=sample_rates=48000:channel_layouts=stereo,"
               "volume=1.9,apad[v];[0:a][v]amix=inputs=2:duration=first:dropout_transition=0,"
               "alimiter=limit=0.95[a]" % (int(LEAD * 1000), int(LEAD * 1000)),
               "-map", "[a]", "-t", "%.3f" % sc["dur"], part]
        subprocess.run(cmd, check=True)
        parts.append(part)
    lst = "/tmp/vo_list.txt"
    with open(lst, "w") as f:
        for p in parts:
            f.write("file '%s'\n" % p)
    vo_wav = "/tmp/vo_only.wav"
    subprocess.run([FFMPEG, "-y", "-v", "error", "-f", "concat", "-safe", "0",
                    "-i", lst, "-c:a", "pcm_s16le", vo_wav], check=True)

    # music bed under the narration, ducked and gently filtered
    total = sum(sc["dur"] for sc in tl)
    music_wav = build_music(total, "/tmp/music.wav")
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", vo_wav, "-i", music_wav,
                    "-filter_complex",
                    "[1:a]volume=0.9,highpass=f=60,lowpass=f=6500[m];"
                    "[0:a]volume=1.35[vo];"
                    "[vo][m]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
                    "alimiter=limit=0.95[a]",
                    "-map", "[a]", "-c:a", "pcm_s16le", out_wav], check=True)
    return out_wav


# ------------------------------------------------------------------ frames --
_CTX = {}


def _init(tl):
    _CTX["tl"] = tl


def render_frame(args):
    import io
    from PIL import Image
    idx, t_global = args
    tl = _CTX["tl"]
    for i, sc in enumerate(tl):
        if t_global < sc["start"] + sc["dur"] or i == len(tl) - 1:
            local = t_global - sc["start"]
            shot = sc["fn"](local, sc["dur"])
            fg = Image.open(io.BytesIO(render_svg(shot["svg"]))).convert("RGBA")
            canvas = plate().copy()
            canvas = canvas.convert("RGBA")
            canvas.alpha_composite(fg)
            o = shot["opacity"]
            if o < 0.999:
                dark = Image.new("RGBA", (1920, 1080), (5, 7, 13, 255))
                dark.putalpha(int(round((1.0 - o) * 255)))
                canvas.alpha_composite(dark)
            return canvas.convert("RGB").tobytes()
    raise RuntimeError("no scene at %.2f" % t_global)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "pace-promo-bn.mp4"))
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--preview", default="", help="dir for a few stills")
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()

    tl, total = build_timeline()
    print("timeline:")
    for sc in tl:
        print("  %-8s %6.2fs  starts %6.2fs" % (sc["name"], sc["dur"], sc["start"]))
    print("total %.2fs" % total)

    if args.preview:
        from PIL import Image
        import io
        os.makedirs(args.preview, exist_ok=True)
        base = plate()
        for i, sc in enumerate(tl):
            for k, frac in enumerate([0.22, 0.55, 0.92]):
                lt = max(0.0, min(sc["dur"] - 0.05, sc["dur"] * frac))
                shot = sc["fn"](lt, sc["dur"])
                fg = Image.open(io.BytesIO(render_svg(shot["svg"]))).convert("RGBA")
                img = base.convert("RGBA").copy()
                img.alpha_composite(fg)
                img.convert("RGB").save(
                    os.path.join(args.preview, "%02d_%s_%d.png" % (i, sc["name"], k)))
        print("stills written to", args.preview)

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    wav = "/tmp/pace_audio.wav"
    build_audio(tl, wav)

    n_frames = int(round(total * args.fps))
    tasks = [(i, i / args.fps) for i in range(n_frames)]

    cmd = [FFMPEG, "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", str(args.fps),
           "-i", "-",
           "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", "20",
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart",
           "-c:a", "aac", "-b:a", "192k", "-shortest", args.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    t0 = time.time()
    try:
        with Pool(os.cpu_count() or 4, initializer=_init, initargs=(tl,)) as pool:
            for i, raw in enumerate(pool.imap(render_frame, tasks, chunksize=6)):
                proc.stdin.write(raw)
                if i % 60 == 0:
                    el = time.time() - t0
                    print("  frame %d/%d  (%.1fs)" % (i, n_frames, el), flush=True)
    finally:
        proc.stdin.close()
        proc.wait()
    print("wrote %s in %.1fs" % (args.out, time.time() - t0))


if __name__ == "__main__":
    main()
