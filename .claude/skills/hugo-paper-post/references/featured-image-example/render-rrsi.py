"""Worked example #2: RRSI's featured image (content/posts/paper-intro/rrsi/). A light, flat 'poster' style,
deliberately NOT the dark/ember style of render.py. Same rules (1200x630 @3x -> 1800x945, English only,
labels traceable to the article); different palette, type, layout and metaphor.

 The noise band, the score floor and the winner's curse, drawn as a plot.

Usage: python3 render.py <out_dir> -> featured-image.png + preview.jpg
"""
import math, random, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = str(Path(__file__).resolve().parents[3] / 'canvas-design' / 'canvas-fonts') + '/'
OUT_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
W, H, S, OUT = 1200, 630, 3, 1800
random.seed(5)
np.random.seed(5)

PAPER = (240, 235, 224)
INK = (26, 27, 31)
VERM = (222, 66, 38)
GREY = (132, 128, 118)
RULE = (196, 190, 178)


def mix(c, a, bg=PAPER):
    return tuple(int(bg[i] + (c[i] - bg[i]) * a) for i in range(3))


base = np.zeros((H * S, W * S, 3), dtype=np.float32)
for i in range(3):
    base[..., i] = PAPER[i]
base += np.random.normal(0, 1.6, (H * S, W * S, 1)).astype(np.float32)   # paper grain
img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
dr = ImageDraw.Draw(img, 'RGBA')


def P(x, y):
    return (x * S, y * S)


def line(pts, color, w=1.0):
    dr.line([P(*p) for p in pts], fill=color, width=max(1, int(round(w * S))), joint='curve')


def disc(x, y, r, col):
    dr.ellipse([P(x - r, y - r), P(x + r, y + r)], fill=col)


def ring(x, y, r, col, w=1.0):
    dr.ellipse([P(x - r, y - r), P(x + r, y + r)], outline=col, width=max(1, int(w * S)))


def dashed(pts, col, w, dash=(4, 3)):
    acc, on, seg = 0.0, True, []
    for i in range(len(pts) - 1):
        (x1, y1), (x2, y2) = pts[i], pts[i + 1]
        acc += math.hypot(x2 - x1, y2 - y1)
        if on:
            seg.append(pts[i])
        if acc >= (dash[0] if on else dash[1]):
            if on and seg:
                seg.append(pts[i + 1])
                line(seg, col, w)
            seg, on, acc = [], not on, 0.0


# ---------------- the plot ----------------
CX0, CX1 = 440, 985          # chart x range
CY0, CY1 = 92, 540           # chart y range (top, bottom)
ROUNDS, DELTA = 20, 0.055
VMIN, VMAX = 0.20, 0.64


def X(t):
    return CX0 + 14 + (CX1 - CX0 - 28) * t / (ROUNDS - 1)


def Y(v):
    return CY1 - (v - VMIN) / (VMAX - VMIN) * (CY1 - CY0)


rounds = []
sstar = 0.34
for t in range(ROUNDS):
    true_base = 0.34 + 0.0042 * t
    cands = []
    for k in range(4):
        true = true_base + random.uniform(-0.012, 0.016)
        meas = true + random.gauss(0, 0.027)
        cands.append((true, meas))
    floor = sstar - DELTA
    ok = [c for c in cands if c[1] >= floor]
    sel = max(ok, key=lambda c: c[1]) if ok else None
    rounds.append(dict(t=t, cands=cands, floor=floor, sstar=sstar, sel=sel))
    if sel and sel[1] > sstar:
        sstar = sel[1]

# baseline ruler
line([(CX0, CY1 + 14), (CX1, CY1 + 14)], INK, 1.4)
for t in range(ROUNDS):
    major = t % 5 == 0 or t == ROUNDS - 1
    line([(X(t), CY1 + 14), (X(t), CY1 + (22 if major else 18))], INK, 1.0 if major else 0.8)

# noise band between floor and S* (step, drawn per round column)
half = (X(1) - X(0)) / 2
for r in rounds:
    x0, x1 = X(r['t']) - half, X(r['t']) + half
    dr.rectangle([P(x0, Y(r['sstar'])), P(x1, Y(r['floor']))], fill=VERM + (46,))
# S* staircase and floor line
stair, flo = [], []
for r in rounds:
    x0, x1 = X(r['t']) - half, X(r['t']) + half
    stair += [(x0, Y(r['sstar'])), (x1, Y(r['sstar']))]
    flo += [(x0, Y(r['floor'])), (x1, Y(r['floor']))]
line(stair, INK, 1.5)
dashed(flo, mix(VERM, 0.95), 1.1)

# candidates
for r in rounds:
    x = X(r['t'])
    offs = [-6.5, -2.2, 2.2, 6.5]
    for (true, meas), dx in zip(r['cands'], offs):
        passed = meas >= r['floor']
        if r['sel'] is not None and (true, meas) == r['sel']:
            # winner: lucky measurement above its true level
            line([(x + dx, Y(meas)), (x + dx, Y(true))], mix(VERM, 0.85), 0.9)
            line([(x + dx - 2.6, Y(true)), (x + dx + 2.6, Y(true))], mix(VERM, 0.85), 0.9)
            disc(x + dx, Y(meas), 3.9, VERM)
        elif passed:
            disc(x + dx, Y(meas), 2.5, INK)
        else:
            s = 2.4
            line([(x + dx - s, Y(meas) - s), (x + dx + s, Y(meas) + s)], mix(GREY, 0.95), 0.9)
            line([(x + dx - s, Y(meas) + s), (x + dx + s, Y(meas) - s)], mix(GREY, 0.95), 0.9)

# ---------------- type ----------------
def F(name, size):
    return ImageFont.truetype(FONTS + name, int(size * S))


def text(x, y, s, font, col, anchor='la', spacing=0.0):
    if spacing:
        tot = sum(font.getlength(ch) / S + spacing for ch in s) - spacing
        cx_ = x - (tot / 2 if anchor[0] == 'm' else tot if anchor[0] == 'r' else 0)
        for ch in s:
            dr.text((cx_ * S, y * S), ch, font=font, fill=col, anchor='l' + anchor[1])
            cx_ += font.getlength(ch) / S + spacing
        return cx_ - spacing
    dr.text((x * S, y * S), s, font=font, fill=col, anchor=anchor)
    return x + font.getlength(s) / S


big = F('BigShoulders-Bold.ttf', 168)
num = F('BigShoulders-Bold.ttf', 46)
sub = F('Lora-Italic.ttf', 19)
mono = F('IBMPlexMono-Regular.ttf', 10)
mono_b = F('IBMPlexMono-Bold.ttf', 10)

# masthead rule
line([(60, 44), (1140, 44)], INK, 2.2)
text(60, 52, 'REGULARIZED RECURSIVE SELF-IMPROVEMENT OF AGENT HARNESSES', mono, INK, spacing=1.0)
text(1140, 52, 'ARXIV 2609.24972', mono, GREY, anchor='ra', spacing=1.0)

# title
text(54, 80, 'RRSI', big, INK)
text(60, 268, 'Guardrails for a loop that', sub, mix(INK, 0.85))
text(60, 292, 'grades itself on the same tasks.', sub, mix(INK, 0.85))

# the three measured values (article's ablation: unregularized vs full RRSI)
rows = [('-2.3', 'EVOLVE SCORE, POINTS', INK), ('+3.3', 'UNSEEN BENCHMARKS, POINTS', VERM), ('-36%', 'TOKENS PER TRIAL', INK)]
y0 = 346
for i, (v, lab, col) in enumerate(rows):
    y = y0 + i * 62
    line([(60, y), (368, y)], mix(INK, 0.9), 1.0)
    text(60, y + 7, v, num, col)
    text(172, y + 44, lab, mono, mix(INK, 0.75), anchor='ls', spacing=0.8)
line([(60, y0 + 3 * 62), (368, y0 + 3 * 62)], mix(INK, 0.9), 1.0)
text(60, y0 + 3 * 62 + 8, 'AGENTIC WORKSPACE, NO REGULARIZATION VS RRSI', mono, GREY, spacing=0.5)

# plot annotations (right gutter, leader lines)
last = rounds[-1]
gx = CX1 + 18
line([(CX0, CY0 - 6), (CX0, CY1 + 14)], mix(RULE, 1.0), 0.8)
lab_x = 1000
yS = Y(last['sstar'])
yF = Y(last['floor'])
line([(X(ROUNDS - 1) + half, yS), (lab_x - 4, yS)], mix(INK, 0.6), 0.7)
text(lab_x, yS + 3, 'S*  BEST SO FAR', mono_b, INK, anchor='ls', spacing=0.5)
line([(X(ROUNDS - 1) + half, yF), (lab_x - 4, yF)], mix(VERM, 0.8), 0.7)
text(lab_x, yF + 3, 'FLOOR  S* - DELTA', mono_b, VERM, anchor='ls', spacing=0.5)
text(lab_x, (yS + yF) / 2 + 3, 'NOISE BAND', mono, mix(VERM, 0.9), anchor='ls', spacing=0.5)

# legend, lower right of plot
lx, ly = 1000, 400
disc(lx + 3, ly - 3, 3.9, VERM)
text(lx + 14, ly, 'LUCKY WINNER', mono, mix(INK, 0.85), anchor='ls', spacing=0.5)
text(lx + 14, ly + 12, 'TICK = TRUE LEVEL', mono, GREY, anchor='ls', spacing=0.5)
disc(lx + 3, ly + 30, 2.5, INK)
text(lx + 14, ly + 33, 'PASSED FLOOR', mono, mix(INK, 0.85), anchor='ls', spacing=0.5)
s = 2.4
line([(lx + 3 - s, ly + 50 - s), (lx + 3 + s, ly + 50 + s)], mix(GREY, 0.95), 0.9)
line([(lx + 3 - s, ly + 50 + s), (lx + 3 + s, ly + 50 - s)], mix(GREY, 0.95), 0.9)
text(lx + 14, ly + 53, 'REJECTED', mono, mix(INK, 0.85), anchor='ls', spacing=0.5)

text(CX0, CY1 + 36, 'ROUND 0', mono, mix(INK, 0.85), spacing=0.6)
text(CX1, CY1 + 36, 'ROUND 19', mono, mix(INK, 0.85), anchor='ra', spacing=0.6)
text(CX0 + (CX1 - CX0) / 2, CY1 + 36, 'FOUR CANDIDATES PER ROUND  -  ILLUSTRATIVE, NOT PAPER DATA', mono, GREY, anchor='ma', spacing=0.6)

final = img.resize((OUT, int(OUT * H / W)), Image.LANCZOS)
final.save(OUT_DIR / 'featured-image.png', optimize=True)
final.resize((1000, 525), Image.LANCZOS).save(OUT_DIR / 'preview.jpg', quality=80)
print(final.size)
