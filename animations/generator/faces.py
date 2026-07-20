#!/usr/bin/env python3
"""
QBIT face engine.

Draws expressive robot-eye faces for the 128x64 monochrome OLED in the same
visual language as the shipped set: two tall rounded-rectangle eyes that glow
white on black, plus a small mouth and occasional particles (zzz, !, tears,
hearts, stars). Everything is drawn at 4x supersample with anti-aliasing then
reduced to crisp 1-bit, which keeps curves smooth the way the originals look.

Convention: we render WHITE artwork on a BLACK background. That is the source
polarity the device expects -- white source pixels light up on the OLED.

Each expression starts and ends on the neutral face so it loops cleanly and
blends into the firmware's shuffle.
"""
import math
import struct
from pathlib import Path
from PIL import Image, ImageDraw

W, H = 128, 64
SS = 4                     # supersample factor
SW, SH = W * SS, H * SS

# --- Canonical neutral geometry (1x pixel coords), matched to the shipped set:
#     eyes ~20x30 rounded rects, centres at x=40 / x=88, y=29 (symmetric +-24).
EYE_DX = 24               # horizontal offset of each eye from centre (x=64)
CX = 64
EYE_CX_L = CX - EYE_DX    # 40
EYE_CX_R = CX + EYE_DX    # 88
EYE_CY = 29
EYE_W = 24
EYE_H = 30
EYE_R = 11                # corner radius
MOUTH_CY = 47


# --------------------------------------------------------------------------- #
# Low-level canvas
# --------------------------------------------------------------------------- #
def new_canvas():
    img = Image.new("L", (SW, SH), 0)
    return img, ImageDraw.Draw(img)


def finalize(img):
    """Downsample supersampled canvas to 128x64 and threshold to 1-bit.
    Returns a bool grid [H][W] (True = lit) and an 'L' preview image."""
    small = img.resize((W, H), Image.LANCZOS)
    px = small.load()
    grid = [[px[x, y] >= 128 for x in range(W)] for y in range(H)]
    # rebuild a clean 1-bit preview from the thresholded grid
    prev = Image.new("L", (W, H), 0)
    pp = prev.load()
    for y in range(H):
        for x in range(W):
            pp[x, y] = 255 if grid[y][x] else 0
    return grid, prev


def s(v):
    """Scale a 1x coordinate/length to supersample space."""
    return v * SS


# --------------------------------------------------------------------------- #
# Drawing primitives (all take 1x coords; scaled internally)
# --------------------------------------------------------------------------- #
def eye_rrect(d, cx, cy, w, h, r):
    """Filled rounded-rectangle eye."""
    w = max(w, 2); h = max(h, 2)
    r = max(0, min(r, w / 2, h / 2))
    x0, y0 = s(cx - w / 2), s(cy - h / 2)
    x1, y1 = s(cx + w / 2), s(cy + h / 2)
    d.rounded_rectangle([x0, y0, x1, y1], radius=s(r), fill=255)


def eye_arc(d, cx, cy, w, kind="happy", thick=6, h=None):
    """A curved eye: 'happy' = upward ^ arc, 'sad' = downward, 'flat' = line."""
    h = h if h is not None else w * 0.55
    x0, y0 = s(cx - w / 2), s(cy - h / 2)
    x1, y1 = s(cx + w / 2), s(cy + h / 2)
    t = int(s(thick))
    if kind == "flat":
        d.line([s(cx - w / 2), s(cy), s(cx + w / 2), s(cy)], fill=255, width=t)
        return
    if kind == "happy":       # smiling closed eye: arc opening downward (a hill)
        d.arc([x0, y0, x1, y1 + s(h)], start=180, end=360, fill=255, width=t)
    else:                      # 'sad' : arc opening upward (a valley)
        d.arc([x0, y0 - s(h), x1, y1], start=0, end=180, fill=255, width=t)


def mouth(d, cx, cy, w, curve, thick=5):
    """Smile (curve>0), frown (curve<0), or flat (curve==0)."""
    t = int(s(thick))
    if abs(curve) < 0.5:
        d.line([s(cx - w / 2), s(cy), s(cx + w / 2), s(cy)], fill=255, width=t)
        return
    bow = s(abs(curve))
    x0, y0, x1, y1 = s(cx - w / 2), s(cy), s(cx + w / 2), s(cy)
    if curve > 0:              # smile
        d.arc([x0, y0 - bow, x1, y1 + bow], start=20, end=160, fill=255, width=t)
    else:                      # frown
        d.arc([x0, y0 - bow, x1, y1 + bow], start=200, end=340, fill=255, width=t)


def mouth_open(d, cx, cy, w, h):
    """Filled open mouth (yawn / surprise)."""
    d.ellipse([s(cx - w / 2), s(cy - h / 2), s(cx + w / 2), s(cy + h / 2)], fill=255)


def heart(d, cx, cy, size):
    """Filled heart centred at (cx,cy). 'size' ~ full width."""
    r = size / 4.0
    # two top lobes
    d.ellipse([s(cx - size/2), s(cy - size/2), s(cx - size/2 + 2*r), s(cy - size/2 + 2*r)], fill=255)
    d.ellipse([s(cx + size/2 - 2*r), s(cy - size/2), s(cx + size/2), s(cy - size/2 + 2*r)], fill=255)
    # bottom triangle
    top = cy - size/2 + r*0.7
    d.polygon([s(cx - size/2 + 0.15*size), s(top),
               s(cx + size/2 - 0.15*size), s(top),
               s(cx), s(cy + size/2)], fill=255)


def star(d, cx, cy, size, spikes=4):
    """A 4-point sparkle star."""
    outer = size / 2.0
    inner = outer * 0.34
    pts = []
    for i in range(spikes * 2):
        ang = math.pi * i / spikes - math.pi / 2
        rad = outer if i % 2 == 0 else inner
        pts.append((s(cx + rad * math.cos(ang)), s(cy + rad * math.sin(ang))))
    d.polygon(pts, fill=255)


def sparkle(d, cx, cy, size):
    """A small 4-ray twinkle (plus + diagonal)."""
    t = int(s(1.6))
    r = size / 2
    d.line([s(cx - r), s(cy), s(cx + r), s(cy)], fill=255, width=t)
    d.line([s(cx), s(cy - r), s(cx), s(cy + r)], fill=255, width=t)
    r2 = r * 0.55
    d.line([s(cx - r2), s(cy - r2), s(cx + r2), s(cy + r2)], fill=255, width=max(1, t-1))
    d.line([s(cx - r2), s(cy + r2), s(cx + r2), s(cy - r2)], fill=255, width=max(1, t-1))


def zchar(d, cx, cy, size):
    """A blocky 'Z' for sleep."""
    t = int(s(2.2))
    r = size / 2
    d.line([s(cx - r), s(cy - r), s(cx + r), s(cy - r)], fill=255, width=t)  # top
    d.line([s(cx + r), s(cy - r), s(cx - r), s(cy + r)], fill=255, width=t)  # diag
    d.line([s(cx - r), s(cy + r), s(cx + r), s(cy + r)], fill=255, width=t)  # bottom


def teardrop(d, cx, cy, size):
    r = size / 2
    d.ellipse([s(cx - r), s(cy - r*0.6), s(cx + r), s(cy + r*1.4)], fill=255)
    d.polygon([s(cx - r*0.5), s(cy - r*0.4), s(cx + r*0.5), s(cy - r*0.4),
               s(cx), s(cy - r*1.5)], fill=255)


def brow(d, cx, cy, w, angle, thick=4):
    """An eyebrow line at 'angle' degrees (positive = inner-down, angry)."""
    t = int(s(thick))
    a = math.radians(angle)
    dx = (w/2) * math.cos(a); dy = (w/2) * math.sin(a)
    d.line([s(cx - dx), s(cy - dy), s(cx + dx), s(cy + dy)], fill=255, width=t)


# --------------------------------------------------------------------------- #
# Easing / helpers
# --------------------------------------------------------------------------- #
def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def lerp(a, b, t):
    return a + (b - a) * t


def ping(t):
    """0->1->0 triangle with easing."""
    return ease(1 - abs(2 * t - 1))


# --------------------------------------------------------------------------- #
# Neutral face
# --------------------------------------------------------------------------- #
def draw_neutral(d, blink=0.0, smile=5.0):
    """blink: 0 open .. 1 fully closed (height collapses)."""
    h = lerp(EYE_H, 3, ease(blink))
    eye_rrect(d, EYE_CX_L, EYE_CY, EYE_W, h, EYE_R)
    eye_rrect(d, EYE_CX_R, EYE_CY, EYE_W, h, EYE_R)
    if smile:
        mouth(d, CX, MOUTH_CY, 18, smile, thick=4)


def neutral_frame():
    img, d = new_canvas()
    draw_neutral(d)
    return finalize(img)[1]


# --------------------------------------------------------------------------- #
# .qgif writer (mirrors tools/gif2qbit.py polarity on white-on-black art)
# --------------------------------------------------------------------------- #
def write_qgif(path, grids, delays):
    """grids: list of bool[H][W] (True = lit face pixel). delays: ms per frame."""
    n = len(grids)
    assert n <= 255, f"{n} frames > 255"
    bpr = W // 8
    with open(path, "wb") as f:
        f.write(struct.pack("<B", n))
        f.write(struct.pack("<H", W))
        f.write(struct.pack("<H", H))
        for dl in delays:
            f.write(struct.pack("<H", int(dl)))
        for g in grids:
            buf = bytearray(bpr * H)
            for y in range(H):
                for x in range(W):
                    # stored bit ON == background (matches gif2qbit on white/black)
                    if not g[y][x]:
                        buf[y * bpr + (x // 8)] |= (1 << (7 - (x % 8)))
            f.write(bytes(buf))
