"""Width-gate helper: text rows of a shot and the ink segments on each.

    python -X utf8 tools/inkrows.py SHOT.png [--min 150] [--gap 9] [--box x0,y0,x1,y1]

A row = a band of pixel rows holding bright pixels (all channels >= --min); on each row, ink columns closer than --gap
merge into one segment. Prints `y0-y1: x0-x1 x0-x1 ...`: a centred list's rows give its centre and the widest line,
a label column its start and the next column's start."""
import argparse

from PIL import Image


def rows(im, lo, box, gap):
    x0, y0, x1, y1 = box
    px = im.load()
    lit = [[x for x in range(x0, x1) if min(px[x, y]) >= lo] for y in range(y0, y1)]
    out, y = [], 0
    while y < len(lit):
        if not lit[y]:
            y += 1
            continue
        top = y
        cols = set()
        while y < len(lit) and lit[y]:
            cols.update(lit[y])
            y += 1
        segs = []
        for x in sorted(cols):
            if segs and x - segs[-1][1] < gap:
                segs[-1][1] = x
            else:
                segs.append([x, x])
        out.append((y0 + top, y0 + y - 1, segs))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("shot")
    ap.add_argument("--min", type=int, default=150)
    ap.add_argument("--gap", type=int, default=9)
    ap.add_argument("--box", help="x0,y0,x1,y1 (default: whole frame)")
    a = ap.parse_args()
    im = Image.open(a.shot).convert("RGB")
    box = tuple(map(int, a.box.split(","))) if a.box else (0, 0) + im.size
    for t, b, segs in rows(im, a.min, box, a.gap):
        print(f"{t}-{b}: " + " ".join(f"{s}-{e}" for s, e in segs))
