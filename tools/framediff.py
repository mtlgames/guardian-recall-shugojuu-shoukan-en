"""Pixel-diff two tour runs of the same scene frame by frame (same file names): which frames differ, and where.

    python -X utf8 tools/framediff.py work/qa/tour/battle work/qa/tour_prev/battle [--inside x0,y0,x1,y1]

Prints one line per differing frame with the bounding box of changed pixels; with --inside, frames whose every
changed pixel lies inside that rect are only counted, so what is left is the change a code fix did not explain.
Exit 1 if any frame differs outside --inside (or at all, without it).
"""
import argparse
import os
import sys

from PIL import Image, ImageChops

ap = argparse.ArgumentParser()
ap.add_argument("new")
ap.add_argument("old")
ap.add_argument("--inside", help="x0,y0,x1,y1 (exclusive end)")
a = ap.parse_args()
rect = tuple(map(int, a.inside.split(","))) if a.inside else None
same = inside = outside = 0
for f in sorted(os.listdir(a.new)):
    if not f.endswith(".png") or not os.path.exists(os.path.join(a.old, f)):
        continue
    n, o = Image.open(os.path.join(a.new, f)).convert("RGB"), Image.open(os.path.join(a.old, f)).convert("RGB")
    if n.size != o.size:
        print(f"{f} size {n.size} vs {o.size}")
        outside += 1
        continue
    box = ImageChops.difference(n, o).getbbox()
    if not box:
        same += 1
    elif rect and box[0] >= rect[0] and box[1] >= rect[1] and box[2] <= rect[2] and box[3] <= rect[3]:
        inside += 1
    else:
        outside += 1
        print(f"{f} diff bbox {box}")
print(f"{same} identical, {inside} differ only inside {rect}, {outside} differ elsewhere", file=sys.stderr)
sys.exit(1 if outside else 0)
