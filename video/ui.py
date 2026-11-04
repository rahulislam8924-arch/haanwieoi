"""UI kit for the screen-recording style promo.

Everything here draws a fake-but-convincing product interface: app window,
sidebar, toolbars, cards, tables, toggles, a cursor that moves and clicks, and
a camera that can pan/zoom into regions with eased keyframes.
"""
from __future__ import annotations

import math
from kit import *  # noqa
from kit import path as kit_path

# ------------------------------------------------------------------ palette --
UI_BG = "#0C1322"
UI_PANEL = "#111C2E"
UI_PANEL_2 = "#16233A"
UI_LINE = "#22304A"
UI_TEXT = "#E8EFFA"
UI_MUTED = "#8FA1BE"
UI_DIM = "#5C6E8C"
UI_ACCENT = MINT
UI_ACCENT_2 = CYAN


def lerp_pt(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def keyframes(t, kfs, ease=ease_in_out):
    """kfs: [(time, value_tuple), ...] -> interpolated tuple"""
    if t <= kfs[0][0]:
        return kfs[0][1]
    for i in range(1, len(kfs)):
        t0, v0 = kfs[i - 1]
        t1, v1 = kfs[i]
        if t <= t1:
            p = ease((t - t0) / max(1e-6, t1 - t0))
            return tuple(lerp(a, b, p) for a, b in zip(v0, v1))
    return kfs[-1][1]


# ------------------------------------------------------------------- window --
def window(x, y, w, h, title="", tabs=None, opacity=1.0, glow=MINT, radius=22,
           toolbar=True, tab_offset=24):
    out = [rect(x + 6, y + 18, w, h, "#000000", rx=radius, opacity=0.35 * opacity),
           rect(x, y, w, h, UI_BG, rx=radius, opacity=opacity,
                extra='stroke="%s" stroke-width="1.6" stroke-opacity="0.55"' % UI_LINE)]
    if toolbar:
        out.append(rect(x, y, w, 58, "#131F33", rx=radius, opacity=opacity))
        out.append(rect(x, y + 36, w, 22, "#131F33", opacity=opacity))
        for i, c in enumerate(["#F2668B", "#F5B759", "#3DDC97"]):
            out.append(circle(x + 30 + i * 22, y + 29, 7, c, 0.85 * opacity))
        # url pill
        out.append(rect(x + w / 2 - 210, y + 14, 420, 30, "#0B1526", rx=15,
                        opacity=0.9 * opacity,
                        extra='stroke="%s" stroke-width="1"' % UI_LINE))
        out.append(circle(x + w / 2 - 190, y + 29, 5, MINT, 0.9 * opacity))
        out.append(text(x + w / 2 - 174, y + 35, title, 17, 500, UI_MUTED,
                        opacity=opacity))
    if tabs:
        ty = y + 58
        out.append(rect(x, ty, w, 46, "#0F1A2B", opacity=opacity))
        out.append(line(x, ty + 46, x + w, ty + 46, UI_LINE, 1, 0.6 * opacity))
        cx = x + tab_offset + 28
        for i, (label, active) in enumerate(tabs):
            tw = display_width(label, 19, 600)
            out.append(rect(cx - 12, ty + 8, tw + 24, 30, "#1B2A44" if active else "none",
                            rx=8, opacity=(0.95 if active else 0) * opacity))
            out.append(text(cx, ty + 29, label, 19, 600 if active else 500,
                            UI_TEXT if active else UI_MUTED, opacity=opacity))
            cx += tw + 52
    return "".join(out)


def sidebar(x, y, w, h, items, active=0, opacity=1.0, t=0.0):
    out = [rect(x, y, w, h, UI_PANEL, rx=0, opacity=opacity)]
    out.append(line(x + w, y, x + w, y + h, UI_LINE, 1, 0.7 * opacity))
    # logo
    out.append(rect(x + 24, y + 24, 26, 26, MINT, rx=8, opacity=opacity))
    out.append(text(x + 62, y + 45, "Pace", 19, 700, UI_TEXT, opacity=opacity))
    iy = y + 92
    for i, label in enumerate(items):
        on = i == active
        if on:
            out.append(rect(x + 14, iy - 20, w - 28, 42, "#1B2B44", rx=12,
                            opacity=0.95 * opacity))
            out.append(rect(x + 14, iy - 20, 3, 42, MINT, rx=2, opacity=opacity))
        out.append(circle(x + 40, iy + 1, 6, MINT if on else UI_DIM, opacity=opacity))
        out.append(text(x + 62, iy + 8, label, 18, 600 if on else 500,
                        UI_TEXT if on else UI_MUTED, opacity=opacity))
        iy += 54
    return "".join(out)


# -------------------------------------------------------------------- pieces --
def stat_tile(x, y, w, h, label, value, delta=None, color=MINT, opacity=1.0, t=0.0,
              chart=None):
    out = [rect(x, y, w, h, UI_PANEL, rx=16, opacity=opacity,
                extra='stroke="%s" stroke-width="1.2"' % UI_LINE),
           text(x + 22, y + 36, label, 17, 500, UI_MUTED, opacity=opacity),
           text(x + 22, y + 84, value, 40, 800, UI_TEXT, opacity=opacity)]
    if delta:
        dw = display_width(delta, 16, 600)
        out.append(rect(x + w - dw - 34, y + 20, dw + 24, 26, color, rx=13,
                        opacity=0.16 * opacity))
        out.append(text(x + w - dw - 22, y + 38, delta, 16, 700, color, opacity=opacity))
    if chart:
        pts = []
        n = len(chart)
        cw = w - 44
        ch = h - 100
        for i, v in enumerate(chart):
            px = x + 22 + cw * i / (n - 1)
            py = y + h - 18 - ch * v
            pts.append((px, py))
        d = "M " + " L ".join("%.1f %.1f" % p for p in pts)
        out.append(kit_path(d, stroke=color, width=3, opacity=0.95 * opacity))
        out.append(kit_path(d + " L %.1f %.1f L %.1f %.1f Z" % (
            pts[-1][0], y + h - 18, pts[0][0], y + h - 18),
            fill=color, opacity=0.10 * opacity))
        out.append(circle(pts[-1][0], pts[-1][1], 5, color, opacity))
    return "".join(out)


def table(x, y, w, headers, rows, opacity=1.0, row_h=46, show=99, t=0.0, start=0.0,
          highlight=None, steps=0.08):
    out = []
    cw = w / len(headers)
    out.append(rect(x, y, w, 38, "#0F1A2B", rx=10, opacity=opacity))
    for i, hd in enumerate(headers):
        out.append(text(x + 18 + i * cw, y + 25, hd, 15, 600, UI_DIM, opacity=opacity))
    for r, row in enumerate(rows[:show]):
        p = ease_out(seg(t, start + r * steps, 0.5))
        if p <= 0:
            continue
        ry = y + 42 + r * row_h
        if highlight is not None and r == highlight:
            out.append(rect(x, ry, w, row_h - 4, "#182B45", rx=10,
                            opacity=0.9 * p * opacity))
        else:
            out.append(rect(x, ry, w, row_h - 4, "#121F33", rx=10,
                            opacity=0.7 * p * opacity))
        out.append(text(x + 18, ry + 27, row[0], 17, 600, UI_TEXT,
                        opacity=p * opacity))
        for i, cell in enumerate(row[1:]):
            col = UI_MUTED
            if isinstance(cell, tuple):
                cell, col = cell
            out.append(text(x + 18 + (i + 1) * cw, ry + 27, cell, 17, 500, col,
                            opacity=p * opacity))
        out.append("")
    return "".join(out)


def toggle(x, y, on, opacity=1.0, w=54, h=30, color=MINT):
    p = on if isinstance(on, float) else (1.0 if on else 0.0)
    knob = lerp(x + h / 2, x + w - h / 2, p)
    return (rect(x, y, w, h, color if p > 0.5 else "#2A3A56", rx=h / 2,
                 opacity=(0.9 if p > 0.5 else 0.8) * opacity) +
            circle(knob, y + h / 2, h / 2 - 4, "#FFFFFF", opacity))


def chip(x, y, label, color=MINT, opacity=1.0, size=15):
    tw = display_width(label, size, 600)
    return (rect(x, y, tw + 26, 28, color, rx=14, opacity=0.16 * opacity) +
            text(x + 13, y + 20, label, size, 600, color, opacity=opacity))


def avatar(x, y, r, label, color=CYAN, opacity=1.0):
    return (circle(x, y, r, color, 0.22 * opacity) +
            circle(x, y, r, "none", opacity,
                   extra='stroke="%s" stroke-width="1.6"' % color) +
            text(x, y + 6, label, r * 0.85, 700, color, anchor="middle", opacity=opacity))


def flow_node(x, y, w, h, title, sub, color=MINT, p=1.0, opacity=1.0, icon=None):
    if p <= 0:
        return ""
    s = pop(p, 0, 0.5) if p < 1 else 1.0
    out = []
    out.append(group(
        rect(x + 4, y + 10, w, h, "#000000", rx=16, opacity=0.3 * opacity) +
        rect(x, y, w, h, "#152238", rx=16, opacity=opacity,
             extra='stroke="%s" stroke-width="1.6" stroke-opacity="0.8"' % color) +
        rect(x, y, 5, h, color, rx=2.5, opacity=opacity) +
        text(x + 24, y + h / 2 - 2, title, 20, 700, UI_TEXT, opacity=opacity) +
        text(x + 24, y + h / 2 + 22, sub, 15, 400, UI_MUTED, opacity=opacity) +
        (icon or ""),
        opacity=s))
    return "".join(out)


def connector(x1, y1, x2, y2, p=1.0, color=MINT, width=3, dash=None, opacity=1.0):
    """elbow wire that draws itself"""
    if p <= 0:
        return ""
    midx = (x1 + x2) / 2
    pts = [(x1, y1), (midx, y1), (midx, y2), (x2, y2)]
    segs = []
    remain = p * 3.0
    for i in range(3):
        a, b = pts[i], pts[i + 1]
        ln = 1.0
        f = clamp(remain)
        if f <= 0:
            break
        segs.append((a, lerp_pt(a, b, f)))
        remain -= 1.0
    out = []
    for a, b in segs:
        out.append(line(a[0], a[1], b[0], b[1], color, width, 0.9 * opacity))
    if p >= 0.999:
        out.append(circle(x2, y2, 5, color, opacity))
    return "".join(out)


# -------------------------------------------------------------------- cursor --
def cursor(t, pathpts, clicks=(), opacity=1.0, scale=1.0):
    """pathpts: [(time,(x,y)),...]; clicks: [(time,(x,y))]. Draws a mac-style
    pointer with a click ripple."""
    x, y = keyframes(t, pathpts)
    out = []
    for ct, (cx, cy) in clicks:
        p = seg(t, ct, 0.5)
        if 0 < p < 1:
            out.append(circle(cx, cy, 10 + 34 * ease_out(p), MINT, 0.35 * (1 - p)))
            out.append(circle(cx, cy, 6 + 18 * ease_out(p), CYAN, 0.25 * (1 - p)))
    s = 1.0 * scale
    out.append(group(
        kit_path("M 0 0 L 0 26 L 7 20 L 12 30 L 17 28 L 12 18 L 21 18 Z",
                 fill="#FFFFFF", stroke="#0A1220", width=2, opacity=1.0),
        opacity=opacity,
        transform="translate(%.2f,%.2f) scale(%.3f)" % (x, y, s)))
    return "".join(out)


def click_ring(t, cx, cy, ct, color=MINT, r=48):
    p = seg(t, ct, 0.55)
    if p <= 0 or p >= 1:
        return ""
    return (circle(cx, cy, 8 + r * ease_out(p), color, 0.45 * (1 - p)) +
            circle(cx, cy, 4 + r * 0.5 * ease_out(p), color, 0.30 * (1 - p)))


# -------------------------------------------------------------------- camera --
def camera(inner, t, kfs, cx_fn=None, cy_fn=None):
    """kfs: [(time, (scale, focus_x, focus_y)), ...] -> eased zoom/pan about focus"""
    s, x, y = keyframes(t, kfs)
    tx = 960 - x * s
    ty = 540 - y * s
    return '<g transform="translate(%.2f,%.2f) scale(%.4f)">%s</g>' % (tx, ty, s, inner)


# ------------------------------------------------------------------ captions --
def caption(t, text_in, start, dur=None, y=980, size=34, color=INK, accent=MINT,
            opacity=1.0, style="pill"):
    """Bangla caption with a slide+fade, sits over the recording."""
    p = ease_out_expo(seg(t, start, 0.45))
    if p <= 0:
        return ""
    out_p = 1.0 - ease_in_out(seg(t, start + (dur or 3.0), 0.35)) if dur else 1.0
    o = p * out_p * opacity
    if o <= 0.01:
        return ""
    w = display_width(text_in, size, 600)
    bw = w + 76
    bx = 960 - bw / 2
    dy = (1 - p) * 26
    if style == "pill":
        return group(
            rect(bx, y + dy, bw, 62, "#070C16", rx=31, opacity=0.78 * o) +
            rect(bx, y + dy, bw, 62, "none", rx=31, opacity=0.5 * o,
                 extra='stroke="%s" stroke-width="1.2"' % UI_LINE) +
            rect(bx + 24, y + dy + 27, 3, 12, accent, rx=1.5, opacity=o) +
            text(bx + 46, y + dy + 40, text_in, size, 600, color, opacity=o),
            opacity=1.0)
    return group(
        rect(bx, y + dy, bw, 62, "#070C16", rx=10, opacity=0.72 * o) +
        text(960, y + dy + 40, text_in, size, 600, color, anchor="middle", opacity=o),
        opacity=1.0)


def rec_badge(t, x=88, y=76, opacity=1.0, label="রেকর্ডিং"):
    """small 'recording' indicator, blink every second"""
    on = 0.55 + 0.45 * math.sin(t * 6.0)
    return (rect(x, y, 152, 40, "#0B1421", rx=20, opacity=0.8 * opacity,
                 extra='stroke="%s" stroke-width="1"' % UI_LINE) +
            circle(x + 24, y + 20, 7, ROSE, on * opacity) +
            text(x + 40, y + 27, label, 16, 600, UI_MUTED, opacity=opacity))
