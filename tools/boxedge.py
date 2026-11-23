"""Width-gate helper: ink and border columns on one pixel row (or band) of a shot.

    python -X utf8 tools/boxedge.py SHOT.png Y [Y2] [--x0 N] [--min 150]
prints the runs of bright pixels (all channels >= --min) on rows Y..Y2 from x0: text ink and window borders show as
runs; the last ink run before a border gives the right edge a line reaches, the border the box limit."""
import argparse

from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("shot")
ap.add_argument("y", type=int)
ap.add_argument("y2", type=int, nargs="?")
ap.add_argument("--x0", type=int, default=0)
ap.add_argument("--min", type=int, default=150)
a = ap.parse_args()
im = Image.open(a.shot).convert("RGB")
y2 = a.y2 if a.y2 is not None else a.y
cols = [x for x in range(a.x0, im.width)
        if any(min(im.getpixel((x, y))) >= a.min for y in range(a.y, y2 + 1))]
runs = []
for x in cols:
    if runs and x == runs[-1][1] + 1:
        runs[-1][1] = x
    else:
        runs.append([x, x])
print(" ".join(f"{s}-{e}" if e > s else str(s) for s, e in runs))
