"""Callers of a function: every `jal TARGET` in the EXE and the DATA/*.BIN overlays (disc 1 dump), as RAM addresses.

    python -X utf8 tools/jal_xref.py 80060688
"""
import struct
import sys
from pathlib import Path

TREE = Path(__file__).resolve().parents[1] / "work/iso/d1/tree"


def main():
    target = int(sys.argv[1], 16)
    want = 0x0C000000 | ((target >> 2) & 0x3FFFFFF)
    for f in [TREE / "SLPS_012.97", *sorted((TREE / "DATA").glob("*.BIN"))]:
        b = f.read_bytes()
        base = 0x8000F800 if f.name.startswith("SLPS") else 0x80166218
        for i in range(0, len(b) - 3, 4):
            if struct.unpack_from("<I", b, i)[0] == want:
                print(f.name, hex(base + i))


if __name__ == "__main__":
    main()
