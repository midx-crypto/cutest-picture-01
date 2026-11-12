#!/usr/bin/env python3
"""cutest-picture-01: "Mochi, my best friend".

A fully procedural, deterministic drawing (Python stdlib only, no network,
no model, no randomness from the environment): one chubby orange kitten,
filling the frame, with huge glossy amber eyes, blush cheeks, a tiny pink
bow and a daisy, a chubby body, and both paws together holding one pink
heart. Warm pastel background with polka dots and floating hearts.
Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png), 512x512 PNG.
"""
import math
import os
import struct
import zlib

W = H = 512
OUT = os.path.join(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"), "entry.png")

# --- deterministic PRNG (splitmix64, fixed seed) ---------------------------
_state = [0x3C6EF372FE94F82B]


def rnd():
    _state[0] = (_state[0] + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
    z = _state[0]
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
    return ((z ^ (z >> 31)) & 0xFFFFFFFFFFFFFFFF) / 18446744073709551616.0


def rrange(a, b):
    return a + (b - a) * rnd()


# --- canvas -----------------------------------------------------------------
fb = [bytearray(W * 3) for _ in range(H)]


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def px(x, y, c, alpha=1.0):
    if 0 <= x < W and 0 <= y < H:
        i = x * 3
        row = fb[y]
        if alpha >= 1.0:
            row[i], row[i + 1], row[i + 2] = c
        else:
            row[i] = int(row[i] + (c[0] - row[i]) * alpha)
            row[i + 1] = int(row[i + 1] + (c[1] - row[i + 1]) * alpha)
            row[i + 2] = int(row[i + 2] + (c[2] - row[i + 2]) * alpha)


def hline(y, x0, x1, c, alpha=1.0):
    if y < 0 or y >= H:
        return
    x0 = max(0, int(x0))
    x1 = min(W - 1, int(x1))
    if x1 < x0:
        return
    row = fb[y]
    if alpha >= 1.0:
        for x in range(x0, x1 + 1):
            i = x * 3
            row[i], row[i + 1], row[i + 2] = c
    else:
        for x in range(x0, x1 + 1):
            i = x * 3
            row[i] = int(row[i] + (c[0] - row[i]) * alpha)
            row[i + 1] = int(row[i + 1] + (c[1] - row[i + 1]) * alpha)
            row[i + 2] = int(row[i + 2] + (c[2] - row[i + 2]) * alpha)


def disc(cx, cy, r, c, alpha=1.0):
    for dy in range(-r, r + 1):
        half = int(math.sqrt(max(0, r * r - dy * dy)))
        hline(cy + dy, cx - half, cx + half, c, alpha)


def ellipse(cx, cy, rx, ry, c, alpha=1.0):
    for dy in range(-ry, ry + 1):
        t = 1.0 - (dy * dy) / float(ry * ry)
        if t <= 0:
            continue
        half = int(rx * math.sqrt(t))
        hline(cy + dy, cx - half, cx + half, c, alpha)


def poly(points, c, alpha=1.0):
    ys = [p[1] for p in points]
    for y in range(max(0, int(min(ys))), min(H - 1, int(max(ys)) + 1)):
        xs = []
        n = len(points)
        for i in range(n):
            x1, y1 = points[i]
            x2, y2 = points[(i + 1) % n]
            if (y1 <= y < y2) or (y2 <= y < y1):
                xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
        xs.sort()
        for i in range(0, len(xs) - 1, 2):
            hline(y, xs[i], xs[i + 1], c, alpha)


def line(x0, y0, x1, y1, c, alpha=1.0):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n + 1):
        t = i / max(1, n)
        px(int(x0 + (x1 - x0) * t), int(y0 + (y1 - y0) * t), c, alpha)


def heart(cx, cy, s, c, alpha=1.0):
    disc(int(cx - s * 0.45), int(cy - s * 0.25), int(s * 0.5), c, alpha)
    disc(int(cx + s * 0.45), int(cy - s * 0.25), int(s * 0.5), c, alpha)
    poly([(cx - s * 0.92, cy - s * 0.05), (cx + s * 0.92, cy - s * 0.05),
          (cx, cy + s * 0.95)], c, alpha)


def flower(cx, cy, r, petal, center):
    for a in range(5):
        th = math.radians(a * 72 - 90)
        disc(int(cx + r * 0.62 * math.cos(th)), int(cy + r * 0.62 * math.sin(th)),
             int(r * 0.45), petal)
    disc(cx, cy, int(r * 0.42), center)


# --- background: soft radial cream -> pink ----------------------------------
for y in range(H):
    for x in range(W):
        d = math.sqrt(((x - W / 2) / (W / 2)) ** 2 + ((y - H / 2) / (H / 2)) ** 2)
        t = min(1.0, d)
        col = lerp((255, 243, 224), (255, 214, 228), t)
        i = x * 3
        fb[y][i], fb[y][i + 1], fb[y][i + 2] = col

# soft warm glow behind the kitten
disc(256, 250, 215, (255, 250, 240), 0.18)

# polka dots
for _ in range(46):
    x = int(rrange(20, W - 20))
    y = int(rrange(20, H - 20))
    r = int(rrange(4, 9))
    col = (255, 255, 255) if rnd() < 0.5 else (255, 183, 205)
    disc(x, y, r, col, 0.5)

# floating hearts in the background
for (hx, hy, hs) in [(72, 96, 16), (448, 84, 13), (462, 300, 15), (52, 330, 12),
                      (420, 430, 12), (88, 440, 14)]:
    heart(hx, hy, hs, (255, 143, 176), 0.75)

# soft ground shadow under the paws
ellipse(256, 474, 150, 14, (244, 170, 195), 0.4)

# --- palette ------------------------------------------------------------------
FUR = (255, 176, 102)      # orange
FUR_D = (224, 138, 60)     # outline / darker fur
CREAM = (255, 232, 205)    # muzzle / belly
PINK = (255, 150, 170)     # inner ear / nose / blush
DARK = (58, 42, 34)        # eyes / whiskers
AMBER = (238, 158, 52)     # iris
CX, CY, R = 256, 258, 148

# --- chubby body (head drawn over its top) ----------------------------------
ellipse(CX, 418, 100, 72, FUR_D)
ellipse(CX, 418, 94, 66, FUR)
ellipse(CX, 432, 56, 40, CREAM)

# --- ears (behind head): rounded triangles, left slightly higher = head tilt --
poly([(128, 196), (152, 96), (216, 158)], FUR_D)
poly([(384, 200), (360, 100), (296, 162)], FUR_D)
poly([(134, 190), (153, 106), (208, 156)], FUR)
poly([(378, 194), (359, 110), (304, 160)], FUR)
poly([(146, 176), (155, 122), (192, 152)], PINK)
poly([(366, 180), (357, 126), (320, 156)], PINK)

# --- head with outline --------------------------------------------------------
disc(CX, CY, R + 6, FUR_D)
disc(CX, CY, R, FUR)

# forehead stripes
for (sx, sy, ln, ang) in [(222, 138, 26, -0.35), (256, 130, 30, 0.0),
                          (290, 138, 26, 0.35)]:
    line(int(sx - ln / 2 * math.cos(ang)), int(sy - ln / 2 * math.sin(ang)),
         int(sx + ln / 2 * math.cos(ang)), int(sy + ln / 2 * math.sin(ang)),
         FUR_D, 0.85)
    line(int(sx - ln / 2 * math.cos(ang)), int(sy + 4 - ln / 2 * math.sin(ang)),
         int(sx + ln / 2 * math.cos(ang)), int(sy + 4 - ln / 2 * math.sin(ang)),
         FUR_D, 0.85)

# muzzle patch
ellipse(CX, 326, 78, 52, CREAM)

# blush
disc(168, 312, 20, (255, 120, 140), 0.55)
disc(344, 312, 20, (255, 120, 140), 0.55)


# --- huge glossy amber eyes (left eye a touch higher: head tilt) -------------
def eye(ex, ey, tilt):
    ellipse(ex, ey, 29, 38, DARK)
    ellipse(ex, ey, 26, 35, AMBER)
    disc(ex, ey + 3, 15, DARK)
    disc(ex - 8, ey - 13, 9, (255, 255, 255))
    disc(ex + 10, ey + 11, 4, (255, 255, 255), 0.9)
    disc(ex + 3, ey - 3, 3, (255, 255, 255), 0.9)
    # tiny lashes on the outer upper edge
    for (lx, ly, dx, dy) in [(-20, -28, -8, -11), (-26, -17, -10, -5)]:
        line(ex + tilt * lx, ey + ly, ex + tilt * (lx + dx), ey + ly + dy, DARK, 0.9)


eye(196, 246, -1)
eye(316, 250, 1)

# nose + mouth
poly([(246, 302), (266, 302), (256, 314)], (255, 110, 140))
line(256, 314, 256, 326, FUR_D, 0.9)
for sgn in (-1, 1):
    cxm = 256 + sgn * 13
    for a in range(10, 171, 4):
        th = math.radians(a)
        px(int(cxm + 12 * math.cos(th)), int(326 + 9 * math.sin(th)), FUR_D, 0.95)
        px(int(cxm + 12 * math.cos(th)), int(327 + 9 * math.sin(th)), FUR_D, 0.95)

# whiskers
for (wy, tilt) in [(308, -8), (320, 0), (332, 8)]:
    line(196, wy, 128, wy + tilt, DARK, 0.55)
    line(316, wy, 384, wy + tilt, DARK, 0.55)

# little pink bow on the right ear + daisy on the left ear
BX, BY = 352, 128
poly([(BX - 26, BY - 12), (BX - 26, BY + 12), (BX - 4, BY)], (255, 110, 150))
poly([(BX + 26, BY - 12), (BX + 26, BY + 12), (BX + 4, BY)], (255, 110, 150))
disc(BX, BY, 8, (230, 70, 120))
disc(BX - 2, BY - 2, 3, (255, 180, 200), 0.9)
flower(112, 150, 10, (255, 255, 255), (255, 200, 90))

# one big heart floating above the kitten
heart(256, 62, 22, (255, 110, 150), 0.95)
heart(150, 88, 11, (255, 143, 176), 0.9)

# --- paws holding one heart ---------------------------------------------------
heart(256, 428, 24, (255, 110, 150), 0.98)


def paw(px_, py_):
    ellipse(px_, py_, 46, 30, FUR_D)
    ellipse(px_, py_, 40, 25, FUR)
    for dx in (-12, 0, 12):
        line(px_ + dx, py_, px_ + dx, py_ + 18, FUR_D, 0.7)


paw(196, 448)
paw(316, 448)

# --- soft vignette + grain ----------------------------------------------------
for y in range(H):
    dy = (y - H / 2) / (H / 2)
    for x in range(W):
        dx = (x - W / 2) / (W / 2)
        d = math.sqrt(dx * dx + dy * dy)
        if d > 0.9:
            px(x, y, (255, 190, 210), min(0.25, (d - 0.9) * 1.0))
for _ in range(6000):
    x = int(rrange(0, W))
    y = int(rrange(0, H))
    v = rrange(-4, 4)
    row = fb[y]
    i = x * 3
    row[i] = max(0, min(255, int(row[i] + v)))
    row[i + 1] = max(0, min(255, int(row[i + 1] + v)))
    row[i + 2] = max(0, min(255, int(row[i + 2] + v)))


# --- PNG encode ---------------------------------------------------------------
def chunk(typ, data):
    c = struct.pack(">I", len(data)) + typ + data
    return c + struct.pack(">I", zlib.crc32(typ + data) & 0xFFFFFFFF)


raw = b"".join(b"\x00" + bytes(row) for row in fb)
png = (b"\x89PNG\r\n\x1a\n"
       + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
       + chunk(b"IDAT", zlib.compress(raw, 9))
       + chunk(b"IEND", b""))
os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "wb") as f:
    f.write(png)
print(f"wrote {OUT} {len(png)} bytes {W}x{H}")
