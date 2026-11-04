"""Scene definitions for the Pace promo (Bangla voice-over, 1920x1080)."""
from __future__ import annotations

import math

from kit import *  # noqa

W, H = 1920, 1080
M = 150  # left margin


def scene_frame(t, dur, inner, prefix="d", fade=0.32):
    """Returns the frame: transparent-background SVG (foreground only) plus the
    opacity used for the dip-to-black transition, composited by the renderer."""
    o = 1.0
    if t < fade:
        o = ease_out(t / fade)
    if t > dur - fade:
        o = min(o, 1.0 - ease_in_out((t - (dur - fade)) / fade))
    return {"svg": svg_doc(inner, prefix), "opacity": o}


# ---------------------------------------------------------------- 1. hook ----
def scene_hook(t, dur):
    chips = [("ডাটা কপি", 1210, 200, -8), ("ফাইল খোঁজা", 1560, 320, 6),
             ("ম্যানুয়াল এন্ট্রি", 1150, 840, 7), ("অনুমোদনের অপেক্ষা", 1520, 960, -5)]
    bgchips = []
    for i, (label, cx, cy, rot) in enumerate(chips):
        p = seg(t, 0.5 + i * 0.18, 0.9)
        e = ease_out(p)
        op = 0.13 * e
        tw = display_width(label, 26, 500)
        w = tw + 56
        bgchips.append(
            '<g opacity="%.3f" transform="rotate(%d %.2f %.2f) translate(0,%.1f)">%s%s</g>'
            % (op, rot, cx, cy, (1 - e) * 40 - t * 6,
               rect(cx - w / 2, cy - 30, w, 60, "#101A2D", rx=30,
                    extra='stroke="#2A3A57" stroke-width="1.2"'),
               text(cx, cy + 9, label, 26, 500, MUTED, anchor="middle")))

    k = ease_out(seg(t, 0.3, 0.6))
    kicker = (rect(M, 244, 46, 4, AMBER, rx=2, opacity=k) +
              text(M + 62, 258, "কর্মক্ষমতার গোপন ক্ষতি", 28, 600, AMBER, opacity=k))

    h1 = text(M, 372, "প্রতি সপ্তাহে", 76, 600, "#B9C6DA",
              opacity=ease_out(seg(t, 0.45, 0.6)))

    v = ease_out(seg(t, 0.75, 0.9))
    big = ('<g transform="translate(0,%.1f)">%s</g>' % (
        (1 - v) * 34,
        text(M - 6, 580, "১০+ ঘণ্টা", 168, 900, MINT, opacity=v)))

    h3 = paragraph(M + 4, 706, "নষ্ট হয় কপি-পেস্ট, ফাইল খোঁজা আর ম্যানুয়াল রিপোর্টে।",
                   50, 500, "#C8D3E6", max_width=1300, t=t, start=1.6, stagger=0.05)

    strike = ease_in_out(seg(t, 3.3, 0.6))
    phrase = "নষ্ট হয় কপি-পেস্ট"
    sp = space_width(50, 500)
    x = M + 4
    hit_x0 = hit_x1 = None
    for word in phrase.split(" "):
        l, r = ink(word, 50, 500)
        if word == "কপি-পেস্ট":
            hl, hr = ink(word, 50, 700)
            hit_x0, hit_x1 = x - l, x - hl + (hr - hl)
        x += (r - l) + sp
    strikeline = line(hit_x0, 694, hit_x0 + (hit_x1 - hit_x0) * strike, 694,
                      ROSE, 4, 0.85 * strike) if hit_x0 is not None else ""

    foot = ease_out(seg(t, 4.2, 0.8))
    footline = group(
        rect(M, 812, 5, 70, 'url(#dmint)', rx=2.5, opacity=foot) +
        text(M + 28, 845, "গড়ে একজন কর্মী সপ্তাহে প্রায় ২ দিন হারান", 32, 600,
             INK, opacity=foot) +
        text(M + 28, 882, "শুধু পুনরাবৃত্ত কাজে", 27, 400, MUTED, opacity=foot),
        opacity=1.0)

    inner = ("".join(bgchips) + kicker + h1 + big + h3 +
             strikeline + footline)
    return scene_frame(t, dur, inner)


# ------------------------------------------------------------- 2. problem ----
def scene_problem(t, dur):
    title = paragraph(M, 228, "কাজ শেষ হয় ঠিকই —", 64, 700, INK, max_width=1400,
                      t=t, start=0.25, stagger=0.06)
    title2 = paragraph(M, 312, "কিন্তু সময়টা যায় এখানেই।", 64, 700, "#A9B7CE",
                       max_width=1400, t=t, start=0.55, stagger=0.05)

    rows = [("ম্যানুয়াল ডাটা এন্ট্রি", 4.2, MINT),
            ("রিপোর্ট বানানো", 3.4, CYAN),
            ("অনুমোদনের জন্য অপেক্ষা", 2.7, VIOLET),
            ("একই ফাইল বারবার খোঁজা", 1.9, AMBER)]
    out = []
    base_x = 900
    max_w = 620
    for i, (label, hrs, col) in enumerate(rows):
        y = 480 + i * 104
        p = ease_out(seg(t, 0.9 + i * 0.28, 0.85))
        out.append(text(M, y + 26, label, 36, 500, INK, opacity=clamp(p * 1.6)))
        # track
        out.append(rect(base_x, y, max_w, 34, "#16203A", rx=17, opacity=0.9 * p))
        bw = (hrs / 5.0) * max_w * p
        out.append(rect(base_x, y, max(bw, 0.01), 34, col, rx=17, opacity=0.95 * p))
        val = hrs * p
        out.append(text(base_x + max(bw, 40) + 22, y + 27,
                        "%.1f ঘণ্টা" % val, 30, 700, col,
                        opacity=clamp(p * 1.4)))

    total = ease_out(seg(t, 2.4, 1.0))
    cy0 = 908
    total_card = group(
        card(M, cy0, 1620, 120, opacity=0.92 * total, rx=26,
             glow=(MINT, 0.12 * total)) +
        icon_clock(M + 72, cy0 + 60, 30, MINT) +
        text(M + 132, cy0 + 54, "সপ্তাহে মোট ১২+ ঘণ্টা", 42, 800, INK,
             opacity=total) +
        text(M + 132, cy0 + 94, "একজন কর্মীর পিছনে, শুধু পুনরাবৃত্ত কাজে",
             26, 400, MUTED, opacity=total),
        opacity=1.0)

    inner = title + title2 + "".join(out) + total_card
    return scene_frame(t, dur, inner)


# --------------------------------------------------------------- 3. intro ----
def logo_mark(cx, cy, s, p=1.0, t=0.0):
    """Pace mark: three ascending rounded bars + orbit ring."""
    bars = []
    heights = [0.42, 0.72, 1.0]
    for i, hh in enumerate(heights):
        hp = ease_out(seg(p, i * 0.16, 0.55))
        bh = s * hh * hp
        bx = cx - s * 0.42 + i * s * 0.34
        bars.append(rect(bx, cy + s * 0.45 - bh, s * 0.20, bh, MINT, rx=s * 0.10,
                         opacity=clamp(hp * 1.4)))
    ring = circle(cx + s * 0.58, cy - s * 0.34, s * 0.13, CYAN,
                  opacity=ease_out(seg(p, 0.5, 0.5)))
    return "".join(bars) + ring


def scene_intro(t, dur):
    cx, cy = W / 2, 430
    p = seg(t, 0.25, 1.5)
    s = 210
    mark = logo_mark(cx - 416, cy + 6, s, p, t)

    word = ease_out(seg(t, 0.75, 0.8))
    wordmark = ('<g transform="translate(%.1f,0)">%s</g>' % (
        (1 - word) * -40,
        text(cx - 196, cy + 66, "Pace", 168, 800, INK, opacity=word) +
        circle(cx + 244, cy + 22, 13, MINT, opacity=word)))

    bn = ease_out(seg(t, 1.35, 0.7))
    bnname = text(cx, cy + 190, "পেস", 62, 700, MINT, anchor="middle", opacity=bn)

    tag = paragraph(cx, cy + 300, "আপনার কাজের ধারা, এখন অটোপাইলটে।", 56, 600,
                    "#C8D3E6", max_width=1500, anchor="middle", t=t, start=2.1,
                    stagger=0.06)

    sub = paragraph(cx, cy + 400, "কোনো কোড নেই। কোনো নতুন সিস্টেম শেখা নেই।", 38, 400,
                    MUTED, max_width=1500, anchor="middle", t=t, start=2.9,
                    stagger=0.04)

    # soft halo behind logo
    halo = circle(cx - 60, cy + 20, 520, "url(#dglow)",
                  opacity=0.55 * ease_in_out(seg(t, 0.2, 1.2)))

    inner = halo + mark + wordmark + bnname + tag + sub
    return scene_frame(t, dur, inner)


# ----------------------------------------------------------------- 4. how ----
def step_card(x, y, w, h, num, title, sub, color, p, icon):
    o = clamp(p * 1.5)
    lift = (1 - ease_out(p)) * 46
    inner = (card(x, y + lift, w, h, opacity=0.95 * o, rx=30,
                  stroke="#2C3E60", glow=(color, 0.10 * o)) +
             circle(x + 74, y + lift + 78, 40, color, 0.14 * o) +
             text(x + 74, y + lift + 92, num, 40, 800, color, anchor="middle", opacity=o) +
             icon +
             text(x + 74, y + lift + 190, title, 46, 700, INK, opacity=o) +
             text(x + 74, y + lift + 244, sub, 30, 400, MUTED, opacity=o))
    return inner


def scene_how(t, dur):
    head = paragraph(M, 200, "মাত্র ৩ ধাপে অটোমেশন", 68, 800, INK, max_width=1500,
                     t=t, start=0.2, stagger=0.06)
    head2 = paragraph(M, 272, "কোনো কোড লিখতে হবে না।", 36, 400, MUTED,
                      max_width=1500, t=t, start=0.6, stagger=0.04)

    cw, ch, gap = 500, 400, 60
    x0 = (W - (cw * 3 + gap * 2)) / 2
    y0 = 400
    steps = [
        ("০১", "কানেক্ট করুন", "Gmail, Sheets, Slack,\nNotion — ২০০+ ইন্টিগ্রেশন", CYAN),
        ("০২", "সাজিয়ে নিন", "ট্রিগার আর অ্যাকশন\nড্র্যাগ করে বসান", VIOLET),
        ("০৩", "চালু করুন", "বাকিটা পেস নিজেই\nকরে নেবে, ২৪/৭", MINT),
    ]
    cards = []
    for i, (num, title, sub, col) in enumerate(steps):
        x = x0 + i * (cw + gap)
        p = seg(t, 0.8 + i * 0.55, 0.75)
        icx, icy = x + cw - 96, y0 + 62 + (1 - ease_out(p)) * 46
        if i == 0:
            icon = icon_dots(icx, icy, 92, col)
        elif i == 1:
            icon = icon_gear(icx, icy - 6, 44, col)
        else:
            icon = group(icon_bolt(icx, icy, 84, col))
        lines = [l for l in sub.split("\n")]
        body = (card(x, y0 + (1 - ease_out(p)) * 46, cw, ch, opacity=0.95 * clamp(p * 1.5),
                     rx=30, stroke="#2C3E60", glow=(col, 0.10 * clamp(p * 1.5))) +
                circle(x + 66, y0 + (1 - ease_out(p)) * 46 + 70, 38, col,
                       0.14 * clamp(p * 1.5)) +
                text(x + 66, y0 + (1 - ease_out(p)) * 46 + 84, num, 36, 800, col,
                     anchor="middle", opacity=clamp(p * 1.5)) +
                icon)
        ty = y0 + ch - 108 + (1 - ease_out(p)) * 46
        body += text(x + 60, ty, title, 48, 700, INK, opacity=clamp(p * 1.5))
        for j, l in enumerate(lines):
            body += text(x + 60, ty + 48 + j * 40, l, 28, 400, MUTED,
                         opacity=clamp(p * 1.5))
        cards.append(body)

    # connecting wires with travelling pulse
    wires = []
    for i in range(2):
        x1 = x0 + i * (cw + gap) + cw + 8
        x2 = x0 + (i + 1) * (cw + gap) - 8
        y = y0 + ch / 2
        p = ease_in_out(seg(t, 2.3 + i * 0.25, 0.5))
        wires.append(line(x1, y, x1 + (x2 - x1) * p, y, MINT, 3, 0.45 * p))
        if p >= 0.99:
            per = 2.0
            ph = ((t - 2.8) % per) / per
            px = lerp(x1, x2, ph)
            wires.append(circle(px, y, 9, MINT, opacity=0.95))
            wires.append(circle(px, y, 22, "url(#dglow)", opacity=0.7))

    # live flow preview strip
    fp = ease_out(seg(t, 4.4, 0.9))
    strip = group(
        card(M, 900, 1620, 118, opacity=0.9 * fp, rx=24) +
        circle(M + 60, 959, 26, MINT, 0.18 * fp) +
        icon_bolt(M + 60, 959, 44, MINT) +
        text(M + 116, 950, "নতুন মেইল এলেই   ›   শিটে এন্ট্রি   ›   Slack অ্যালার্ট   ›   রিপোর্ট আপডেট",
             33, 600, INK, opacity=fp) +
        text(M + 116, 990, "একবার সেট করুন, বছরের পর বছর চলবে।", 26, 400, MUTED,
             opacity=fp * 0.9),
        opacity=1.0)

    inner = head + head2 + "".join(cards) + "".join(wires) + strip
    return scene_frame(t, dur, inner)


# -------------------------------------------------------------- 5. result ----
def scene_result(t, dur):
    kicker = text(M, 210, "ফলাফল", 30, 700, MINT,
                  opacity=ease_out(seg(t, 0.2, 0.5)))
    head = paragraph(M, 292, "সপ্তাহে ১২ ঘণ্টা", 74, 900, INK, max_width=1700,
                     t=t, start=0.3, stagger=0.06)
    arrow_p = ease_out(seg(t, 0.72, 0.6))
    hw = display_width("সপ্তাহে ১২ ঘণ্টা", 74, 900)
    ax, ay = M + hw + 46, 292 - 26
    atip = ax + 74 * arrow_p
    arrow = group(
        line(ax, ay, atip - 6, ay, MINT, 9, arrow_p) +
        path("M %.1f %.1f L %.1f %.1f L %.1f %.1f" % (
            atip - 24, ay - 18, atip, ay, atip - 24, ay + 18),
            stroke=MINT, width=9, opacity=arrow_p),
        opacity=1.0)
    head2b = paragraph(M + hw + 150, 292, "১ ঘণ্টা", 74, 900, MINT, max_width=600,
                       t=t, start=0.85, stagger=0.06)
    head2 = paragraph(M, 372, "একই কাজ, এখন ৯০% কম হাতের ছোঁয়া লাগে।", 42, 500,
                      "#C8D3E6", max_width=1500, t=t, start=1.2, stagger=0.04)

    # dashboard mock
    p = ease_out(seg(t, 1.4, 0.8))
    dx, dy, dw, dh = M, 452, 980, 452
    dash = [card(dx, dy, dw, dh, opacity=0.95 * p, rx=30, glow=(CYAN, 0.10 * p))]
    dash.append(rect(dx, dy, dw, 74, "#182444", rx=30, opacity=0.9 * p))
    dash.append(rect(dx, dy + 44, dw, 30, "#182444", opacity=0.9 * p))
    for i, c in enumerate([ROSE, AMBER, MINT]):
        dash.append(circle(dx + 40 + i * 28, dy + 37, 8, c, opacity=0.8 * p))
    dash.append(text(dx + 150, dy + 46, "Pace · অটোমেশন ড্যাশবোর্ড", 26, 600, MUTED,
                     opacity=p))

    # animated bars
    heights = [0.35, 0.55, 0.42, 0.78, 0.62, 0.92]
    bw, bg_gap = 74, 40
    for i, hh in enumerate(heights):
        bp = ease_out(seg(t, 1.9 + i * 0.09, 0.7))
        bx = dx + 80 + i * (bw + bg_gap)
        bh = 220 * hh * bp
        dash.append(rect(bx, dy + 380 - bh, bw, bh, "url(#dmint)" if i % 2 == 0 else "url(#dviolet)",
                         rx=16, opacity=0.9 * bp))
    dash.append(text(dx + 40, dy + 424, "স্বয়ংক্রিয়ভাবে সম্পন্ন হওয়া কাজ", 24, 500, MUTED,
                     opacity=p))

    # checklist
    items = ["সাপ্তাহিক রিপোর্ট নিজে নিজে তৈরি",
             "অনুমোদন সঠিক মানুষের কাছে পৌঁছায়",
             "নতুন কর্মীকে শেখাতে লাগে ১ দিন"]
    cl = []
    for i, s in enumerate(items):
        q = ease_out(seg(t, 2.6 + i * 0.35, 0.6))
        y = 560 + i * 120
        cl.append(rect(1180, y - 40, 590, 104, "#101A2D", rx=22, opacity=0.85 * q,
                       extra='stroke="#2A3A57" stroke-width="1.2"'))
        cl.append(icon_check(1234, y + 12, 30, MINT) if i != 2 else
                  circle(1234, y + 12, 30, MINT, 0.18 * q))
        if i == 2:
            cl.append(icon_bolt(1234, y + 12, 40, MINT))
        cl.append(text(1288, y + 25, s, 32, 500, INK, opacity=q))

    big = ease_out(seg(t, 4.6, 0.9))
    by0 = 900
    badge = group(
        card(1180, by0, 590, 112, opacity=0.95 * big, rx=24, glow=(MINT, 0.16 * big)) +
        text(1216, by0 + 70, "৯০%", 58, 900, MINT, opacity=big) +
        text(1408, by0 + 48, "কম ম্যানুয়াল কাজ", 31, 700, INK, opacity=big) +
        text(1408, by0 + 86, "গড়ে প্রথম মাসেই", 25, 400, MUTED, opacity=big),
        opacity=1.0)

    inner = (kicker + head + arrow + head2b + head2 + "".join(dash) +
             "".join(cl) + badge)
    return scene_frame(t, dur, inner)


# --------------------------------------------------------------- 6. social ---
def stat_block(x, y, value, suffix, label, color, p):
    return (text(x, y, value, 116, 900, color, anchor="middle", opacity=p) +
            text(x + text_width(value, 116, 900) / 2 + 6, y, suffix, 44, 700, color,
                 opacity=p) +
            text(x, y + 56, label, 30, 400, MUTED, anchor="middle", opacity=p))


def scene_social(t, dur):
    head = paragraph(W / 2, 300, "আর এই মুহূর্তে", 44, 500, MUTED, max_width=1600,
                     anchor="middle", t=t, start=0.2, stagger=0.05)
    head2 = paragraph(W / 2, 390, "৪৫,০০০+ টিম পেস-এর সাথে চলছে", 76, 800, INK,
                      max_width=1700, anchor="middle", t=t, start=0.45, stagger=0.05)

    stats = [("৪৫,০০০", "+", "টিম ব্যবহার করছে", MINT),
             ("৩২", "টি", "দেশে সক্রিয়", CYAN),
             ("৪.৮", "/৫", "গড় রেটিং", AMBER),
             ("৯৯.৯", "%", "আপটাইম", VIOLET)]
    out = []
    for i, (val, suf, label, col) in enumerate(stats):
        p = ease_out(seg(t, 1.1 + i * 0.32, 0.7))
        cx = 300 + i * 440
        out.append(rect(cx - 195, 520, 390, 250, "#101A2D", rx=30,
                        opacity=0.85 * clip_helper(p),
                        extra='stroke="%s" stroke-width="1.4" stroke-opacity="%.2f"' % (col, 0.35 * p)))
        out.append(stat_block_bn(cx, 640, val, suf, label, col, p))

    # review quotes
    q = ease_out(seg(t, 2.9, 0.8))
    quote = group(
        text(W / 2, 880, "“আগে সোমবার মানেই ৬ ঘণ্টার রিপোর্ট ম্যারাথন। এখন সকাল ৯টায় রিপোর্ট রেডি।”",
             40, 600, INK, anchor="middle", opacity=q) +
        text(W / 2, 936, "— তাহমিদা রহমান, অপারেশনস লিড", 30, 400, MUTED,
             anchor="middle", opacity=q),
        opacity=1.0)

    inner = head + head2 + "".join(out) + quote
    return scene_frame(t, dur, inner)


def clip_helper(x):
    return max(0.0, min(1.0, x))


def stat_block_bn(cx, y, val, suf, label, col, p):
    vs = 96 if len(val) > 4 else 112
    vw = display_width(val, vs, 900)
    sw = display_width(suf, 40, 700)
    gap = 10
    total = vw + gap + sw
    x = cx - total / 2
    return (text(x, y, val, vs, 900, col, opacity=p) +
            text(x + vw + gap, y, suf, 40, 700, col, opacity=p) +
            text(cx, y + 58, label, 30, 400, MUTED, anchor="middle", opacity=p))


# ------------------------------------------------------------------ 7. cta ---
def scene_cta(t, dur):
    halo = circle(W / 2, 400, 560, "url(#dglow)",
                  opacity=0.5 * ease_in_out(seg(t, 0.2, 1.0)))
    mark = logo_mark(W / 2 - 160, 300, 130, seg(t, 0.15, 1.2), t)
    word = ease_out(seg(t, 0.5, 0.8))
    wordmark = text(W / 2 + 40, 358, "Pace", 112, 800, INK, opacity=word)

    head = paragraph(W / 2, 570, "আজই ফ্রি শুরু করুন।", 86, 900, INK,
                     max_width=1600, anchor="middle", t=t, start=0.7, stagger=0.06)
    sub = paragraph(W / 2, 660, "১৪ দিনের ফ্রি ট্রায়াল · কার্ডের দরকার নেই · ২ মিনিটে সেটআপ",
                    38, 500, "#C8D3E6", max_width=1700, anchor="middle",
                    t=t, start=1.2, stagger=0.035)

    btn = ease_out_back(seg(t, 1.7, 0.8))
    label = "শুরু করুন — pace.com.bd"
    bw = text_width(label, 44, 700) + 120
    bx = W / 2 - bw / 2
    button = ('<g transform="%s">%s%s%s</g>' % (
        scale_about(btn, btn, W / 2, 820),
        rect(bx, 770, bw, 100, "url(#dmint)", rx=50, opacity=clamp(btn * 1.5)),
        text(W / 2, 834, label, 44, 700, BG_0, anchor="middle",
             opacity=clamp(btn * 1.5)),
        ""))

    foot = ease_out(seg(t, 2.5, 0.7))
    footline = text(W / 2, 960, "৪৫,০০০+ টিম ইতিমধ্যেই ব্যবহার করছে", 30, 500, MUTED,
                    anchor="middle", opacity=foot)

    inner = (halo + mark + wordmark + head + sub + button + footline)
    return scene_frame(t, dur, inner)


SCENES = [
    ("hook", scene_hook),
    ("problem", scene_problem),
    ("intro", scene_intro),
    ("how", scene_how),
    ("result", scene_result),
    ("social", scene_social),
    ("cta", scene_cta),
]
