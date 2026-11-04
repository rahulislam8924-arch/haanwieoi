"""Scenes for the Pace promo (Bangla voice-over, 1920x1080).

Every scene is a pure function of (local time, scene duration) returning an SVG
string. Motion vocabulary: expo/spring easings, staggered word reveals, counting
numbers, gradient typography, drifting particles, travelling comets and pulse
rings. The background plate is baked once by the renderer and composited under
the transparent scene SVG, so scenes only draw foreground.
"""
from __future__ import annotations

import math
import random

from kit import *  # noqa
from kit import _gap

W, H = 1920, 1080
M = 150  # left margin
CONTAINER = 1620


# ------------------------------------------------------------------ shared ---
def scene_frame(t, dur, inner, fade=0.30, push=0.012):
    """Returns {svg, opacity}. Adds a slow camera push-in and a dip-to-black at
    the scene edges so cuts feel deliberate rather than abrupt."""
    o = 1.0
    if t < fade:
        o = ease_out(t / fade)
    if t > dur - fade:
        o = min(o, 1.0 - ease_in_out((t - (dur - fade)) / fade))
    return {"svg": svg_doc(chrome(t) + inner, "d"), "opacity": o}


def stage(t, seed=5, dots=True, parts=52, speed=1.0, rings=None):
    """Foreground atmosphere: particles, bokeh rings, faint dot grid."""
    out = [particles(t, n=parts, seed=seed, speed=speed, opacity=0.42)]
    out.append(bokeh(t, n=8, seed=seed + 1))
    if dots:
        out.append(dot_grid(t=t, opacity=0.075))
    for (cx, cy, r, col, per) in (rings or []):
        out.append(pulse_ring(cx, cy, r * 0.55, r, t, period=per, color=col,
                              width=2.0, opacity=0.35))
    return "".join(out)


def kicker(t, label, start=0.2, color=AMBER):
    p = ease_out_expo(seg(t, start, 0.5))
    w = display_width(label, 28, 600)
    return (rect(M, 254, 48 * p, 4, color, rx=2, opacity=1.0) +
            text(M + 64 * p, 268, label, 28, 600, color,
                 opacity=ease_out(seg(t, start + 0.1, 0.4))))


def caption_bar(t, icon_svg, title, sub, y=930, start=1.2, color=MINT, width=CONTAINER):
    """Bottom info bar that slides up."""
    p = ease_out_expo(seg(t, start, 0.7))
    if p <= 0:
        return ""
    dy = (1 - p) * 40
    return group(
        card(M, y + dy, width, 112, opacity=0.92 * p, rx=26, glow=(color, 0.10 * p)) +
        icon_svg(y + dy) +
        text(M + 116, y + dy + 46, title, 34, 700, INK, opacity=p) +
        text(M + 116, y + dy + 84, sub, 25, 400, MUTED, opacity=p),
        opacity=1.0)


# ------------------------------------------------------------------- 1. hook -
HOOK_CHIPS = [("ডাটা কপি-পেস্ট", 1245, 210, -7, CYAN),
              ("ফাইল খোঁজাখুঁজি", 1585, 330, 6, VIOLET),
              ("ম্যানুয়াল এন্ট্রি", 1230, 760, 6, AMBER),
              ("অনুমোদনের অপেক্ষা", 1590, 862, -5, ROSE)]


def scene_hook(t, dur):
    chipset = []
    for i, (label, cx, cy, rot, col) in enumerate(HOOK_CHIPS):
        p = pop(t, 0.45 + i * 0.16, 0.55)
        if p <= 0:
            continue
        tw = display_width(label, 26, 600) + 60
        drift = math.sin(t * 0.8 + i) * 7 - t * 3 + (1 - ease_out_expo(p)) * 90
        chipset.append(
            '<g opacity="%.3f" transform="rotate(%d %.1f %.1f) translate(%.1f,%.1f) '
            'scale(%.3f)"><g transform="translate(%.1f,%.1f) scale(1) translate(%.1f,%.1f)">'
            % (0.9 * clamp(p * 1.6), rot, cx, cy, 0, drift, p, cx, cy, -cx, -cy))
        chipset.append(
            rect(cx - tw / 2, cy - 28, tw, 56, "#101A2D", rx=28,
                 extra='stroke="%s" stroke-width="1.3" stroke-opacity="0.55"' % col))
        chipset.append(circle(cx - tw / 2 + 28, cy, 5.5, col, 0.95))
        chipset.append(text(cx - tw / 2 + 48, cy + 9, label, 26, 500, "#C8D3E6"))
        chipset.append("</g></g>")

    head = kicker(t, "কর্মক্ষমতার গোপন ক্ষতি", 0.25, AMBER)

    l1 = paragraph(M, 360, "প্রতি সপ্তাহে", 74, 600, "#B9C6DA",
                   t=t, start=0.4, stagger=0.09, rise=34, duration=0.6)

    v = ease_out_expo(seg(t, 0.7, 0.7))
    num = counter(10 * ease_out(seg(t, 0.7, 1.3)))
    big = ('<g transform="translate(0,%.1f)" opacity="%.3f">%s</g>' % (
        (1 - v) * 42, v,
        grad_text(M - 6, 572, "%s+ ঘণ্টা" % num, 166, 900, MINT, CYAN,
                  phase=0.5 + 0.35 * math.sin(t * 0.8), spread=0.9)))

    # energy line under the number
    ul = underline_glow(M + 4, 622, display_width("১০+ ঘণ্টা", 166, 900) * 0.86,
                        seg(t, 1.15, 0.7), MINT)

    sub = paragraph(M + 4, 700, "নষ্ট হয় কপি-পেস্ট, ফাইল খোঁজা আর ম্যানুয়াল রিপোর্টে।",
                    48, 500, "#C8D3E6", max_width=1260, t=t, start=1.5, stagger=0.05)

    # strike-through lands after the sentence, on measured ink
    strike = ease_in_out(seg(t, 3.2, 0.55))
    x = M + 4
    hx0 = hx1 = None
    for word in "নষ্ট হয় কপি-পেস্ট".split(" "):
        l, r = ink(word, 48, 500)
        if word == "কপি-পেস্ট":
            hl, hr = ink(word, 48, 800)
            hx0, hx1 = x - l, x - hl + (hr - hl)
        x += (r - l) + _gap(word, 48, 500)
    strike_svg = ""
    if hx0 is not None and strike > 0:
        strike_svg = (line(hx0, 688, hx0 + (hx1 - hx0) * strike, 688, ROSE, 4, 0.9) +
                      circle(hx0 + (hx1 - hx0) * strike, 688, 6, ROSE, 0.9 * strike))

    bar = caption_bar(
        t, lambda yy: (circle(M + 62, yy + 56, 26, MINT, 0.18) +
                       icon_clock(M + 62, yy + 56, 20, MINT)),
        "গড়ে একজন কর্মী সপ্তাহে প্রায় ২ দিন হারান",
        "শুধু পুনরাবৃত্ত কাজে — যা অটোমেট করা যেত", 912, 3.9, MINT)

    inner = stage(t, 5, parts=64, speed=0.8) + "".join(chipset) + head + l1 + big + ul + sub + strike_svg + bar
    return scene_frame(t, dur, inner)


# ---------------------------------------------------------------- 2. problem -
PROBLEM_ROWS = [("ম্যানুয়াল ডাটা এন্ট্রি", 4.2, MINT),
                ("রিপোর্ট বানানো", 3.4, CYAN),
                ("অনুমোদনের জন্য অপেক্ষা", 2.7, VIOLET),
                ("একই ফাইল বারবার খোঁজা", 1.9, AMBER)]


def scene_problem(t, dur):
    title = paragraph(M, 222, "কাজ শেষ হয় ঠিকই —", 62, 700, INK, max_width=1400,
                      t=t, start=0.2, stagger=0.06)
    title2 = paragraph(M, 306, "কিন্তু সময়টা যায় এখানেই।", 62, 700, "#A9B7CE",
                       max_width=1400, t=t, start=0.5, stagger=0.05)

    out = []
    base_x, max_w = 880, 620
    for i, (label, hrs, col) in enumerate(PROBLEM_ROWS):
        y = 476 + i * 96
        p = ease_out_quint(seg(t, 0.8 + i * 0.22, 0.9))
        if p <= 0:
            continue
        out.append(text(M + (1 - p) * -20, y + 26, label, 36, 500, INK,
                        opacity=clamp(p * 1.8)))
        out.append(rect(base_x, y, max_w, 34, "#16203A", rx=17, opacity=0.9 * p))
        bw = (hrs / 5.0) * max_w * p
        out.append(rect(base_x, y, max(bw, 0.01), 34, col, rx=17, opacity=0.95))
        # bright leading edge
        if 0.05 < p < 0.99:
            out.append(circle(base_x + bw, y + 17, 19, col, 0.28))
        out.append(text(base_x + max(bw, 46) + 22, y + 27, "%s ঘণ্টা" % counter(hrs * ease_out(p), 1),
                        30, 700, col, opacity=clamp(p * 1.5)))

    # total card
    tp = pop(t, 2.5, 0.6)
    cy0 = 918
    total = group(
        card(M, cy0, CONTAINER, 112, opacity=0.94 * clamp(tp * 1.4), rx=26,
             glow=(MINT, 0.16 * clamp(tp * 1.4))) +
        circle(M + 62, cy0 + 56, 32, MINT, 0.16 * tp) +
        icon_clock(M + 62, cy0 + 56, 24, MINT) +
        text(M + 118, cy0 + 50, "%s ঘণ্টা" % counter(12 * ease_out(seg(t, 2.6, 1.0))),
             42, 900, MINT, opacity=tp) +
        text(M + 320, cy0 + 48, "প্রতি সপ্তাহে, প্রতি কর্মী", 29, 600, INK, opacity=tp) +
        text(M + 320, cy0 + 84, "যা কেবল পুনরাবৃত্ত কাজেই যাচ্ছে", 24, 400, MUTED,
             opacity=0.9 * tp),
        opacity=1.0)

    inner = stage(t, 9, parts=44) + title + title2 + "".join(out) + total
    return scene_frame(t, dur, inner)


# ------------------------------------------------------------------ 3. intro -
def logo_mark(cx, cy, s, p=1.0, t=0.0, glow=True):
    """Pace mark: three ascending bars + an orbiting dot."""
    bars = []
    for i, hh in enumerate([0.42, 0.72, 1.0]):
        hp = ease_out_back(seg(p, i * 0.13, 0.6), 2.2)
        bh = max(0.01, s * hh * hp)
        bx = cx - s * 0.42 + i * s * 0.34
        bars.append(rect(bx, cy + s * 0.45 - bh, s * 0.20, bh, MINT, rx=s * 0.10,
                         opacity=clamp(hp * 1.6)))
    ring = ''
    if glow:
        ring = (circle(cx + s * 0.58, cy - s * 0.34, s * 0.13, CYAN,
                       opacity=ease_out(seg(p, 0.45, 0.5))) +
                circle(cx + s * 0.58, cy - s * 0.34, s * 0.30, "none",
                       0.25 * ease_out(seg(p, 0.5, 0.5)),
                       extra='stroke="%s" stroke-width="1.6"' % CYAN))
    return "".join(bars) + ring


def scene_intro(t, dur):
    cx, cy = W / 2, 420
    p = seg(t, 0.2, 1.5)
    s = 210
    halo = glow_orb(cx, cy + 40, 560, t, True, 0.55 * ease_in_out(seg(t, 0.15, 1.0)))
    rings = (pulse_ring(cx + 60, cy + 20, 240, 720, t, 2.6, MINT, 2.0, 0.30) +
             pulse_ring(cx + 60, cy + 20, 200, 620, t + 1.1, 2.6, CYAN, 1.4, 0.22))
    mark = logo_mark(cx - 416, cy + 6, s, p, t)

    word_p = ease_out_expo(seg(t, 0.7, 0.9))
    wordmark = ('<g transform="translate(%.1f,0)" opacity="%.3f">%s</g>' % (
        (1 - word_p) * -60, word_p,
        text(cx - 196, cy + 66, "Pace", 168, 800, INK) +
        circle(cx + 244, cy + 22, 13, MINT, ease_out(seg(t, 1.25, 0.4)))))

    bn = ease_out_expo(seg(t, 1.3, 0.6))
    bnname = text(cx, cy + 196, "পেস", 60, 700, MINT, anchor="middle", opacity=bn)

    tag = paragraph(cx, cy + 306, "আপনার কাজের ধারা, এখন অটোপাইলটে।", 56, 700,
                    "#E7EEF9", max_width=1500, anchor="middle", t=t, start=1.95,
                    stagger=0.07, rise=22)

    sub = paragraph(cx, cy + 402, "কোনো কোড নেই। কোনো নতুন সিস্টেম শেখা নেই।", 36, 400,
                    MUTED, max_width=1500, anchor="middle", t=t, start=2.8,
                    stagger=0.04, rise=14)

    inner = (stage(t, 21, parts=90, speed=1.2, rings=[(cx + 60, cy + 20, 620, MINT, 2.6)]) +
             halo + rings + mark + wordmark + bnname + tag + sub)
    return scene_frame(t, dur, inner, push=0.02)


# -------------------------------------------------------------------- 4. how -
STEPS = [("০১", "কানেক্ট করুন", ["Gmail, Sheets, Slack,", "Notion — ২০০+ ইন্টিগ্রেশন"], CYAN),
         ("০২", "সাজিয়ে নিন", ["ট্রিগার আর অ্যাকশন", "ড্র্যাগ করে বসান"], VIOLET),
         ("০৩", "চালু করুন", ["বাকিটা পেস নিজেই", "করে নেবে, ২৪/৭"], MINT)]


def scene_how(t, dur):
    head = paragraph(M, 196, "মাত্র ৩ ধাপে অটোমেশন", 66, 800, INK, max_width=1500,
                     t=t, start=0.15, stagger=0.06)
    head2 = paragraph(M, 268, "কোনো কোড লিখতে হবে না।", 34, 400, MUTED,
                      max_width=1500, t=t, start=0.5, stagger=0.04)

    cw, ch, gap = 500, 400, 60
    x0 = (W - (cw * 3 + gap * 2)) / 2
    y0 = 400
    cards = []
    for i, (num, title, lines, col) in enumerate(STEPS):
        p = pop(t, 0.7 + i * 0.42, 0.6)
        if p <= 0:
            continue
        x = x0 + i * (cw + gap)
        skew = 1.0 - (1 - ease_out_expo(seg(t, 0.7 + i * 0.42, 0.5))) * 0.14
        lift = (1 - ease_out(seg(t, 0.7 + i * 0.42, 0.6))) * 56
        y = y0 + lift
        icx, icy = x + cw - 96, y + 74
        icon = {0: icon_dots(icx, icy, 92, col),
                1: icon_gear(icx, icy - 6, 44, col),
                2: icon_bolt(icx, icy, 84, col)}[i]
        body = [card_shadow(x, y, cw, ch, 30, 0.30), 
                tilt_card(x, y, cw, ch, skew, opacity=0.96, stroke="#2E4066"),
                circle(x + 66, y + 70, 38, col, 0.16),
                text(x + 66, y + 84, num, 36, 800, col, anchor="middle"),
                icon]
        ty = y + ch - 112
        body.append(text(x + 60, ty, title, 48, 700, INK))
        for j, l in enumerate(lines):
            body.append(text(x + 60, ty + 46 + j * 40, l, 27, 400, MUTED))
        cards.append("".join(body))

    wires = []
    for i in range(2):
        x1 = x0 + i * (cw + gap) + cw + 10
        x2 = x0 + (i + 1) * (cw + gap) - 10
        y = y0 + ch / 2
        p = ease_in_out(seg(t, 2.1 + i * 0.22, 0.5))
        if p > 0:
            wires.append(line(x1, y, x1 + (x2 - x1) * p, y, MINT, 3, 0.35 * p))
        if p >= 0.99:
            per = 1.9
            ph = ((t - 2.6) % per) / per
            px = lerp(x1, x2, ease_in_out(ph))
            wires.append(circle(px, y, 8, MINT, 0.95))
            wires.append(circle(px, y, 24, MINT, 0.18))

    # flow strip with steps that light up in order
    fp = ease_out_expo(seg(t, 3.9, 0.7))
    strip = []
    if fp > 0:
        sy = 890
        strip.append(card(M, sy, CONTAINER, 118, opacity=0.92 * fp, rx=24, glow=(CYAN, 0.10 * fp)))
        strip.append(circle(M + 60, sy + 59, 26, MINT, 0.18 * fp))
        strip.append(icon_bolt(M + 60, sy + 59, 44, MINT))
        flow = "নতুন মেইল এলেই  ›  শিটে এন্ট্রি  ›  Slack অ্যালার্ট  ›  রিপোর্ট আপডেট"
        p = ease_out(seg(t, 4.2, 1.1))
        strip.append(text(M + 116, sy + 52, typed(flow, p) if False else flow,
                          32, 600, INK, opacity=fp * (0.35 + 0.65 * p)))
        # a comet sweeping across the flow text
        if fp > 0.2:
            span = display_width(flow, 32, 600)
            ph = ((t - 4.6) % 2.4) / 2.4
            cx = M + 116 + span * ph
            strip.append(circle(cx, sy + 44, 46, "url(#dglow)", 0.5))
        strip.append(text(M + 116, sy + 90, "একবার সেট করুন, বছরের পর বছর চলবে।", 25, 400,
                          MUTED, opacity=fp * 0.9))

    inner = stage(t, 31, parts=40) + head + head2 + "".join(cards) + "".join(wires) + "".join(strip)
    return scene_frame(t, dur, inner)


# ----------------------------------------------------------------- 5. result -
def scene_result(t, dur):
    k = kicker(t, "ফলাফল", 0.15, MINT)
    l1 = paragraph(M, 352, "সপ্তাহে", 74, 900, INK, max_width=900, t=t, start=0.25, stagger=0.06)
    w1 = display_width("সপ্তাহে ", 74, 900)

    from_h = counter(12 * ease_out_quint(seg(t, 0.35, 0.9)))
    to_h = counter(1 * ease_out_quint(seg(t, 1.05, 0.7)))

    x_from = M + w1
    from_txt = grad_text(x_from, 352, from_h + " ঘণ্টা", 74, 900, "#F4F7FB", "#A9C7FF",
                         phase=0.5, spread=0.7)
    wf = display_width(from_h + " ঘণ্টা", 74, 900)
    ax = x_from + wf + 40
    ar = arrow(ax, 328, 92, seg(t, 1.0, 0.6), MINT, 9)
    x_to = ax + 136
    to_txt = grad_text(x_to, 352, to_h + " ঘণ্টা", 74, 900, MINT, CYAN,
                       phase=0.5 + 0.3 * math.sin(t), spread=0.8)

    head2 = paragraph(M, 430, "একই কাজ, এখন ৯০% কম হাতের ছোঁয়া লাগে।", 42, 500,
                      "#C8D3E6", max_width=1500, t=t, start=1.5, stagger=0.04)

    # dashboard
    p = ease_out_expo(seg(t, 1.3, 0.8))
    dx, dy, dw, dh = M, 470, 970, 420
    dash = [card_shadow(dx, dy, dw, dh, 30, 0.30),
            card(dx, dy + (1 - p) * 40, dw, dh, opacity=0.96 * p, rx=30, glow=(CYAN, 0.10 * p))]
    yo = dy + (1 - p) * 40
    dash.append(rect(dx, yo, dw, 72, "#182444", rx=30, opacity=0.92 * p))
    dash.append(rect(dx, yo + 42, dw, 30, "#182444", opacity=0.92 * p))
    for i, c in enumerate([ROSE, AMBER, MINT]):
        dash.append(circle(dx + 40 + i * 28, yo + 36, 8, c, opacity=0.85 * p))
    dash.append(text(dx + 150, yo + 44, "Pace · অটোমেশন ড্যাশবোর্ড", 26, 600, MUTED, opacity=p))
    dash.append(circle(dx + dw - 54, yo + 36, 6, MINT, 0.9 * p))

    heights = [0.35, 0.55, 0.42, 0.78, 0.62, 0.92]
    bw, bg_ = 74, 40
    for i, hh in enumerate(heights):
        bp = ease_out_back(seg(t, 1.7 + i * 0.08, 0.75), 1.4)
        bx = dx + 80 + i * (bw + bg_)
        bh = max(0.01, 196 * hh * bp)
        dash.append(rect(bx, yo + 352 - bh, bw, bh,
                         "url(#dmint)" if i % 2 == 0 else "url(#dviolet)", rx=16, opacity=0.92))
    dash.append(text(dx + 40, yo + 392, "স্বয়ংক্রিয়ভাবে সম্পন্ন হওয়া কাজ", 24, 500,
                     MUTED, opacity=p))

    items = ["সাপ্তাহিক রিপোর্ট নিজে নিজে তৈরি",
             "অনুমোদন সঠিক মানুষের কাছে পৌঁছায়",
             "নতুন কর্মীকে শেখাতে লাগে ১ দিন"]
    cl = []
    for i, s_ in enumerate(items):
        q = pop(t, 2.1 + i * 0.3, 0.5)
        if q <= 0:
            continue
        y = 536 + i * 112
        cl.append(card(1180, y, 590, 96, opacity=0.9 * clamp(q * 1.5), rx=22))
        if i == 2:
            cl.append(circle(1230, y + 48, 26, MINT, 0.18))
            cl.append(icon_bolt(1230, y + 48, 38, MINT))
        else:
            cl.append(icon_check(1230, y + 48, 26, MINT))
        cl.append(text(1276, y + 58, s_, 30, 500, INK, opacity=clamp(q * 1.5)))

    bp2 = pop(t, 3.5, 0.6)
    by0 = 898
    badge = ""
    if bp2 > 0:
        badge = group(
            card(1180, by0, 590, 104, opacity=0.96 * clamp(bp2 * 1.4), rx=24,
                 glow=(MINT, 0.22 * bp2)) +
            text(1206, by0 + 68, "%s%%" % counter(90 * ease_out(seg(t, 3.6, 0.8))),
                 52, 900, MINT) +
            text(1384, by0 + 46, "কম ম্যানুয়াল কাজ", 29, 700, INK) +
            text(1384, by0 + 84, "গড়ে প্রথম মাসেই", 23, 400, MUTED),
            opacity=1.0)

    inner = (stage(t, 41, parts=40) + k + l1 + from_txt + ar + to_txt + head2 +
             "".join(dash) + "".join(cl) + badge)
    return scene_frame(t, dur, inner)


# ---------------------------------------------------------------- 6. social --
def star(cx, cy, r, color=AMBER):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        pts.append("%.2f,%.2f" % (cx + math.cos(ang) * rr, cy + math.sin(ang) * rr))
    return '<polygon points="%s" fill="%s"/>' % (" ".join(pts), color)


def scene_social(t, dur):
    head = paragraph(W / 2, 286, "আর এই মুহূর্তে", 42, 500, MUTED, max_width=1600,
                     anchor="middle", t=t, start=0.15, stagger=0.05)
    head2 = paragraph(W / 2, 380, "৪৫,০০০+ টিম পেস-এর সাথে চলছে", 74, 800, INK,
                      max_width=1700, anchor="middle", t=t, start=0.4, stagger=0.05)

    stats = [(45000, 0, "+", "টিম ব্যবহার করছে", MINT),
             (32, 0, "টি", "দেশে সক্রিয়", CYAN),
             (4.8, 1, "/৫", "গড় রেটিং", AMBER),
             (99.9, 1, "%", "আপটাইম", VIOLET)]
    out = []
    for i, (val, dec, suf, label, col) in enumerate(stats):
        q = pop(t, 0.95 + i * 0.22, 0.55)
        if q <= 0:
            continue
        cx = 300 + i * 440
        out.append(card_shadow(cx - 195, 508, 390, 250, 30, 0.28))
        out.append(rect(cx - 195, 508, 390, 250, "#101A2D", rx=30, opacity=0.9,
                        extra='stroke="%s" stroke-width="1.4" stroke-opacity="%.2f"' % (col, 0.40 * q)))
        cur = val * ease_out_quint(seg(t, 1.0 + i * 0.22, 0.9))
        vs = 96 if len(counter(val, dec)) > 4 else 110
        vw = display_width(counter(cur, dec), vs, 900)
        sw = display_width(suf, 40, 700)
        total = vw + 10 + sw
        x = cx - total / 2
        out.append(text(x, 632, counter(cur, dec), vs, 900, col, opacity=clamp(q * 1.4)))
        out.append(text(x + vw + 10, 632, suf, 40, 700, col, opacity=clamp(q * 1.4)))
        out.append(text(cx, 690, label, 30, 400, MUTED, anchor="middle", opacity=clamp(q * 1.4)))

    # stars under the rating card
    out.append(stars(1280, 560, 5, 11, AMBER, seg(t, 2.0, 1.0)))

    qp = ease_out_expo(seg(t, 2.7, 0.8))
    quote = ""
    if qp > 0:
        quote = group(
            text(W / 2, 872, "“আগে সোমবার মানেই ৬ ঘণ্টার রিপোর্ট ম্যারাথন। এখন সকাল ৯টায় রিপোর্ট রেডি।”",
                 39, 600, INK, anchor="middle") +
            line(W / 2 - 240, 902, W / 2 + 240, 902, MINT, 2, 0.35 * qp) +
            text(W / 2, 942, "— তাহমিদা রহমান, অপারেশনস লিড", 29, 400, MUTED,
                 anchor="middle"),
            opacity=qp)

    inner = stage(t, 51, parts=70, speed=1.1) + head + head2 + "".join(out) + quote
    return scene_frame(t, dur, inner)


# ------------------------------------------------------------------- 7. cta ---
def scene_cta(t, dur):
    cx = W / 2
    halo = glow_orb(cx, 380, 620, t, True, 0.6 * ease_in_out(seg(t, 0.15, 1.0)))
    rings = (pulse_ring(cx + 60, 300, 260, 780, t, 2.4, MINT, 2.0, 0.32) +
             pulse_ring(cx + 60, 300, 220, 660, t + 1.2, 2.4, CYAN, 1.4, 0.22))

    mark = logo_mark(cx - 170, 286, 132, seg(t, 0.1, 1.2), t)
    word_p = ease_out_expo(seg(t, 0.45, 0.8))
    wordmark = ('<g transform="translate(%.1f,0)" opacity="%.3f">%s</g>' % (
        (1 - word_p) * -40, word_p,
        text(cx + 30, 342, "Pace", 110, 800, INK)))

    head = grad_text(cx, 560, "আজই ফ্রি শুরু করুন।", 84, 900, INK, "#B9FFE3",
                     phase=0.5 + 0.35 * math.sin(t * 0.9), spread=1.0, anchor="middle")
    head = group(head, opacity=ease_out(seg(t, 0.75, 0.7)))

    sub = paragraph(cx, 650, "১৪ দিনের ফ্রি ট্রায়াল · কার্ডের দরকার নেই · ২ মিনিটে সেটআপ",
                    37, 500, "#C8D3E6", max_width=1700, anchor="middle",
                    t=t, start=1.15, stagger=0.035, rise=16)

    btn_p = pop(t, 1.65, 0.7)
    button = ""
    if btn_p > 0:
        label = "শুরু করুন — pace.com.bd"
        bw = display_width(label, 42, 700) + 120
        bx = cx - bw / 2
        pulse = 1 + 0.02 * math.sin((t - 1.6) * 4.2) if t > 2.3 else 1.0
        button = ('<g transform="%s">%s%s%s</g>' % (
            scale_about(btn_p * pulse, btn_p * pulse, cx, 800),
            rect(bx - 8, 762, bw + 16, 116, MINT, rx=58, opacity=0.12),
            rect(bx, 770, bw, 100, "url(#dmint)", rx=50, opacity=clamp(btn_p * 1.5)),
            text(cx, 833, label, 42, 700, BG_0, anchor="middle",
                 opacity=clamp(btn_p * 1.5))))

    foot = text(cx, 936, "%s টিম ইতিমধ্যেই ব্যবহার করছে" % counter(45000), 29, 500, MUTED,
                anchor="middle", opacity=ease_out(seg(t, 2.4, 0.7)))

    inner = (stage(t, 61, parts=95, speed=1.3, rings=[(cx + 60, 300, 700, MINT, 2.4)]) +
             halo + rings + mark + wordmark + head + sub + button + foot)
    return scene_frame(t, dur, inner, push=0.02)


SCENES = [
    ("hook", scene_hook),
    ("problem", scene_problem),
    ("intro", scene_intro),
    ("how", scene_how),
    ("result", scene_result),
    ("social", scene_social),
    ("cta", scene_cta),
]
