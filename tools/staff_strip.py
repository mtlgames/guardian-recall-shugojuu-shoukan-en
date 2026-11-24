"""G15: stitch the STAFF.STR credits text column (x 0-159, scrolling up) into one tall strip.

    python -X utf8 tools/staff_strip.py [STR] [--out work/staff]

Per frame: the vertical shift of the left column against the previous frame (0-8 px; 2 while scrolling), summed
into an offset; strip row = frame row + offset. Writes OUT/strip.png (first frame wins per row), OUT/offsets.tsv
(frame, offset) and OUT/strip_NN.png pages of 400 rows (zoom 2) for reading. `scan` is shared with staff_str.py."""
import argparse
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent))
import mdec  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STR = ROOT / "work/iso/d2/tree/STR/STAFF.STR"
W = 160
_FR = {}


def _left(f):
    q, b = mdec.decode(_FR[f][1])[:2]
    p = mdec.to_pixels(q, b)
    return p[:, :W].mean(-1), int(p.max())


def _chunk(fs):
    """[(frame, shift, new rows (uint8), frame max)] for consecutive frames fs."""
    out = []
    prev = _left(fs[0] - 1)[0] if fs[0] - 1 in _FR else None
    for f in fs:
        cur, top = _left(f)
        d = 0
        if prev is not None and cur.max() > 40 and prev.max() > 40:
            d = min(range(9), key=lambda k: np.abs(prev[k:] - cur[:240 - k]).mean())
        new = cur if prev is None else cur[240 - d:] if d else cur[:0]
        out.append((f, d, new.clip(0, 255).astype(np.uint8), top))
        prev = cur
    return out


def _init(path):
    _FR.update(mdec.frames(Path(path).read_bytes()))


def scan(path=STR):
    """(offsets {frame: strip offset}, strip uint8 (rows, 160), frame max {frame: max pixel}) of an STR."""
    _init(path)
    fs = sorted(_FR)
    chunks = [fs[i:i + 120] for i in range(0, len(fs), 120)]
    with Pool(initializer=_init, initargs=(str(path),)) as pool:
        res = [r for c in pool.map(_chunk, chunks) for r in c]
    off, offsets, rows, top = 0, {}, [], {}
    for f, d, new, mx in res:
        off += d
        offsets[f], top[f] = off, mx
        rows.extend(new)              # new rows always continue the strip: offsets only grow
    return offsets, np.array(rows), top


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("str", nargs="?", default=str(STR))
    ap.add_argument("--out", default=str(ROOT / "work/staff"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    offsets, strip, _ = scan(a.str)
    Image.fromarray(strip).save(out / "strip.png")
    (out / "offsets.tsv").write_text("".join(f"{f}\t{o}\n" for f, o in offsets.items()))
    for k, y in enumerate(range(0, strip.shape[0], 400)):
        Image.fromarray(strip[y:y + 400]).resize((W * 2, min(400, strip.shape[0] - y) * 2), Image.NEAREST).save(
            out / f"strip_{k:02d}.png")
    print(strip.shape, "pages", k + 1)


if __name__ == "__main__":
    main()
