"""Screen-recording style scenes, timed to the supplied Bangla voice-over.

Each scene is a pure function of (t, duration) -> {svg, opacity}. Inside a scene
there is a slow camera pan/zoom so it reads like a real screen recording that
someone is driving, and Bangla captions follow the narration.
"""
from __future__ import annotations

import math

from kit import *  # noqa
from kit import _gap
from ui import *  # noqa
try:
    from scenes import logo_mark
except Exception:  # pragma: no cover
    def logo_mark(cx, cy, s, p=1.0, t=0.0, glow=True):
        out = []
        for i, hh in enumerate([0.42, 0.72, 1.0]):
            hp = ease_out_back(seg(p, i * 0.13, 0.6), 2.2)
            bh = max(0.01, s * hh * hp)
            out.append(rect(cx - s * 0.42 + i * s * 0.34, cy + s * 0.45 - bh,
                            s * 0.20, bh, MINT, rx=s * 0.10, opacity=clamp(hp * 1.6)))
        out.append(circle(cx + s * 0.58, cy - s * 0.34, s * 0.13, CYAN,
                          ease_out(seg(p, 0.45, 0.5))))
        return "".join(out)

W, H = 1920, 1080
M = 150


def scene_out(t, dur, inner, fade=0.28, push=0.008):
    o = 1.0
    if t < fade:
        o = ease_out(t / fade)
    if t > dur - fade:
        o = min(o, 1.0 - ease_in_out((t - (dur - fade)) / fade))
    return {"svg": svg_doc(chrome(t) + inner, "d"), "opacity": o}


def ambience(t, seed=3, parts=34):
    return (particles(t, n=parts, seed=seed, speed=0.6, opacity=0.28) +
            bokeh(t, n=5, seed=seed + 2))


# ============================================================ 1. dashboard ===
def scene_dash(t, dur):
    """Pace dashboard: KPI tiles count up, table fills, chart draws."""
    win_x, win_y, win_w, win_h = 250, 96, 1540, 900
    p = ease_out_expo(seg(t, 0.15, 0.9))

    cam = camera("", t, [(0, (1.0, 960, 540))])  # placeholder, we compose directly

    body = []
    body.append(window(win_x, win_y, win_w, win_h, "app.pace.com.bd/dashboard",
                       tabs=[("ওভারভিউ", True), ("ফ্লো", False), ("ইন্টিগ্রেশন", False),
                             ("রিপোর্ট", False)], opacity=p, tab_offset=226))
    body.append(sidebar(win_x, win_y + 58, 226, win_h - 58,
                        ["ড্যাশবোর্ড", "ফ্লো", "টিম", "রিপোর্ট", "সেটিংস"], 0, p))

    cx = win_x + 226 + 34
    cw = win_w - 226 - 68
    # page title
    tp = ease_out(seg(t, 0.5, 0.6))
    body.append(text(cx, win_y + 172, "ওভারভিউ", 32, 800, UI_TEXT, opacity=tp))
    body.append(text(cx, win_y + 202, "গত ৭ দিনে আপনার টিমের অটোমেশন", 17, 400,
                     UI_MUTED, opacity=tp))
    body.append(chip(cx + cw - 190, win_y + 156, "লাইভ", MINT, tp))
    body.append(circle(cx + cw - 22, win_y + 170, 6, MINT, 0.9 * tp *
                       (0.6 + 0.4 * math.sin(t * 4))))

    # KPI tiles
    tiles = [("বাঁচানো সময়", "%s ঘণ্টা" % counter(412 * ease_out(seg(t, 0.7, 1.4))),
              "+১৮%", MINT, [0.2, 0.35, 0.3, 0.55, 0.7, 0.85, 1.0]),
             ("অটোমেটেড রান", counter(2841 * ease_out(seg(t, 0.8, 1.4))),
              "+৯%", CYAN, [0.4, 0.3, 0.5, 0.45, 0.7, 0.6, 0.9]),
             ("ব্যর্থ রান", counter(7), "−৪২%", AMBER, [0.8, 0.6, 0.5, 0.3, 0.2, 0.15, 0.1])]
    tw = (cw - 2 * 20) / 3
    for i, (label, val, delta, col, chart) in enumerate(tiles):
        q = pop(t, 0.75 + i * 0.16, 0.55)
        if q <= 0:
            continue
        body.append(group(stat_tile(cx + i * (tw + 20), win_y + 224, tw, 146,
                                    label, val, delta, col, 1.0, t, chart),
                          opacity=clamp(q * 1.3)))

    # main table
    rows = [("সাপ্তাহিক রিপোর্ট", ("সক্রিয়", MINT), "প্রতিদিন ০৯:০০", "১২৪ রান"),
            ("নতুন লিড → CRM", ("সক্রিয়", MINT), "ইভেন্টে", "৮৯২ রান"),
            ("ইনভয়েস অ্যাপ্রুভাল", ("সক্রিয়", MINT), "ম্যানুয়াল", "৩১ রান"),
            ("Slack ডেইলি ডাইজেস্ট", ("সক্রিয়", MINT), "প্রতিদিন ১৮:০০", "৫৬ রান"),
            ("স্টক রিকনসিল", ("বিরতি", AMBER), "সাপ্তাহিক", "৪ রান")]
    th_p = ease_out(seg(t, 1.6, 0.6))
    body.append(text(cx, win_y + 416, "আজকের অটোমেশন", 22, 700, UI_TEXT, opacity=th_p))
    body.append(table(cx, win_y + 434, cw,
                      ["ফ্লো", "স্ট্যাটাস", "শিডিউল", "রান"],
                      rows, th_p, t=t, start=1.75, steps=0.11, row_h=40))

    # lower row: activity feed + next run
    ly = win_y + 712
    lp = ease_out(seg(t, 2.6, 0.6))
    body.append(text(cx, ly, "সাম্প্রতিক অ্যাক্টিভিটি", 22, 700, UI_TEXT, opacity=lp))
    acts = [("সাপ্তাহিক রিপোর্ট তৈরি হয়েছে", "২ মিনিট আগে", MINT),
            ("নতুন লিড CRM-এ গেছে", "১১ মিনিট আগে", CYAN),
            ("ইনভয়েস অ্যাপ্রুভ হয়েছে", "৩৪ মিনিট আগে", VIOLET),
            ("Anomaly অ্যালার্ট পাঠানো হয়েছে", "১ ঘণ্টা আগে", AMBER)]
    for i, (label, when, col) in enumerate(acts):
        q = ease_out(seg(t, 2.7 + i * 0.1, 0.5))
        yy = ly + 26 + i * 34
        body.append(circle(cx + 8, yy - 5, 4, col, 0.9 * q * lp))
        body.append(text(cx + 26, yy, label, 17, 500, UI_TEXT, opacity=q * lp))
        body.append(text(cx + cw * 0.58, yy, when, 15, 400, UI_MUTED,
                         anchor="end", opacity=q * lp))

    # next scheduled run card
    np_ = pop(t, 2.9, 0.6)
    nx0 = cx + cw * 0.64
    nw0 = cw * 0.36
    if np_ > 0:
        body.append(group(
            rect(nx0, ly - 16, nw0, 178, UI_PANEL, rx=16, opacity=0.96,
                 extra='stroke="%s" stroke-width="1.2"' % UI_LINE) +
            text(nx0 + 22, ly + 18, "পরবর্তী রান", 17, 500, UI_MUTED) +
            text(nx0 + 22, ly + 58, "০৯:০০", 34, 800, MINT) +
            text(nx0 + 120, ly + 58, "সোমবার", 20, 600, UI_TEXT) +
            line(nx0 + 22, ly + 82, nx0 + nw0 - 22, ly + 82, UI_LINE, 1, 0.6) +
            text(nx0 + 22, ly + 112, "সাপ্তাহিক রিপোর্ট + Slack ডাইজেস্ট", 15, 400, UI_MUTED) +
            chip(nx0 + 22, ly + 124, "অটো-শিডিউল", MINT),
            opacity=np_))

    # cursor that moves and clicks "Flow" tab
    body.append(cursor(t, [(1.0, (1560, 250)), (2.2, (1430, 300)), (3.2, (1300, 470)),
                           (5.0, (980, 560)), (7.0, (900, 780)), (9.5, (1180, 700)),
                           (12.0, (1040, 330))],
                       clicks=[(2.35, (1430, 300)), (3.3, (1300, 470))]))

    # gentle screen-recording camera: settle, push into the table, drift down
    cam = keyframes(t, [(0.0, (1.02, 960, 540)), (3.0, (1.05, 980, 520)),
                        (8.0, (1.11, 930, 585)), (13.0, (1.06, 975, 540)),
                        (dur, (1.13, 900, 600))], ease=ease_in_out)
    inner = ambience(t, 11) + camera("".join(body), 0, [(0, cam)])
    return scene_out(t, dur, inner)


# ========================================================= 2. flow builder ===
def scene_flow(t, dur):
    win_x, win_y, win_w, win_h = 200, 80, 1640, 920
    p = ease_out_expo(seg(t, 0.1, 0.8))
    body = [window(win_x, win_y, win_w, win_h, "app.pace.com.bd/flow/new",
                   tabs=[("ফ্লো বিল্ডার", True), ("টেস্ট রান", False), ("লগ", False)],
                   opacity=p, tab_offset=210),
            sidebar(win_x, win_y + 58, 210, win_h - 58,
                    ["ড্যাশবোর্ড", "ফ্লো", "টিম", "রিপোর্ট"], 1, p)]

    bx = win_x + 210
    body.append(rect(bx, win_y + 58, win_w - 210, win_h - 58, "#0A1120", rx=0,
                     opacity=p))
    body.append(dot_grid(cols=26, rows=16, t=t, opacity=0.07))

    head = ease_out(seg(t, 0.4, 0.5))
    body.append(text(bx + 40, win_y + 116, "নতুন ফ্লো · লিড ফলো-আপ", 26, 800,
                     UI_TEXT, opacity=head))
    body.append(chip(bx + 40, win_y + 132, "খসড়া", AMBER, head))

    # nodes: 3 across, then 2 below — all inside the builder area
    nw, nh = 300, 92
    n1 = (bx + 40, win_y + 200)
    n2 = (bx + 430, win_y + 200)
    n3 = (bx + 820, win_y + 200)
    n4 = (bx + 430, win_y + 360)
    n5 = (bx + 820, win_y + 360)
    nodes = [
        (n1, "ট্রিগার", "নতুন ফর্ম রেসপন্স", CYAN, 0.9),
        (n2, "অ্যাকশন", "Sheets-এ এন্ট্রি", VIOLET, 1.4),
        (n3, "শর্ত", "বাজেট > ৳৫০,০০০ হলে", AMBER, 1.9),
        (n4, "অ্যাকশন", "Slack-এ অ্যালার্ট", MINT, 2.5),
        (n5, "নোটিফাই", "সেলস টিমকে অ্যাসাইন", MINT, 3.1),
    ]
    for (nx, ny), title, sub, col, st in nodes:
        q = seg(t, st, 0.5)
        body.append(flow_node(nx, ny, nw, nh, title, sub, col, q, p,
                              icon=circle(nx + nw - 34, ny + 32, 7, col, q * 0.9)))
    body.append(connector(n1[0] + nw, n1[1] + nh / 2, n2[0], n2[1] + nh / 2,
                          seg(t, 1.15, 0.45), CYAN, 3, opacity=p))
    body.append(connector(n2[0] + nw, n2[1] + nh / 2, n3[0], n3[1] + nh / 2,
                          seg(t, 1.7, 0.45), VIOLET, 3, opacity=p))
    body.append(connector(n2[0] + nw / 2, n2[1] + nh, n4[0] + nw / 2, n4[1],
                          seg(t, 2.2, 0.45), MINT, 3, opacity=p))
    body.append(connector(n3[0] + nw / 2, n3[1] + nh, n5[0] + nw / 2, n5[1],
                          seg(t, 2.7, 0.45), MINT, 3, opacity=p))

    # travelling pulse along the top chain
    t0 = 3.4
    if t > t0:
        ph = ((t - t0) % 2.4) / 2.4
        pts = [(n1[0] + nw, n1[1] + nh / 2), (n2[0], n2[1] + nh / 2),
               (n2[0] + nw, n2[1] + nh / 2), (n3[0], n3[1] + nh / 2)]
        total = len(pts) - 1
        idx = min(int(ph * total), total - 1)
        local = ph * total - idx
        a, b = pts[idx], pts[idx + 1]
        px, py = a[0] + (b[0] - a[0]) * local, a[1] + (b[1] - a[1]) * local
        body.append(circle(px, py, 6, MINT, 0.95))
        body.append(circle(px, py, 20, MINT, 0.16))

    # run history strip at the bottom of the builder
    hp = ease_out(seg(t, 3.0, 0.6))
    hy = win_y + 556
    body.append(text(bx + 40, hy + 6, "সাম্প্রতিক রান", 20, 700, UI_TEXT, opacity=hp))
    rows = [("আজ ০৯:০০", "সফল", "১.২ সে", "১২৪ আইটেম"),
            ("আজ ০৮:১৫", "সফল", "০.৯ সে", "৮৮ আইটেম"),
            ("গতকাল ১৮:০০", "সফল", "১.৪ সে", "১৩১ আইটেম"),
            ("গতকাল ০৯:০০", "সতর্কতা", "২.১ সে", "১১৯ আইটেম")]
    body.append(table(bx + 40, hy + 18, 1080, ["সময়", "স্ট্যাটাস", "সময় লেগেছে", "আইটেম"],
                      rows, hp, t=t, start=3.1, steps=0.12, row_h=42))

    # right panel: status
    rp = ease_out(seg(t, 2.2, 0.6))
    px = win_x + win_w - 296
    body.append(rect(px, win_y + 140, 262, 420, UI_PANEL, rx=18, opacity=0.96 * rp,
                     extra='stroke="%s" stroke-width="1.2"' % UI_LINE))
    body.append(text(px + 24, win_y + 182, "ফ্লো স্ট্যাটাস", 19, 700, UI_TEXT, opacity=rp))
    stats = [("ধাপ", "৫"), ("গড় সময়", "১.২ সে"), ("সফলতা", "৯৮.৬%")]
    for i, (k, v) in enumerate(stats):
        yy = win_y + 224 + i * 62
        body.append(text(px + 24, yy, k, 16, 500, UI_MUTED, opacity=rp))
        body.append(text(px + 238, yy, v, 22, 800, MINT, anchor="end", opacity=rp))
        body.append(line(px + 24, yy + 20, px + 238, yy + 20, UI_LINE, 1, 0.5 * rp))
    body.append(text(px + 24, win_y + 440, "সক্রিয়", 16, 600, UI_MUTED, opacity=rp))
    body.append(toggle(px + 180, win_y + 424, ease_out(seg(t, 3.4, 0.5)), rp))
    body.append(text(px + 24, win_y + 496, "২৪/৭ চলছে", 15, 500, MINT,
                     opacity=rp * ease_out(seg(t, 3.8, 0.4))))

    body.append(cursor(t, [(0.8, (1300, 700)), (1.9, (900, 420)), (2.7, (1180, 520)),
                           (3.5, (1420, 560)), (4.2, (1150, 300))],
                       clicks=[(2.0, (900, 420)), (3.6, (1420, 560))]))

    cam = keyframes(t, [(0.0, (1.04, 960, 520)), (5.0, (1.10, 900, 470)),
                        (dur, (1.05, 940, 600))])
    inner = ambience(t, 21) + camera("".join(body), 0, [(0, cam)])
    return scene_out(t, dur, inner)


# ==================================================== 3. integrations page ===
def scene_integrations(t, dur):
    win_x, win_y, win_w, win_h = 240, 110, 1500, 860
    p = ease_out_expo(seg(t, 0.1, 0.8))
    body = [window(win_x, win_y, win_w, win_h, "app.pace.com.bd/integrations",
                   tabs=[("সব", False), ("ইন্টিগ্রেশন", True), ("API", False)], opacity=p)]

    head = ease_out(seg(t, 0.4, 0.6))
    body.append(text(win_x + 60, win_y + 160, "ইন্টিগ্রেশন", 34, 800, UI_TEXT, opacity=head))
    body.append(text(win_x + 60, win_y + 194, "আপনার টিম যে টুল ব্যবহার করে, সব একই জায়গায়",
                     18, 400, UI_MUTED, opacity=head))
    body.append(rect(win_x + 60, win_y + 216, 420, 46, "#0F1A2B", rx=12,
                     opacity=0.95 * head, extra='stroke="%s" stroke-width="1.2"' % UI_LINE))
    body.append(text(win_x + 84, win_y + 245, "অ্যাপ খুঁজুন…", 17, 400, UI_DIM, opacity=head))

    apps = [("Gmail", CYAN), ("Sheets", MINT), ("Slack", VIOLET), ("Notion", INK),
            ("Drive", AMBER), ("Zoom", CYAN), ("HubSpot", ROSE), ("Stripe", VIOLET),
            ("WhatsApp", MINT), ("Calendar", CYAN), ("Jira", VIOLET), ("Trello", MINT)]
    cols, cw, ch = 4, 330, 150
    for i, (name, col) in enumerate(apps):
        q = pop(t, 0.7 + i * 0.07, 0.45)
        if q <= 0:
            continue
        r_, c_ = divmod(i, cols)
        ax = win_x + 60 + c_ * (cw + 24)
        ay = win_y + 300 + r_ * (ch + 24)
        on = (i in (0, 1, 2, 3))
        body.append(group(
            rect(ax, ay, cw, ch, UI_PANEL, rx=18, opacity=0.95,
                 extra='stroke="%s" stroke-width="1.4" stroke-opacity="%.2f"' % (
                     col if on else UI_LINE, 0.7 if on else 0.5)) +
            circle(ax + 46, ay + 46, 22, col, 0.18) +
            circle(ax + 46, ay + 46, 12, col, 0.85) +
            text(ax + 84, ay + 54, name, 21, 700, UI_TEXT) +
            text(ax + 24, ay + ch - 26, "কানেক্টেড" if on else "কানেক্ট করুন",
                 16, 600, MINT if on else UI_DIM) +
            (icon_check(ax + cw - 34, ay + 34, 14, MINT) if on else
             circle(ax + cw - 34, ay + 34, 12, "none", 0.5,
                    extra='stroke="%s" stroke-width="1.4"' % UI_LINE)),
            opacity=q))

    # toast that slides in
    tp = ease_out_expo(seg(t, 2.6, 0.6))
    if tp > 0:
        tx = win_x + win_w - 470
        ty = win_y + win_h - 120 + (1 - tp) * 40
        body.append(group(
            rect(tx, ty, 420, 74, "#10261F", rx=16, opacity=0.97,
                 extra='stroke="%s" stroke-width="1.4"' % MINT) +
            icon_check(tx + 40, ty + 37, 18, MINT) +
            text(tx + 74, ty + 33, "Gmail কানেক্ট হয়েছে", 19, 700, UI_TEXT) +
            text(tx + 74, ty + 56, "৩টি ফ্লোতে ব্যবহার হচ্ছে", 15, 400, UI_MUTED),
            opacity=tp))

    body.append(cursor(t, [(0.6, (1500, 300)), (1.4, (760, 470)), (2.2, (760, 640)),
                           (3.0, (1120, 470)), (3.9, (1420, 760))],
                       clicks=[(1.5, (760, 470)), (3.1, (1120, 470))]))

    cam = keyframes(t, [(0.0, (1.03, 960, 540)), (3.0, (1.09, 930, 500)),
                        (dur, (1.12, 900, 560))])
    inner = ambience(t, 31) + camera("".join(body), 0, [(0, cam)])
    return scene_out(t, dur, inner)


# ======================================================= 4. reporting view ===
def scene_reports(t, dur):
    win_x, win_y, win_w, win_h = 260, 90, 1460, 900
    p = ease_out_expo(seg(t, 0.1, 0.8))
    body = [window(win_x, win_y, win_w, win_h, "app.pace.com.bd/reports/weekly",
                   tabs=[("রিপোর্ট", True), ("শেয়ার", False), ("শিডিউল", False)],
                   opacity=p, tab_offset=210),
            sidebar(win_x, win_y + 104, 210, win_h - 104,
                    ["ড্যাশবোর্ড", "ফ্লো", "টিম", "রিপোর্ট"], 3, p)]
    bx = win_x + 210
    body.append(text(bx + 44, win_y + 132, "সাপ্তাহিক রিপোর্ট", 30, 800, UI_TEXT,
                     opacity=ease_out(seg(t, 0.35, 0.5))))
    body.append(text(bx + 44, win_y + 164, "স্বয়ংক্রিয়ভাবে তৈরি · প্রতি সোমবার ০৯:০০",
                     17, 400, UI_MUTED, opacity=ease_out(seg(t, 0.4, 0.5))))

    # big chart card
    q = ease_out_expo(seg(t, 0.6, 0.7))
    cx0, cy0, cwd, chd = bx + 44, win_y + 200, 1140, 340
    body.append(group(
        rect(cx0, cy0, cwd, chd, UI_PANEL, rx=18, opacity=0.96,
             extra='stroke="%s" stroke-width="1.2"' % UI_LINE) +
        text(cx0 + 28, cy0 + 40, "সপ্তাহে বাঁচানো সময় (ঘণ্টা)", 19, 600, UI_MUTED),
        opacity=q))

    bars = [("সোম", 0.55), ("মঙ্গল", 0.68), ("বুধ", 0.60), ("বৃহঃ", 0.82),
            ("শুক্র", 0.74), ("শনি", 0.42), ("রবি", 0.30)]
    bwid = 78
    for i, (lab, v) in enumerate(bars):
        bp = ease_out_back(seg(t, 1.0 + i * 0.1, 0.8), 1.3)
        bxpos = cx0 + 80 + i * (bwid + 54)
        bh = max(1, 220 * v * bp)
        body.append(rect(bxpos, cy0 + 290 - bh, bwid, bh,
                         "url(#dmint)" if i % 2 == 0 else "url(#dviolet)", rx=12,
                         opacity=0.92 * q))
        body.append(text(bxpos + bwid / 2, cy0 + 316, lab, 16, 600, UI_MUTED,
                         anchor="middle", opacity=q))

    # summary rows + export button
    rows = [("মোট বাঁচানো সময়", "৪১২ ঘণ্টা", MINT), ("অটোমেটেড রান", "২,৮৪১", CYAN),
            ("গড় রেসপন্স টাইম", "১.২ মিনিট", VIOLET), ("ব্যর্থ রান", "৭", AMBER)]
    for i, (k, v, col) in enumerate(rows):
        rp = pop(t, 1.9 + i * 0.16, 0.5)
        if rp <= 0:
            continue
        yy = cy0 + chd + 26 + i * 62
        body.append(group(
            rect(cx0, yy, cwd, 52, "#111D31", rx=12, opacity=0.9,
                 extra='stroke="%s" stroke-width="1"' % UI_LINE) +
            circle(cx0 + 28, yy + 26, 6, col, 0.9) +
            text(cx0 + 50, yy + 33, k, 18, 500, UI_TEXT) +
            text(cx0 + cwd - 28, yy + 33, v, 19, 800, col, anchor="end"),
            opacity=rp))

    ex = pop(t, 2.8, 0.6)
    if ex > 0:
        body.append(group(
            rect(cx0 + cwd - 210, cy0 - 58, 210, 44, "url(#dmint)", rx=12,
                 opacity=0.95) +
            text(cx0 + cwd - 105, cy0 - 29, "PDF এক্সপোর্ট", 17, 700, BG_0,
                 anchor="middle"),
            opacity=ex))

    body.append(cursor(t, [(0.7, (900, 700)), (1.5, (1180, 620)), (2.6, (1400, 560)),
                           (3.2, (1180, 260))],
                       clicks=[(1.6, (1180, 620)), (3.3, (1180, 260))]))

    cam = keyframes(t, [(0.0, (1.02, 960, 540)), (4.0, (1.08, 940, 520)),
                        (dur, (1.12, 900, 560))])
    inner = ambience(t, 41) + camera("".join(body), 0, [(0, cam)])
    return scene_out(t, dur, inner)


# ========================================================== 5. team/roles ===
def scene_team(t, dur):
    win_x, win_y, win_w, win_h = 300, 120, 1340, 840
    p = ease_out_expo(seg(t, 0.1, 0.8))
    body = [window(win_x, win_y, win_w, win_h, "app.pace.com.bd/team",
                   tabs=[("সদস্য", True), ("রোল", False), ("লগ", False)], opacity=p)]
    body.append(text(win_x + 60, win_y + 150, "টিম ও অ্যাক্সেস", 30, 800, UI_TEXT,
                     opacity=ease_out(seg(t, 0.35, 0.5))))
    body.append(text(win_x + 60, win_y + 182, "কে কী করতে পারবে, সব নিয়ন্ত্রণে",
                     17, 400, UI_MUTED, opacity=ease_out(seg(t, 0.4, 0.5))))

    members = [("তাহমিদা রহমান", "অপারেশনস লিড", "অ্যাডমিন", MINT, "ত"),
               ("রাফিদ হাসান", "সেলস", "এডিটর", CYAN, "র"),
               ("নুসরাত জাহান", "মার্কেটিং", "এডিটর", VIOLET, "ন"),
               ("সাদিয়া আফরিন", "ফাইন্যান্স", "ভিউয়ার", AMBER, "স")]
    for i, (name, role, perm, col, ini) in enumerate(members):
        q = pop(t, 0.7 + i * 0.2, 0.5)
        if q <= 0:
            continue
        yy = win_y + 214 + i * 96
        body.append(group(
            rect(win_x + 60, yy, win_w - 120, 80, "#121F33", rx=14,
                 opacity=0.92, extra='stroke="%s" stroke-width="1.1"' % UI_LINE) +
            avatar(win_x + 108, yy + 40, 24, ini, col) +
            text(win_x + 148, yy + 34, name, 20, 700, UI_TEXT) +
            text(win_x + 148, yy + 58, role, 15, 400, UI_MUTED) +
            chip(win_x + win_w - 300, yy + 26, perm, col) +
            toggle(win_x + win_w - 140, yy + 25, 1.0, 1.0),
            opacity=q))

    # invite row
    ip = ease_out_expo(seg(t, 2.2, 0.7))
    yy = win_y + 214 + 4 * 96
    body.append(group(
        rect(win_x + 60, yy, win_w - 120, 70, "#0F1A2B", rx=14, opacity=0.9,
             extra='stroke="%s" stroke-width="1.4" stroke-opacity="0.7"' % MINT) +
        circle(win_x + 108, yy + 35, 22, MINT, 0.14) +
        text(win_x + 108, yy + 43, "+", 26, 700, MINT, anchor="middle") +
        text(win_x + 148, yy + 42, "নতুন সদস্য ইনভাইট করুন", 18, 600, MINT) +
        text(win_x + win_w - 150, yy + 42, "ইমেইল দিন", 16, 400, UI_DIM, anchor="end"),
        opacity=ip))

    body.append(cursor(t, [(0.8, (1000, 780)), (1.6, (1150, 700)), (2.4, (900, 300))],
                       clicks=[(1.7, (1150, 700))]))

    cam = keyframes(t, [(0.0, (1.02, 960, 540)), (4.0, (1.07, 950, 520)),
                        (dur, (1.10, 930, 580))])
    inner = ambience(t, 51) + camera("".join(body), 0, [(0, cam)])
    return scene_out(t, dur, inner)


# ============================================================= 6. closing ===
def scene_close(t, dur):
    cx = W / 2
    halo = glow_orb(cx, 360, 620, t, True, 0.55 * ease_in_out(seg(t, 0.1, 1.0)))
    rings = (pulse_ring(cx, 330, 260, 780, t, 2.4, MINT, 2.0, 0.30) +
             pulse_ring(cx, 330, 220, 660, t + 1.2, 2.4, CYAN, 1.4, 0.22))
    mark = logo_mark(cx - 150, 282, 128, seg(t, 0.1, 1.1), t) if "logo_mark" in globals() else ""
    if isinstance(mark, tuple):
        mark = ""
    word = ease_out_expo(seg(t, 0.4, 0.8))
    wordmark = ('<g transform="translate(%.1f,0)" opacity="%.3f">%s</g>' % (
        (1 - word) * -40, word, text(cx + 40, 336, "Pace", 106, 800, INK)))
    head = group(grad_text(cx, 552, "আজই শুরু করুন।", 82, 900, INK, "#B9FFE3",
                           phase=0.5 + 0.3 * math.sin(t * 0.9), spread=1.0,
                           anchor="middle"),
                 opacity=ease_out(seg(t, 0.7, 0.7)))
    sub = paragraph(cx, 640, "১৪ দিন ফ্রি · কার্ড লাগবে না · ২ মিনিটে সেটআপ", 36, 500,
                    "#C8D3E6", max_width=1700, anchor="middle", t=t, start=1.1,
                    stagger=0.04, rise=16)
    bp = pop(t, 1.6, 0.7)
    button = ""
    if bp > 0:
        label = "শুরু করুন — pace.com.bd"
        bw = display_width(label, 42, 700) + 120
        button = ('<g transform="%s">%s%s%s</g>' % (
            scale_about(bp, bp, cx, 780),
            rect(cx - bw / 2 - 8, 722, bw + 16, 116, MINT, rx=58, opacity=0.12),
            rect(cx - bw / 2, 730, bw, 100, "url(#dmint)", rx=50, opacity=clamp(bp * 1.5)),
            text(cx, 793, label, 42, 700, BG_0, anchor="middle",
                 opacity=clamp(bp * 1.5))))
    foot = text(cx, 900, "%s টিম ইতিমধ্যেই পেস ব্যবহার করছে" % counter(45000),
                28, 500, MUTED, anchor="middle", opacity=ease_out(seg(t, 2.2, 0.8)))
    inner = (ambience(t, 61, 60) + halo + rings + mark + wordmark + head + sub +
             button + foot)
    return scene_out(t, dur, inner)


# ==================================================== 7. social proof card ===
def scene_stats(t, dur):
    """Full-screen social proof: big numbers + testimonial, gentle camera drift."""
    cx = W / 2
    body = []
    body.append(caption_bg := "")
    halo = glow_orb(cx, 380, 700, t, True, 0.30 * ease_in_out(seg(t, 0.1, 1.2)))

    head = group(paragraph(cx, 250, "আর এই মুহূর্তে", 40, 500, MUTED, max_width=1600,
                           anchor="middle", t=t, start=0.2, stagger=0.05),
                 opacity=1.0)
    head2 = paragraph(cx, 350, "%s+ টিম পেস-এ চলছে" % counter(45000), 72, 800, INK,
                      max_width=1700, anchor="middle", t=t, start=0.45, stagger=0.05)

    stats = [(45000, 0, "+", "টিম ব্যবহার করছে", MINT),
             (32, 0, "টি", "দেশে সক্রিয়", CYAN),
             (4.8, 1, "/৫", "গড় রেটিং", AMBER),
             (99.9, 1, "%", "আপটাইম", VIOLET)]
    out = []
    for i, (val, dec, suf, label, col) in enumerate(stats):
        q = pop(t, 0.9 + i * 0.22, 0.55)
        if q <= 0:
            continue
        bx = 300 + i * 440
        out.append(rect(bx - 195, 470, 390, 230, UI_PANEL, rx=26, opacity=0.92,
                        extra='stroke="%s" stroke-width="1.4" stroke-opacity="%.2f"'
                        % (col, 0.4 * q)))
        cur = val * ease_out_quint(seg(t, 1.0 + i * 0.22, 0.9))
        vs = 92 if len(counter(val, dec)) > 4 else 106
        vw = display_width(counter(cur, dec), vs, 900)
        sw = display_width(suf, 38, 700)
        total = vw + 10 + sw
        x0 = bx - total / 2
        out.append(text(x0, 590, counter(cur, dec), vs, 900, col, opacity=clamp(q * 1.4)))
        out.append(text(x0 + vw + 10, 590, suf, 38, 700, col, opacity=clamp(q * 1.4)))
        out.append(text(bx, 646, label, 28, 400, MUTED, anchor="middle",
                        opacity=clamp(q * 1.4)))
    out.append(stars(1280, 520, 5, 11, AMBER, seg(t, 1.9, 1.0)))

    qp = ease_out_expo(seg(t, 2.6, 0.8))
    quote = ""
    if qp > 0:
        quote = group(
            text(cx, 800, "“আগে সোমবার মানেই ৬ ঘণ্টার রিপোর্ট ম্যারাথন। এখন সকাল ৯টায় রিপোর্ট রেডি।”",
                 37, 600, INK, anchor="middle") +
            line(cx - 240, 828, cx + 240, 828, MINT, 2, 0.35 * qp) +
            text(cx, 868, "— তাহমিদা রহমান, অপারেশনস লিড", 27, 400, MUTED,
                 anchor="middle"),
            opacity=qp)

    cam = keyframes(t, [(0.0, (1.03, 960, 540)), (dur, (1.08, 940, 520))])
    inner = (ambience(t, 71, 50) + halo + camera(head + head2 + "".join(out) + quote,
                                                 0, [(0, cam)]))
    return scene_out(t, dur, inner)


# ======================================================= 8. three-step recap ==
def scene_steps(t, dur):
    cx = W / 2
    head = paragraph(cx, 230, "শুরু করা মাত্র ৩ ধাপ", 68, 800, INK, max_width=1600,
                     anchor="middle", t=t, start=0.15, stagger=0.06)
    sub = paragraph(cx, 300, "কোনো কোড নেই · কার্ড লাগবে না", 34, 400, MUTED,
                    max_width=1600, anchor="middle", t=t, start=0.5, stagger=0.04)

    cards = []
    data = [("০১", "সাইন আপ", "ইমেইল দিয়ে ২ মিনিটে", CYAN),
            ("০২", "টুল কানেক্ট", "Gmail, Sheets, Slack…", VIOLET),
            ("০৩", "ফ্লো চালু", "বাকিটা পেস করে নেবে", MINT)]
    cw, gap = 460, 70
    x0 = cx - (cw * 3 + gap * 2) / 2
    for i, (num, title, desc, col) in enumerate(data):
        q = pop(t, 0.7 + i * 0.35, 0.6)
        if q <= 0:
            continue
        x = x0 + i * (cw + gap)
        y = 420 + (1 - ease_out(seg(t, 0.7 + i * 0.35, 0.6))) * 40
        cards.append(group(
            rect(x, y, cw, 300, UI_PANEL, rx=26, opacity=0.95,
                 extra='stroke="%s" stroke-width="1.5" stroke-opacity="0.65"' % col) +
            circle(x + 60, y + 62, 34, col, 0.16) +
            text(x + 60, y + 74, num, 30, 800, col, anchor="middle") +
            text(x + 60, y + 150, title, 38, 700, INK) +
            text(x + 60, y + 200, desc, 24, 400, MUTED) +
            rect(x + 60, y + 236, cw - 120, 6, "#1B2A44", rx=3) +
            rect(x + 60, y + 236, (cw - 120) * ease_out(seg(t, 1.1 + i * 0.35, 0.8)),
                6, col, rx=3),
            opacity=q))

    cta_p = pop(t, 2.6, 0.6)
    cta = ""
    if cta_p > 0:
        label = "pace.com.bd"
        bw = display_width(label, 40, 700) + 110
        cta = ('<g transform="%s">%s%s</g>' % (
            scale_about(cta_p, cta_p, cx, 800),
            rect(cx - bw / 2, 762, bw, 96, "url(#dmint)", rx=48,
                 opacity=clamp(cta_p * 1.5)),
            text(cx, 822, label, 40, 700, BG_0, anchor="middle",
                 opacity=clamp(cta_p * 1.5))))

    cam = keyframes(t, [(0.0, (1.02, 960, 540)), (dur, (1.07, 950, 560))])
    inner = (ambience(t, 81, 45) +
             camera(head + sub + "".join(cards) + cta, 0, [(0, cam)]))
    return scene_out(t, dur, inner)
