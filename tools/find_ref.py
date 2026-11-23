"""Find code references (lui/addiu|load|store pairs) to a RAM address in the EXE and every DATA/*.BIN overlay.

    python -X utf8 tools/find_ref.py 0x800C4E78
Overlays are taken at base 0x80166218 (docs/re/text.md); the pair must sit within 8 instructions."""
import os
import struct
import sys

ROOT = os.path.join(os.path.dirname(__file__), "..", "work", "iso", "d1", "tree")


def scan(b, base, target):
    hi = ((target + 0x8000) >> 16) & 0xFFFF
    lo = target & 0xFFFF
    for o in range(0, len(b) - 3, 4):
        w = struct.unpack_from("<I", b, o)[0]
        if w >> 26 == 0xF and w & 0xFFFF == hi:
            r = (w >> 16) & 31
            for k in range(1, 9):
                if o + 4 * k + 4 > len(b):
                    break
                w2 = struct.unpack_from("<I", b, o + 4 * k)[0]
                if (w2 >> 21) & 31 == r and w2 & 0xFFFF == lo:
                    yield base + o
                    break


if __name__ == "__main__":
    t = int(sys.argv[1], 16)
    files = [("SLPS_012.97", 0x8000F800)] + [("DATA/" + f, 0x80166218)
                                              for f in sorted(os.listdir(os.path.join(ROOT, "DATA"))) if f.endswith(".BIN")]
    for f, base in files:
        b = open(os.path.join(ROOT, f), "rb").read()
        hits = list(scan(b, base, t))
        if hits:
            print(f, " ".join(f"{h:08X}" for h in hits[:16]), f"({len(hits)})")
