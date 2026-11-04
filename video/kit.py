"""Small SVG / typography toolkit used by the video renderer.

Everything is plain functions returning SVG strings, so scenes stay declarative.
Text is laid out manually (word by word) using HarfBuzz shaping, which gives us
correct Bengali advances *and* per-word animation.
"""
from __future__ import annotations

import os
import math
import functools

import uharfbuzz as hb

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")

BENGALI = "BengaliUI"
LATIN = "InterUI"

# ---------------------------------------------------------------- colours ----
BG_0 = "#05070D"
BG_1 = "#0B1220"
BG_2 = "#111C33"
INK = "#F4F7FB"
MUTED = "#93A2BC"
DIM = "#5A6A85"
MINT = "#3DDC97"
CYAN = "#43C3F0"
VIOLET = "#8B7CF6"
AMBER = "#F5B759"
ROSE = "#F2668B"


# ------------------------------------------------------------------ easing ---
def clamp(x, lo=0.0, hi=1.0):
    return max(lo, min(hi, x))


def lerp(a, b, t):
    return a + (b - a) * t


def seg(t, start, dur):
    """normalised 0..1 progress of a sub-timeline"""
    if dur <= 0:
        return 1.0
    return clamp((t - start) / dur)


def ease_out(t):
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t):
    t = clamp(t)
    return 3 * t * t - 2 * t * t * t


def ease_out_back(t, s=1.6):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def fade_out(t, start, dur):
    return 1.0 - ease_in_out(seg(t, start, dur))


# --------------------------------------------------------------- typography --
def is_bengali(s: str) -> bool:
    return any("\u0980" <= ch <= "\u09ff" for ch in s)


def font_file(weight: int, bengali: bool) -> str:
    if bengali:
        w = min([400, 500, 600, 700, 800, 900], key=lambda x: abs(x - weight))
        return os.path.join(FONT_DIR, "BengaliUI-%d.ttf" % w)
    w = min([400, 500, 600, 700, 900], key=lambda x: abs(x - weight))
    return os.path.join(FONT_DIR, "InterUI-%d.ttf" % w)


@functools.lru_cache(maxsize=64)
def _hb_font(path: str):
    blob = hb.Blob.from_file_path(path)
    face = hb.Face(blob)
    return hb.Font(face)


def space_width(size: float, weight: int = 400) -> float:
    """Gap between words. Bengali words are drawn as separate <text> elements
    (per-word animation, and resvg does not reorder clusters across elements),
    so the gap has to be set explicitly."""
    return size * 0.30


def _gap(prev_word: str, size: float, weight: int) -> float:
    g = space_width(size, weight)
    if prev_word and prev_word[-1] in ",.।!?;:":
        g *= 1.45
    return g


@functools.lru_cache(maxsize=20000)
def _advances(text: str, weight: int, size: float):
    bengali = is_bengali(text)
    font = _hb_font(font_file(weight, bengali))
    font.scale = (int(size * 64), int(size * 64))
    buf = hb.Buffer()
    buf.add_str(text)
    buf.guess_segment_properties()
    hb.shape(font, buf, {"kern": True, "liga": True, "clig": True})
    return tuple(p.x_advance / 64.0 for p in buf.glyph_positions)


def text_width(text: str, size: float, weight: int = 400) -> float:
    return sum(_advances(text, weight, size))


def display_width(text: str, size: float, weight: int = 400) -> float:
    """Visual (ink) width of a full string, laid out word by word."""
    if not text:
        return 0.0
    words = text.split(" ")
    total = 0.0
    for i, word in enumerate(words):
        l, r = ink(word, size, weight)
        total += (r - l)
        if i < len(words) - 1:
            total += _gap(word, size, weight)
    return total


def _run_width(text: str, size: float, weight: int) -> float:
    l, r = ink(text, size, weight)
    return r - l


def _runs(s: str):
    """split into (text, is_bengali) runs"""
    out, cur, cur_bn = [], "", None
    for ch in s:
        bn = "\u0980" <= ch <= "\u09ff" or ch in "\u200c\u200d"
        if cur_bn is None or bn == cur_bn:
            cur += ch
            cur_bn = bn
        else:
            out.append((cur, cur_bn))
            cur, cur_bn = ch, bn
    if cur:
        out.append((cur, cur_bn))
    return out


# --- ink metrics -----------------------------------------------------------
# resvg draws Bengali words wider than HarfBuzz's advance (conjuncts overhang),
# so laying words out on advances makes them collide. Every word is measured
# once by rendering it and taking its ink box; layout then anchors on ink.
_INK_PAD = 400
_INK_TOP = 900


def _plain_text_svg(word, size, weight):
    fam = BENGALI if is_bengali(word) else LATIN
    return ('<text x="%d" y="%d" font-family="%s" font-size="%s" font-weight="%d" '
            'fill="#fff">%s</text>' % (_INK_PAD, _INK_TOP, fam, size, weight, esc(word)))


@functools.lru_cache(maxsize=6000)
def ink(word: str, size: float, weight: int):
    """left/right ink extent of a word, relative to a pen at x=0."""
    import io
    import resvg_py
    from PIL import Image
    if not word:
        return (0.0, 0.0)
    body = _plain_text_svg(word, size, weight)
    svg = svg_doc(rect(0, 0, _INK_PAD * 2, _INK_TOP + 300, "#000000") + body)
    png = resvg_py.svg_to_bytes(svg_string=svg, font_files=_font_list(),
                                skip_system_fonts=True)
    img = Image.open(io.BytesIO(png)).convert("L")
    box = img.point(lambda v: 255 if v > 40 else 0).getbbox()
    if not box:
        return (0.0, 0.0)
    l, _, r, _ = box
    return (float(l - _INK_PAD), float(r - _INK_PAD))


def _font_list():
    if not _FONTS:
        _FONTS.extend(os.path.join(FONT_DIR, f) for f in sorted(os.listdir(FONT_DIR))
                      if f.endswith(".ttf"))
    return _FONTS


_FONTS = []


def esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def family_for(text: str) -> str:
    # One family only: mixing families makes resvg split the string into font
    # runs, which breaks Bengali cluster reordering. BengaliUI carries Latin
    # glyphs too, so it is always safe.
    return BENGALI


def _runs_svg(x, y, s, size, weight, fill, opacity, letter_spacing, extra):
    """Draw one word (or no-space chunk): one <text> when the script is pure,
    otherwise explicit tspans, because resvg splits mixed strings into font runs
    itself and that breaks Bengali cluster reordering."""
    runs = _runs(s) if is_bengali(s) else [(s, False)]
    mixed = any(not bn for _, bn in runs) and any(bn for _, bn in runs)
    ls = ' letter-spacing="%s"' % letter_spacing if letter_spacing else ""
    if not mixed:
        return ('<text x="%.2f" y="%.2f" font-family="%s" font-size="%s" font-weight="%d" '
                'fill="%s" opacity="%.3f"%s %s>%s</text>'
                % (x, y, family_for(s), size, weight, fill, opacity, ls, extra, esc(s)))
    out = ['<text y="%.2f" font-size="%s" font-weight="%d" fill="%s" opacity="%.3f"%s %s>'
           % (y, size, weight, fill, opacity, ls, extra)]
    cx = x
    for run, bn in runs:
        fam = BENGALI if bn else LATIN
        out.append('<tspan x="%.2f" font-family="%s">%s</tspan>' % (cx, fam, esc(run)))
        cx += text_width(run, size, weight) if bn else _latin_width(run, size, weight)
    out.append("</text>")
    return "".join(out)


def _runs_svg(x, y, s, size, weight, fill, opacity, letter_spacing, extra):
    """Draw one word: one <text> when the script is pure, otherwise explicit
    tspans, because resvg splits mixed strings into font runs itself and that
    breaks Bengali cluster reordering."""
    runs = _runs(s) if is_bengali(s) else [(s, False)]
    mixed = any(not bn for _, bn in runs) and any(bn for _, bn in runs)
    ls = ' letter-spacing="%s"' % letter_spacing if letter_spacing else ""
    if not mixed:
        return ('<text x="%.2f" y="%.2f" font-family="%s" font-size="%s" font-weight="%d" '
                'fill="%s" opacity="%.3f"%s %s>%s</text>'
                % (x, y, family_for(s), size, weight, fill, opacity, ls, extra, esc(s)))
    out = ['<text y="%.2f" font-size="%s" font-weight="%d" fill="%s" opacity="%.3f"%s %s>'
           % (y, size, weight, fill, opacity, ls, extra)]
    cx = x
    for run, bn in runs:
        fam = BENGALI if bn else LATIN
        out.append('<tspan x="%.2f" font-family="%s">%s</tspan>' % (cx, fam, esc(run)))
        cx += ink(run, size, weight)[1] - ink(run, size, weight)[0]
    out.append("</text>")
    return "".join(out)


def text(x, y, s, size=48, weight=400, fill=INK, anchor="start", opacity=1.0,
         letter_spacing=0.0, extra=""):
    """s is placed so its ink starts at x (anchor=start); words are laid out on
    measured ink boxes so Bengali conjuncts never collide."""
    words = s.split(" ")
    w = display_width(s, size, weight)
    if anchor == "middle":
        cursor = x - w / 2
    elif anchor == "end":
        cursor = x - w
    else:
        cursor = x
    parts = []
    for i, word in enumerate(words):
        l, r = ink(word, size, weight)
        if word:
            parts.append(_runs_svg(cursor - l, y, word, size, weight, fill, opacity,
                                   letter_spacing, extra))
        cursor += (r - l)
        if i < len(words) - 1:
            cursor += _gap(word, size, weight)
    return "".join(parts)


def wrap_lines(s: str, size: float, weight: int, max_width: float):
    """greedy wrap on spaces -> list of (line_text, width)"""
    words = s.split(" ")
    lines, cur, cur_w = [], [], 0.0
    space = space_width(size, weight)
    for w in words:
        ww = display_width(w, size, weight)
        add = ww if not cur else space + ww
        if cur and cur_w + add > max_width:
            lines.append((" ".join(cur), cur_w))
            cur, cur_w = [w], ww
        else:
            cur.append(w)
            cur_w += add
    if cur:
        lines.append((" ".join(cur), cur_w))
    return lines


def paragraph(x, y, s, size=48, weight=400, fill=INK, max_width=1600,
              line_height=1.42, anchor="start", t=999, stagger=0.06,
              duration=0.55, rise=26, opacity=1.0, start=0.0):
    """Word-by-word revealed, wrapped paragraph."""
    lines = wrap_lines(s, size, weight, max_width)
    out = []
    idx = 0
    sp = space_width(size, weight)
    for i, (line, w) in enumerate(lines):
        if anchor == "middle":
            cursor = x - w / 2
        elif anchor == "end":
            cursor = x - w
        else:
            cursor = x
        ly = y + i * size * line_height
        for word in line.split(" "):
            l, r = ink(word, size, weight)
            p = seg(t, start + idx * stagger, duration)
            e = ease_out(p)
            out.append(
                text(cursor - l, ly + (1 - e) * rise, word, size, weight, fill,
                     opacity=opacity * e)
            )
            cursor += (r - l) + _gap(word, size, weight)
            idx += 1
    return "".join(out)


# ------------------------------------------------------------------ shapes ---
def rect(x, y, w, h, fill="none", rx=0, opacity=1.0, extra=""):
    return ('<rect x="%.2f" y="%.2f" width="%.2f" height="%.2f" rx="%.2f" fill="%s" '
            'opacity="%.3f" %s/>' % (x, y, w, h, rx, fill, opacity, extra))


def circle(cx, cy, r, fill="none", opacity=1.0, extra=""):
    return ('<circle cx="%.2f" cy="%.2f" r="%.2f" fill="%s" opacity="%.3f" %s/>'
            % (cx, cy, r, fill, opacity, extra))


def line(x1, y1, x2, y2, stroke=MUTED, width=2, opacity=1.0, dash=None, cap="round"):
    d = ' stroke-dasharray="%s"' % dash if dash else ""
    return ('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" stroke-width="%s" '
            'stroke-linecap="%s" opacity="%.3f"%s/>'
            % (x1, y1, x2, y2, stroke, width, cap, opacity, d))


def path(d, fill="none", stroke="none", width=2, opacity=1.0, extra=""):
    return ('<path d="%s" fill="%s" stroke="%s" stroke-width="%s" opacity="%.3f" '
            'stroke-linecap="round" stroke-linejoin="round" %s/>'
            % (d, fill, stroke, width, opacity, extra))


def group(inner, opacity=1.0, transform=""):
    tr = ' transform="%s"' % transform if transform else ""
    return '<g opacity="%.3f"%s>%s</g>' % (opacity, tr, inner)


def translate(x, y):
    return "translate(%.2f,%.2f)" % (x, y)


def scale_about(sx, sy, cx, cy):
    return "translate(%.2f,%.2f) scale(%.4f,%.4f) translate(%.2f,%.2f)" % (
        cx, cy, sx, sy, -cx, -cy)


# ------------------------------------------------------------- backgrounds ---
def defs_common(prefix="d"):
    return """
<defs>
  <linearGradient id="{p}bg" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="{b0}"/><stop offset="55%" stop-color="{b1}"/>
    <stop offset="100%" stop-color="{b2}"/>
  </linearGradient>
  <linearGradient id="{p}mint" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0%" stop-color="{mint}"/><stop offset="100%" stop-color="{cyan}"/>
  </linearGradient>
  <linearGradient id="{p}violet" x1="0" y1="1" x2="1" y2="0">
    <stop offset="0%" stop-color="{violet}"/><stop offset="100%" stop-color="{cyan}"/>
  </linearGradient>
  <radialGradient id="{p}glow" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="{mint}" stop-opacity="0.55"/>
    <stop offset="100%" stop-color="{mint}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="{p}glowv" cx="50%" cy="50%" r="50%">
    <stop offset="0%" stop-color="{violet}" stop-opacity="0.45"/>
    <stop offset="100%" stop-color="{violet}" stop-opacity="0"/>
  </radialGradient>
  <linearGradient id="{p}fade" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="{b0}" stop-opacity="0.95"/>
    <stop offset="100%" stop-color="{b0}" stop-opacity="0"/>
  </linearGradient>
  <linearGradient id="{p}card" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0%" stop-color="#16203A" stop-opacity="0.92"/>
    <stop offset="100%" stop-color="#0C1424" stop-opacity="0.92"/>
  </linearGradient>
</defs>""".format(p=prefix, b0=BG_0, b1=BG_1, b2=BG_2, mint=MINT, cyan=CYAN, violet=VIOLET)


def background(t, prefix="d", grid=True, drift=1.0):
    """Dark canvas + soft drifting glow blobs + subtle grid."""
    w, h = 1920, 1080
    ax = 1420 + math.sin(t * 0.35 * drift) * 90
    ay = 250 + math.cos(t * 0.29 * drift) * 70
    bx = 380 + math.cos(t * 0.24 * drift + 1.1) * 110
    by = 900 + math.sin(t * 0.31 * drift + 0.4) * 60
    out = [rect(0, 0, w, h, 'url(#%sbg)' % prefix)]
    out.append(circle(ax, ay, 620, 'url(#%sglow)' % prefix, opacity=0.30))
    out.append(circle(bx, by, 560, 'url(#%sglowv)' % prefix, opacity=0.28))
    if grid:
        g = []
        step = 80
        ox = (t * 14) % step
        for x in range(-step, w + step, step):
            g.append(line(x + ox, 0, x + ox, h, "#7E8FAB", 1, 0.045))
        for y in range(0, h + step, step):
            g.append(line(0, y, w, y, "#7E8FAB", 1, 0.045))
        out.append("".join(g))
    # vignette
    out.append(rect(0, 0, w, h, 'url(#%sglow)' % prefix, opacity=0.0))
    return "".join(out)


def vignette(prefix="d"):
    return ('<rect width="1920" height="1080" fill="none"/>')


def svg_doc(inner, prefix="d", w=1920, h=1080):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
        'viewBox="0 0 %d %d">%s%s</svg>' % (w, h, w, h, defs_common(prefix), inner)
    )


# ------------------------------------------------------------------- chips ---
def pill(x, y, label, size=26, weight=600, fill=MINT, text_fill=BG_0, pad=26,
         h=52, opacity=1.0, icon=None):
    tw = display_width(label, size, weight)
    w = tw + pad * 2 + (34 if icon else 0)
    out = [rect(x, y, w, h, fill, rx=h / 2, opacity=opacity)]
    tx = x + pad + (34 if icon else 0)
    out.append(text(tx, y + h / 2 + size * 0.35, label, size, weight, text_fill,
                    opacity=opacity))
    return "".join(out), w


def card(x, y, w, h, prefix="d", opacity=1.0, stroke="#2A3A57", rx=28, fill=None,
         glow=None):
    f = fill if fill else 'url(#%scard)' % prefix
    core = rect(x, y, w, h, f, rx=rx, opacity=opacity,
                extra='stroke="%s" stroke-width="1.6"' % stroke)
    if glow:
        core = rect(x, y, w, h, f, rx=rx, opacity=opacity,
                    extra='stroke="%s" stroke-width="1.6"' % stroke) + \
            rect(x, y, w, h, "none", rx=rx, opacity=glow[1],
                 extra='stroke="%s" stroke-width="6"' % glow[0])
    return core


# ------------------------------------------------------------------- icons ---
def icon_check(cx, cy, r, color=MINT, sw=None):
    return (circle(cx, cy, r, color, 0.16) +
            path("M %.2f %.2f L %.2f %.2f L %.2f %.2f" % (
                cx - r * 0.42, cy + r * 0.02,
                cx - r * 0.10, cy + r * 0.34,
                cx + r * 0.46, cy - r * 0.34),
                stroke=color, width=sw or max(3, r * 0.16)))


def icon_bolt(cx, cy, s, color=MINT):
    return path(
        "M %.2f %.2f L %.2f %.2f L %.2f %.2f L %.2f %.2f L %.2f %.2f L %.2f %.2f Z" % (
            cx + s * .12, cy - s * .55, cx - s * .34, cy + s * .06,
            cx - s * .02, cy + s * .06, cx - s * .16, cy + s * .55,
            cx + s * .36, cy - s * .10, cx + s * .03, cy - s * .10),
        fill=color)


def icon_clock(cx, cy, r, color=CYAN):
    return (circle(cx, cy, r, "none", 1.0,
                   extra='stroke="%s" stroke-width="%.1f"' % (color, max(2.5, r * .17))) +
            path("M %.2f %.2f L %.2f %.2f L %.2f %.2f" % (
                cx, cy - r * .52, cx, cy, cx + r * .38, cy + r * .22),
                stroke=color, width=max(2.5, r * .17)))


def icon_gear(cx, cy, r, color=VIOLET):
    """simple 8-tooth gear approximation"""
    teeth = []
    for i in range(8):
        a0 = i * math.pi / 4
        a1 = a0 + math.pi / 9
        for a in (a0, a1):
            pass
    d = ""
    for i in range(8):
        a = i * math.pi / 4
        x1 = cx + math.cos(a) * r * 0.62
        y1 = cy + math.sin(a) * r * 0.62
        x2 = cx + math.cos(a) * r
        y2 = cy + math.sin(a) * r
        teeth.append('<line x1="%.2f" y1="%.2f" x2="%.2f" y2="%.2f" stroke="%s" '
                     'stroke-width="%.1f" stroke-linecap="round"/>'
                     % (x1, y1, x2, y2, color, r * 0.34))
    return (circle(cx, cy, r * 0.66, "none", 1.0,
                   extra='stroke="%s" stroke-width="%.1f"' % (color, r * 0.24)) +
            "".join(teeth))


def icon_chat(cx, cy, s, color=AMBER):
    return path(
        "M %.2f %.2f h %.2f a %.2f %.2f 0 0 1 %.2f %.2f v %.2f a %.2f %.2f 0 0 1 %.2f %.2f "
        "h %.2f l %.2f %.2f v %.2f h %.2f a %.2f %.2f 0 0 1 %.2f %.2f v %.2f "
        "a %.2f %.2f 0 0 1 %.2f %.2f Z" % (
            cx - s * .5, cy - s * .40, s, s * .12, s * .12, 0, s * .12,
            s * .30, s * .12, s * .12, 0, s * .12,
            -s * .22, -s * .18, -s * .16, -s * .30, -s * .14,
            -s * .10, s * .10, 0, -s * .10, -s * .44,
            s * .10, s * .10, 0, -s * .10, s * .74),
        stroke=color, width=max(3, s * .06))


def icon_dots(cx, cy, s, color=CYAN):
    out = []
    for i, col in enumerate([MINT, CYAN, VIOLET]):
        out.append(circle(cx - s * .5 + i * s * .5, cy, s * .16, col))
    return "".join(out)


# ---------------------------------------------------------------- sprites ----
# Radial-gradient glows are expensive to rasterise every frame, so we bake the
# static canvas + glow sprites once to PNG and composite them as <image>.
import base64
from io import BytesIO

SPRITE_DIR = os.path.join(ROOT, "assets", "sprites")


def _render_png(inner, w, h, name):
    import resvg_py
    from PIL import Image
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
           'viewBox="0 0 %d %d">%s%s</svg>' % (w, h, w, h, defs_common("s"), inner))
    fonts = [os.path.join(FONT_DIR, f) for f in sorted(os.listdir(FONT_DIR))
             if f.endswith(".ttf")]
    data = resvg_py.svg_to_bytes(svg_string=svg, font_files=fonts, skip_system_fonts=True)
    os.makedirs(SPRITE_DIR, exist_ok=True)
    path = os.path.join(SPRITE_DIR, name)
    Image.open(BytesIO(data)).save(path)
    return path


def _ensure_sprites():
    plate = os.path.join(SPRITE_DIR, "plate.png")
    if os.path.exists(plate):
        return
    grid = []
    step = 80
    for x in range(0, 1920 + step, step):
        grid.append(line(x, 0, x, 1080, "#7E8FAB", 1, 0.05))
    for y in range(0, 1080 + step, step):
        grid.append(line(0, y, 1920, y, "#7E8FAB", 1, 0.05))
    inner = (rect(0, 0, 1920, 1080, 'url(#sbg)') +
             circle(1420, 250, 700, 'url(#sglow)', opacity=0.22) +
             circle(380, 900, 640, 'url(#sglowv)', opacity=0.24) +
             "".join(grid))
    _render_png(inner, 1920, 1080, "plate.png")
    glob_inner = circle(400, 400, 400, 'url(#sglow)', opacity=1.0)
    _render_png(glob_inner, 800, 800, "glow_mint.png")
    _render_png(circle(400, 400, 400, 'url(#sglowv)'), 800, 800, "glow_violet.png")


@functools.lru_cache(maxsize=8)
def _img_b64(name):
    _ensure_sprites()
    with open(os.path.join(SPRITE_DIR, name), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def image(name, x, y, w, h, opacity=1.0):
    return ('<image x="%.2f" y="%.2f" width="%.2f" height="%.2f" opacity="%.3f" '
            'preserveAspectRatio="none" href="%s"/>'
            % (x, y, w, h, opacity, _img_b64(name)))


def background_fast(t, drift=1.0):
    """Static baked plate + two drifting glow sprites."""
    out = [image("plate.png", 0, 0, 1920, 1080, 1.0)]
    ax = 900 + math.sin(t * 0.33 * drift) * 260
    ay = -60 + math.cos(t * 0.27 * drift) * 180
    out.append(image("glow_mint.png", ax, ay, 900, 900, 0.30))
    bx = 120 + math.cos(t * 0.23 * drift + 1.2) * 240
    by = 560 + math.sin(t * 0.29 * drift + 0.4) * 200
    out.append(image("glow_violet.png", bx, by, 860, 860, 0.32))
    return "".join(out)
