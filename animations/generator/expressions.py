#!/usr/bin/env python3
"""Expression choreography for QBIT. Each generator returns (grids, delays),
starting and ending on (or near) the neutral face so it blends into shuffle."""
import math
from faces import (
    new_canvas, finalize, s, lerp, ease, ping,
    eye_rrect, eye_arc, mouth, mouth_open, heart, star, sparkle, zchar,
    teardrop, brow, draw_neutral,
    CX, EYE_CX_L, EYE_CX_R, EYE_CY, EYE_W, EYE_H, EYE_R, MOUTH_CY, W, H,
)

def _grid(drawfn):
    img, d = new_canvas()
    drawfn(d)
    return finalize(img)[0]

def eyes(d, w=EYE_W, h=EYE_H, r=EYE_R, dxL=0, dyL=0, dxR=0, dyR=0, hL=None, hR=None):
    eye_rrect(d, EYE_CX_L + dxL, EYE_CY + dyL, w, hL if hL is not None else h, r)
    eye_rrect(d, EYE_CX_R + dxR, EYE_CY + dyR, w, hR if hR is not None else h, r)

def hold(grids, delays, grid, n, ms):
    for _ in range(n):
        grids.append(grid); delays.append(ms)


# --------------------------------------------------------------------------- #
def blink():
    """Sit neutral, then two quick natural blinks."""
    g, dl = [], []
    neutral = _grid(lambda d: draw_neutral(d))
    hold(g, dl, neutral, 8, 70)
    for _ in range(2):
        for k in range(7):                      # close and open
            b = ping(k / 6)
            g.append(_grid(lambda d, b=b: draw_neutral(d, blink=b))); dl.append(40)
        hold(g, dl, neutral, 5, 70)
    hold(g, dl, neutral, 6, 70)
    return g, dl


def happy():
    """Eyes arc into a big smile with a gentle bob."""
    g, dl = [], []
    def frame(t, bob):
        def dr(d):
            if t < 1:                            # rrect eyes morphing up
                h = lerp(EYE_H, EYE_H * 0.5, ease(t))
                eyes(d, h=h, dyL=-bob, dyR=-bob)
                mouth(d, CX, MOUTH_CY, lerp(18, 24, ease(t)), lerp(5, 8, ease(t)), thick=4)
            else:
                eye_arc(d, EYE_CX_L, EYE_CY - 2 - bob, 22, "happy", thick=6)
                eye_arc(d, EYE_CX_R, EYE_CY - 2 - bob, 22, "happy", thick=6)
                mouth(d, CX, MOUTH_CY, 24, 8, thick=4)
        return _grid(dr)
    for k in range(6):                           # ease into happy
        g.append(frame(k / 5, 0)); dl.append(55)
    for k in range(20):                          # hold + bob
        bob = 2 * math.sin(k / 20 * 2 * math.pi * 2)
        g.append(frame(1, max(0, bob))); dl.append(55)
    for k in range(6):                           # ease back
        g.append(frame(1 - k / 5, 0)); dl.append(55)
    return g, dl


def love():
    """Eyes become pulsing hearts."""
    g, dl = [], []
    neutral = _grid(lambda d: draw_neutral(d))
    hold(g, dl, neutral, 4, 70)
    for k in range(5):                            # morph rrect -> heart
        t = ease(k / 4)
        def dr(d, t=t):
            h = lerp(EYE_H, 6, t)
            if t < 0.9:
                eyes(d, h=h)
            sz = lerp(6, 22, t)
            heart(d, EYE_CX_L, EYE_CY, sz); heart(d, EYE_CX_R, EYE_CY, sz)
            mouth(d, CX, MOUTH_CY, 20, lerp(5, 8, t), thick=4)
        g.append(_grid(dr)); dl.append(55)
    for k in range(22):                           # heartbeat pulse
        beat = 22 + 3 * math.sin(k / 22 * 2 * math.pi * 3)
        def dr(d, sz=beat):
            heart(d, EYE_CX_L, EYE_CY, sz); heart(d, EYE_CX_R, EYE_CY, sz)
            mouth(d, CX, MOUTH_CY, 20, 8, thick=4)
        g.append(_grid(dr)); dl.append(55)
    for k in range(5):                            # back to neutral
        t = ease(1 - k / 4)
        def dr(d, t=t):
            h = lerp(EYE_H, 6, t)
            if t < 0.9: eyes(d, h=h)
            heart(d, EYE_CX_L, EYE_CY, lerp(6, 22, t)); heart(d, EYE_CX_R, EYE_CY, lerp(6, 22, t))
            mouth(d, CX, MOUTH_CY, 20, lerp(5, 8, t), thick=4)
        g.append(_grid(dr)); dl.append(55)
    hold(g, dl, neutral, 4, 70)
    return g, dl


def sleepy():
    """Eyes droop and close, z-z-z rises, then a small wake blink."""
    g, dl = [], []
    neutral = _grid(lambda d: draw_neutral(d))
    hold(g, dl, neutral, 4, 90)
    for k in range(8):                            # droop: eyes shrink from top
        t = ease(k / 7)
        h = lerp(EYE_H, 4, t)
        dy = lerp(0, 6, t)                        # settle downward
        g.append(_grid(lambda d, h=h, dy=dy: (
            eyes(d, h=h, dyL=dy, dyR=dy),
            mouth(d, CX, MOUTH_CY + 1, 12, 2, thick=4)))); dl.append(90)
    # closed + zzz cycling
    def closed(zc):
        def dr(d):
            # flat droopy closed eyes (asleep, not smiling)
            eye_arc(d, EYE_CX_L, EYE_CY + 6, 22, "happy", thick=5, h=6)
            eye_arc(d, EYE_CX_R, EYE_CY + 6, 22, "happy", thick=5, h=6)
            mouth(d, CX, MOUTH_CY + 1, 10, 1, thick=4)
            for i, (zx, zy, zs) in enumerate(zc):
                zchar(d, zx, zy, zs)
        return _grid(dr)
    zseq = [
        [(96, 20, 4)],
        [(96, 18, 5), (104, 12, 6)],
        [(96, 16, 5), (104, 10, 6), (112, 5, 7)],
        [(104, 9, 6), (112, 4, 7)],
        [(112, 4, 7)],
        [],
    ]
    for _ in range(2):
        for zc in zseq:
            g.append(closed(zc)); dl.append(120)
    for k in range(6):                            # wake up
        t = ease(k / 5)
        h = lerp(4, EYE_H, t); dy = lerp(6, 0, t)
        g.append(_grid(lambda d, h=h, dy=dy: (
            eyes(d, h=h, dyL=dy, dyR=dy), mouth(d, CX, MOUTH_CY, 16, 4, thick=4)))); dl.append(70)
    hold(g, dl, neutral, 3, 70)
    return g, dl


def surprised():
    """Quick pop-wide with an exclamation and a small shake."""
    g, dl = [], []
    neutral = _grid(lambda d: draw_neutral(d))
    hold(g, dl, neutral, 5, 70)
    def bang(jx=0, sz=1.0):
        def dr(d):
            w = EYE_W * lerp(1, 1.35, sz); h = EYE_H * lerp(1, 1.28, sz)
            eyes(d, w=w, h=h, r=EYE_R + 3, dxL=jx, dxR=jx, dyL=-1, dyR=-1)
            mouth_open(d, CX + jx, MOUTH_CY + 3, 13 * sz, 13 * sz)
        return _grid(dr)
    g.append(bang(0, 0.4)); dl.append(50)
    g.append(bang(0, 1.0)); dl.append(60)
    for k in range(8):                            # jitter shake
        jx = (1 if k % 2 else -1) * 2
        g.append(bang(jx, 1.0)); dl.append(45)
    for k in range(6):                            # settle back
        t = ease(1 - k / 5)
        g.append(bang(0, t)); dl.append(55)
    hold(g, dl, neutral, 4, 70)
    return g, dl


def look_around():
    """Curious: eyes glance left, right, then re-centre."""
    g, dl = [], []
    def look(dx, squash=0):
        return _grid(lambda d: (
            eyes(d, w=EYE_W - squash, dxL=dx, dxR=dx),
            mouth(d, CX + dx * 0.5, MOUTH_CY, 14, 4, thick=4)))
    seq = [(0, 6), (-14, 8), (-14, 6), (14, 12), (14, 8), (0, 8)]
    prev = 0
    hold(g, dl, look(0), 4, 70)
    for target, n in seq:
        for k in range(n):
            t = ease(k / max(1, n - 1))
            dx = lerp(prev, target, t)
            sq = 4 * math.sin(t * math.pi) if abs(target - prev) > 4 else 0
            g.append(look(dx, sq)); dl.append(55)
        prev = target
    hold(g, dl, look(0), 4, 70)
    return g, dl


def wink():
    """A friendly right-eye wink with a cheeky smile."""
    g, dl = [], []
    neutral = _grid(lambda d: draw_neutral(d))
    hold(g, dl, neutral, 5, 70)
    def frame(t):
        def dr(d):
            eye_rrect(d, EYE_CX_L, EYE_CY, EYE_W, EYE_H, EYE_R)      # left open
            if t < 0.6:
                eye_rrect(d, EYE_CX_R, EYE_CY, EYE_W, lerp(EYE_H, 4, ease(t / 0.6)), EYE_R)
            else:
                eye_arc(d, EYE_CX_R, EYE_CY + 2, 22, "happy", thick=6)  # closed arc
            mouth(d, CX, MOUTH_CY, lerp(18, 22, ease(t)), lerp(5, 8, ease(t)), thick=4)
        return _grid(dr)
    for k in range(6): g.append(frame(k / 5)); dl.append(50)
    hold(g, dl, frame(1.0), 10, 70)
    for k in range(6): g.append(frame(1 - k / 5)); dl.append(50)
    hold(g, dl, neutral, 3, 70)
    return g, dl


def dizzy():
    """Eyes shrink to circling dots with orbiting sparkles and a wavy mouth."""
    g, dl = [], []
    neutral = _grid(lambda d: draw_neutral(d))
    hold(g, dl, neutral, 3, 70)
    N = 26
    for k in range(N):
        a = k / N * 2 * math.pi * 2
        def dr(d, a=a):
            rx, ry = 5 * math.cos(a), 4 * math.sin(a)
            eye_rrect(d, EYE_CX_L + rx, EYE_CY + ry, 10, 10, 5)
            eye_rrect(d, EYE_CX_R - rx, EYE_CY - ry, 10, 10, 5)
            # wavy mouth
            from faces import s as sc, SS
            import faces
            pts = []
            for i in range(9):
                mx = CX - 12 + i * 3
                my = MOUTH_CY + 2 + 2 * math.sin(a + i * 0.9)
                pts.append((sc(mx), sc(my)))
            d.line(pts, fill=255, width=int(sc(2)))
            # orbiting sparkles above
            for j in range(2):
                sa = a * 1.5 + j * math.pi
                sparkle(d, CX + 20 * math.cos(sa), 12 + 5 * math.sin(sa), 7)
        g.append(_grid(dr)); dl.append(60)
    for k in range(6):                            # refocus to neutral
        t = ease(k / 5)
        def dr(d, t=t):
            eye_rrect(d, EYE_CX_L, EYE_CY, lerp(10, EYE_W, t), lerp(10, EYE_H, t), lerp(5, EYE_R, t))
            eye_rrect(d, EYE_CX_R, EYE_CY, lerp(10, EYE_W, t), lerp(10, EYE_H, t), lerp(5, EYE_R, t))
            mouth(d, CX, MOUTH_CY, 16, lerp(0, 5, t), thick=4)
        g.append(_grid(dr)); dl.append(55)
    hold(g, dl, neutral, 3, 70)
    return g, dl


def angry():
    """Brows slam down, eyes narrow, frown, and a tremble."""
    g, dl = [], []
    neutral = _grid(lambda d: draw_neutral(d))
    hold(g, dl, neutral, 4, 70)
    def frame(t, jx=0):
        def dr(d):
            h = lerp(EYE_H, 16, ease(t))
            eyes(d, h=h, dyL=4, dyR=4, dxL=jx, dxR=jx)
            bl = lerp(0, 22, ease(t))
            brow(d, EYE_CX_L + jx, EYE_CY - 12, 20, +bl, thick=5)     # inner-down
            brow(d, EYE_CX_R + jx, EYE_CY - 12, 20, -bl, thick=5)
            mouth(d, CX + jx, MOUTH_CY + 2, 16, lerp(-1, -6, ease(t)), thick=4)
        return _grid(dr)
    for k in range(6): g.append(frame(k / 5)); dl.append(50)
    for k in range(12):                           # tremble
        jx = (1 if k % 2 else -1) * 1
        g.append(frame(1, jx)); dl.append(45)
    for k in range(6): g.append(frame(1 - k / 5)); dl.append(50)
    hold(g, dl, neutral, 3, 70)
    return g, dl


def sad():
    """Eyes droop into sad arcs, a tear wells and falls."""
    g, dl = [], []
    neutral = _grid(lambda d: draw_neutral(d))
    hold(g, dl, neutral, 4, 80)
    def face(t, tear_y=None, tear_sz=0):
        def dr(d):
            # upper eyelids come down -> sad half-eyes
            h = lerp(EYE_H, 12, ease(t))
            eyes(d, h=h, dyL=6 * ease(t), dyR=6 * ease(t))
            brow(d, EYE_CX_L, EYE_CY - 12 + 4 * ease(t), 18, -14 * ease(t), thick=4)
            brow(d, EYE_CX_R, EYE_CY - 12 + 4 * ease(t), 18, +14 * ease(t), thick=4)
            mouth(d, CX, MOUTH_CY + 3, 16, lerp(2, -6, ease(t)), thick=4)
            if tear_sz > 0:
                teardrop(d, EYE_CX_L - 8, tear_y, tear_sz)
        return _grid(dr)
    for k in range(7): g.append(face(k / 6)); dl.append(70)
    # tear falls
    for k in range(12):
        ty = lerp(EYE_CY + 6, H - 4, ease(k / 11))
        g.append(face(1, tear_y=ty, tear_sz=6)); dl.append(60)
    hold(g, dl, face(1), 3, 80)
    for k in range(6): g.append(face(1 - k / 5)); dl.append(70)
    hold(g, dl, neutral, 3, 80)
    return g, dl


def excited():
    """Eyes turn into twinkling stars with a bouncy open smile."""
    g, dl = [], []
    neutral = _grid(lambda d: draw_neutral(d))
    hold(g, dl, neutral, 3, 70)
    for k in range(5):                            # morph to stars
        t = ease(k / 4)
        def dr(d, t=t):
            if t < 0.8:
                eyes(d, h=lerp(EYE_H, 8, t))
            star(d, EYE_CX_L, EYE_CY, lerp(6, 26, t))
            star(d, EYE_CX_R, EYE_CY, lerp(6, 26, t))
            mouth(d, CX, MOUTH_CY, lerp(18, 22, t), lerp(5, 9, t), thick=4)
        g.append(_grid(dr)); dl.append(50)
    for k in range(18):                           # twinkle + bounce
        tw = 26 + 4 * math.sin(k / 18 * 2 * math.pi * 3)
        bob = 2 * abs(math.sin(k / 18 * 2 * math.pi * 2))
        def dr(d, tw=tw, bob=bob):
            star(d, EYE_CX_L, EYE_CY - bob, tw)
            star(d, EYE_CX_R, EYE_CY - bob, tw)
            sparkle(d, 22, 12, 6); sparkle(d, 106, 14, 6)
            mouth_open(d, CX, MOUTH_CY + 1, 12, 8)
        g.append(_grid(dr)); dl.append(50)
    for k in range(5):
        t = ease(1 - k / 4)
        def dr(d, t=t):
            if t < 0.8: eyes(d, h=lerp(EYE_H, 8, t))
            star(d, EYE_CX_L, EYE_CY, lerp(6, 26, t)); star(d, EYE_CX_R, EYE_CY, lerp(6, 26, t))
            mouth(d, CX, MOUTH_CY, 20, 6, thick=4)
        g.append(_grid(dr)); dl.append(50)
    hold(g, dl, neutral, 3, 70)
    return g, dl


def laugh():
    """Closed happy arcs giggling up and down with an open mouth."""
    g, dl = [], []
    neutral = _grid(lambda d: draw_neutral(d))
    hold(g, dl, neutral, 4, 70)
    def frame(bob, mo):
        def dr(d):
            eye_arc(d, EYE_CX_L, EYE_CY - 2 - bob, 22, "happy", thick=6)
            eye_arc(d, EYE_CX_R, EYE_CY - 2 - bob, 22, "happy", thick=6)
            mouth_open(d, CX, MOUTH_CY + 2 - bob, 14, mo)
        return _grid(dr)
    for k in range(4): g.append(frame(0, lerp(2, 9, ease(k / 3)))); dl.append(50)
    for k in range(18):                           # giggle bounce
        bob = 3 * abs(math.sin(k / 18 * 2 * math.pi * 4))
        mo = 6 + 4 * math.sin(k / 18 * 2 * math.pi * 4)
        g.append(frame(bob, mo)); dl.append(45)
    for k in range(5): g.append(frame(0, lerp(9, 2, ease(k / 4)))); dl.append(50)
    hold(g, dl, neutral, 3, 70)
    return g, dl


def skeptical():
    """One brow up, eyes narrow to a slow side-eye, flat mouth."""
    g, dl = [], []
    neutral = _grid(lambda d: draw_neutral(d))
    hold(g, dl, neutral, 4, 80)
    def frame(t, dx=0):
        def dr(d):
            hL = lerp(EYE_H, 14, ease(t)); hR = lerp(EYE_H, 20, ease(t))
            eye_rrect(d, EYE_CX_L + dx, EYE_CY + 4 * ease(t), EYE_W, hL, EYE_R)
            eye_rrect(d, EYE_CX_R + dx, EYE_CY + 2 * ease(t), EYE_W, hR, EYE_R)
            brow(d, EYE_CX_R + dx, EYE_CY - 14 - 3 * ease(t), 18, -8, thick=4)  # raised
            brow(d, EYE_CX_L + dx, EYE_CY - 11, 16, 4, thick=4)
            mouth(d, CX + dx, MOUTH_CY + 2, 14, lerp(4, 0, ease(t)), thick=4)
        return _grid(dr)
    for k in range(6): g.append(frame(k / 5)); dl.append(60)
    for k in range(8):                            # glance right
        g.append(frame(1, lerp(0, 8, ease(k / 7)))); dl.append(60)
    hold(g, dl, frame(1, 8), 4, 70)
    for k in range(8):                            # glance back
        g.append(frame(1, lerp(8, 0, ease(k / 7)))); dl.append(60)
    for k in range(6): g.append(frame(1 - k / 5)); dl.append(60)
    hold(g, dl, neutral, 3, 80)
    return g, dl


ALL = {
    "eye_blink":       blink,
    "mood_happy":      happy,
    "mood_love":       love,
    "action_sleepy":   sleepy,
    "mood_surprised":  surprised,
    "action_lookaround": look_around,
    "eye_wink_smile":  wink,
    "action_dizzy":    dizzy,
    "mood_angry":      angry,
    "mood_sad":        sad,
    "mood_excited":    excited,
    "action_laugh":    laugh,
    "mood_skeptical":  skeptical,
}
