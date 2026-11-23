"""Compact MIPS disassembly of the EXE or any DATA/*.BIN overlay (disc 1 dump), no nops.

    python -X utf8 tools/dis_ovl.py DATA/DAY.BIN 8016AB30 40      overlays at base 0x80166218
    python -X utf8 tools/dis_ovl.py SLPS_012.97 8005DED0 20       EXE (RAM = file + 0x8000F800)
"""
import sys
from pathlib import Path

from capstone import CS_ARCH_MIPS, CS_MODE_32, CS_MODE_LITTLE_ENDIAN, Cs

TREE = Path(__file__).resolve().parents[1] / "work/iso/d1/tree"
f, a, n = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3]) if len(sys.argv) > 3 else 40
base = 0x80166218 if f.upper().startswith("DATA") else 0x8000F800
b = (TREE / f).read_bytes()
for i in Cs(CS_ARCH_MIPS, CS_MODE_32 + CS_MODE_LITTLE_ENDIAN).disasm(b[a - base:a - base + 4 * n], a):
    if i.mnemonic != "nop":
        print(f"{i.address:08X} {i.mnemonic} {i.op_str}")
