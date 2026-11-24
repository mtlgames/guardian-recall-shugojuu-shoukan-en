"""G15: stitch the STAFF.STR credits text column (x 0-159, scrolling up) into one tall strip.

    python -X utf8 tools/staff_strip.py [STR] [--out work/staff]

Per frame: the vertical shift of the left column against the previous frame (0-8 px; 2 while scrolling), summed
into an offset; strip row = frame row + offset. Writes OUT/strip.png (first frame wins per row), OUT/offsets.tsv
(frame, offset, right-half max luminance in x 0-159 of the frame's video side check) and OUT/strip_NN.png pages
of 400 rows (zoom 2) for reading."""
import argparse
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import mdec  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
W = 160


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("str", nargs="?", default=str(ROOT / "work/iso/d2/tree/STR/STAFF.STR"))
    ap.add_argument("--out", default=str(ROOT / "work/staff"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    fr = mdec.frames(Path(a.str).read_bytes())
    off, prev, rows, log = 0, None, {}, []
    for f in sorted(fr):
        q, b = mdec.decode(fr[f][1])[:2]
        cur = mdec.to_pixels(q, b)[:, :W].mean(-1)
        if prev is not None and cur.max() > 40 and prev.max() > 40:
            off += min(range(9), key=lambda d: np.abs(prev[d:] - cur[:240 - d]).mean())
        for y in range(240):
            rows.setdefault(off + y, cur[y])
        log.append(f"{f}\t{off}\n")
        prev = cur
    strip = np.array([rows.get(r, np.zeros(W)) for r in range(max(rows) + 1)]).clip(0, 255).astype(np.uint8)
    Image.fromarray(strip).save(out / "strip.png")
    (out / "offsets.tsv").write_text("".join(log))
    for k, y in enumerate(range(0, strip.shape[0], 400)):
        Image.fromarray(strip[y:y + 400]).resize((W * 2, min(400, strip.shape[0] - y) * 2), Image.NEAREST).save(
            out / f"strip_{k:02d}.png")
    print(strip.shape, "pages", k + 1)


if __name__ == "__main__":
    main()
