#!/usr/bin/env python3
"""Build shareable animated previews:
   - reel.gif : each expression full-screen (4x) with its name, in sequence
   - grid.gif : all expressions playing at once in a labelled grid
"""
from pathlib import Path
from PIL import Image, ImageDraw
from pathlib import Path
import faces
from expressions import ALL
from render import grid_to_img

HERE = Path(__file__).resolve().parent
PREV = HERE.parent / "previews"; PREV.mkdir(exist_ok=True)
SCALE = 4
CW, CH = faces.W*SCALE, faces.H*SCALE
anims = {name: fn() for name, fn in ALL.items()}


def reel():
    frames, durs = [], []
    for name, (grids, delays) in anims.items():
        for g, dl in zip(grids, delays):
            canvas = Image.new("RGB", (CW, CH+26), (10, 10, 12))
            canvas.paste(grid_to_img(g).convert("RGB").resize((CW, CH), Image.NEAREST), (0, 26))
            d = ImageDraw.Draw(canvas)
            d.text((6, 8), name, fill=(120, 230, 140))
            frames.append(canvas.convert("P", palette=Image.ADAPTIVE, colors=8)); durs.append(dl)
        # brief pause on last frame
        for _ in range(6):
            frames.append(frames[-1]); durs.append(60)
    frames[0].save(PREV / "_reel.gif", save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, disposal=2)
    print("saved previews/_reel.gif", len(frames), "frames")


def grid():
    import math
    names = list(anims)
    n = len(names); cols = 4; rows = math.ceil(n/cols)
    s = 2; cw, ch = faces.W*s, faces.H*s
    pad = 6; lab = 16
    gw = cols*cw + (cols+1)*pad
    gh = rows*(ch+lab) + (rows+1)*pad
    maxlen = max(len(g) for g, _ in anims.values())
    frames, durs = [], []
    for t in range(maxlen):
        canvas = Image.new("RGB", (gw, gh), (12, 12, 15))
        d = ImageDraw.Draw(canvas)
        for i, name in enumerate(names):
            grids, _ = anims[name]
            g = grids[t % len(grids)]
            r, c = divmod(i, cols)
            x = pad + c*(cw+pad); y = pad + r*(ch+lab)
            d.text((x, y), name, fill=(150, 210, 150))
            canvas.paste(grid_to_img(g).convert("RGB").resize((cw, ch), Image.NEAREST), (x, y+lab))
        frames.append(canvas.convert("P", palette=Image.ADAPTIVE, colors=16)); durs.append(60)
    frames[0].save(HERE / "grid.gif", save_all=True, append_images=frames[1:],
                   duration=durs, loop=0, disposal=2)
    print("saved grid.gif (dev preview)", len(frames), "frames", (gw, gh))


if __name__ == "__main__":
    reel()
    grid()
