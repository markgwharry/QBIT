#!/usr/bin/env python3
"""Shared helpers: decode .qgif -> frames, and render an OLED-appearance
contact sheet so we can eyeball a face the way the device shows it
(bright pixels glowing on a dark background)."""
import struct
from pathlib import Path
from PIL import Image, ImageDraw

W, H = 128, 64
FRAME_SIZE = (W // 8) * H  # 1024


def decode_qgif(path):
    """Return (frames, delays) where each frame is a PIL 'L' image showing the
    OLED appearance: source-white -> lit (white), source-black -> dark (black)."""
    data = Path(path).read_bytes()
    fc = data[0]
    w = struct.unpack_from("<H", data, 1)[0]
    h = struct.unpack_from("<H", data, 3)[0]
    fsz = (w // 8) * h
    off = 5
    delays = [struct.unpack_from("<H", data, off + 2 * i)[0] for i in range(fc)]
    off += 2 * fc
    frames = []
    for i in range(fc):
        bm = data[off:off + fsz]; off += fsz
        img = Image.new("L", (w, h), 0)
        px = img.load()
        bpr = w // 8
        for y in range(h):
            for x in range(w):
                bit = (bm[y * bpr + (x // 8)] >> (7 - (x % 8))) & 1
                # qgif bit ON == source-dark; OLED lights source-light pixels.
                # So OLED-lit (white) iff bit OFF.
                px[x, y] = 0 if bit else 255
        frames.append(img)
    return frames, delays


def contact_sheet(frames, delays=None, scale=3, cols=8, pad=6, label=None):
    """Lay frames out in a grid on a dark sheet, each in a rounded 'screen'."""
    n = len(frames)
    cols = min(cols, n)
    rows = (n + cols - 1) // cols
    cw, ch = W * scale, H * scale
    top = 22 if label else 0
    sheet = Image.new("RGB", (cols * cw + (cols + 1) * pad,
                              top + rows * ch + (rows + 1) * pad), (18, 18, 22))
    d = ImageDraw.Draw(sheet)
    if label:
        d.text((pad, 6), label, fill=(230, 230, 235))
    for i, fr in enumerate(frames):
        r, c = divmod(i, cols)
        x = pad + c * (cw + pad)
        y = top + pad + r * (ch + pad)
        d.rectangle([x - 1, y - 1, x + cw, y + ch], fill=(0, 0, 0))
        sheet.paste(fr.convert("RGB").resize((cw, ch), Image.NEAREST), (x, y))
        if delays:
            d.text((x + 2, y + 2), f"{i}:{delays[i]}ms", fill=(120, 200, 120))
    return sheet
