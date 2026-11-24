"""G15: English STAFF.STR credits (disc 2 ending; docs/re/graphics.md G15).

    python -X utf8 tools/staff_str.py [--out work/staff/STAFF.STR] [--preview DIR] [--frames 300,2000]
    python -X utf8 tools/staff_str.py --lines DIR      every redrawn line, zoomed, for checking the lettering

The credits scroll as white text in the left column (x 0-159 = macroblock columns 0-9) at one strip offset per frame
(staff_strip.scan); each display line of gfx/staff.tsv is one ink band of the strip. Per frame that shows a redrawn
line: decode; background = grey opening of the frame (drops the text strokes, keeps the video behind the end
copyright); the redrawn lines' rows are set to it and the English is drawn at the brightness the Japanese had in that
frame (fades); macroblock columns 0-9 are re-encoded at the frame's qscale, raised until the frame fits its own
sectors. Every other block, frame, sector and the audio sectors stay as they are.

`patch(tree_file, log)` (insert.patch_tree) writes the cached result (work/staff/, keyed by a hash of the inputs) over
the dumped file and logs each changed sector."""
import argparse
import csv
import hashlib
import struct
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).parent))
import mdec  # noqa: E402
import staff_strip  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TSV = ROOT / "gfx/staff.tsv"
FONT = ROOT / "fonts/LiberationSerif-Bold.ttf"
CACHE = ROOT / "work/staff"
W, SS, CAP = 160, 4, 9          # column width, supersampling, cap height (px) of the English
LEFT_MBS = 10 * 15              # macroblocks of x 0-159 (stream order is column-major, 15 per column)


def lines(path=TSV):
    """[(kind, jp, en)] per display line, in scroll order."""
    rows = [r for r in csv.reader(path.open(encoding="utf-8"), delimiter="\t") if r and not r[0].startswith("#")]
    out = []
    for kind, jp, en in rows[1:]:
        j, e = jp.split(" / "), en.split(" / ")
        assert len(j) == len(e), (jp, en)
        out += [(kind, a, b) for a, b in zip(j, e)]
    return out


def bands(strip):
    """[(y0, y1, x0, x1)] ink bands of the strip; a band two lines tall is split at its emptiest middle row."""
    ink = strip > 100
    rows = ink.any(1)
    out, y = [], 0
    while y < len(rows):
        if rows[y]:
            y0 = y
            while y < len(rows) and rows[y]:
                y += 1
            n = round((y - y0) / 13)
            cuts = [y0]
            for k in range(1, n):
                mid = y0 + (y - y0) * k // n
                cuts.append(min(range(mid - 3, mid + 4), key=lambda r: ink[r].sum()))
            cuts.append(y)
            for a, b in zip(cuts, cuts[1:]):
                cols = np.where(ink[a:b].any(0))[0]
                out.append((a, b, int(cols.min()), int(cols.max()) + 1))
        y += 1
    return out


def _font(cap=CAP):
    size = 6 * SS
    while (lambda b: b[3] - b[1])(ImageFont.truetype(str(FONT), size + 1).getbbox("H")) <= cap * SS:
        size += 1
    return ImageFont.truetype(str(FONT), size)


CAST_X0, CAST_X1, CAST_GAP = 3, 157, 8      # cast lines: name left from x0, actor right to x1, min gap


def cast_squeeze(ls, f):
    """One horizontal squeeze for every cast line, so they all keep the same letter width."""
    room = (CAST_X1 - CAST_X0 - CAST_GAP) * SS
    return min([1.0] + [room / sum(_word(s.strip(), f).width for s in en.split("……"))
                        for kind, jp, en in ls if kind == "cast"])


def _word(text, f):
    """Supersampled alpha (float, rows 0..16*SS) of one run of text, baseline at row 11*SS - 1."""
    w = int(f.getlength(text)) + 2 * SS
    img = Image.new("L", (w, 16 * SS))
    ImageDraw.Draw(img).text((SS, 11 * SS - 1), text, font=f, fill=255, anchor="ls")
    return img


def line_alpha(kind, en, f=None, fc=None, csq=1.0):
    """(alpha (16, W) float 0..1, cap top at row 2, squeeze factor): one English credit line. f = font, fc = cast
    font, csq = cast_squeeze."""
    f = f or _font()
    canvas = Image.new("L", (W * SS, 16 * SS))
    if kind == "cast":
        fc = fc or _font(CAP - 1)
        a, b = (_word(s.strip(), fc) for s in en.split("……"))
        sq = csq
        a = a.resize((int(a.width * sq), a.height), Image.LANCZOS)
        b = b.resize((int(b.width * sq), b.height), Image.LANCZOS)
        canvas.paste(a, ((CAST_X0 - 1) * SS, 0))
        canvas.paste(b, ((CAST_X1 + 1) * SS - b.width, 0))
        gap0, gap1 = (CAST_X0 - 1) * SS + a.width + SS, (CAST_X1 + 1) * SS - b.width - SS
        d = ImageDraw.Draw(canvas)
        for x in range(gap1 - 3 * SS, gap0, -4 * SS):          # dot leader on the baseline, from the actor side
            d.rectangle((x, 11 * SS - 1 - SS, x + SS - 1, 11 * SS - 2), fill=200)
    else:
        text = f"-{en}-" if kind == "role" else en
        a = _word(text, f)
        sq = min(1.0, (W - 4) * SS / a.width)
        a = a.resize((int(a.width * sq), a.height), Image.LANCZOS)
        canvas.paste(a, ((W * SS - a.width) // 2, 0))
    small = canvas.resize((W, 16), Image.BOX)
    return np.asarray(small, float) / 255, sq


def plan(strip):
    """[(y0, y1, x0, x1, e0, e1, alpha)] for every redrawn line: ink band, rows to clear, English alpha (16, W)."""
    ls, bs = lines(), bands(strip)
    assert len(ls) == len(bs), f"{len(ls)} staff.tsv lines vs {len(bs)} ink bands"
    f, fc, out = _font(), _font(CAP - 1), []
    csq = cast_squeeze(ls, fc)
    for i, ((kind, jp, en), (y0, y1, x0, x1)) in enumerate(zip(ls, bs)):
        if jp == en:
            continue
        e0 = max(y0 - 3, bs[i - 1][1] if i else 0)
        e1 = min(y1 + 3, bs[i + 1][0] if i + 1 < len(bs) else y1 + 3)
        out.append((y0, y1, x0, x1, e0, e1, line_alpha(kind, en, f, fc, csq)[0]))
    return out


def _planes(rgb):
    """The 6 signed 8x8 sample blocks (Cr, Cb, Y1-Y4) of a 16x16 RGB patch."""
    r, g, b = (rgb[..., k].astype(float) for k in range(3))
    y = 0.299 * r + 0.587 * g + 0.114 * b
    cb, cr = (b - y) / 1.772, (r - y) / 1.402
    sub = lambda c: c.reshape(8, 2, 8, 2).mean((1, 3))  # noqa: E731
    return [sub(cr), sub(cb)] + [y[dy:dy + 8, dx:dx + 8] - 128 for dy, dx in ((0, 0), (0, 8), (8, 0), (8, 8))]


def rgb_blocks(rgb, q):
    """6 blocks (Cr, Cb, Y1-Y4) of a 16x16 RGB patch; None if an AC level would clip at this qscale."""
    out = []
    for p in _planes(rgb):
        F = mdec._C @ p @ mdec._C.T
        F[0, 0] = 0
        if np.abs(F * 8 / (q * mdec.QUANT)).max() > 511:
            return None
        out.append(mdec.block_levels(p, q))
    return out


def requant(blocks, q0, q):
    return [(dc, [(r, int(np.clip(round(l * q0 / q), -511, 511))) for r, l in ac]) for dc, ac in blocks]


def _renum(blocks):
    """Drop zero levels left by requant, merging their runs into the next coefficient."""
    out = []
    for dc, ac in blocks:
        new, carry = [], 0
        for r, l in ac:
            if l:
                new.append((r + carry, l))
                carry = 0
            else:
                carry += r + 1
        out.append((dc, new))
    return out


def redraw(data, off, todo, cap):
    """New frame bytes (fitting cap) for frame data at strip offset off; todo = plan entries; None if none shows."""
    q0, blocks = mdec.decode(data)[:2]
    pix = mdec.to_pixels(q0, blocks).astype(float)
    # 15 px: taller than a text line, so blurred kanji clusters vanish too
    bg = np.stack([ndimage.grey_opening(pix[..., k], size=(15, 15)) for k in range(3)], -1)
    lum = pix.mean(-1)
    text = ndimage.binary_dilation((lum - bg.mean(-1))[:, :W] > 12, iterations=3)   # strokes + their ringing
    new, touched = pix[:, :W].copy(), set()
    for y0, y1, x0, x1, e0, e1, alpha in todo:
        r0, r1 = max(y0 - off, 0), min(y1 - off, 240)
        if r0 >= r1:
            continue
        v = lum[r0:r1, x0:x1].max()
        if v - bg[r0:r1, x0:x1].mean(-1).max() < 16:
            continue                                   # faded out
        a0, a1 = max(e0 - off, 0), min(e1 - off, 240)
        m = text[a0:a1, :, None]
        new[a0:a1] = np.where(m, bg[a0:a1, :W], new[a0:a1])
        for r in range(16):
            y = y0 - 1 + r - off
            if 0 <= y < 240:
                new[y] = new[y] * (1 - alpha[r, :, None]) + v * alpha[r, :, None]
                touched.add(y // 16)
        touched.update(range(a0 // 16, (a1 - 1) // 16 + 1))
    if not touched:
        return None
    new = np.clip(np.rint(new), 0, 255)
    # only macroblocks the redrawn rows touch are re-encoded; the rest keep their coefficients
    redo = [i for i, (mx, my) in enumerate(mdec.mb_order()[:LEFT_MBS]) if my in touched]
    for q in range(q0, 64):
        out = blocks if q == q0 else _renum(requant(blocks, q0, q))
        out = list(out)
        for i in redo:
            mx, my = mdec.mb_order()[i]
            bl = rgb_blocks(new[my * 16:my * 16 + 16, mx * 16:mx * 16 + 16], q)
            if bl is None:
                break
            out[6 * i:6 * i + 6] = bl
        else:
            data = mdec.encode(q, out)
            if len(data) <= cap:
                return data
    raise ValueError("frame does not fit at any qscale")


_S = {}


def _init(path, todo, offsets, end):
    _S.update(fr=mdec.frames(Path(path).read_bytes()), todo=todo, off=offsets, end=end)


def _job(f):
    if f >= _S["end"]:
        return f, None
    secs, data = _S["fr"][f]
    return f, redraw(data, _S["off"][f], _S["todo"], len(secs) * mdec.DATA)


def build(src=staff_strip.STR, frames=None):
    """{frame: new frame bytes} for every frame with a redrawn line (or only `frames`)."""
    offsets, strip, top = staff_strip.scan(src)
    todo = plan(strip)
    last_move = max(f for f in offsets if offsets[f] != offsets[max(offsets)]) + 1
    end = next(f for f in sorted(top) if f > last_move and top[f] == 0)   # black gap before the closing card
    fs = frames or [f for f in sorted(offsets)
                    if any(y1 > offsets[f] and y0 < offsets[f] + 240 for y0, y1, *_ in todo)]
    with Pool(initializer=_init, initargs=(str(src), todo, offsets, end)) as pool:
        return {f: d for f, d in pool.map(_job, fs, chunksize=8) if d is not None}


def write(s, frames_new):
    """Copy of STR bytes s with the frames replaced (same sectors; size and header fields updated)."""
    s = bytearray(s)
    fr = mdec.frames(bytes(s))
    for f, data in frames_new.items():
        secs = fr[f][0]
        assert len(data) <= len(secs) * mdec.DATA
        for k, i in enumerate(secs):
            o = i * mdec.SECTOR
            struct.pack_into("<I", s, o + 0x14, len(data))
            s[o + 0x1C:o + 0x24] = data[:8]
            s[o + 0x28:o + 0x28 + mdec.DATA] = data[k * mdec.DATA:(k + 1) * mdec.DATA].ljust(mdec.DATA, b"\0")
    return bytes(s)


def _key(src):
    h = hashlib.sha1()
    for p in (TSV, FONT, Path(__file__), Path(mdec.__file__), Path(staff_strip.__file__)):
        h.update(p.read_bytes())
    h.update(str(Path(src).stat().st_size).encode())
    return h.hexdigest()[:16]


def cached(src):
    """English STAFF.STR bytes, built once per input hash into work/staff/."""
    out = CACHE / f"STAFF.{_key(src)}.STR"
    if not out.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        for old in CACHE.glob("STAFF.*.STR"):
            old.unlink()
        out.write_bytes(write(Path(src).read_bytes(), build(src)))
    return out.read_bytes()


def patch(path, log, rel="STR/STAFF.STR"):
    """Overwrite the dumped STAFF.STR at path with the English one; log every changed sector."""
    old = Path(path).read_bytes()
    new = cached(path)
    assert len(new) == len(old)
    for o in range(0, len(old), mdec.SECTOR):
        if old[o:o + mdec.SECTOR] != new[o:o + mdec.SECTOR]:
            log(rel, o, old[o:o + mdec.SECTOR], new[o:o + mdec.SECTOR], "G15 staff")
    Path(path).write_bytes(new)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--preview")
    ap.add_argument("--frames")
    ap.add_argument("--lines")
    a = ap.parse_args()
    if a.lines:
        d = Path(a.lines)
        d.mkdir(parents=True, exist_ok=True)
        f, fc, ls = _font(), _font(CAP - 1), [x for x in lines() if x[1] != x[2]]
        csq = cast_squeeze(ls, fc)
        print(f"cast squeeze {csq:.2f}")
        img = np.zeros((18 * len(ls), W))
        for i, (kind, jp, en) in enumerate(ls):
            al, sq = line_alpha(kind, en, f, fc, csq)
            img[18 * i:18 * i + 16] = al * 255
            if sq < 0.8:
                print(f"squeezed {sq:.2f}: {en}")
        for k in range(0, len(ls), 40):
            Image.fromarray(img[18 * k:18 * (k + 40)].astype(np.uint8)).resize((W * 3, min(40, len(ls) - k) * 54),
                                                                             Image.NEAREST).save(d / f"lines_{k // 40}.png")
        return
    src = staff_strip.STR
    if a.preview:
        fs = [int(x) for x in a.frames.split(",")]
        new = build(src, fs)
        d = Path(a.preview)
        d.mkdir(parents=True, exist_ok=True)
        fr = mdec.frames(src.read_bytes())
        for f in fs:
            q, b = mdec.decode(fr[f][1])[:2]
            Image.fromarray(mdec.to_pixels(q, b)).save(d / f"f{f:04d}_jp.png")
            if f in new:
                q, b = mdec.decode(new[f])[:2]
                Image.fromarray(mdec.to_pixels(q, b)).save(d / f"f{f:04d}_en.png")
                print(f, "q", q, "bytes", len(new[f]), "/", len(fr[f][0]) * mdec.DATA)
        return
    data = cached(src)
    if a.out:
        Path(a.out).write_bytes(data)
    print("ok", len(data))


if __name__ == "__main__":
    main()
