"""swap_layout.py: dump the DAY.BIN disc-swap screen layouts (G8; docs/re/graphics.md).
Task 0x8016BAC4 draws lists picked from pointer tables 0x8016C3A0[state (+4 if mode != 0)] and 0x8016C3C0[mode];
a list = {u32 sprite ptr, u16 x, u16 y}.. ended by ptr 0; sprite (12 bytes) = {u32 ot, u16 tpage, u16 clut, u8 u, v,
w, h} drawn by 0x8016B828 (a1 = x, a2 = y). Extra single sprites: 0x8016C0D0 at (0xD8, 0xD8), 0x8016C0DC at (0x108, 0x48).
python -X utf8 tools/swap_layout.py [DAY.BIN]
python -X utf8 tools/swap_layout.py --render work/build/d1 work/gfx/swap   (all 8 screens' text from a built tree)"""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = 0x80166218
TABLES = {0x8016C3A0: 8, 0x8016C3C0: 3}


def sprite(b, p):
    ot, tpage, clut, u, v, w, h = struct.unpack_from("<IHHBBBB", b, p - BASE)
    return dict(ot=ot, tpage=tpage, clut=clut, u=u, v=v, w=w, h=h)


def lists(b):
    """{(table, i): [(sprite ptr, x, y)]}"""
    out = {}
    for t, n in TABLES.items():
        for i in range(n):
            p = struct.unpack_from("<I", b, t - BASE + 4 * i)[0]
            if not BASE <= p < BASE + len(b):
                continue
            items = []
            while True:
                s, x, y = struct.unpack_from("<IHH", b, p - BASE)
                if s == 0:
                    break
                items.append((s, x, y))
                p += 8
            out[(t, i)] = items
    return out


def render(tree, out):
    """Compose every list (+ digit) from tree's DAY.BIN and the g9 TX03 sheet onto 640x480 PNGs in `out` (grey)."""
    import numpy as np
    from PIL import Image
    sys.path.insert(0, str(ROOT / "tools"))
    import gfx
    import gr_index
    import tx03
    tree, out = Path(tree), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    b = (tree / "DATA/DAY.BIN").read_bytes()
    exe = next(tree.glob("SLPS_*")).read_bytes()
    unn = (tree / "DATA/UNN.PAK").read_bytes()
    d = tx03.decompress(unn, gr_index.toc(exe)[9][0] * 0x800 + gfx.SWAP_REL)[0]
    sheet = gfx.unpack(d[4:], gfx.SWAP_W)
    word = lambda a: struct.unpack_from("<I", b, a - BASE)[0]   # noqa: E731
    digits = {0: (0x8016C0D0, 0x8016BC08, 0x8016BC10), 1: (0x8016C0DC, 0x8016BC18, 0x8016BC1C)}
    for (t, i), items in lists(b).items():
        if t != 0x8016C3A0:
            continue
        img = np.zeros((480, 640), np.uint8)
        dp, ax, ay = digits[i >= 4]
        if i % 4 == 0:
            items = items + [(dp, word(ax) & 0xFFFF, word(ay) & 0xFFFF)]
        for p, x, y in items:
            s = sprite(b, p)
            u = s["u"] + 256 * ((s["tpage"] & 0x1F) - 10)
            img[y:y + s["h"], x:x + s["w"]] = np.maximum(img[y:y + s["h"], x:x + s["w"]],
                                                         sheet[s["v"]:s["v"] + s["h"], u:u + s["w"]])
        Image.fromarray(img * 17).save(out / f"state{i}.png")


if __name__ == "__main__":
    if "--render" in sys.argv:      # --render TREE OUTDIR
        render(*sys.argv[2:4])
        sys.exit()
    b = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "work/iso/d1/tree/DATA/DAY.BIN").read_bytes()
    for k, items in lists(b).items():
        print(f"{k[0]:08X}[{k[1]}]")
        for s, x, y in items:
            print(f"  {s:08X} x {x:3d} y {y:3d}", sprite(b, s))
    for s in (0x8016C0D0, 0x8016C0DC):
        print(f"{s:08X}", sprite(b, s))
