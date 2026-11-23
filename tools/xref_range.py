"""xref_range.py LO HI FILE..: MIPS code references (lui + addiu/ori/load/store on the same register) whose absolute
address falls in [LO, HI). Position-independent, so it works on the EXE and every overlay alike. Use it before
claiming a RAM gap as free: python -X utf8 tools/xref_range.py 0x800CABF4 0x800D16F8 work/iso/d1/tree/SLPS_012.97
work/iso/d1/tree/DATA/*.BIN"""
import struct
import sys

MEM_OPS = {0x09, 0x0D, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x28, 0x29, 0x2A, 0x2B, 0x2E, 0x32, 0x3A}


def refs(data, lo, hi):
    """(file offset of the low-half instruction, address) for every lui pair landing in [lo, hi)."""
    n = len(data) // 4
    words = struct.unpack_from(f"<{n}I", data)
    for i, w in enumerate(words):
        if w >> 26 != 0x0F:
            continue
        rt, up = (w >> 16) & 31, (w & 0xFFFF) << 16
        for j in range(i + 1, min(i + 16, n)):
            x = words[j]
            if x >> 26 in MEM_OPS and (x >> 21) & 31 == rt:
                imm = x & 0xFFFF
                if x >> 26 != 0x0D and imm & 0x8000:  # ori is zero-extended
                    imm -= 0x10000
                a = (up + imm) & 0xFFFFFFFF
                if lo <= a < hi:
                    yield j * 4, a
                break
            if x >> 26 == 0x0F and (x >> 16) & 31 == rt:  # register reloaded
                break


def main():
    lo, hi, files = int(sys.argv[1], 16), int(sys.argv[2], 16), sys.argv[3:]
    total = 0
    for f in files:
        for off, a in refs(open(f, "rb").read(), lo, hi):
            print(f"{f}\t+{off:#x}\t{a:#010x}")
            total += 1
    print(f"{total} refs")


if __name__ == "__main__":
    assert list(refs(struct.pack("<2I", 0x3C04800D, 0x24841678), 0x800D0000, 0x800E0000)) == [(4, 0x800D1678)]
    main()
