#!/usr/bin/env python3
"""Mechanical checks for a generated cover (featured-image.md): size, and whether anything is drawn inside the
60px margins (1200x630 logical, so 90px at 1800x945) or below the y=570 text limit. Needs Pillow + numpy
(`uv run python`). Does not judge design: look at the preview for that.
Usage: uv run python .claude/skills/hugo-paper-post/scripts/check_cover.py <featured-image.png>"""
import sys
import numpy as np
from PIL import Image

im = Image.open(sys.argv[1]).convert("RGB")
a = np.asarray(im).astype(int)
ok = True
if im.size != (1800, 945):
    print(f"FAIL size {im.size}, expected (1800, 945)"); ok = False
vals, counts = np.unique(a.reshape(-1, 3), axis=0, return_counts=True)
bg = vals[counts.argmax()]                      # most common colour = ground
ys, xs = np.where(np.abs(a - bg).sum(2) > 60)   # ignores faint texture such as ruled lines
k = im.size[0] / 1200
l, r, t, b = xs.min() / k, xs.max() / k, ys.min() / k, ys.max() / k
print(f"content box (logical px of 1200x630): x {l:.0f}-{r:.0f}, y {t:.0f}-{b:.0f}")
for name, bad in (("left", l < 60), ("right", r > 1140), ("top", t < 60), ("bottom", b > 570)):
    if bad:
        print(f"FAIL content crosses the {name} limit"); ok = False
print("OK" if ok else "see FAIL lines")
sys.exit(0 if ok else 1)
