#!/usr/bin/env python3
"""cutest-picture-01: "Mochi & Mimi, best friends".

A fully procedural, deterministic drawing (Python stdlib only, no network,
no model, no randomness from the environment): two chubby kittens
cheek-to-cheek, heads tilted toward each other, big amber eyes with
sparkle, blush cheeks, and their paws together holding one pink heart.
Warm pastel background with polka dots and floating hearts.
Writes /output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png), 512x512 PNG.
"""
import math
import os
import struct
import zlib

W = H = 512
OUT = os.path.join(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"), "entry.png")

# --- deterministic PRNG (splitmix64, fixed seed) ---------------------------
_state = [0x2B7E151628AED2A6]


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
        col = lerp((255, 244, 226), (255, 211, 227), t)
        i = x * 3
        fb[y][i], fb[y][i + 1], fb[y][i + 2] = col

# soft warm glow behind the kittens
disc(256, 250, 215, (255, 250, 240), 0.18)

# polka dots (kept away from the very centre so the faces stay clean)
for _ in range(38):
    x = int(rrange(18, W - 18))
    y = int(rrange(18, H - 18))
    if 130 < x < 385 and 150 < y < 400:
        continue
    r = int(rrange(4, 9))
    col = (255, 255, 255) if rnd() < 0.5 else (255, 183, 205)
    disc(x, y, r, col, 0.45)

# floating hearts at the edges
for (hx, hy, hs) in [(64, 92, 15), (452, 80, 12), (466, 300, 14), (48, 322, 12),
                      (428, 428, 12), (80, 442, 13)]:
    heart(hx, hy, hs, (255, 143, 176), 0.7)

# soft ground shadow under the paws
ellipse(256, 472, 158, 15, (244, 170, 195), 0.4)

# --- palette ------------------------------------------------------------------
ORANGE = (255, 178, 104)
ORANGE_D = (222, 136, 58)
CREAM_FUR = (255, 238, 210)
CREAM_D = (230, 192, 148)
MUZZLE = (255, 232, 205)
PINK = (255, 150, 170)
DARK = (58, 42, 34)
AMBER = (238, 158, 52)
GREEN_EYE = (126, 186, 148)


def body(bx, by, fur, dark, belly):
    """Little chubby sitting body; the head is drawn over its top."""
    ellipse(bx, by, 84, 66, dark)
    ellipse(bx, by, 78, 60, fur)
    ellipse(bx, by + 14, 48, 36, belly)


def kitten_head(cx, cy, r, fur, dark, inner, muzzle, stripes):
    """Head disc + ears. Ears lean slightly inward (toward the other kitten)."""
    # ears (behind head): tall rounded triangles, inner ear leans in
    # outer ear
    poly([(cx - r - 6, cy - r + 42), (cx - r + 4, cy - r - 52),
          (cx - r + 52, cy - r + 6)], dark)
    poly([(cx - r, cy - r + 38), (cx - r + 6, cy - r - 42),
          (cx - r + 46, cy - r + 6)], fur)
    poly([(cx - r + 10, cy - r + 26), (cx - r + 10, cy - r - 28),
          (cx - r + 36, cy - r + 4)], inner)
    # inner ear
    poly([(cx + r - 52, cy - r + 6), (cx + r - 4, cy - r - 52),
          (cx + r + 6, cy - r + 42)], dark)
    poly([(cx + r - 46, cy - r + 6), (cx + r - 6, cy - r - 42),
          (cx + r, cy - r + 38)], fur)
    poly([(cx + r - 36, cy - r + 4), (cx + r - 10, cy - r - 28),
          (cx + r - 10, cy - r + 26)], inner)
    # head with outline
    disc(cx, cy, r + 5, dark)
    disc(cx, cy, r, fur)
    # forehead stripes
    if stripes:
        for (sx, sy, ln, ang) in [(cx - 34, cy - r + 26, 22, -0.35),
                                  (cx, cy - r + 18, 26, 0.0),
                                  (cx + 34, cy - r + 26, 22, 0.35)]:
            line(int(sx - ln / 2 * math.cos(ang)), int(sy - ln / 2 * math.sin(ang)),
                 int(sx + ln / 2 * math.cos(ang)), int(sy + ln / 2 * math.sin(ang)),
                 dark, 0.8)
            line(int(sx - ln / 2 * math.cos(ang)), int(sy + 4 - ln / 2 * math.sin(ang)),
                 int(sx + ln / 2 * math.cos(ang)), int(sy + 4 - ln / 2 * math.sin(ang)),
                 dark, 0.8)
    # muzzle patch
    ellipse(cx, cy + 56, 52, 34, muzzle)


def eye(ex, ey, iris, tilt):
    """Big glossy eye: dark rim, coloured iris, dark pupil, sparkle, lashes."""
    ellipse(ex, ey, 20, 27, DARK)
    ellipse(ex, ey, 18, 25, iris)
    disc(ex, ey + 2, 11, DARK)
    disc(ex - 6, ey - 9, 6, (255, 255, 255))
    disc(ex + 7, ey + 8, 3, (255, 255, 255), 0.9)
    disc(ex + 2, ey - 2, 2, (255, 255, 255), 0.9)
    # two tiny lashes on the outer upper edge
    for (lx, ly, dx, dy) in [(-14, -20, -6, -8), (-18, -12, -7, -4)]:
        line(ex + tilt * lx, ey + ly, ex + tilt * (lx + dx), ey + ly + dy, DARK, 0.9)


def face(cx, cy, iris, nose_y, tilt_dir):
    """Eyes, nose, mouth, blush, whiskers for a head centred at (cx, cy)."""
    # eyes: inner eye a touch lower -> head tilts toward the other kitten
    eye(cx - 32, cy - 4, iris, -tilt_dir)
    eye(cx + 32, cy - 4 + 4 * tilt_dir, iris, tilt_dir)
    # blush
    disc(cx - 58, cy + 38, 13, (255, 120, 140), 0.5)
    disc(cx + 58, cy + 42, 13, (255, 120, 140), 0.5)
    # nose + mouth
    poly([(cx - 10, nose_y), (cx + 10, nose_y), (cx, nose_y + 12)], (255, 110, 140))
    line(cx, nose_y + 12, cx, nose_y + 24, DARK, 0.9)
    for sgn in (-1, 1):
        cxm = cx + sgn * 13
        for a in range(10, 171, 4):
            th = math.radians(a)
            px(int(cxm + 12 * math.cos(th)), int(nose_y + 24 + 9 * math.sin(th)), DARK, 0.95)
            px(int(cxm + 12 * math.cos(th)), int(nose_y + 25 + 9 * math.sin(th)), DARK, 0.95)
    # whiskers on the outer side only (inner ones would cross the gap)
    for (wy, tilt) in [(cy + 34, -7), (cy + 46, 0), (cy + 58, 7)]:
        if tilt_dir > 0:  # left kitten: whiskers point left
            line(cx - 58, wy, cx - 118, wy + tilt, DARK, 0.5)
        else:             # right kitten: whiskers point right
            line(cx + 58, wy, cx + 118, wy + tilt, DARK, 0.5)


def paw(px_, py_, fur, dark):
    ellipse(px_, py_, 40, 26, dark)
    ellipse(px_, py_, 34, 21, fur)
    for dx in (-11, 0, 11):
        line(px_ + dx, py_, px_ + dx, py_ + 18, dark, 0.6)


# --- Mochi (left, orange) + Mimi (right, cream), cheek to cheek -------------
# bodies first, heads over them, paws in front of the bodies
body(158, 414, ORANGE, ORANGE_D, MUZZLE)
body(354, 416, CREAM_FUR, CREAM_D, (255, 244, 224))

kitten_head(158, 262, 96, ORANGE, ORANGE_D, PINK, MUZZLE, True)
kitten_head(354, 264, 94, CREAM_FUR, CREAM_D, PINK, MUZZLE, False)

face(158, 262, AMBER, 300, 1)
face(354, 264, GREEN_EYE, 302, -1)

# Mimi's forehead flower + Mochi's tiny daisy on his outer ear
flower(354, 178, 13, (255, 170, 195), (255, 220, 110))
flower(110, 146, 10, (255, 255, 255), (255, 200, 90))

# Mimi's pink bow, sitting on her outer ear
BX, BY = 408, 168
poly([(BX - 24, BY - 11), (BX - 24, BY + 11), (BX - 4, BY)], (255, 110, 150))
poly([(BX + 24, BY - 11), (BX + 24, BY + 11), (BX + 4, BY)], (255, 110, 150))
disc(BX, BY, 7, (230, 70, 120))
disc(BX - 2, BY - 2, 3, (255, 180, 200), 0.9)

# a small heart floating right where their cheeks meet
heart(256, 196, 13, (255, 110, 150), 0.95)
# one big heart above them
heart(256, 64, 20, (255, 110, 150), 0.95)

# paws: outer paws, then the two inner paws cupping one heart
heart(256, 412, 24, (255, 110, 150), 0.98)
paw(106, 448, ORANGE, ORANGE_D)
paw(406, 448, CREAM_FUR, CREAM_D)
paw(214, 446, ORANGE, ORANGE_D)
paw(298, 446, CREAM_FUR, CREAM_D)

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
