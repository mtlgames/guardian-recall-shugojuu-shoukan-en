"""gr_index.py: UNN.PAK index as stored in the EXE (verified by matching group sizes; see docs/re/containers.md).

Top TOC: 28 entries at EXE RAM 0x800914DC, {u16 sector, u16 nsec, u32 bytes}, header {0, -1, "DATA\\UNN.PAK", toc}.
Sub-tables: same entry format, each followed by a header {lba (runtime), -1, 0, table_start}. Sector = offset in group.
Run: python tools/gr_index.py EXE  -> prints each sub-table and the group whose size it matches.
"""
import re
import struct
import sys

BASE = 0x80010000 - 0x800  # RAM address of EXE file offset 0
TOC = 0x800914DC
NGROUPS = 28


def ram(e, a, n):
    return e[a - BASE:a - BASE + n]


def toc(e):
    return [struct.unpack_from("<HHI", e, TOC - BASE + 8 * i) for i in range(NGROUPS)]


def subtables(e):
    """Yield (header_ram, table_ram, entries) for every {0,-1,0,ptr} header whose table ends at the header."""
    for m in re.finditer(rb"\x00\x00\x00\x00\xff\xff\xff\xff\x00\x00\x00\x00", e):
        hdr = m.start()
        (ptr,) = struct.unpack_from("<I", e, hdr + 12)
        start, end = ptr - BASE, hdr
        if not (0 < start < end and (end - start) % 8 == 0):
            continue
        ents = [struct.unpack_from("<HHI", e, p) for p in range(start, end, 8)]
        yield hdr + BASE, ptr, ents


if __name__ == "__main__":
    e = open(sys.argv[1], "rb").read()
    groups = toc(e)
    for h, t, ents in subtables(e):
        span = max(s + n for s, n, _ in ents)
        match = [i for i, (s, n, z) in enumerate(groups) if n - 1 <= span <= n]  # groups carry one spare sector
        print(f"hdr {h:#x} table {t:#x} entries {len(ents):4d} span {span:#x} sectors -> groups {match}")
