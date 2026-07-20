#!/usr/bin/env python3
"""Generate all .qgif faces, per-expression preview GIFs, and a contact sheet."""
from pathlib import Path
from PIL import Image, ImageDraw
import faces
from expressions import ALL

OUT = Path("out"); OUT.mkdir(exist_ok=True)
GIF = Path("preview_gifs"); GIF.mkdir(exist_ok=True)


def grid_to_img(g):
    im = Image.new("L", (faces.W, faces.H), 0); px = im.load()
    for y in range(faces.H):
        for x in range(faces.W):
            px[x, y] = 255 if g[y][x] else 0
    return im


def sheet_row(name, grids, delays, scale=2, cols=14):
    n = len(grids)
    idx = list(range(n)) if n <= cols else [round(i*(n-1)/(cols-1)) for i in range(cols)]
    cw, ch = faces.W*scale, faces.H*scale
    pad = 5; top = 20
    sh = Image.new("RGB", (len(idx)*cw + (len(idx)+1)*pad, top + ch + 2*pad), (16, 16, 20))
    d = ImageDraw.Draw(sh)
    kb = (5 + n*2 + n*1024)/1024
    d.text((pad, 5), f"{name}   {n} frames, {kb:.0f} KB", fill=(235, 235, 240))
    for j, fi in enumerate(idx):
        x = pad + j*(cw+pad); y = top+pad
        sh.paste(grid_to_img(grids[fi]).convert("RGB").resize((cw, ch), Image.NEAREST), (x, y))
    return sh


def main():
    rows = []
    total_kb = 0
    for name, fn in ALL.items():
        grids, delays = fn()
        faces.write_qgif(OUT/f"{name}.qgif", grids, delays)
        kb = (OUT/f"{name}.qgif").stat().st_size/1024
        total_kb += kb
        ims = [grid_to_img(g).convert("P").resize((faces.W*3, faces.H*3), Image.NEAREST) for g in grids]
        ims[0].save(GIF/f"{name}.gif", save_all=True, append_images=ims[1:],
                    duration=delays, loop=0, disposal=2)
        rows.append(sheet_row(name, grids, delays))
        print(f"{name:20} {len(grids):3d} frames  {kb:6.1f} KB")

    print(f"\nTOTAL {total_kb:.0f} KB across {len(ALL)} files")
    w = max(r.width for r in rows); tot = sum(r.height+6 for r in rows)
    combo = Image.new("RGB", (w, tot), (16, 16, 20)); y = 0
    for r in rows:
        combo.paste(r, (0, y)); y += r.height+6
    combo.save("preview_all.png")
    print("saved preview_all.png", combo.size)


if __name__ == "__main__":
    main()
