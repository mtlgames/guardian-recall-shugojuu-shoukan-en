"""gfx.py: redrawn graphics text (docs/re/graphics.md), written by insert.patch_tree before the UNN repack.

Title cards G1/G2: gfx/cards.tsv -> 320x240 4bpp images (index 15 = background, 0 = full ink: the card CLUT runs
white..black and the game adds it over the scene) -> TX03 streams written in place into
  - DATA/SUBTI.PAK: index {u16 sector, u16 nsec, u32 bytes} x53 at ACTION.BIN file 0x12664;
  - UNN group 17: alternate layouts of the same cards, TX03 after a 64-byte TIM header (rows `g17.N` override).
A new stream must fit its entry's sectors; SUBTI index byte counts follow a grown stream (logged ACTION.BIN
write), g17 streams must fit their old byte count (its index sits in the EXE; asserted).
CLI: python tools/gfx.py [--out DIR] -> preview PNGs of every card (as the sweep shows them: ink black on white)."""
import argparse
import hashlib
import struct
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import gr_index
import tx03

ROOT = Path(__file__).resolve().parents[1]
SECTOR = 0x800
SUBTI_INDEX = 0x12664          # ACTION.BIN file offset of the SUBTI.PAK index
G17_TAB, TIM_HDR = 0x800922E4, 64
G18_TAB = 0x800915CC           # condition cards: plain TX03 per entry, 256x240
G24_TAB = 0x80092D9C           # location cards: plain TX03 320x240 in entries 17-82
W, H, NCARDS, CW = 320, 240, 53, 256
CHAPTER = {"sky": "Sky Chapter", "earth": "Earth Chapter", "seven": "Seven Dragons Chapter",
           "awake": "Awakening Chapter", "ryuki": "Ryuki Chapter"}
SERIF = ROOT / "fonts/LiberationSerif-Bold.ttf"
SERIF_BI = ROOT / "fonts/LiberationSerif-BoldItalic.ttf"
CACHE = ROOT / "work/gfx/tx03"


def rows():
    """{key: (chapter, episode or None, title or None)}; key = 'N' (both copies) or 'g17.N' (g17 only)."""
    out = {}
    for ln in (ROOT / "gfx/cards.tsv").read_text(encoding="utf-8").splitlines():
        if ln and not ln.startswith("#"):
            k, ch, ep, title = ln.split("\t")
            assert ch in CHAPTER, ln
            out[k] = (ch, None if ep == "-" else int(ep), None if title == "-" else title)
    return out


def _font(size):
    return ImageFont.truetype(str(SERIF), size)


def _wrap(text, f, width):
    lines, cur = [], ""
    for word in text.split():
        t = f"{cur} {word}".strip()
        if cur and f.getlength(t) > width:
            lines.append(cur)
            cur = word
        else:
            cur = t
    return lines + [cur]


def card(ch, ep, title):
    """Ink coverage 0..255, H x W."""
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    if title is None:                                   # chapter card: the name alone, centred
        # 26 px: SUBTI's chapter entries are 1 sector; "Seven Dragons Chapter" at 30 px packs to 0x8EF
        d.text((W / 2, H / 2), CHAPTER[ch], font=_font(26), fill=255, anchor="mm")
        return np.asarray(img)
    small = _font(20)
    if ep is not None:
        d.text((14, 12), f"Episode {ep}", font=small, fill=255)
    d.text((W - 14, H - 12), CHAPTER[ch], font=small, fill=255, anchor="rd")
    for size in range(46, 19, -2):                      # largest size that fits 3 lines in the title area
        f = _font(size)
        lines = _wrap(title, f, W - 28)
        lh = size * 1.15
        if len(lines) <= 3 and max(f.getlength(x) for x in lines) <= W - 28 and lh * len(lines) <= 170:
            break
    y0 = 36 + (168 - lh * len(lines)) / 2
    for i, ln in enumerate(lines):
        d.text((W / 2, y0 + lh * (i + 0.5)), ln, font=f, fill=255, anchor="mm")
    return np.asarray(img)


def condition_rows():
    """[(retreat, [victory lines], [defeat lines])] by g18 entry, from gfx/conditions.tsv."""
    out = []
    for ln in (ROOT / "gfx/conditions.tsv").read_text(encoding="utf-8").splitlines():
        if ln and not ln.startswith("#"):
            k, r, v, d = ln.split("\t")
            assert int(k) == len(out), ln
            out.append((r == "1", v.split("|"), d.split("|")))
    return out


def condition(retreat, victory, defeat):
    """Ink coverage of a 256x240 condition card; geometry from the originals (headers y 46/121, x 17; lines x 38,
    25 px apart; 撤退可能 tag right of the header at y 32)."""
    img = Image.new("L", (CW, H), 0)
    d = ImageDraw.Draw(img)
    head = ImageFont.truetype(str(SERIF_BI), 26)
    if retreat:
        d.text((CW - 8, 30), "Retreat allowed", font=ImageFont.truetype(str(SERIF_BI), 14), fill=255, anchor="ra")
    for y, title, lines in ((48, "Victory Conditions", victory), (123, "Defeat Conditions", defeat)):
        d.text((17, y + 22), title, font=head, fill=255, anchor="ls")
        for i, ln in enumerate(lines):
            size = 20
            while ImageFont.truetype(str(SERIF_BI), size).getlength(ln) > CW - 38 - 6:
                size -= 1
            assert size >= 13, ln
            d.text((38, y + 46 + 25 * i), ln, font=ImageFont.truetype(str(SERIF_BI), size), fill=255, anchor="ls")
    return np.asarray(img)


def location_rows():
    """{g24 entry: [English lines]} from gfx/locations.tsv."""
    out = {}
    for ln in (ROOT / "gfx/locations.tsv").read_text(encoding="utf-8").splitlines():
        if ln and not ln.startswith("#"):
            k, en, _ = ln.split("\t")
            out[int(k)] = en.split("|")
    return out


def _bands(idx, gap=3):
    """[(y0, y1)] row runs holding ink, runs closer than `gap` blank rows merged."""
    ys = np.flatnonzero(idx.any(1))
    out = []
    for y in ys:
        if out and y - out[-1][1] <= gap:
            out[-1][1] = y + 1
        else:
            out.append([y, y + 1])
    return out


def location(idx, lines, maxsize=34):
    """Redraw a location card (idx: H x W indices 0..15, 0 = background): the Japanese block = the tallest row band
    (the big name; the region/time lines are <= 16 px) plus small bands within 8 rows of it (furigana). Its rows are
    cleared and the English name drawn there, aligned like the Japanese (left, right or centred)."""
    bands = _bands(idx)
    j = max(range(len(bands)), key=lambda i: bands[i][1] - bands[i][0])
    assert bands[j][1] - bands[j][0] >= 20, bands
    lo, hi = j, j
    while lo > 0 and bands[lo][0] - bands[lo - 1][1] <= 8 and bands[lo - 1][1] - bands[lo - 1][0] <= 17:
        lo -= 1
    while hi + 1 < len(bands) and bands[hi + 1][0] - bands[hi][1] <= 8 and bands[hi + 1][1] - bands[hi + 1][0] <= 17:
        hi += 1
    y0, y1 = bands[lo][0], bands[hi][1]
    xs = np.flatnonzero(idx[y0:y1].any(0))
    x0, x1 = xs[0], xs[-1] + 1
    top = bands[lo - 1][1] + 4 if lo else 4                 # free rows the English may use
    bot = bands[hi + 1][0] - 4 if hi + 1 < len(bands) else H - 4
    for size in range(maxsize, 15, -1):
        f = _font(size)
        lh = round(size * 1.1)
        if max(f.getlength(t) for t in lines) <= W - 16 and lh * len(lines) <= bot - top:
            break
    else:
        raise AssertionError(f"location {lines} does not fit rows {top}-{bot}")
    hgt = lh * len(lines)
    cy = min(max((y0 + y1) / 2, top + hgt / 2), bot - hgt / 2)
    if x0 >= 24 and x1 > W - 24:
        x, anchor = min(x1, W - 8), "r"
    elif x0 < 24 and x1 <= W - 24:
        x, anchor = max(x0, 8), "l"
    else:
        x, anchor = W / 2, "m"
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    for i, t in enumerate(lines):
        d.text((x, cy - hgt / 2 + lh * (i + 0.5)), t, font=f, fill=255, anchor=anchor + "m")
    new = np.rint(np.asarray(img, np.float32) * 15 / 255).astype(np.uint8)
    out = idx.copy()
    out[y0:y1] = 0
    return np.maximum(out, new)


def unpack(data, w):
    b = np.frombuffer(data, np.uint8).reshape(-1, w)
    return np.stack([b & 15, b >> 4], -1).reshape(b.shape[0], -1)


def g24_images(exe, unn):
    """{entry: packed redrawn card} for every row of gfx/locations.tsv."""
    gs = gr_index.toc(exe)[24][0]
    sub = {t: e for _, t, e in gr_index.subtables(exe)}[G24_TAB]
    out = {}
    for n, lines in location_rows().items():
        off = (gs + sub[n][0]) * SECTOR
        d = tx03.decompress(unn, off)[0]
        assert struct.unpack_from("<hh", d) == (W // 2, H), n
        for size in range(34, 20, -2):          # smaller text until the stream fits the entry's byte count
            idx = location(unpack(d[4:], W // 2), lines, size)
            out[n] = (idx[:, 0::2] | idx[:, 1::2] << 4).astype(np.uint8).tobytes()
            if len(stream(out[n])) <= sub[n][2]:
                break
    return out


# Title screen pieces (G6/G18, D15): UNN g21 offsets in the group -> (w bytes, h, text, font, size, kind). 4bpp.
# kind "ruby": index 7 = transparent, 1 = ink, 2-4 = edge levels; kind "copy": 0 = background, ink level 1-15.
TITLE = {0x24410: (96, 40, "Shugojuu Shoukan", SERIF, 26, "ruby"),    # 守護獣召喚 under the logo
         0x249D8: (64, 36, "", SERIF, 0, "ruby"),                     # ガーディアンリコール ruby: blank (D15)
         # 藺宮 涼、龍炎 狼牙: romanized as the disc-swap logo credits them ("RYO KAMIYA & RUEN ROUGA")
         0x64750: (118, 16, "Agumix / Ryo Kamiya, Ruen Rouga", ROOT / "fonts/LiberationSerif-Regular.ttf", 14, "copy")}


def title_piece(w, h, text, font, size, kind):
    """Packed 4bpp piece; text shrinks to fit the width (2 px margin)."""
    img = Image.new("L", (w * 2, h), 0)
    if text:
        while ImageFont.truetype(str(font), size).getlength(text) > w * 2 - 4:
            size -= 1
        ImageDraw.Draw(img).text((w, h / 2), text, font=ImageFont.truetype(str(font), size), fill=255, anchor="mm")
    c = np.asarray(img, np.float32) / 255
    if kind == "copy":
        idx = np.rint(c * 15).astype(np.uint8)
    else:
        idx = np.select([c >= .8, c >= .55, c >= .35, c >= .15], [1, 2, 3, 4], 7).astype(np.uint8)
    return (idx[:, 0::2] | idx[:, 1::2] << 4).astype(np.uint8).tobytes()


# Disc-swap screen (G8): sheet = UNN g09 +0x65018 (TX03 4bpp 488x160, VRAM x 640 = tpage 10, x 896 = tpage 11; bg 0,
# ink 15), sprites and layouts in DAY.BIN (tools/swap_layout.py). DISC, CHECK, OK! and the digits are the original
# English art; the Japanese pieces become caps words on their freed sheet areas: "INSERT DISC 1", "WRONG DISC",
# "DISC CHECK...", "DISC OK!" (one line in mode 0, two lines in the heroine + logo screens).
SWAP_REL, SWAP_W, SWAP_H = 0x65018, 244, 160
G9_TAB = 0x80092D1C
DAY_BASE = 0x80166218
SW_DISC, SW_D1, SW_D2, SW_CHECK, SW_OK = 0x8016C0C4, 0x8016C0D0, 0x8016C0DC, 0x8016C118, 0x8016C130
SW_NEW = {0x8016C100: ("INSERT", 11, 0, 104, 232), 0x8016C10C: ("WRONG", 10, 0, 56, 250),
          0x8016C124: ("...", 11, 0, 56, 56)}       # descriptor: text, tpage, u, v, w (h 48, baseline 44)
SW_CLEAR = [(10, 0, 56, 256, 48), (10, 112, 104, 144, 56), (11, 0, 104, 232, 56), (11, 0, 56, 152, 48),
            (11, 152, 0, 40, 48)]               # tpage, u, v, w, h: 違います, 入れて, ください, 中です, を
SW_INSERT, SW_WRONG, SW_DOTS = SW_NEW
SW_LISTS = {0: [[SW_INSERT, SW_DISC, SW_D1]], 1: [[SW_WRONG, SW_DISC]], 2: [[SW_DISC, SW_CHECK, SW_DOTS]],
            3: [[SW_DISC, SW_OK]], 4: [[SW_INSERT], [SW_DISC, SW_D2]], 5: [[SW_WRONG], [SW_DISC]],
            6: [[SW_DISC], [SW_CHECK, SW_DOTS]], 7: [[SW_DISC], [SW_OK]]}   # 0x8016C3A0[i]: 0-3 mode 0, 4-7 stacked
SW_DIGIT_CODE = {SW_D1: (0x8016BC08, 0x8016BC10), SW_D2: (0x8016BC18, 0x8016BC1C)}   # addiu a1 x / a2 y


def swap_sheet(idx, outline=False):
    """Redraw the Japanese pieces of the disc-swap sheet (H x 488 indices) in place. outline: index 1 (black) ring
    of 2 px round the new words, as the TIM copy's art has (it sits on the white yin-yang)."""
    for tp, u, v, w, h in SW_CLEAR:
        x = u + 256 * (tp - 10)
        idx[v:v + h, x:x + w] = 0
    f = ImageFont.truetype(str(SERIF), 60)
    for text, tp, u, v, w in SW_NEW.values():
        img = Image.new("L", (w, 48), 0)
        ImageDraw.Draw(img).text((2, 44), text, font=f, fill=255, anchor="ls")
        assert f.getlength(text) <= w - 4, text
        x = u + 256 * (tp - 10)
        new = np.rint(np.asarray(img, np.float32) * 15 / 255).astype(np.uint8)
        if outline:
            ink = np.pad(new > 3, 2)
            ring = np.zeros_like(new, bool)
            for dy in range(-2, 3):
                for dx in range(-2, 3):
                    ring |= ink[2 + dy:2 + dy + new.shape[0], 2 + dx:2 + dx + new.shape[1]]
            new = np.where(ring & (new <= 3), 1, new).astype(np.uint8)
        idx[v:v + 48, x:x + w] = new
    return idx


LOGO_REL, LOGO_W, LOGO_H = 0x678CC, 248, 144      # g09 small logo (8bpp, disc-swap screens 2/3), +rel in the group
LOGO_BOX = (107, 123, 143, 247)                    # rows y0-y1, cols x0-x1: the 守護獣召喚 subtitle and free space right


def logo_sub(b):
    """8bpp logo (H x W): subtitle -> "Shugojuu Shoukan", binary 12 px bold; each ink pixel keeps the original's
    colour index where the kanji had ink there, else the kanji's most common index (the CLUT is not a ramp)."""
    y0, y1, x0, x1 = LOGO_BOX
    old = b[y0:y1, x0:x1].copy()
    vals = old[old > 20]
    common = np.bincount(vals).argmax()
    img = Image.new("L", (x1 - x0, y1 - y0), 0)
    f = ImageFont.truetype(str(SERIF), 12)
    assert f.getlength("Shugojuu Shoukan") <= x1 - x0 - 2
    ImageDraw.Draw(img).text(((x1 - x0) / 2, (y1 - y0) / 2), "Shugojuu Shoukan", font=f, fill=255, anchor="mm")
    ink = np.asarray(img) > 110
    b = b.copy()
    b[y0:y1, x0:x1] = np.where(ink, np.where(old > 20, old, common), 0)
    return b


def swap_layout(idx, day):
    """[(DAY.BIN offset, old, new bytes)] for sprites, layout lists and digit positions; ink extents from `idx`."""
    def spr(p):
        return struct.unpack_from("<IHHBBBB", day, p - DAY_BASE)

    writes = []
    for p, (text, tp, u, v, w) in SW_NEW.items():
        ot, tpage, clut, *_ = spr(p)
        writes.append((p - DAY_BASE + 4, struct.pack("<HHBBBB", tpage & ~0x1F | tp, clut, u, v, w, 48)))
    sprites = {p: spr(p) for p in (SW_DISC, SW_D1, SW_D2, SW_CHECK, SW_OK)}
    sprites.update({p: (0, tp, 0, u, v, w, 48) for p, (_, tp, u, v, w) in SW_NEW.items()})

    def ink(p):
        _, tpage, _, u, v, w, h = sprites[p]
        a = idx[v:v + h, u + 256 * ((tpage & 0x1F) - 10):][:, :w] > 3
        xs, ys = np.flatnonzero(a.any(0)), np.flatnonzero(a.any(1))
        return xs[0], xs[-1] + 1, ys[-1] + 1          # ink x0, x1, baseline (caps: ink bottom)

    digit = {}
    tab = DAY_BASE
    for i, lines in SW_LISTS.items():
        lp = struct.unpack_from("<I", day, 0x8016C3A0 - tab + 4 * i)[0]
        old_n = 0
        while struct.unpack_from("<I", day, lp - tab + 8 * old_n)[0]:
            old_n += 1
        centre, base, step = (320, 259, 0) if i < 4 else (176, 115, 80)
        ents = []
        for li, line in enumerate(lines):
            e = [ink(p) for p in line]
            gaps = [2 if q == SW_DOTS else 20 for q in line[1:]]
            x = centre - (sum(x1 - x0 for x0, x1, _ in e) + sum(gaps)) // 2
            for j, (p, (x0, x1, b)) in enumerate(zip(line, e)):
                pos = (int(x - x0), int(base + step * li - b))
                if p in SW_DIGIT_CODE:
                    digit[p] = pos
                else:
                    ents.append((p, *pos))
                x += x1 - x0 + (gaps[j] if j < len(gaps) else 0)
        assert len(ents) <= old_n, i
        writes.append((lp - tab, b"".join(struct.pack("<IHH", *e) for e in ents) + bytes(8)))
    for p, (ax, ay) in SW_DIGIT_CODE.items():
        x, y = digit[p]
        assert struct.unpack_from("<I", day, ax - tab)[0] >> 16 == 0x2405, hex(ax)
        writes.append((ax - tab, struct.pack("<I", 0x24050000 | x)))    # addiu a1, zero, x
        writes.append((ay - tab, struct.pack("<I", 0x24060000 | y)))    # addiu a2, zero, y
    return [(o, day[o:o + len(n)], n) for o, n in writes]


def pack(cov, ink0=True):
    """4bpp, low nibble = left pixel; ink0: index 15 - ink level (title cards), else index = ink level."""
    idx = np.rint(cov.astype(np.float32) * 15 / 255).astype(np.uint8)
    if ink0:
        idx = 15 - idx
    return (idx[:, 0::2] | idx[:, 1::2] << 4).astype(np.uint8).tobytes()


def stream(data, w=W // 2):
    """TX03 of a packed card (w bytes per row), cached by content (the compressor is pure Python)."""
    h = hashlib.sha1(data + bytes([w])).hexdigest()
    p = CACHE / f"{h}.bin"
    if p.exists():
        return p.read_bytes()
    s = tx03.compress(w, len(data) // w, data)
    assert tx03.decompress(s)[0][4:] == data
    CACHE.mkdir(parents=True, exist_ok=True)
    p.write_bytes(s)
    return s


def images():
    """{'subti': {n: packed}, 'g17': {n: packed}, 'g18': {n: packed}}."""
    r = rows()
    out = {"subti": {}, "g17": {}, "g18": {}}
    for n in range(NCARDS):
        base = r[str(n)]
        out["subti"][n] = pack(card(*base))
        out["g17"][n] = pack(card(*r.get(f"g17.{n}", base)))
    for n, c in enumerate(condition_rows()):
        out["g18"][n] = pack(condition(*c), ink0=False)
    return out


def patch(tree, exe, unn, log):
    """Write every card into tree's SUBTI.PAK and into `unn` (bytearray, pre-repack layout). log(rel, off, orig, new,
    who) records each write (UNN offsets are pre-repack; writecheck maps them per group)."""
    tree = Path(tree)
    action = (tree / "DATA/ACTION.BIN").read_bytes()
    action_new = bytearray(action)
    pak_path = tree / "DATA/SUBTI.PAK"
    pak = bytearray(pak_path.read_bytes())
    gs = gr_index.toc(exe)[17][0]
    sub = {t: e for _, t, e in gr_index.subtables(exe)}[G17_TAB]
    imgs = images()
    for n in range(NCARDS):
        sec, nsec, size = struct.unpack_from("<HHI", action, SUBTI_INDEX + 8 * n)
        s = stream(imgs["subti"][n])
        assert len(s) <= nsec * SECTOR, f"SUBTI card {n}: {len(s):#x} > {nsec} sectors"
        if len(s) > size:   # grows inside its sectors: the index byte count follows
            o = SUBTI_INDEX + 8 * n + 4
            log("DATA/ACTION.BIN", o, action[o:o + 4], struct.pack("<I", len(s)), "gfx cards index")
            action_new[o:o + 4] = struct.pack("<I", len(s))
        off = sec * SECTOR
        log("DATA/SUBTI.PAK", off, pak[off:off + len(s)], s, "gfx cards")
        pak[off:off + len(s)] = s
        s = stream(imgs["g17"][n])
        sec, _, size = sub[n]
        assert len(s) <= size - TIM_HDR, f"g17 card {n}: {len(s):#x} > {size - TIM_HDR:#x}"
        off = (gs + sec) * SECTOR + TIM_HDR
        assert unn[off - TIM_HDR + 8:off - TIM_HDR + 12] == b"\x2c\0\0\0" and unn[off:off + 4] == b"TX03"
        log("DATA/UNN.PAK", off, unn[off:off + len(s)], s, "gfx cards g17")
        unn[off:off + len(s)] = s
    gs = gr_index.toc(exe)[18][0]
    sub = {t: e for _, t, e in gr_index.subtables(exe)}[G18_TAB]
    assert len(sub) == len(imgs["g18"])
    for n, data in imgs["g18"].items():
        s = stream(data, CW // 2)
        sec, _, size = sub[n]
        assert len(s) <= size, f"g18 card {n}: {len(s):#x} > {size:#x}"
        off = (gs + sec) * SECTOR
        assert unn[off:off + 4] == b"TX03"
        log("DATA/UNN.PAK", off, unn[off:off + len(s)], s, "gfx conditions g18")
        unn[off:off + len(s)] = s
    gs = gr_index.toc(exe)[24][0]
    sub = {t: e for _, t, e in gr_index.subtables(exe)}[G24_TAB]
    for n, data in g24_images(exe, unn).items():
        s = stream(data)
        sec, _, size = sub[n]
        assert len(s) <= size, f"g24 card {n}: {len(s):#x} > {size:#x}"
        off = (gs + sec) * SECTOR
        log("DATA/UNN.PAK", off, unn[off:off + len(s)], s, "gfx locations g24")
        unn[off:off + len(s)] = s
    gs = gr_index.toc(exe)[21][0] * SECTOR
    for rel, (w, h, *rest) in TITLE.items():
        off = gs + rel
        d, end = tx03.decompress(unn, off)
        assert struct.unpack_from("<hh", d) == (w, h), hex(rel)
        s = stream(title_piece(w, h, *rest), w)
        assert len(s) <= end - off, f"title piece {rel:#x}: {len(s):#x} > {end - off:#x}"
        log("DATA/UNN.PAK", off, unn[off:off + len(s)], s, "gfx title g21")
        unn[off:off + len(s)] = s
    off = gr_index.toc(exe)[9][0] * SECTOR + SWAP_REL
    d, end = tx03.decompress(unn, off)
    assert struct.unpack_from("<hh", d) == (SWAP_W, SWAP_H)
    idx = swap_sheet(unpack(d[4:], SWAP_W))
    s = stream((idx[:, 0::2] | idx[:, 1::2] << 4).astype(np.uint8).tobytes(), SWAP_W)
    assert len(s) <= end - off, f"swap sheet {len(s):#x} > {end - off:#x}"
    log("DATA/UNN.PAK", off, unn[off:off + len(s)], s, "gfx disc swap g09")
    unn[off:off + len(s)] = s
    off = gr_index.toc(exe)[9][0] * SECTOR + LOGO_REL
    d, end = tx03.decompress(unn, off)
    assert struct.unpack_from("<hh", d) == (LOGO_W, LOGO_H)
    s = stream(logo_sub(np.frombuffer(d[4:], np.uint8).reshape(LOGO_H, LOGO_W)).tobytes(), LOGO_W)
    assert len(s) <= end - off, f"swap logo {len(s):#x} > {end - off:#x}"
    log("DATA/UNN.PAK", off, unn[off:off + len(s)], s, "gfx disc swap logo g09")
    unn[off:off + len(s)] = s
    # mode 0 (DISC 1 screen) loads an uncompressed TIM copy of the sheet: g9 entry 8, pixels at +0x60
    o = (gr_index.toc(exe)[9][0] + {t: e for _, t, e in gr_index.subtables(exe)}[G9_TAB][8][0]) * SECTOR
    assert struct.unpack_from("<IIIhhhh", unn, o)[:2] == (0x10, 8) and struct.unpack_from("<hh", unn, o + 0x5C) == (
        SWAP_W // 2, SWAP_H)
    o += 0x60
    t = swap_sheet(unpack(unn[o:o + SWAP_W * SWAP_H], SWAP_W), outline=True)
    new = (t[:, 0::2] | t[:, 1::2] << 4).astype(np.uint8).tobytes()
    log("DATA/UNN.PAK", o, unn[o:o + len(new)], new, "gfx disc swap g09 TIM")
    unn[o:o + len(new)] = new
    day_path = tree / "DATA/DAY.BIN"
    day = bytearray(day_path.read_bytes())
    for o, old, new in swap_layout(idx, bytes(day)):
        log("DATA/DAY.BIN", o, old, new, "gfx disc swap layout")
        day[o:o + len(new)] = new
    day_path.write_bytes(day)
    pak_path.write_bytes(pak)
    (tree / "DATA/ACTION.BIN").write_bytes(action_new)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "work/gfx/cards"))
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    for kind, d in images().items():
        for n, data in d.items():
            b = np.frombuffer(data, np.uint8).reshape(H, -1)
            px = np.stack([b & 15, b >> 4], -1).reshape(H, -1) * 17
            Image.fromarray(px.astype(np.uint8)).save(out / f"{kind}_{n:02d}.png")
    tree = ROOT / "work/iso/d1/tree"
    exe = next(tree.glob("SLPS_*")).read_bytes()
    for n, data in g24_images(exe, (tree / "DATA/UNN.PAK").read_bytes()).items():
        Image.fromarray((unpack(data, W // 2) * 17).astype(np.uint8)).save(out / f"g24_{n:02d}.png")
    for rel, (w, *rest) in TITLE.items():
        Image.fromarray((unpack(title_piece(w, *rest), w) * 17).astype(np.uint8)).save(out / f"title_{rel:05x}.png")
    unn = (tree / "DATA/UNN.PAK").read_bytes()
    d = tx03.decompress(unn, gr_index.toc(exe)[9][0] * SECTOR + SWAP_REL)[0]
    idx = swap_sheet(unpack(d[4:], SWAP_W))
    Image.fromarray((idx * 17).astype(np.uint8)).save(out / "swap_sheet.png")
    for o, old, new in swap_layout(idx, (tree / "DATA/DAY.BIN").read_bytes()):
        print(f"DAY {o + DAY_BASE:08X}: {old.hex()} -> {new.hex()}")
    print(out)
