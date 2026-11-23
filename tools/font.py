"""English VWF font for the 12x14 glyph font (docs/re/text.md "English font").

The game's one font texture is UNN.PAK group 9 sub-entry 0, item 7 (a 4bpp TIM at VRAM 896,256: 21 x 18 cells of
12x14 px, 4 bit planes, one 1bpp glyph per cell and plane); item 10 is the SJIS -> cell map (TX03). We draw
fonts/vwf12.txt into cells: letters and digits replace the full-width Ａ-Ｚ ａ-ｚ ０-９ glyphs (same codes keep
working, now left-aligned), punctuation goes into cells the map never uses. The EXE hook (asm/hooks.asm) maps a byte
0x20-0x7F to a cell through `cell_tab` and advances the pen by `adv_tab`.

    python -X utf8 tools/font.py UNN.PAK OUT_DIR    -> OUT_DIR/{font_tables.bin, font.png} (no UNN change)
"""
import struct
import sys
from pathlib import Path

import gr_index
import tx03

ROOT = Path(__file__).resolve().parents[1]
FONT = ROOT / "fonts/vwf12.txt"
G9_TABLE = 0x80092D1C  # UNN group 9 sub-table
TOP = 2                # glyph row 0 -> cell row 2
CW, CH, COLS, ROWS = 12, 14, 21, 18
GAP = 1                # px between glyphs (the game's drop shadow fills one of them)


def load_glyphs(path=FONT):
    """{char: (advance, [row strings])}."""
    out, cur = {}, None
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# ") or not line.strip():  # glyph rows never hold a space
            continue
        if line.startswith("== "):
            f = line[3:].split()
            if f[0] == "space":
                out[" "] = (int(f[1]), [])
                cur = None
            else:
                cur = line[3]
                out[cur] = (0, [])
            continue
        out[cur][1].append(line)
    for c, (adv, rows) in list(out.items()):
        if rows:
            w = max(len(r) for r in rows)
            assert w <= CW and len(rows) + TOP <= CH, f"glyph {c!r} too big"
            out[c] = (w + GAP, [r.ljust(w, ".") for r in rows])
    return out


def g9_entry0(exe, unn):
    """(offset of g9 sub-entry 0 in UNN.PAK, its bytes)."""
    toc = gr_index.toc(exe)
    subs = {t: e for _, t, e in gr_index.subtables(exe)}
    s, _, size = subs[G9_TABLE][0]
    off = (toc[9][0] + s) * 0x800
    return off, unn[off:off + size]


def tim_image(a, item):
    """Offset (in a) of the pixel data of the 4bpp TIM at item, asserting the font's place and size."""
    t = struct.unpack_from("<I", a, 4 * item)[0]
    assert struct.unpack_from("<II", a, t) == (0x10, 8)
    n = struct.unpack_from("<I", a, t + 8)[0]
    x, y, w, h = struct.unpack_from("<4H", a, t + 8 + n + 4)
    assert (x, y, w) == (896, 256, 64) and h >= CH * ROWS, (x, y, w, h)
    return t + 8 + n + 12


def glyph_map(a):
    m, _ = tx03.decompress(a, struct.unpack_from("<I", a, 4 * 10)[0])
    return struct.unpack_from(f"<{(len(m) - 4) // 2}H", m, 4)


def cell_of(entry):
    return entry >> 9, (entry >> 2) & 127, entry & 3


def plan(a):
    """{char: map-format cell entry} for every glyph in the font. Space gets a blank free cell: a lookup miss draws
    ？ in the txd renderer (0x80017F10) and doesn't advance in 0x80044624."""
    gmap = glyph_map(a)
    used = {cell_of(e) for e in gmap if e}
    # entry 0 means "no glyph", so cell (0, 0, 0) can't be named
    free = [(r, c, p) for p in range(4) for r in range(ROWS) for c in range(COLS)
            if (r, c, p) not in used and (r, c, p) != (0, 0, 0)]
    glyphs = load_glyphs()
    cells, fi = {}, 0
    for ch in sorted(glyphs):
        if ch.isalnum():
            sj = chr(ord(ch) + 0xFEE0).encode("cp932")
            e = gmap[(sj[0] << 8 | sj[1]) - 0x813F]
            assert e, ch
        else:
            r, c, p = free[fi]
            fi += 1
            e = r << 9 | c << 2 | p
        cells[ch] = e
    return cells, glyphs


def draw(a, img, cells, glyphs):
    """Draw every glyph into its cell plane of the TIM pixels at img (a: bytearray)."""
    for ch, e in cells.items():
        if not e:
            continue
        r, c, p = cell_of(e)
        rows = glyphs[ch][1]
        for y in range(CH):
            for x in range(CW):
                u, v = c * CW + x, r * CH + y
                i = img + v * 128 + u // 2
                sh = 4 * (u & 1) + p
                gy = y - TOP
                on = 0 <= gy < len(rows) and x < len(rows[gy]) and rows[gy][x] == "#"
                a[i] = (a[i] & ~(1 << sh)) | (on << sh)


def tables(cells, glyphs):
    """cell_tab u16[96] + adv_tab u8[96] for bytes 0x20-0x7F (0 = no glyph; adv 0 = byte unused)."""
    cell = [cells.get(chr(b), 0) for b in range(0x20, 0x80)]
    adv = [glyphs[chr(b)][0] if chr(b) in glyphs else 0 for b in range(0x20, 0x80)]
    return struct.pack("<96H", *cell) + bytes(adv)


def patch_unn(exe, unn):
    """Font drawn into UNN.PAK (bytearray, in place); returns the hook tables."""
    off, a = g9_entry0(exe, unn)
    a = bytearray(a)
    img = tim_image(a, 7)
    cells, glyphs = plan(a)
    draw(a, img, cells, glyphs)
    unn[off:off + len(a)] = a
    return tables(cells, glyphs)


def width(text, glyphs=None):
    """Pixel width of one line of ASCII text (a full-width SJIS character, e.g. a card title, counts 13)."""
    glyphs = glyphs or load_glyphs()
    return sum(glyphs[ch][0] if ch in glyphs or ord(ch) < 0x80 else 13 for ch in text)


def preview(a, cells, out):
    from PIL import Image
    img = tim_image(a, 7)
    im = Image.new("L", (16 * 13, 6 * 15))
    for i, b in enumerate(range(0x20, 0x80)):
        e = cells.get(chr(b))
        if not e:
            continue
        r, c, p = cell_of(e)
        for y in range(CH):
            for x in range(CW):
                u, v = c * CW + x, r * CH + y
                if a[img + v * 128 + u // 2] >> (4 * (u & 1) + p) & 1:
                    im.putpixel(((i % 16) * 13 + x, (i // 16) * 15 + y), 255)
    im.resize((im.width * 3, im.height * 3), Image.NEAREST).save(out)


if __name__ == "__main__":
    exe = (Path(sys.argv[1]).parent.parent / "SLPS_012.97").read_bytes()
    unn = bytearray(Path(sys.argv[1]).read_bytes())
    out = Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    (out / "font_tables.bin").write_bytes(patch_unn(exe, unn))
    _, a = g9_entry0(exe, unn)
    cells, _ = plan(a)
    preview(a, cells, out / "font.png")
    print("ok", out)
