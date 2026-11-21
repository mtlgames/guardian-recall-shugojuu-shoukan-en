"""gr_codes.py PAK START SIZE: count non-text bytes inside text blocks, with a context sample each."""
import collections
import sys

import gr_scan_blocks
from gr_text import decode

if __name__ == "__main__":
    pak, start, size = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
    with open(pak, "rb") as f:
        f.seek(start)
        d = f.read(size)
    c, ex = collections.Counter(), {}
    for o, n, k, end in gr_scan_blocks.scan(d):
        import struct
        offs = [x for x in struct.unpack_from("<%dI" % n, d, o + 8) if x]
        i = o + min(offs)
        while i < end:
            b = d[i]
            if 0x81 <= b <= 0x9F or 0xE0 <= b <= 0xEF:
                i += 2
                continue
            if b not in (0x0A,) and (b < 0x20 or 0x7F <= b <= 0xA0 or b >= 0xF0):
                c[b] += 1
                ex.setdefault(b, (start + i, decode(d[i - 12:i + 12])))
            i += 1
    for b, v in sorted(c.items()):
        a, t = ex[b]
        print(f"{b:02X} {v:6d} @{a:#x} {t!r}")
