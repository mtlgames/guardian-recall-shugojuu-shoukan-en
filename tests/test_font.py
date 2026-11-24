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
        0x80044FEC: "addiu a0,a0,0x16f8", 0x80044BC0: "addiu a0,zero,0x2800",
        0x8001A708: "ori v0,v0,0x7700", 0x80044BC8: "jal 0x80064370", 0x80044C24: "jal 0x80064390",
        0x80043B60: "bnez v0,0x80043af4", 0x80043D6C: "j 0x80043ab0", 0x8004471C: "bnez v0,0x80044680",
        0x80044928: "j 0x80044680", 0x80017DC8: "lw v0,0x14(a0)", 0x80012F18: "andi v0,a2,4",
        0x80012F24: "andi v0,a2,3", 0x80012F5C: "addiu v0,zero,0x20", 0x80012F64: "addiu v0,zero,0x3a",
        0x8001E278: "sw v1,0x10(v0)", 0x8004F4B8: "lw v0,0x30(s0)",
        0x80034228: "addiu a3,zero,0x4a", 0x80034284: "addiu a3,zero,0x54", 0x80034370: "addiu a1,a1,0x33",
        0x800630E0: "addiu a0,a0,0x29", 0x80030B5C: "addiu a3,zero,0x45", 0x80030BDC: "addiu a3,zero,0x36",
        0x80063988: "addiu a0,a0,0x68", 0x800639B8: "move a1,s1", 0x800639D4: "addiu a0,a0,0xfa",
        0x80032130: "addiu a0,zero,0xdb",
        0x8002DD84: "addiu a1,zero,0x7d", 0x8002DD90: "addiu a3,zero,0x3c", 0x8002DD94: "addiu a0,zero,0x81",
        0x8004FF6C: "jal 0x8006bb54", 0x8004FF74: "srl v0,v0,1",
        0x800376D4: "addiu a3,zero,0x2b", 0x80037770: "addiu a2,fp,0x1c"}  # unit command menu box / highlight
DATA_ORIG = {0x8009BEE4: (176, 80, 240, 80, 184, 96, 248, 96)}  # 情報 Aura slot table (halfwords)
# DIC.BIN (overlay base 0x80166218): file offset -> original first word
DIC_ORIG = {0xC1C: "slti v0,s1,8", 0xC24: "addiu s1,s1,1", 0xCD0: "slti v0,s1,8", 0xD4C: "addiu s1,s1,1",
            0xD58: "addiu s5,s5,0x1a", 0xD60: "addiu s2,s2,0x1a", 0xD6C: "addiu v0,v0,1", 0x227C: "sll v0,a0,3",
            0xB94: "sll v0,v1,1", 0xD5C: "sb v0,(s2)", 0x2564: "sll v0,v1,1", 0x25A4: "addiu s1,s1,0x1a",
            0x23E8: "lui v0,3", 0x1D20: "sw a0,0x50(sp)"}
# DAY.BIN (same base): RAM address -> original word
DAY_ORIG = {0x8016ABB8: "jal 0x80012ee0"}
# ACTION.BIN (same base): ring > UNIT list column x immediates (RAM address -> original instruction)
ACTION_ORIG = {0x80171558: "addiu s0,s7,0x96", 0x80171570: "addiu a0,t2,0x5d", 0x80171578: "addiu a1,s7,0x78",
               0x801715EC: "addiu a3,s7,0xad", 0x80171614: "addiu a0,s7,0x9b", 0x8017163C: "ori s0,s7,0xb4",
               0x8017165C: "addiu a3,s7,0xcb", 0x80171674: "addiu a0,s7,0xb9", 0x80171684: "addiu s0,s7,0xd2",
               0x801716A4: "addiu a3,s7,0xe9", 0x801716BC: "addiu a0,s7,0xd7", 0x801716CC: "ori s0,s7,0xf0",
               0x801716EC: "addiu a3,s7,0x107", 0x80171704: "ori a0,s7,0xf5", 0x80171E40: "addiu a0,s1,0x5a",
               0x80171E58: "addiu a0,s1,0x96", 0x80171E70: "ori a0,s1,0xb4", 0x80171FEC: "addiu a0,t1,0x5d",
               0x80172024: "addiu a0,t3,0x99", 0x8017202C: "ori a1,s7,0xb4",
               0x80171FE8: "jal 0x80043a64",
               0x80176400: "addiu a1,zero,0x78", 0x80176408: "addiu a3,zero,0x47", 0x80176478: "addiu a0,zero,0x81",
               0x801769EC: "addiu a3,zero,0xb1", 0x80176A44: "addiu a3,zero,0xb1",
               # ring > SEARCH tabs
               0x80174284: "addiu a1,zero,0x28", 0x80174290: "addiu a3,zero,0x2d", 0x80174294: "addiu a0,zero,0x32",
               0x801742B8: "addiu a0,zero,0x50", 0x801742D8: "addiu a0,zero,0x6e", 0x80174300: "addiu a1,zero,0x46",
               0x8017430C: "addiu a3,zero,0x2d", 0x80174310: "addiu a0,zero,0x50", 0x80174334: "addiu a0,zero,0x32",
               0x80174354: "addiu a0,zero,0x6e", 0x8017437C: "addiu a1,zero,0x66", 0x80174388: "addiu a3,zero,0x2d",
               0x8017438C: "addiu a0,zero,0x6e", 0x801743B0: "addiu a0,zero,0x32", 0x801743D0: "addiu a0,zero,0x50",
               # UNIT list pages 2/3 (Master At..Mv-Type, Guardian As..Hi, Short/Long/Heal)
               0x80171928: "addiu s0,s7,0x5a", 0x80171950: "addiu s0,s7,0x5a", 0x801719A0: "ori a3,s7,0x71",
               0x801719C8: "addiu a0,s7,0x5f", 0x801719F4: "addiu s0,s7,0x78", 0x80171A1C: "addiu s0,s7,0x78",
               0x80171A6C: "addiu a3,s7,0x8f", 0x80171A94: "addiu a0,s7,0x7d", 0x80171AC0: "addiu s0,s7,0x96",
               0x80171AE8: "addiu s0,s7,0x96", 0x80171B38: "addiu a3,s7,0xad", 0x80171B60: "addiu a0,s7,0x9b",
               0x80171B8C: "ori s0,s7,0xb4", 0x80171BB4: "ori s0,s7,0xb4", 0x80171C04: "addiu a3,s7,0xcb",
               0x80171C2C: "addiu a0,s7,0xb9", 0x80171C58: "addiu s0,s7,0xd2", 0x80171C80: "addiu s0,s7,0xd2",
               0x80171CD4: "addiu a3,s7,0xe9", 0x80171CFC: "addiu a0,s7,0xd7", 0x80171D30: "addiu a0,t2,0xf3",
               0x80172250: "addiu a0,s1,0x5a", 0x80172268: "addiu a0,s1,0x78", 0x80172280: "addiu a0,s1,0x96",
               0x80172298: "ori a0,s1,0xb4", 0x8017240C: "addiu s0,s7,0x5a", 0x80172434: "addiu s0,s7,0x5a",
               0x8017246C: "ori a3,s7,0x71", 0x80172494: "addiu a0,s7,0x5f", 0x801724C0: "addiu s0,s7,0x78",
               0x801724E8: "addiu s0,s7,0x78", 0x80172520: "addiu a3,s7,0x8f", 0x80172548: "addiu a0,s7,0x7d",
               0x80172574: "addiu s0,s7,0x96", 0x8017259C: "addiu s0,s7,0x96", 0x801725D4: "addiu a3,s7,0xad",
               0x801725FC: "addiu a0,s7,0x9b", 0x80172628: "ori s0,s7,0xb4", 0x80172650: "ori s0,s7,0xb4",
               0x80172688: "addiu a3,s7,0xcb", 0x801726B0: "addiu a0,s7,0xb9", 0x801728B0: "addiu a0,s1,0x5a",
               0x801728C8: "addiu a0,s1,0x82", 0x801728E0: "addiu a0,s1,0xaa", 0x80172ADC: "addiu a0,s6,0xaa",
               0x80172AF4: "ori a0,s7,0xb5", 0x80172A40: "addiu a0,s6,0x5a", 0x80172A58: "ori a0,s7,0x65",
               0x80172A98: "addiu a0,s6,0x82", 0x80172AB0: "addiu a0,s7,0x8d"}
# ACTION.BIN UNIT list header x (halfword at RAM address; Ali Lv Exp Sp Mp Ap)
# BATTLE.BIN (same base): G9 label advance / centring
BATTLE_ORIG = {0x8016AEDC: "sll v1,v0,1", 0x8016AEF0: "sll v1,v1,1", 0x8016AFBC: "addiu v1,v1,0x1a"}
ACTION_DATA = {0x80167188: 0x5A, 0x80167190: 0x78, 0x80167198: 0x96, 0x801671A0: 0xB4, 0x801671A8: 0xD2,
               0x801671B0: 0xF0,
               0x801671DC: 0x5A, 0x801671E4: 0x78, 0x801671EC: 0x96, 0x801671F4: 0xB4, 0x801671FC: 0xD2,
               0x80167204: 0xF0}  # Master page 2 header x (At In Df Ag Mv Mv-Type)


@need_dump
def test_hooked_words_are_original():
    from capstone import CS_ARCH_MIPS, CS_MODE_32, CS_MODE_LITTLE_ENDIAN, Cs
    md = Cs(CS_ARCH_MIPS, CS_MODE_32 + CS_MODE_LITTLE_ENDIAN)
    exe = (TREE / "SLPS_012.97").read_bytes()
    dic = (TREE / "DATA/DIC.BIN").read_bytes()
    day = (TREE / "DATA/DAY.BIN").read_bytes()
    act = (TREE / "DATA/ACTION.BIN").read_bytes()
    bat = (TREE / "DATA/BATTLE.BIN").read_bytes()
    for a, want in ACTION_DATA.items():
        assert struct.unpack_from("<h", act, a - 0x80166218)[0] == want, hex(a)
    for img, base, orig in ((exe, BASE, ORIG), (dic, 0x80166218, {0x80166218 + o: w for o, w in DIC_ORIG.items()}),
                            (day, 0x80166218, DAY_ORIG), (act, 0x80166218, ACTION_ORIG),
                            (bat, 0x80166218, BATTLE_ORIG)):
        for a, want in orig.items():
            i = next(md.disasm(img[a - base:a - base + 4], a))
            assert f"{i.mnemonic} {i.op_str}".replace("$", "").replace(", ", ",") == want, hex(a)
    for a, want in DATA_ORIG.items():
        assert struct.unpack_from(f"<{len(want)}h", exe, a - BASE) == want, hex(a)
    asm = (ROOT / "asm/hooks.asm").read_text(encoding="utf-8")
    assert set(int(x, 16) for x in re.findall(r"^\.org (0x8[0-9A-F]+)\b(?!\s*\+)", asm, re.M)) - {0x8000F810, } <= set(ORIG) | set(DAY_ORIG) | set(DATA_ORIG) | set(ACTION_ORIG) | set(ACTION_DATA) | set(BATTLE_ORIG) | {
        int(re.search(r"STUB\s+equ \((0x[0-9A-F]+)", asm).group(1), 16)}
    assert set(int(x, 16) for x in re.findall(r"^\.org 0x80166218 \+ (0x[0-9A-F]+)", asm, re.M)) <= set(DIC_ORIG)
    assert struct.unpack_from("<I", exe, 0x10)[0] == 0x8006B1CC  # entry point the stub jumps to


@need_dump
def test_marker_blocks_fit():
    groups = insert.text_groups("marker")  # asserts every block against its buffer
    assert len(groups[23]) == 69 and len(groups[13]) == 19
