"""EXE recon helpers (MIPS, SLPS_012.97: RAM = file + 0x8000F800).

    python -X utf8 tools/re.py fn ADDR          function start (scan back to `addiu sp,sp,-N`) + its jal callers
    python -X utf8 tools/re.py dis ADDR [N]     compact disassembly (no nops, no file offsets)
    python -X utf8 tools/re.py jal ADDR         jal ADDR callers in the EXE and every DATA/*.BIN overlay (by word)
"""
import os
import struct
import sys

from capstone import CS_ARCH_MIPS, CS_MODE_32, CS_MODE_LITTLE_ENDIAN, Cs

ROOT = os.path.join(os.path.dirname(__file__), "..", "work", "iso", "d1", "tree")
EXE = os.path.join(ROOT, "SLPS_012.97")
BASE = 0x8000F800
img = open(EXE, "rb").read()
md = Cs(CS_ARCH_MIPS, CS_MODE_32 + CS_MODE_LITTLE_ENDIAN)


def word(a):
    return struct.unpack_from("<I", img, a - BASE)[0]


def fn_start(a):
    a &= ~3
    while a > BASE + 0x800:
        w = word(a)
        if w >> 16 == 0x27BD and w & 0x8000:  # addiu sp,sp,-N
            return a
        a -= 4
    return None


def jal_refs(target):
    t = 0x0C000000 | ((target >> 2) & 0x3FFFFFF)
    out = [("EXE", BASE + o) for o in range(0x800, len(img) - 3, 4) if struct.unpack_from("<I", img, o)[0] == t]
    d = os.path.join(ROOT, "DATA")
    for f in sorted(os.listdir(d)):
        if f.upper().endswith(".BIN"):
            b = open(os.path.join(d, f), "rb").read()
            out += [(f, o) for o in range(0, len(b) - 3, 4) if struct.unpack_from("<I", b, o)[0] == t]
    return out


def dis(a, n):
    for i in md.disasm(img[a - BASE:a - BASE + 4 * n], a):
        if i.mnemonic != "nop":
            print(f"{i.address:08X} {i.mnemonic} {i.op_str}")


if __name__ == "__main__":
    cmd, a = sys.argv[1], int(sys.argv[2], 16)
    if cmd == "fn":
        s = fn_start(a)
        print(f"start {s:08X}", "callers", " ".join(f"{f}:{o:X}" for f, o in jal_refs(s)))
    elif cmd == "dis":
        dis(a, int(sys.argv[3]) if len(sys.argv) > 3 else 40)
    elif cmd == "jal":
        print(" ".join(f"{f}:{o:X}" for f, o in jal_refs(a)))
