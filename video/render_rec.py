#!/usr/bin/env python3
"""Render the screen-recording style promo, driven by the supplied voice-over.

Usage:
  python3 video/render_rec.py \
      --vo assets/vo_user/user_vo.mp3 \
      --out out/pace-screenrec-bn-v1.mp4 \
      [--fps 30] [--preview stills]

The visuals are cut to fixed beats that line up with the narration; the audio
is the user's own voice-over (loudness-normalised) plus a quiet music bed.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from multiprocessing import Pool

import imageio_ffmpeg
import resvg_py

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import kit  # noqa: E402
import scenes_rec as S  # noqa: E402

ROOT = kit.ROOT
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FONTS = [os.path.join(kit.FONT_DIR, f) for f in sorted(os.listdir(kit.FONT_DIR))
         if f.endswith(".ttf")]

# scene -> start time, aligned to the narration beats in the supplied VO
SCENE_PLAN = [
    ("dash", S.scene_dash, 0.0, [
        (0.6, 2.4, "এক ড্যাশবোর্ডেই পুরো টিমের কাজ"),
        (3.1, 2.6, "সময় বাঁচছে, রিপোর্ট নিজে তৈরি হচ্ছে"),
        (5.8, 2.6, "কে কী করছে — সবই এক নজরে"),
        (8.6, 2.6, "ম্যানুয়াল কাজ কমছে, রান বাড়ছে"),
    ]),
    ("flow", S.scene_flow, 11.6, [
        (0.5, 2.4, "ট্রিগার, শর্ত, অ্যাকশন — সাজিয়ে দিন"),
        (3.1, 2.6, "কোনো কোড নয় — এক ক্লিকে ফ্লো লাইভ"),
        (5.8, 2.4, "প্রতিটা রান লগ হয়ে থাকে"),
        (8.6, 2.4, "একবার সেট, চিরকাল চলবে"),
    ]),
    ("integrations", S.scene_integrations, 21.8, [
        (0.5, 2.6, "২০০+ অ্যাপ — এক ক্লিকে কানেক্ট"),
        (3.3, 2.6, "Gmail, Sheets, Slack, Notion — সব রেডি"),
    ]),
    ("reports", S.scene_reports, 26.9, [
        (0.5, 2.6, "রিপোর্ট নিজে তৈরি হয়, প্রতি সপ্তাহে"),
        (3.2, 2.6, "আর কেউ হাতে রিপোর্ট বানায় না"),
        (6.0, 2.6, "এক ক্লিকে PDF, এক ক্লিকে শেয়ার"),
    ]),
    ("team", S.scene_team, 37.1, [
        (0.5, 2.6, "টিমের সবাই, একই সিস্টেমে"),
        (3.2, 2.8, "রোল অনুযায়ী অ্যাক্সেস — নিয়ন্ত্রণ আপনার হাতে"),
        (6.2, 2.6, "নতুন সদস্য যোগ করুন এক মিনিটে"),
        (9.2, 3.0, "কাজ ভাগ হয়, দায়িত্বও স্পষ্ট"),
        (12.4, 2.4, "সব লগ সংরক্ষিত থাকে"),
    ]),
    ("stats", S.scene_stats, 50.4, [
        (0.6, 3.0, "%s+ টিম ইতিমধ্যেই ব্যবহার করছে" % "৪৫,০০০"),
        (4.0, 3.0, "৩২টি দেশে, প্রতিদিন"),
        (7.2, 3.0, "গড় রেটিং ৪.৮/৫ · ৯৯.৯% আপটাইম"),
    ]),
    ("steps", S.scene_steps, 63.6, [
        (0.6, 3.0, "শুরু করা মাত্র ৩ ধাপ"),
        (3.8, 3.0, "সাইন আপ, কানেক্ট, চালু — ব্যস"),
        (6.8, 3.0, "টিমের সবাই ২ মিনিটেই ঢুকে পড়বে"),
    ]),
    ("close", S.scene_close, 76.8, [
        (0.6, 2.6, "আজই শুরু করুন — pace.com.bd"),
        (3.6, 2.8, "১৪ দিন ফ্রি, কার্ড লাগবে না"),
        (6.6, 2.6, "আজই টিমকে অটোপাইলটে বসান"),
        (9.6, 3.0, "পেস — আপনার কাজের ধারা, এখন অটো"),
    ]),
]

# the closing card repeats the same four beats until the voice-over ends
CLOSE_LOOP = [(0.6, 2.6, "আজই শুরু করুন — pace.com.bd"),
              (3.6, 2.8, "১৪ দিন ফ্রি, কার্ড লাগবে না"),
              (6.6, 2.6, "আজই টিমকে অটোপাইলটে বসান"),
              (9.6, 3.0, "পেস — আপনার কাজের ধারা, এখন অটো")]


def vo_duration(path):
    out = subprocess.run([FFMPEG, "-i", path, "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    times = __import__("re").findall(r"time=(\d+):(\d+):(\d+\.\d+)", out)
    h, m, s = times[-1]
    return int(h) * 3600 + int(m) * 60 + float(s)


def build_timeline(vo_path):
    total_vo = vo_duration(vo_path)
    tail = 2.4
    total = total_vo + tail
    scenes = []
    for i, (name, fn, abs_t, caps) in enumerate(SCENE_PLAN):
        nxt = SCENE_PLAN[i + 1][2] if i + 1 < len(SCENE_PLAN) else total
        dur = nxt - abs_t
        scenes.append({"name": name, "fn": fn, "start": abs_t,
                       "dur": dur, "caps": caps})
    return scenes, total


def wrap_caps(fn, caps):
    """bind the captions list into the scene function"""

    def wrapped(t, dur, _fn=fn, _caps=caps):
        shot = _fn(t, dur)
        extra = "".join(
            S.caption(t, label, st, d, y=976, accent=kit.MINT)
            for (st, d, label) in _caps
        )
        shot["svg"] = shot["svg"].replace("</svg>", extra + "</svg>")
        return shot

    return wrapped


# ------------------------------------------------------------------- frames --
_CTX = {}


def _init(tl):
    _CTX["tl"] = tl


def _plate():
    kit._ensure_sprites()
    from PIL import Image
    return Image.open(os.path.join(kit.SPRITE_DIR, "plate.png")).convert("RGB")


def render_frame(args):
    import io
    from PIL import Image
    idx, t_global = args
    tl = _CTX["tl"]
    for i, sc in enumerate(tl):
        if t_global < sc["start"] + sc["dur"] or i == len(tl) - 1:
            local = max(0.0, t_global - sc["start"])
            shot = sc["fn"](local, sc["dur"])
            fg = Image.open(io.BytesIO(resvg_py.svg_to_bytes(
                svg_string=shot["svg"], font_files=FONTS,
                skip_system_fonts=True))).convert("RGBA")
            canvas = _CTX["plate"].copy().convert("RGBA")
            canvas.alpha_composite(fg)
            o = shot["opacity"]
            if o < 0.999:
                dark = Image.new("RGBA", (1920, 1080), (5, 7, 13, 255))
                dark.putalpha(int(round((1.0 - o) * 255)))
                canvas.alpha_composite(dark)
            return canvas.convert("RGB").tobytes()
    raise RuntimeError("no scene at %.2f" % t_global)


def _frame_init(tl, plate):
    _CTX["tl"] = tl
    _CTX["plate"] = plate


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vo", default=os.path.join(ROOT, "assets", "vo_user", "user_vo.mp3"))
    ap.add_argument("--out", default=os.path.join(ROOT, "out", "pace-screenrec-bn-v1.mp4"))
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--preview", default="")
    ap.add_argument("--crf", default="20")
    args = ap.parse_args()

    scenes, total = build_timeline(args.vo)
    # warm the ink cache once in this process (children inherit it via fork)
    for sc in scenes:
        sc["fn"](0.5, sc["dur"])
    kit._flush_ink_disk()

    tl = [{"name": sc["name"], "fn": wrap_caps(sc["fn"], sc["caps"]),
           "start": sc["start"], "dur": sc["dur"]} for sc in scenes]

    print("timeline (total %.2fs)" % total)
    for sc in tl:
        print("  %-14s %6.2fs  starts %6.2fs" % (sc["name"], sc["dur"], sc["start"]))

    if args.preview:
        from PIL import Image
        import io
        os.makedirs(args.preview, exist_ok=True)
        plate = _plate()
        for sc in tl:
            for k, frac in enumerate([0.25, 0.6, 0.92]):
                lt = max(0.0, min(sc["dur"] - 0.05, sc["dur"] * frac))
                shot = sc["fn"](lt, sc["dur"])
                fg = Image.open(io.BytesIO(resvg_py.svg_to_bytes(
                    svg_string=shot["svg"], font_files=FONTS,
                    skip_system_fonts=True))).convert("RGBA")
                img = plate.convert("RGBA").copy()
                img.alpha_composite(fg)
                img.convert("RGB").save(os.path.join(
                    args.preview, "%s_%d.png" % (sc["name"], k)))
        print("stills ->", args.preview)

    # ---------------- audio: user VO (normalised) + quiet music bed ----------
    wav = "/tmp/rec_audio.wav"
    music = "/tmp/rec_music.wav"
    from music import build as build_music
    build_music(total, music, level=0.10)
    filt = (
        "[0:a]highpass=f=80,lowpass=f=12000,"
        "loudnorm=I=-16:TP=-1.5:LRA=11,volume=1.0[vo];"
        "[1:a]volume=0.9[bed];"
        "[vo][bed]amix=inputs=2:duration=first:dropout_transition=0:normalize=0,"
        "alimiter=limit=0.95,afade=t=out:st=%.2f:d=2.0[a]"
        % (total - 2.0)
    )
    subprocess.run([FFMPEG, "-y", "-v", "error", "-i", args.vo, "-i", music,
                    "-filter_complex", filt, "-map", "[a]",
                    "-t", "%.3f" % total, "-c:a", "pcm_s16le", wav], check=True)

    # ---------------- frames -------------------------------------------------
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    n = int(round(total * args.fps))
    tasks = [(i, i / args.fps) for i in range(n)]
    cmd = [FFMPEG, "-y", "-v", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "1920x1080", "-r", str(args.fps),
           "-i", "-", "-i", wav,
           "-c:v", "libx264", "-preset", "medium", "-crf", args.crf,
           "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart",
           "-c:a", "aac", "-b:a", "192k", "-shortest", args.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    plate = _plate()
    t0 = time.time()
    try:
        with Pool(os.cpu_count() or 2, initializer=_frame_init,
                  initargs=(tl, plate)) as pool:
            for i, raw in enumerate(pool.imap(render_frame, tasks, chunksize=6)):
                proc.stdin.write(raw)
                if i % 120 == 0:
                    print("  frame %d/%d (%.1fs)" % (i, n, time.time() - t0), flush=True)
    finally:
        proc.stdin.close()
        proc.wait()
    print("wrote %s in %.1fs" % (args.out, time.time() - t0))


if __name__ == "__main__":
    main()
