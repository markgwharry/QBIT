# QBIT Face Pack

A set of **13 expressive `.qgif` faces** for QBIT's 128×64 OLED, drawn in the
same visual language as the shipped animations (two glowing rounded‑rectangle
eyes + a little mouth). They're meant to make QBIT feel a bit more alive when
it's idle — blinks, moods, and reactions rather than static eyes.

These are **standalone, upload‑at‑will files**. They are intentionally kept out
of `firmware/data/` so they are *not* baked into the flashed default set — pick
the ones you like and upload them to a device.

## Preview

Animated previews for each face live in [`previews/`](previews/), plus
[`previews/_reel.gif`](previews/_reel.gif) which plays the whole set in sequence.

## The collection

| File | Frames | Size | What it does |
|---|---|---|---|
| `eye_blink.qgif` | 38 | 38 KB | Sits calm, then two natural blinks |
| `mood_happy.qgif` | 32 | 32 KB | Eyes curve into a big smile with a gentle bob |
| `mood_love.qgif` | 40 | 40 KB | Eyes turn into pulsing hearts |
| `mood_excited.qgif` | 34 | 34 KB | Eyes become twinkling stars with a bouncy grin |
| `action_laugh.qgif` | 34 | 34 KB | Squeezed happy eyes giggling with an open mouth |
| `eye_wink_smile.qgif` | 30 | 30 KB | A friendly one‑eye wink with a cheeky smile |
| `mood_surprised.qgif` | 25 | 25 KB | Eyes pop wide with a startled o‑mouth and a shake |
| `action_lookaround.qgif` | 56 | 56 KB | Curious glance left, right, then re‑centres |
| `mood_sad.qgif` | 35 | 35 KB | Eyes droop, brows lift, and a tear rolls down |
| `mood_angry.qgif` | 31 | 31 KB | Brows slam down, eyes narrow, a cross little tremble |
| `mood_skeptical.qgif` | 39 | 39 KB | One brow raised, a slow unconvinced side‑eye |
| `action_dizzy.qgif` | 38 | 38 KB | Eyes spin to dazed dots with orbiting sparkles |
| `action_sleepy.qgif` | 33 | 33 KB | Eyes droop shut and z‑z‑z drifts up, then wakes |

**≈466 KB total.** For reference, the SPIFFS partition is ~1.94 MB and the
shipped set + web dashboard use roughly 0.6 MB, so there's plenty of room —
but you only need to upload the ones you want.

Each face starts and ends on (or near) the neutral resting face, so it blends
smoothly into the firmware's shuffle instead of snapping between poses.

## How to put them on your QBIT

**Easiest — the device dashboard (no reflash):**

1. Browse to `http://qbit.local` on the same network as the device.
2. Open **Files** and upload any `.qgif` from [`faces/`](faces/).
3. They join the idle shuffle immediately. (Use **Next Animation**, a double‑tap,
   or the Home Assistant button to skip to one.)

**Alternative — bake into a filesystem image:** drop the files into
`firmware/data/` and run `pio run --target uploadfs`. Note this makes them part
of the flashed default set for that device.

The device accepts a `.qgif` as long as the header says 128×64 with at least one
frame — all of these do. Filenames just need to end in `.qgif` (≤64 chars); the
`eye_ / mood_ / action_` prefixes are only for tidy grouping.

## Format

`.qgif` is QBIT's binary animation format: 128×64, 1‑bit monochrome, one delay
per frame. Artwork is authored **white‑on‑black** — white pixels are the ones
that light up on the OLED. See the root README's *Animation Format* section for
the byte layout.

## Regenerating / adding more

The faces are generated procedurally, so they're easy to tweak or extend. From
[`generator/`](generator/):

```bash
pip install Pillow numpy
cd generator
python render.py      # writes out/*.qgif + preview_gifs/*.gif + preview_all.png
python previews.py    # writes reel.gif (sequence) + grid.gif (all at once)
```

- `faces.py` — the drawing engine (eye/heart/star/brow primitives, easing, the
  `.qgif` writer, which is byte‑for‑byte identical to `tools/gif2qbit.py`).
- `expressions.py` — one function per expression; add a new entry to `ALL` to
  grow the set.
- `render.py` / `previews.py` — build the `.qgif` files and the preview art.

## License

Part of the QBIT project — [CC BY‑NC‑SA 4.0](../LICENSE), same as the repo.
