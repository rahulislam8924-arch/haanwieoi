# Pace — SaaS promo video (Bangla)

A 62-second social/marketing ad for **Pace**, a fictional SaaS automation product,
rendered to MP4 with a Bangla voice-over.

**Output:** `out/pace-promo-bn.mp4` — 1920×1080, 30 fps, H.264 + AAC.

## What's in the video

| # | Scene | On screen | Voice-over (Bangla) |
|---|-------|-----------|---------------------|
| 1 | Hook | "প্রতি সপ্তাহে ১০+ ঘণ্টা" + strike-through on কপি-পেস্ট | আপনার টিম কি প্রতি সপ্তাহে দশ ঘণ্টার বেশি সময় নষ্ট করছে… |
| 2 | Problem | Animated bar chart of wasted hours + total card | কাজ শেষ হচ্ছে ঠিকই, কিন্তু সময় চলে যাচ্ছে… |
| 3 | Product intro | Pace logo reveal + tagline | পরিচয় করিয়ে দিচ্ছি — পেস। আপনার কাজের ধারা, এখন অটোপাইলটে। |
| 4 | How it works | 3 step cards + live flow preview strip | ধাপ এক, আপনার সব টুল কানেক্ট করুন… |
| 5 | Result | "সপ্তাহে ১২ ঘণ্টা → ১ ঘণ্টা", dashboard mock | ফলাফল? রিপোর্ট তৈরি হয় নিজে নিজে… |
| 6 | Social proof | 45,000+ teams, 32 countries, 4.8/5, 99.9% | বাংলাদেশ এবং বিশ্বের পঁয়তাল্লিশ হাজার টিম… |
| 7 | CTA | "আজই ফ্রি শুরু করুন" + pace.com.bd button | আজই ফ্রি শুরু করুন। চৌদ্দ দিনের ট্রায়াল… |

Full script with timings: [`video/script_bn.md`](video/script_bn.md)

## Motion & visual design

* **Gradient typography** — headlines and key numbers are filled with an animated
  mint→cyan or white→mint gradient band instead of flat colour.
* **Counting numbers** — ১০+, ১২ ঘণ্টা, ৪৫,০০০, ৯০% and ৯৯.৯% all count up on entry
  (Bangla numerals with thousands separators).
* **Staggered reveals** — every headline arrives word by word with an expo ease and
  a soft rise; cards pop in with a spring overshoot and a slight scale tilt.
* **Living background** — drifting particles, out-of-focus bokeh rings, a faint dot
  grid and slow expanding pulse rings behind the logo.
* **Comet sweep** — a light pulse travels along the flow diagram in "how it works"
  and across the flow strip, so the eye follows the process.
* **Animated arrow + underline** — the ১২ ঘণ্টা → ১ ঘণ্টা arrow draws itself; key
  phrases get a sweeping glow underline; the strikethrough on কপি-পেস্ট snaps in.
* **Brand furniture** — a thin mint accent line with a progress bar sits on top of
  every frame, so the whole spot reads as one piece.
* **Beat-synced edits** — each segment lands on the voice-over (0.55s lead-in,
  0.75s tail), with a 0.3s dip-to-black on the cuts.

## How it's built

No After Effects, no browser — a small Python render pipeline:

```
video/kit.py      SVG drawing kit: colours, easing, text layout, icons, sprites
video/scenes.py   the 7 scenes, pure functions of (t, duration) -> SVG
video/render.py   timeline + audio mix + parallel frame render -> ffmpeg
assets/vo/*.mp3   Bangla voice-over, one clip per scene
assets/fonts/     Noto Sans Bengali (Bengali) + Inter (Latin), renamed for reliability
assets/sprites/   baked background plate (cached, auto-generated)
```

### Typography notes

Bengali does not render correctly if you let the rasteriser split a string into
font runs, and resvg's advance widths for Bengali conjuncts do not match the
ink it draws. So:

* every word is its own `<text>` element (also gives per-word reveal animation);
* Latin runs inside a mixed string are placed with explicit `<tspan x=…>`;
* word positions come from **measured ink boxes** (`kit.ink`), not font advances.

## Re-rendering

```bash
pip install pillow numpy imageio-ffmpeg uharfbuzz fonttools brotli resvg-py
python3 video/render.py --out out/pace-promo-bn.mp4          # full render (~12 min, 2 cores)
python3 video/render.py --preview stills                     # quick PNG stills per scene
```

Anything in `video/scenes.py` can be changed and re-rendered; the audio timeline
follows the voice-over clip lengths automatically, so the visuals stay in sync
with the narration.

> Pace is a made-up product used for this ad. Swap the copy, colours (`kit.py`
> top) and voice-over clips (`assets/vo/`) to reuse the template for a real product.
