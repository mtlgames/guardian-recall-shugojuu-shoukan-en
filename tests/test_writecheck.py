"""tools/writecheck.py: armips listing spans, asm run rules, and a patched mini tree passes while stray
writes in each file kind fail."""
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import insert  # noqa: E402
import writecheck  # noqa: E402

LISTING = """\ufeff; 1 file included
FFFFFFFF .psx                                   ; x
FFFFFFFF .open "C:/t/SLPS_012.97",0x8000F800; x
8000F800 .org 0x8000F810                        ; x
8000F810 .word 0x800CAC00                       ; x
8000F814 .org 0x800CAC00                        ; x
800CAC00 boot_stub:                             ; x
800CAC00    lui     t0,-0x7FF3                  ; x
800CAC04 .headersize 0x80134BD0                 ; x
801F0000 lookup_hook:                           ; x
801F0000    nop                                 ; x
801F0008 .headersize 0x8000F800                 ; x
800CAC0C .close                                 ; x
FFFFFFFF .open "C:/t/DIC.BIN",0x80166218; x
80166218 .org 0x80166F70                        ; x
80166F70    addu    s5,s5,t8                    ; x
80166F74 .org 0x80166F74                        ; x
80166F74    nop                                 ; x
80166F78 .close                                 ; x
"""


def test_asm_blocks():
    b = writecheck.asm_blocks(LISTING)
    assert b["SLPS_012.97"] == [(0x10, 0x14), (0xBB400, 0xBB404), (0x801F0000 - 0x80134BD0, 0x801F0008 - 0x80134BD0)]
    assert b["DIC.BIN"] == [(0xD58, 0xD5C), (0xD5C, 0xD60)]


def test_asm_writes_rules():
    pre = bytes(range(1, 101)) + bytes(200)
    post = bytearray(pre)
    post[10:12] = b"\xaa\xbb"            # hook site
    post[150:250] = b"\x11" * 100        # long block over zeros
    w, e = writecheck.asm_writes("F", pre, bytes(post), [(8, 12), (12, 16), (140, 260)])
    assert e == [] and [x[0] for x in w] == [10, 150]
    w, e = writecheck.asm_writes("F", pre, bytes(post), [(8, 11), (140, 260)])
    assert "outside its listed output" in e[0]
    post[20:90] = b"\xee" * 70           # long block over code (0xEE: no byte of pre, so one run)
    w, e = writecheck.asm_writes("F", pre, bytes(post), [(8, 12), (20, 90), (140, 260)])
    assert "non-zero original bytes" in e[0]


MINI = ["DATA/UNN.PAK", "DATA/GRETC.RLZ", "DATA/ACTION.BIN", "DATA/BATTLE.BIN", "DATA/HEN.BIN", "DATA/DAY.BIN",
        "DATA/BRAIN.BIN", "DATA/DIC.BIN", "DATA/CF.BIN"]


def test_patched_tree_and_stray_writes(tmp_path):  # ~2 s: kept in the commit gate
    src = ROOT / "work/iso/d1/tree"
    if not src.is_dir():
        pytest.skip("no dump: run build.py once")
    orig, tree = tmp_path / "orig", tmp_path / "tree"
    exe = next(src.glob("SLPS_*")).name
    for rel in MINI + [exe]:
        for t in (orig, tree):
            (t / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src / rel, t / rel)
    assert insert.patch_tree(tree) == []
    assert writecheck.verify(orig, tree, insert.LOG, insert.GRETC_REBUILT) == []

    def errs_after(rel, off):
        p = tree / rel
        b = bytearray(p.read_bytes())
        b[off] ^= 0xFF
        p.write_bytes(b)
        try:
            return writecheck.verify(orig, tree, insert.LOG, insert.GRETC_REBUILT)
        finally:
            b[off] ^= 0xFF
            p.write_bytes(b)

    assert any("differing bytes outside" in e for e in errs_after(exe, 0x20000))      # EXE code
    off = insert.LOG[exe][0][0]
    assert any("overwritten" in e for e in errs_after(exe, off))                      # clobbered logged write
    assert any("group 0" in e for e in errs_after("DATA/UNN.PAK", 0x800 * 30))         # non-text UNN group
    assert any("never patches" in e for e in errs_after("DATA/CF.BIN", 100))           # file insert.py never patches
    first_kept = min(set(range(50)) - insert.GRETC_REBUILT)
    import gretc
    e = gretc.directory((tree / "DATA/GRETC.RLZ").read_bytes())[1][first_kept]
    assert any("stored bytes changed" in x for x in errs_after("DATA/GRETC.RLZ", e["off"] + 4))
