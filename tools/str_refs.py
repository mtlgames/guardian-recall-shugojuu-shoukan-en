"""How code reaches each string: absolute u32 pointer words and lui/addiu (or lui/ori, lui/load) pairs.

    python -X utf8 tools/str_refs.py FILE BASE [--code FILE:BASE ..] [--min 2]

FILE is a PS-X EXE (BASE = 0x8000F800, i.e. RAM of file offset 0) or an overlay (BASE = its load address).
Strings come from gr_strings.STR. Each string's RAM address is searched as a u32 word and as a lui/low pair in FILE
and every --code image. Prints: offset, ram, words, pairs, text; then totals (strings with no reference at all are
reached some other way: table + index, or a string inside a fixed-stride record).
"""
import argparse
import struct

from gr_strings import STR
from gr_text import decode


def pairs(b, base):
    """RAM addresses built by lui rX,hi + (addiu|ori|lw|lb|lbu|lh|lhu|sw|sb|sh) rY,lo(rX) within 8 instructions."""
    n = len(b) // 4
    w = struct.unpack_from(f"<{n}I", b)
    out = {}
    for i, x in enumerate(w):
        if x >> 26 != 0x0F:
            continue
        rt, hi = (x >> 16) & 31, x & 0xFFFF
        if not 0x8000 <= hi <= 0x801F:
            continue
        for j in range(i + 1, min(i + 9, n)):
            y = w[j]
            op = y >> 26
            if (y >> 21) & 31 != rt or op not in (0x09, 0x0D, 0x20, 0x21, 0x23, 0x24, 0x25, 0x28, 0x29, 0x2B):
                continue
            lo = y & 0xFFFF
            a = (hi << 16) | lo if op == 0x0D else ((hi << 16) + (lo - 0x10000 if lo & 0x8000 else lo)) & 0xFFFFFFFF
            out.setdefault(a, []).append(base + 4 * i)
            break
    return out


def words(b, base):
    out = {}
    for i in range(0, len(b) - 3, 4):
        v = struct.unpack_from("<I", b, i)[0]
        if 0x80000000 <= v < 0x80200000:
            out.setdefault(v, []).append(base + i)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("base", type=lambda s: int(s, 16))
    ap.add_argument("--code", nargs="*", default=[])
    ap.add_argument("--min", type=int, default=2)
    a = ap.parse_args()
    b = open(a.file, "rb").read()
    images = [(b, a.base)] + [(open(f, "rb").read(), int(x, 16)) for f, x in (c.rsplit(":", 1) for c in a.code)]
    W, P = {}, {}
    for img, base in images:
        for k, v in words(img, base).items():
            W.setdefault(k, []).extend(v)
        for k, v in pairs(img, base).items():
            P.setdefault(k, []).extend(v)
    tot = [0, 0, 0, 0]
    for m in STR.finditer(b):
        t = decode(m.group())
        if len(t) < a.min:
            continue
        ram = a.base + m.start()
        nw, np_ = len(W.get(ram, [])), len(P.get(ram, []))
        tot[0] += 1
        tot[1] += nw > 0
        tot[2] += np_ > 0
        tot[3] += not (nw or np_)
        print(f"{m.start():#07x}\t{ram:#x}\t{nw}\t{np_}\t{t[:60]!r}")
    print(f"# strings {tot[0]}  by pointer word {tot[1]}  by lui pair {tot[2]}  unreferenced {tot[3]}")


if __name__ == "__main__":
    main()
