"""Phase 5 engine: English font cells, hook tables, patched EXE words, text block limits."""
import re
import struct
from pathlib import Path

import pytest

import font
import insert

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work/iso/d1/tree"
need_dump = pytest.mark.skipif(not (TREE / "DATA/UNN.PAK").is_file(), reason="no dump (python build.py --identity)")
BASE = 0x8000F800


def test_glyphs_cover_ascii():
    g = font.load_glyphs()
    assert set(g) == {chr(c) for c in range(0x20, 0x7F)}
    for ch, (adv, rows) in g.items():
        assert 2 <= adv <= font.CW + font.GAP, ch
        assert all(set(r) <= {"#", "."} for r in rows), ch
    assert font.width("Hello, world!") == sum(g[c][0] for c in "Hello, world!")


@need_dump
def test_font_cells_and_tables():
    exe = (TREE / "SLPS_012.97").read_bytes()
    _, a = font.g9_entry0(exe, (TREE / "DATA/UNN.PAK").read_bytes())
    cells, glyphs = font.plan(a)
    used = [e for c, e in cells.items() if c != " "]
    assert len(set(used)) == len(used) == 94 and 0 not in used
    gmap = set(font.glyph_map(a))
    for c, e in cells.items():  # punctuation only in cells the game's map never names
        if c != " " and not c.isalnum():
            assert e not in gmap, c
    t = font.tables(cells, glyphs)
    assert len(t) == 288 and t[192] == glyphs[" "][0]


# original words at every address asm/hooks.asm overwrites (guards against a wrong or already-patched EXE)
ORIG = {0x8001A6FC: "lui v0,0x801f", 0x80044C48: "move a2,a0", 0x80044480: "addiu s3,s3,0xd",
        0x80044B4C: "lui s0,0x800d", 0x80044B50: "addiu s0,s0,0x16f8", 0x80044C30: "lui v0,0x800d",
        0x80044C38: "addiu v0,v0,0x16f8", 0x80044DE4: "lui v0,0x800d", 0x80044DE8: "addiu v0,v0,0x16f8",
        0x80044F40: "lui v1,0x800d", 0x80044F44: "addiu v1,v1,0x16f8", 0x80044FE8: "lui a0,0x800d",
        0x80044FEC: "addiu a0,a0,0x16f8", 0x80044BC0: "addiu a0,zero,0x2800"}


@need_dump
def test_hooked_words_are_original():
    from capstone import CS_ARCH_MIPS, CS_MODE_32, CS_MODE_LITTLE_ENDIAN, Cs
    md = Cs(CS_ARCH_MIPS, CS_MODE_32 + CS_MODE_LITTLE_ENDIAN)
    exe = (TREE / "SLPS_012.97").read_bytes()
    for a, want in ORIG.items():
        i = next(md.disasm(exe[a - BASE:a - BASE + 4], a))
        assert f"{i.mnemonic} {i.op_str}".replace("$", "").replace(", ", ",") == want, hex(a)
    asm = (ROOT / "asm/hooks.asm").read_text(encoding="utf-8")
    assert set(int(x, 16) for x in re.findall(r"^\.org (0x8[0-9A-F]+)", asm, re.M)) - {0x8000F810, } <= set(ORIG) | {
        int(re.search(r"STUB\s+equ \((0x[0-9A-F]+)", asm).group(1), 16)}
    assert struct.unpack_from("<I", exe, 0x10)[0] == 0x8006B1CC  # entry point the stub jumps to


@need_dump
def test_marker_blocks_fit():
    groups = insert.text_groups("marker")  # asserts every block against its buffer
    assert len(groups[23]) == 69 and len(groups[13]) == 19
