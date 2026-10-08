"""Worked example #3: Ctx2Skill's featured image (content/posts/paper-intro/ctx2skill/). Blueprint style
(cobalt ground, white line work, one amber accent; Gloock + Geist Mono) with LARGE type: use this one as the
reference for sizes (title 112px, labels 12.5-14px on the 1200x630 canvas), not the 10px labels of the first two.
Metaphor: a Challenger/Reasoner/Judge loop above the skill length growing round after round.
1200x630 logical, 3x supersample, 1800x945 out. English only; labels from the article.
Usage: uv run python render-ctx2skill.py <out_dir>
"""
import math, sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONTS = str(Path(__file__).resolve().parents[3] / "canvas-design" / "canvas-fonts") + "/"
OUT_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else '.')
W, H, S, OUT = 1200, 630, 3, 1800

BG = (23, 52, 126)
WHITE = (240, 244, 255)
AMBER = (255, 196, 64)


def mix(c, a, bg=BG):
    return tuple(int(bg[i] + (c[i] - bg[i]) * a) for i in range(3))


yy, xx = np.mgrid[0:H * S, 0:W * S].astype(np.float32)
d = np.sqrt(((xx / (W * S)) - 0.62) ** 2 + ((yy / (H * S)) - 0.45) ** 2)
glow = np.clip(1 - d * 1.5, 0, 1) ** 2
base = np.zeros((H * S, W * S, 3), dtype=np.float32)
for i in range(3):
    base[..., i] = BG[i] + glow * [14, 26, 40][i] - d * 6
img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
dr = ImageDraw.Draw(img, 'RGBA')


def P(x, y):
    return (x * S, y * S)


def line(pts, color, w=1.0):
    dr.line([P(*p) for p in pts], fill=color, width=max(1, int(round(w * S))), joint='curve')


def rect(x0, y0, x1, y1, fill=None, outline=None, w=1.0):
    dr.rectangle([P(x0, y0), P(x1, y1)], fill=fill, outline=outline, width=max(1, int(w * S)))


def ring(x, y, r, col, w=1.0, fill=None):
    dr.ellipse([P(x - r, y - r), P(x + r, y + r)], outline=col, width=max(1, int(w * S)), fill=fill)


def arrowhead(x, y, ang, col, s=7):
    pts = [(x, y), (x - s * math.cos(ang - 0.4), y - s * math.sin(ang - 0.4)),
           (x - s * math.cos(ang + 0.4), y - s * math.sin(ang + 0.4))]
    dr.polygon([P(*p) for p in pts], fill=col)


def bez(p0, c, p1, n=80):
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * c[0] + t * t * p1[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * c[1] + t * t * p1[1]) for t in [k / n for k in range(n + 1)]]


for gx in range(0, W + 1, 30):
    line([(gx, 0), (gx, H)], mix(WHITE, 0.07 if gx % 150 else 0.14), 0.6)
for gy in range(0, H + 1, 30):
    line([(0, gy), (W, gy)], mix(WHITE, 0.07 if gy % 150 else 0.14), 0.6)


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


title = F('Gloock-Regular.ttf', 112)
num = F('Gloock-Regular.ttf', 66)
mono = F('GeistMono-Regular.ttf', 14)
mono_b = F('GeistMono-Bold.ttf', 14)
mono_s = F('GeistMono-Regular.ttf', 12.5)

# ---------------- left column ----------------
text(60, 66, 'SELF-PLAY SKILL DISTILLATION', mono, mix(WHITE, 0.8), spacing=1.0)
line([(60, 84), (170, 84)], AMBER, 2.5)
text(54, 108, 'Ctx2Skill', title, WHITE)
text(60, 262, 'CHALLENGER VS REASONER,', mono_b, WHITE, spacing=0.8)
text(60, 284, 'ONE REUSABLE SKILL FILE', mono_b, WHITE, spacing=0.8)

pct = F('Gloock-Regular.ttf', 30)
text(60, 366, '11.1', num, mix(WHITE, 0.62))
text(172, 410, '%', pct, mix(WHITE, 0.62))
line([(212, 404), (268, 404)], mix(WHITE, 0.85), 1.8)
arrowhead(270, 404, 0, mix(WHITE, 0.85), 8)
text(288, 366, '16.5', num, AMBER)
text(400, 410, '%', pct, AMBER)
text(60, 468, 'GPT-4.1 TASK-SOLVING RATE', mono, mix(WHITE, 0.88), spacing=0.6)
text(60, 490, 'CL-BENCH, NO SKILL -> CTX2SKILL', mono_s, mix(WHITE, 0.68), spacing=0.6)

# ---------------- self-play loop (top right) ----------------
LY = 168
R = 56
rC, rR = (650, LY), (1050, LY)
mx = (rC[0] + rR[0]) / 2
for (cx, cy), lab in ((rC, 'CHALLENGER'), (rR, 'REASONER')):
    ring(cx, cy, R, WHITE, 2.2, fill=mix(BG, 1.0) + (0,))
    ring(cx, cy, R - 8, mix(WHITE, 0.45), 1.0)
    text(cx, cy + 5, lab, mono_b, WHITE, anchor='ms', spacing=0.3)
topc = bez((rC[0] + 22, LY - R + 5), (mx, 36), (rR[0] - 22, LY - R + 5))
line(topc, WHITE, 2.0)
(ax, ay), (bx, by) = topc[-2], topc[-1]
arrowhead(bx, by, math.atan2(by - ay, bx - ax), WHITE, 11)
text(mx, 112, 'TASKS + BINARY RUBRICS', mono, mix(WHITE, 0.92), anchor='ms', spacing=0.6)
botc = bez((rR[0] - 22, LY + R - 5), (mx, 284), (rC[0] + 22, LY + R - 5))
for i in range(0, len(botc) - 4, 4):
    line(botc[i:i + 3], mix(WHITE, 0.85), 2.0)
(ax, ay), (bx, by) = botc[-3], botc[-1]
arrowhead(bx, by, math.atan2(by - ay, bx - ax), mix(WHITE, 0.85), 10)
jx, jy = mx, LY - 6
rect(jx - 50, jy - 22, jx + 50, jy + 22, fill=BG + (255,), outline=AMBER, w=2.2)
text(jx, jy + 5, 'JUDGE', mono_b, AMBER, anchor='ms', spacing=0.8)
text(mx, 272, 'ANSWERS, GRADED ALL-OR-NOTHING', mono, mix(WHITE, 0.82), anchor='ms', spacing=0.5)

# ---------------- skill growth bars (bottom right) ----------------
BX0 = 580
BASE = 502
words = [313.9, 657.8, 1005.6, 1354.2, 1704.1]    # GPT-4.1 mean skill words per iteration (article Table 4)
unit = 136 / 1704.1
bw, gap = 78, 38
line([(BX0 - 12, BASE), (BX0 + 5 * bw + 4 * gap + 12, BASE)], mix(WHITE, 0.9), 2.0)
for i, wd in enumerate(words):
    x0 = BX0 + i * (bw + gap)
    h = wd * unit
    kept = i == 0
    if kept:
        rect(x0, BASE - h, x0 + bw, BASE, fill=AMBER + (240,), outline=AMBER, w=1.6)
    else:
        rect(x0, BASE - h, x0 + bw, BASE, fill=WHITE + (26,), outline=mix(WHITE, 0.95), w=1.8)
        for k in range(int(h // 8)):
            yk = BASE - 6 - k * 8
            line([(x0 + 6, yk), (x0 + bw - 6, yk)], mix(WHITE, 0.24), 0.9)
    text(x0 + bw / 2, BASE + 22, f'ITER-{i + 1}', mono, AMBER if kept else mix(WHITE, 0.88), anchor='ma', spacing=0.5)
text(BX0 + bw / 2, BASE - words[0] * unit - 10, '313.9', mono_b, AMBER, anchor='ms', spacing=0.3)
x4 = BX0 + 4 * (bw + gap)
text(x4 + bw / 2, BASE - words[4] * unit - 10, '1704.1', mono_b, WHITE, anchor='ms', spacing=0.3)
text(BX0 - 12, 322, 'SKILL WORD COUNT, GPT-4.1 MEAN', mono, mix(WHITE, 0.9), spacing=0.5)
text(BX0 - 12, 346, 'SOLVE RATE 15.9% -> 14.7% BY ITER-5', mono_b, AMBER, spacing=0.5)
text(BX0 - 12, 556, 'REPLAY PICKS BY HARD x EASY PASS RATE', mono_s, mix(WHITE, 0.7), spacing=0.5)

for (x, y, sx, sy) in ((30, 30, 1, 1), (1170, 30, -1, 1), (30, 600, 1, -1), (1170, 600, -1, -1)):
    line([(x, y), (x + 14 * sx, y)], mix(WHITE, 0.5), 0.9)
    line([(x, y), (x, y + 14 * sy)], mix(WHITE, 0.5), 0.9)

final = img.resize((OUT, int(OUT * H / W)), Image.LANCZOS)
final.save(OUT_DIR / 'featured-image.png', optimize=True)
final.resize((1000, 525), Image.LANCZOS).save(OUT_DIR / 'preview.jpg', quality=80)
print(final.size)
