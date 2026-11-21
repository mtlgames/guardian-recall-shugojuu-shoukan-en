"""gr_scan_blocks.py PAK START SIZE: list 0x800-aligned text blocks ([u32 count][u32 0][count x u32 offsets][text])."""
import struct
import sys


def scan(d):
    """Yield (offset, count, nonzero, end) for each block that parses."""
    for o in range(0, len(d), 0x800):
        if o + 8 > len(d):
            break
        n, z = struct.unpack_from("<II", d, o)
        if not (0 < n < 0x1000 and z == 0 and o + 8 + 4 * n <= len(d)):
            continue
        offs = struct.unpack_from("<%dI" % n, d, o + 8)
        nz = [x for x in offs if x]
        if not nz or min(nz) < 8 + 4 * n or o + max(nz) >= len(d):
            continue
        end = o + max(nz)
        while end < len(d) and d[end:end + 3] != b"\x01\x00\x0a":
            end += 1
        yield o, n, len(nz), end + 3


if __name__ == "__main__":
    pak, start, size = sys.argv[1], int(sys.argv[2], 0), int(sys.argv[3], 0)
    with open(pak, "rb") as f:
        f.seek(start)
        d = f.read(size)
    for o, n, k, end in scan(d):
        print(f"{start + o:#09x} +{o:#07x} count {n:4d} used {k:4d} end +{end:#07x}")
