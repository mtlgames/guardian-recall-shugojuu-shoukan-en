"""Margins of every distinct message-box text row in a run (tools/boxfind.py boxes, white ink):
python tools/inkscan.py RUNDIR [--from N] -> one line per distinct box content: frame, box, per row "left/right (diff)".
Compare with the same route on the original disc (rows the JP centres show the same diff there)."""
import argparse
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from boxfind import boxes  # noqa: E402


def rows(img, box):
    x0, y0, x1, y1 = box
    px = img.load()
    out = []
    band = None
    for y in range(y0 + 1, y1):
        xs = [x for x in range(x0 + 1, x1) if min(px[x, y]) >= 200]
        if xs:
            band = band or [y, x1, x0]
            band[1], band[2] = min(band[1], xs[0]), max(band[2], xs[-1])
        elif band and y - 1 > band[0]:
            out.append((band[0], band[1] - x0 - 1, x1 - 1 - band[2]))
            band = None
    if band:
        out.append((band[0], band[1] - x0 - 1, x1 - 1 - band[2]))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--from", dest="start", type=int, default=0)
    ap.add_argument("--jp", help="same route's run on the original: its rows at the same frame follow ' | jp'")
    a = ap.parse_args()

    def fmt(img):
        return "; ".join(f"box {b[0]},{b[1]}-{b[2]},{b[3]} " + " ".join(f"{L}/{R}({R - L:+d})" for _, L, R in rows(img, b))
                         for b in boxes(img))
    seen = set()
    for f in sorted(Path(a.run).glob("f[0-9]*.png")):
        if int(f.stem[1:]) < a.start:
            continue
        img = Image.open(f).convert("RGB")
        for b in boxes(img):
            r = rows(img, b)
            if not r:
                continue
            key = (b, tuple(r))
            if key in seen:
                continue
            seen.add(key)
            jp = Path(a.jp or "", f.name)
            print(f.stem, f"box {b[0]},{b[1]}-{b[2]},{b[3]}", " ".join(f"{L}/{R}({R - L:+d})" for _, L, R in r),
                  ("| jp " + fmt(Image.open(jp).convert("RGB"))) if a.jp and jp.exists() else "")
