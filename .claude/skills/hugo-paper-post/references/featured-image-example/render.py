"""Worked example: Resource2Skill's featured image (content/posts/paper-intro/resource2skill/).

Not a template to fill in -- every post gets its own metaphor (see ../featured-image.md).
It is here to show the house skeleton in code: palette, 1200x630 logical canvas drawn at
3x and downsampled, margins + corner registration marks, sans title and subtitle (one family) / mono
annotations, text kept clear of the drawing, and a final contact-sheet-sized preview.

Usage:  python3 render.py <out_dir>      -> <out_dir>/featured-image.png + preview.jpg
Needs:  pip install pillow numpy
"""
import math, random, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = str(Path(__file__).resolve().parents[3] / 'canvas-design' / 'canvas-fonts') + '/'
OUT_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
W, H = 1200, 630          # logical units (OG ratio)
S = 3                     # supersample
OUT = 1800                # final width
random.seed(7)

BG = (8, 15, 30)
EMBER = (244, 176, 72)
EMBER_HI = (255, 226, 170)
ICE = (122, 176, 255)
ICE_HI = (206, 228, 255)
SLATE = (98, 114, 140)


def mix(c, a):
    return tuple(int(BG[i] + (c[i] - BG[i]) * a) for i in range(3))


# --- background: midnight ink with a soft vignette + faint dot lattice
yy, xx = np.mgrid[0:H * S, 0:W * S]
cx, cy = 0.50 * W * S, 0.52 * H * S
d = np.sqrt(((xx - cx) / (W * S)) ** 2 + ((yy - cy) / (H * S)) ** 2)
glow = np.clip(1 - d * 1.5, 0, 1) ** 2
base = np.zeros((H * S, W * S, 3), dtype=np.float32)
for i in range(3):
    base[..., i] = BG[i] + glow * ([10, 18, 34][i])
img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), 'RGB')
dr = ImageDraw.Draw(img)


def P(x, y):
    return (x * S, y * S)


def line(pts, color, w=1.0):
    dr.line([P(*p) for p in pts], fill=color, width=max(1, int(round(w * S))), joint='curve')


def smooth(t):
    return t * t * (3 - 2 * t)


# faint dot lattice
for gx in range(60, W - 40, 30):
    for gy in range(54, H - 30, 30):
        dr.ellipse([P(gx - 0.7, gy - 0.7), P(gx + 0.7, gy + 0.7)], fill=mix(SLATE, 0.22))

AX, AY = 472, 330          # the aperture

# --- the ember bundle: abundant, phase-shifted streams converging on the aperture
X0 = 60
N = 150
for k in range(N):
    o = (k / (N - 1)) * 2 - 1                       # -1..1
    ph = random.uniform(0, math.tau)
    fr = random.uniform(0.9, 1.6)
    amp0 = random.uniform(8, 26)
    pts = []
    steps = 160
    for s in range(steps + 1):
        t = s / steps
        x = X0 + (AX - X0) * t
        spread = 104 * (1 - smooth(t)) ** 1.15 + 0.6
        a = amp0 * (1 - t) ** 1.4
        y = AY + o * spread + math.sin(t * math.tau * fr * 1.6 + ph) * a
        pts.append((x, y))
    # per-segment brightness: fades in from the left, blazes into the aperture
    bright = 0.42 + 0.38 * (1 - abs(o)) ** 0.8 + random.uniform(-0.08, 0.08)
    for s in range(0, steps, 4):
        t = s / steps
        al = bright * (0.20 + 0.80 * smooth(min(1, t * 1.6))) * (0.65 + 0.35 * t)
        col = mix(EMBER_HI if abs(o) < 0.06 else EMBER, min(1, al))
        line(pts[s:s + 5], col, 0.9 if abs(o) > 0.06 else 1.2)

# --- the quiet slate companions: three thin dashed lines (code / article / artifact)
for yoff, dash in ((-134, (5, 5)), (138, (5, 5)), (166, (2, 5))):
    pts = []
    steps = 200
    for s in range(steps + 1):
        t = s / steps
        x = X0 + (AX - X0) * t
        y = AY + yoff * (1 - smooth(t)) ** 1.1
        pts.append((x, y))
    # dashed polyline
    acc, on = 0.0, True
    seg = []
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        dl = math.hypot(x2 - x1, y2 - y1)
        acc += dl
        if on:
            seg.append(pts[i])
        lim = dash[0] if on else dash[1]
        if acc >= lim:
            if on and seg:
                seg.append(pts[i + 1])
                line(seg, mix(SLATE, 0.85), 0.9)
            seg = []
            on = not on
            acc = 0.0

# --- ruler of time beneath the field: ticks, every 8th a keyframe
for i in range(0, 65):
    x = X0 + i * (AX - X0 - 12) / 64
    key = i % 8 == 0
    h = 11 if key else 4
    line([(x, 506), (x, 506 + h)], mix(EMBER if key else SLATE, 0.85 if key else 0.6), 0.9)
line([(X0, 506), (AX - 12, 506)], mix(SLATE, 0.55), 0.7)

# --- the tree: domain -> category -> skill
L0, L1, L2, L3 = AX, 650, 880, 1128
TOP, BOT = 92, 588
n1, per2, per3 = 5, 3, 3
leaves = n1 * per2 * per3
leaf_y = [TOP + (BOT - TOP) * i / (leaves - 1) for i in range(leaves)]
nodes2, nodes1 = [], []
for a in range(n1 * per2):
    ys = leaf_y[a * per3:(a + 1) * per3]
    nodes2.append(sum(ys) / len(ys))
for a in range(n1):
    ys = nodes2[a * per2:(a + 1) * per2]
    nodes1.append(sum(ys) / len(ys))
root = (L0, AY)

HL = (1, 1, 2)     # highlighted path: branch 2 -> category 1 -> leaf 1  (e.g. blender/lighting/jewelry)


def bez(p0, p1):
    (x0, y0), (x1, y1) = p0, p1
    mx = (x0 + x1) / 2
    pts = []
    for s in range(41):
        t = s / 40
        u = 1 - t
        x = u ** 3 * x0 + 3 * u * u * t * mx + 3 * u * t * t * mx + t ** 3 * x1
        y = u ** 3 * y0 + 3 * u * u * t * y0 + 3 * u * t * t * y1 + t ** 3 * y1
        pts.append((x, y))
    return pts


hl1 = HL[0]
hl2 = HL[0] * per2 + HL[1]
hl3 = hl2 * per3 + HL[2]

edge_cols = mix(ICE, 0.48)
# draw ordinary edges first, highlight after
for a in range(n1):
    line(bez(root, (L1, nodes1[a])), edge_cols, 0.8)
    for b in range(per2):
        i2 = a * per2 + b
        line(bez((L1, nodes1[a]), (L2, nodes2[i2])), edge_cols, 0.8)
        for c in range(per3):
            i3 = i2 * per3 + c
            line(bez((L2, nodes2[i2]), (L3, leaf_y[i3])), mix(ICE, 0.34), 0.7)

line(bez(root, (L1, nodes1[hl1])), mix(EMBER, 0.95), 1.6)
line(bez((L1, nodes1[hl1]), (L2, nodes2[hl2])), mix(EMBER, 0.95), 1.6)
line(bez((L2, nodes2[hl2]), (L3, leaf_y[hl3])), mix(EMBER, 0.95), 1.6)


def disc(x, y, r, col):
    dr.ellipse([P(x - r, y - r), P(x + r, y + r)], fill=col)


def ring(x, y, r, col, w=0.8):
    dr.ellipse([P(x - r, y - r), P(x + r, y + r)], outline=col, width=max(1, int(w * S)))


def sq(x, y, r, col):
    dr.rectangle([P(x - r, y - r), P(x + r, y + r)], fill=col)


for a in range(n1):
    disc(L1, nodes1[a], 3.4, mix(ICE, 0.85))
    for b in range(per2):
        i2 = a * per2 + b
        disc(L2, nodes2[i2], 2.6, mix(ICE, 0.75))
for i in range(leaves):
    sq(L3, leaf_y[i], 1.7, mix(ICE_HI, 0.85))

# highlighted nodes
disc(L1, nodes1[hl1], 4.6, EMBER_HI)
disc(L2, nodes2[hl2], 3.6, EMBER_HI)
sq(L3, leaf_y[hl3], 4.0, EMBER_HI)
ring(L3, leaf_y[hl3], 9, mix(EMBER, 0.85), 1.0)
ring(L3, leaf_y[hl3], 15, mix(EMBER, 0.35), 0.8)

# --- aperture: concentric rings where abundance becomes order
for r, al in ((9, 0.95), (18, 0.6), (30, 0.38), (46, 0.2)):
    ring(AX, AY, r, mix(EMBER_HI, al), 0.9)
disc(AX, AY, 4.2, EMBER_HI)
# registration cross-hair
line([(AX, AY - 62), (AX, AY - 54)], mix(EMBER_HI, 0.5), 0.8)
line([(AX, AY + 54), (AX, AY + 62)], mix(EMBER_HI, 0.5), 0.8)

# --- registration marks at the corners
for (x, y, dx, dy) in ((34, 30, 1, 1), (W - 34, 30, -1, 1), (34, H - 30, 1, -1), (W - 34, H - 30, -1, -1)):
    line([(x, y), (x + 12 * dx, y)], mix(SLATE, 0.9), 0.9)
    line([(x, y), (x, y + 12 * dy)], mix(SLATE, 0.9), 0.9)

# --- typography
def F(name, size):
    return ImageFont.truetype(FONTS + name, int(size * S))


def text(x, y, s, font, col, anchor='la', spacing=0.0):
    if spacing:
        cx_ = x
        for ch in s:
            dr.text((cx_ * S, y * S), ch, font=font, fill=col, anchor=anchor)
            cx_ += font.getlength(ch) / S + spacing
        return cx_ - spacing
    dr.text((x * S, y * S), s, font=font, fill=col, anchor=anchor)
    return x + font.getlength(s) / S


title = F('InstrumentSans-Regular.ttf', 62)
sub = F('InstrumentSans-Regular.ttf', 19)
mono = F('DMMono-Regular.ttf', 10.5)
mono_b = F('DMMono-Regular.ttf', 11.5)

text(60, 62, 'Resource2Skill', title, (236, 240, 248), spacing=1.2)
text(62, 146, 'Distilling tutorial video into agent skills', sub, mix(ICE_HI, 0.72), spacing=0.5)

# column headers of the lattice
for x, s in ((L1, 'DOMAIN'), (L2, 'CATEGORY'), (L3, 'SKILL')):
    text(x, 62, s, mono, mix(ICE, 0.62), anchor='ma', spacing=1.6)
    line([(x, 80), (x, 86)], mix(ICE, 0.5), 0.8)

# measured values beneath the field
ty = 552
line([(62, ty + 6), (86, ty + 6)], mix(EMBER, 1.0), 1.6)
xe = text(94, ty, 'VIDEO ONLY  66.8', mono_b, mix(EMBER_HI, 0.95), spacing=1.0)
xs = xe + 26
for i in range(3):
    line([(xs + i * 8, ty + 6), (xs + i * 8 + 4, ty + 6)], mix(SLATE, 0.95), 1.2)
text(xs + 34, ty, 'CODE + ARTICLE + ARTIFACT  59.4', mono_b, mix(SLATE, 1.0), spacing=1.0)

text(62, 578, 'arXiv 2606.29538  ·  11.9 pp average gain', mono, mix(SLATE, 0.9), spacing=0.6)

final = img.resize((OUT, int(OUT * H / W)), Image.LANCZOS)
final.save(OUT_DIR / 'featured-image.png', optimize=True)
final.resize((1000, 525), Image.LANCZOS).save(OUT_DIR / 'preview.jpg', quality=80)  # the only thing you view
print(final.size)
