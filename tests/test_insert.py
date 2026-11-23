"""insert.py relocation helpers: repoint (u32 word + lui/low pair) and the evd name table."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import insert  # noqa: E402

BASE = 0x80010000


def test_repoint_word_and_pairs():
    old, new = 0x80012760, 0x801F8123  # new lo >= 0x8000: addiu needs hi + 1, ori doesn't
    img = bytearray(32)
    struct.pack_into("<I", img, 0, old)
    struct.pack_into("<IIII", img, 4, 0x3C048001, 0x00000000, 0x24842760, 0x3C058001)  # lui a0 / nop / addiu a0,a0
    struct.pack_into("<I", img, 20, 0x34A52760)                                          # ori a1,a1
    insert.repoint(img, BASE, f"w{BASE:08X}", old, new)
    insert.repoint(img, BASE, f"p{BASE + 4:08X}", old, new)
    insert.repoint(img, BASE, f"p{BASE + 16:08X}", old, new)
    w = struct.unpack_from("<8I", img)
    assert w[0] == new
    assert w[1] & 0xFFFF == 0x8020 and w[3] & 0xFFFF == 0x8123  # (0x801F << 16) + sign-extended 0x8123 = new
    assert w[4] & 0xFFFF == 0x801F and w[5] & 0xFFFF == 0x8123
    assert w[1] >> 16 == 0x3C04 and w[3] >> 16 == 0x2484 and w[5] >> 16 == 0x34A5


def test_name_table():
    t = insert.name_table([b"Miyuki Amagi", b"Bomb"])
    offs = struct.unpack_from("<2H", t)
    assert [t[o:t.index(b"\0", o)] for o in offs] == [b"Miyuki Amagi", b"Bomb"]
