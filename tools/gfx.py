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
    lvl = np.rint(np.asarray(img, np.float32) * 15 / 255).astype(np.uint8)
    out = idx.copy()
    out[y0:y1] = 0
    return np.where(lvl > 0, LOC_LUT[lvl], out).astype(np.uint8)


# g24 CLUT as it shows on screen (PCSX-Redux, card 51 over its gradient, ~85 grey there): index -> brightness.
# Not a ramp: 1-5 ~ background, 14 = dark grey 131. Ink level k -> the index nearest bg + k/15 of the way to white
# (index = ink level put 94% edge pixels on grey 131: rough letters, user report on 雪花旅館).
LOC_LUM = {0: 85, 6: 98, 14: 131, 7: 156, 8: 180, 9: 189, 10: 213, 11: 230, 12: 238, 15: 255}
LOC_LUT = np.array([min(LOC_LUM, key=lambda i: abs(LOC_LUM[i] - (85 + 170 * k / 15))) for k in range(16)], np.uint8)


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


# G5 route choice (GRETC rsel, RSEL.BIN): 天 / 地 brush kanji, 8bpp 192x128 TIMs, index 0 = transparent; blk = dark
# stone texture, whi = white brush (the picked side). The word stays inside the kanji's ink columns: the right-hand
# sprite runs off-screen past them.
RSEL = {220: "EARTH", 221: "SKY", 223: "EARTH", 226: "SKY"}


def tim_pixels(b):
    """(offset of the pixel data, w in pixels, h) of an 8bpp TIM with a CLUT."""
    assert struct.unpack_from("<II", b) == (0x10, 9), "8bpp TIM with CLUT"
    p = 8 + struct.unpack_from("<I", b, 8)[0]
    _, _, _, w16, h = struct.unpack_from("<I4H", b, p)
    return p + 12, w16 * 2, h


def brush_word(b, word, stretch=2.4):
    """New TIM bytes: the kanji ink -> `word` (bold serif as wide as the ink columns, drawn up to `stretch` x taller
    and at most 60% of the kanji height), textured with patches of the kanji's own stroke interiors."""
    from scipy import ndimage
    p, w, h = tim_pixels(b)
    a = np.frombuffer(b, np.uint8, w * h, p).reshape(h, w)
    ys, xs = np.nonzero(a)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    size = 120
    while ImageFont.truetype(str(SERIF), size).getlength(word) > x1 - x0 - 4:
        size -= 1
    f = ImageFont.truetype(str(SERIF), size)
    l, t, r, btm = f.getbbox(word)
    img = Image.new("L", (r - l + 4, btm - t + 4), 0)
    ImageDraw.Draw(img).text((2 - l, 2 - t), word, font=f, fill=255)
    hh = max(img.height, min(round(img.height * stretch), round(0.6 * (y1 - y0))))
    img = img.resize((img.width, hh), Image.LANCZOS)
    mask = np.zeros((h, w), bool)
    ox, oy = (x0 + x1 - img.width) // 2, (y0 + y1 - img.height) // 2
    mask[oy:oy + img.height, ox:ox + img.width] = np.asarray(img) > 100
    # shading field = smooth noise (marble) + distance from the stroke edge (brush relief), mapped by quantile onto the
    # kanji's own ink colours sorted by brightness, so the word has the same colour mix as the kanji
    clut = struct.unpack_from("<256H", b, 20)
    lum = np.array([(c & 31) * 3 + (c >> 5 & 31) * 6 + (c >> 10 & 31) for c in clut])
    src = np.sort(a[a != 0])
    src = src[np.argsort(lum[src], kind="stable")]
    noise = ndimage.gaussian_filter(np.random.default_rng(len(word)).random((h, w)), 3)
    edge = np.minimum(ndimage.distance_transform_edt(mask), 4) / 4
    white = lum[src].mean() > 200
    field = (0.3 if white else 0.7) * (noise - noise.min()) / np.ptp(noise) + (0.7 if white else 0.3) * edge
    rank = np.argsort(np.argsort(field[mask]))
    new = np.zeros_like(a)
    new[mask] = src[rank * len(src) // len(rank)]
    return b[:p] + new.tobytes() + b[p + w * h:]


# G13 character-file VOICE PLAY legend (GRETC cf 217 cfvc.tim, 8bpp 140x55, index 0 transparent): "○召 △戦 CV" ->
# two stacked lines "○Summon" / "△Battle" left of CV (the game prints the voice actor's name right after CV, so the
# legend can't grow right; the box has free rows under the old line). VWF font, fill 5 = the kanji's light grey,
# shadow 1; ○ / △ redrawn 9 px tall in their own colours (13/14 red, 10/7 teal).
CFVC = 217
CFVC_X0, CFVC_X1 = 14, 68          # free columns left of CV (TIM x 69-79)
SMALL_O = ["..###..", ".#...#.", "#.....#", "#.....#", "#.....#", ".#...#.", "..###.."]
SMALL_T = ["...#...", "...#...", "..#.#..", "..#.#..", ".#...#.", ".#...#.", "#######"]


def cfvc(b):
    import font
    p, w, h = tim_pixels(b)
    a = np.frombuffer(b, np.uint8, w * h, p).reshape(h, w).copy()
    a[27:51, CFVC_X0 - 2:CFVC_X1 + 1] = 0
    glyphs = font.load_glyphs()

    def put(x, y, rows, fill, shade):
        for dy, r in enumerate(rows):
            for dx, c in enumerate(r):
                if c == "#":
                    a[y + dy + 1, x + dx + 1] = a[y + dy + 1, x + dx + 1] or shade
                    a[y + dy, x + dx] = fill

    def line(y, sym, fill, shade, text):
        put(CFVC_X0, y + 1, sym, fill, shade)
        x = CFVC_X0 + len(sym[0]) + 2
        for ch in text:
            adv, rows = glyphs[ch]
            put(x, y, rows, 5, 1)
            x += adv
        assert x <= CFVC_X1, text
    line(28, SMALL_O, 13, 14, "Summon")
    line(40, SMALL_T, 10, 7, "Battle")
    return b[:p] + a.tobytes() + b[p + w * h:]


# G11 dictionary cover (GRETC dic 204 anim00.tim, 8bpp 160x240): the orange katakana ガーディアンリコール across the
# dragon relief -> "Guardian Recall". The katakana (orange, R - B > 50, plus a 1 px ring for its shadow) is filled by
# diffusion from the relief round it, then the English is drawn orange with a dark shadow like the katakana. The
# 用語辞典 seals stay (D16: decorative stamps; the cover already says GUARDIAN RECALL DICTIONARY in English).
DIC_COVER = 204
DIC_BAND = (104, 128, 14, 140)     # y0, y1, x0, x1 holding the katakana


def nearest_index(rgb, pal, used):
    d = ((rgb[..., None, :] - pal[used][None, None]) ** 2).sum(-1)
    return used[d.argmin(-1)]


def dic_cover(b):
    from scipy import ndimage
    p, w, h = tim_pixels(b)
    a = np.frombuffer(b, np.uint8, w * h, p).reshape(h, w).copy()
    clut = np.array(struct.unpack_from("<256H", b, 20))
    pal = np.stack([clut & 31, clut >> 5 & 31, clut >> 10 & 31], -1).astype(np.float32) * 8
    y0, y1, x0, x1 = DIC_BAND
    rgb = pal[a]
    mask = np.zeros((h, w), bool)
    mask[y0:y1, x0:x1] = rgb[y0:y1, x0:x1, 0] - rgb[y0:y1, x0:x1, 2] > 50
    text_idx = a[mask]
    mask = ndimage.binary_dilation(mask, iterations=1)
    fill = rgb.copy()
    for _ in range(300):            # diffusion inpaint: masked pixels -> mean of their 4 neighbours
        avg = (np.roll(fill, 1, 0) + np.roll(fill, -1, 0) + np.roll(fill, 1, 1) + np.roll(fill, -1, 1)) / 4
        fill[mask] = avg[mask]
    used = np.unique(a[~mask])
    used = used[pal[used].sum(1) > 0]
    a[mask] = nearest_index(fill[mask][None], pal, used)[0]
    lum = pal[text_idx].sum(1)
    hi = np.bincount(text_idx[lum >= np.median(lum)]).argmax()      # orange face
    lo = np.bincount(text_idx[lum < np.percentile(lum, 25)]).argmax()  # dark shadow
    size = 22
    while ImageFont.truetype(str(SERIF), size).getlength("Guardian Recall") > x1 - x0 - 6:
        size -= 1
    img = Image.new("L", (w, h), 0)
    ImageDraw.Draw(img).text(((x0 + x1) / 2, (y0 + y1) / 2), "Guardian Recall", font=ImageFont.truetype(str(SERIF), size),
                             fill=255, anchor="mm")
    ink = np.asarray(img) > 110
    a[np.roll(ink, (1, 1), (0, 1)) & ~ink] = lo
    a[ink] = hi
    return b[:p] + a.tobytes() + b[p + w * h:]


# G10 OPTION background pentagram (GRETC brain 244 penta.tim, 8bpp 320x240): the glowing kanji in the 8 spheres round
# the circle -> the element names (glossary 主 row) in the G17 orb caps font, same glow colour, dark outline. Kanji
# ink = pixels brighter than a 9-px median of their sphere; filled from that median before the word is drawn.
PENTA = 244
PENTA_SPHERES = [((128, 40), "SKY"), ((192, 43), "NETHER"), ((233, 87), "SEA"), ((235, 152), "THUNDER"),
                 ((192, 195), "EARTH"), ((128, 193), "HOLY"), ((85, 148), "FLAME"), ((85, 90), "WIND")]


def penta(b):
    from scipy import ndimage
    p, w, h = tim_pixels(b)
    a = np.frombuffer(b, np.uint8, w * h, p).reshape(h, w).copy()
    clut = np.array(struct.unpack_from("<256H", b, 20))
    pal = np.stack([clut & 31, clut >> 5 & 31, clut >> 10 & 31], -1).astype(float)
    rgb = pal[a]
    lum = rgb @ [0.3, 0.59, 0.11]
    yy, xx = np.mgrid[0:h, 0:w]
    for (cx, cy), word in PENTA_SPHERES:
        disk = np.hypot(yy - cy, xx - cx) < 15
        y0, y1, x0, x1 = cy - 20, cy + 21, cx - 20, cx + 21
        med = np.stack([ndimage.median_filter(rgb[y0:y1, x0:x1, c], 9) for c in range(3)], -1)
        ink = np.zeros((h, w), bool)
        ink[y0:y1, x0:x1] = lum[y0:y1, x0:x1] - med @ [0.3, 0.59, 0.11] > 2.5
        ink = ndimage.binary_dilation(ink & disk) & disk
        glow = rgb[ink].max(0) if ink.any() else np.array([31, 24, 8.0])
        patch = rgb[y0:y1, x0:x1]
        m = ink[y0:y1, x0:x1]
        patch[m] = med[m]
        txt = _orb_word(word)
        th, tw = txt.shape
        t = np.zeros((h, w), bool)
        t[cy - th // 2:cy - th // 2 + th, cx - tw // 2:cx - tw // 2 + tw] = txt
        halo = ndimage.binary_dilation(t, np.ones((3, 3), bool)) & ~t
        rgb[halo] = rgb[halo] * 0.35
        rgb[t] = glow
        changed = ink | t | halo
        # nearest CLUT colour (index 0 is transparent black: never chosen)
        dist = ((rgb[changed][:, None, :] - pal[None, 1:, :]) ** 2).sum(-1)
        a[changed] = 1 + dist.argmin(1)
    return b[:p] + a.tobytes() + b[p + w * h:]


def gretc_images(rlz, battle):
    """{GRETC entry: new plain TIM bytes} for the redrawn GRETC graphics (same sizes; insert.patch_tree repacks).
    battle = DATA/BATTLE.BIN (G9 label words)."""
    import gretc
    ents = gretc.directory(rlz)[1]
    assert ents[SPLIT]["name"] == "split.tim"
    out = {SPLIT: split_sheet(gretc.expand(rlz, ents[SPLIT]), battle)}
    for i, word in RSEL.items():
        out[i] = brush_word(gretc.expand(rlz, ents[i]), word)
    out[CFVC] = cfvc(gretc.expand(rlz, ents[CFVC]))
    out[DIC_COVER] = dic_cover(gretc.expand(rlz, ents[DIC_COVER]))
    out[PENTA] = penta(gretc.expand(rlz, ents[PENTA]))
    return out


# Element orbs (G17: ring > DIAGRAM, unit HUD emblem): UNN g09 +0x1323C = TX03 of a TIM (w 124, h 470) whose CLUT
# block is really pixels for VRAM (960,40) 64x216 and whose image block is (960,0) 60x255; the CLUT block is uploaded
# last. Orbs are 4bpp 40x40, index 15 = transparent: image block rows 0-39 = orbs 0-5, CLUT block rows 0-39 x 0-159
# = orbs 6-9; orb k's CLUT = CLUT block row k, halfwords 48-63 (VRAM 1008,40+k). The kanji becomes the English
# element name (glossary 主 row) in a 7-px caps pixel font on a re-shaded sphere; the glass rim is kept.
ORB_REL, ORB_W, ORB_H = 0x1323C, 124, 470
ORB_WORDS = ["SKY", "EARTH", "THUNDER", "SEA", "FLAME", "WIND", "NETHER", "HOLY", "EMPEROR", "MASTER"]
ORB_FONT = {
    "A": ".##.|#..#|#..#|####|#..#|#..#|#..#", "D": "###.|#..#|#..#|#..#|#..#|#..#|###.",
    "E": "####|#...|#...|###.|#...|#...|####", "F": "####|#...|#...|###.|#...|#...|#...",
    "H": "#..#|#..#|#..#|####|#..#|#..#|#..#", "I": "###|.#.|.#.|.#.|.#.|.#.|###",
    "K": "#..#|#..#|#.#.|##..|#.#.|#..#|#..#", "L": "#...|#...|#...|#...|#...|#...|####",
    "M": "#...#|##.##|#.#.#|#.#.#|#...#|#...#|#...#", "N": "#..#|##.#|##.#|#.##|#.##|#..#|#..#",
    "O": ".##.|#..#|#..#|#..#|#..#|#..#|.##.", "P": "###.|#..#|#..#|###.|#...|#...|#...",
    "R": "###.|#..#|#..#|###.|#.#.|#..#|#..#", "S": ".###|#...|#...|.##.|...#|...#|###.",
    "T": "###|.#.|.#.|.#.|.#.|.#.|.#.", "U": "#..#|#..#|#..#|#..#|#..#|#..#|.##.",
    "W": "#...#|#...#|#...#|#.#.#|#.#.#|##.##|#...#", "Y": "#...#|#...#|.#.#.|..#..|..#..|..#..|..#..",
}


def _orb_word(word):
    """Bool ink mask (7 rows) of a caps word, 1 px between letters."""
    gl = [np.array([[c == "#" for c in r] for r in ORB_FONT[ch].split("|")]) for ch in word]
    out = np.zeros((7, sum(g.shape[1] for g in gl) + len(gl) - 1), bool)
    x = 0
    for g in gl:
        out[:, x:x + g.shape[1]] = g
        x += g.shape[1] + 1
    return out


def _lum(c):
    return 0.3 * (c & 31) + 0.59 * (c >> 5 & 31) + 0.11 * (c >> 10 & 31)


def orb(idx, clut, word):
    """Redraw one 40x40 orb (4bpp indices) with its CLUT (16 u16): rim kept, inside a lit sphere quantized to the
    CLUT's own colours (darkest..lightest by luminance), word dark with a light outline."""
    idx = idx.copy()
    yy, xx = np.mgrid[0:40, 0:40]
    r = np.hypot(yy - 19.5, xx - 19.5)
    inside = (idx != 15) | (r < 16)               # the art has a few transparent highlight pixels inside
    rim = inside & (r >= 17)
    lum = np.array([_lum(int(c)) for c in clut[:15]])
    order = np.argsort(lum)                       # palette indices dark -> light
    lit = 1 - np.hypot(yy - 12, xx - 13) / 34     # highlight upper left
    lit = np.clip(lit * 1.15, 0, 1) ** 1.3
    shade = order[np.clip((lit * 14).round().astype(int), 0, 14)]
    body = inside & ~rim
    idx[body] = shade[body]
    m = _orb_word(word)
    h, w = m.shape
    y0, x0 = 20 - h // 2, 20 - (w + 1) // 2
    ink = np.zeros((40, 40), bool)
    ink[y0:y0 + h, x0:x0 + w] = m
    halo = np.zeros_like(ink)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            halo |= np.roll(np.roll(ink, dy, 0), dx, 1)
    idx[halo & inside & ~ink] = order[-1]
    idx[ink] = order[0]
    return idx


def orb_sheet(d):
    """Decoded g09 orb stream (w, h + TIM) -> new TIM bytes (same layout), every orb redrawn."""
    assert struct.unpack_from("<hhIIIhhhh", d) == (ORB_W, ORB_H, 0x10, 8, 0x6C0C, 960, 40, 64, 216)
    assert struct.unpack_from("<hhhh", d, 27676) == (960, 0, 60, 255)
    t = bytearray(d[4:])
    cb = unpack(bytes(t[20:20 + 128 * 216]), 128)
    ib = unpack(bytes(t[27680:27680 + 120 * 255]), 120)
    for k, word in enumerate(ORB_WORDS):
        clut = struct.unpack_from("<16H", t, 20 + 128 * k + 96)
        blk, x = (ib, 40 * k) if k < 6 else (cb, 40 * (k - 6))
        blk[0:40, x:x + 40] = orb(blk[0:40, x:x + 40], clut, word)
    t[20:20 + 128 * 216] = (cb[:, 0::2] | cb[:, 1::2] << 4).astype(np.uint8).tobytes()
    t[27680:27680 + 120 * 255] = (ib[:, 0::2] | ib[:, 1::2] << 4).astype(np.uint8).tobytes()
    return bytes(t)


def orb_preview(d, new):
    """Original over redrawn orbs in their CLUT colours, 4x (PIL image)."""
    rows = []
    for t in (d[4:], new):
        cb = unpack(bytes(t[20:20 + 128 * 216]), 128)
        ib = unpack(bytes(t[27680:27680 + 120 * 255]), 120)
        tiles = []
        for k in range(10):
            clut = np.array(struct.unpack_from("<16H", t, 20 + 128 * k + 96))
            o = ib[0:40, 40 * k:40 * k + 40] if k < 6 else cb[0:40, 40 * (k - 6):40 * (k - 6) + 40]
            c = clut[o]
            rgb = np.stack([(c & 31) << 3, (c >> 5 & 31) << 3, (c >> 10 & 31) << 3], -1)
            rgb[o == 15] = (40, 40, 80)
            tiles.append(rgb.astype(np.uint8))
        rows.append(np.concatenate(tiles, 1))
    im = Image.fromarray(np.concatenate(rows, 0))
    return im.resize((im.width * 4, im.height * 4), Image.NEAREST)


# Battle trait/skill labels (G9): GRETC entry 4 = mill/split.tim, 4bpp 256x256, one CLUT (15 transparent, 1 dark
# outline, 2 white core, 3-8 red bands, 10-14 blue bands), 64 cells of 32x32 (index k -> column k%8, row k//8). Label
# record n (BATTLE 0x801713E8 + 12n: +0 type, +4 cell-index list, FF end, inside 0x80171374-0x801713E7, +8 the
# Japanese name, never read) draws one sprite per cell at an x advance of 26 (asm/hooks.asm makes it 32 and the
# centring 16n, so English runs on across cells). Each label is laid out as one strip of n whole cells; red (traits,
# records 0-19) or blue (skills, 20-28) as the original cells. The words are the en of the +8 strings.
SPLIT, LABEL_RECS, NLABELS = 4, 0x801713E8, 29
LABEL_LISTS = (0x80171374, 0x801713E8)
LABEL_FONT, LABEL_SIZE, LABEL_SX, LABEL_SY = SERIF, 18, 0.8, 1.375
RED_RING = {12: 6, 13: 7, 14: 8, 15: 8, 16: 8, 17: 8, 18: 7, 19: 6, 20: 5, 21: 5, 22: 4}      # row -> index, else 3
BLUE_RING = {8: 14, 9: 14, 10: 14, 11: 14, 12: 12, 13: 11, 14: 10, 15: 10, 16: 10, 17: 10, 18: 11, 19: 12, 20: 14,
             21: 14, 22: 14, 23: 14}                                                       # else 13


def label_words(battle):
    """[(English word, blue?)] per label record, from script/exe/battle.json by the record's +8 string."""
    import json
    en = {s["off"]: s["en"] for s in json.loads((ROOT / "script/exe/battle.json").read_text(encoding="utf-8"))["strings"]}
    out = []
    for n in range(NLABELS):
        _, p, s = struct.unpack_from("<III", battle, LABEL_RECS + 12 * n - DAY_BASE)
        out.append((en[s - DAY_BASE], n >= 20))
    return out


def label_art(word, blue):
    """Index array (32, 32n): `word` in condensed bold serif, white core, a band-coloured ring (+ dark outline on red)."""
    from scipy import ndimage
    ss = 4
    f = ImageFont.truetype(str(LABEL_FONT), LABEL_SIZE * ss)
    top, bot = f.getbbox("Hg")[1], f.getbbox("Hg")[3]
    w = int(f.getlength(word)) + 2 * ss
    im = Image.new("L", (w, bot - top + 2 * ss), 0)
    ImageDraw.Draw(im).text((ss, ss - top), word, font=f, fill=255)
    cw, ch = round(w * LABEL_SX / ss), round(im.height * LABEL_SY / ss)
    core = np.array(im.resize((cw, ch), Image.BOX)) >= 110
    ys, xs = np.nonzero(core)
    core = core[:, xs.min():xs.max() + 1]
    rings = 1 if blue else 2
    n = -(-(core.shape[1] + 2 * rings) // 32)
    m = np.zeros((32, 32 * n), bool)
    y0 = (32 - ch) // 2 + 1
    x0 = (32 * n - core.shape[1]) // 2
    m[y0:y0 + ch, x0:x0 + core.shape[1]] = core
    k = np.ones((3, 3), bool)
    r1 = ndimage.binary_dilation(m, k) & ~m
    a = np.full(m.shape, 15, np.uint8)
    rows = np.arange(32)[:, None].repeat(32 * n, 1)
    band = np.vectorize((BLUE_RING if blue else RED_RING).get)(rows, 13 if blue else 3)
    a[r1] = band[r1]
    if not blue:
        r2 = ndimage.binary_dilation(m | r1, k) & ~(m | r1)
        a[r2] = 1
    a[m] = 2
    return a


def label_layout(battle):
    """(cells: list of 32x32 index arrays, lists: [cell indices] per record)."""
    cells, lists = [], []
    for word, blue in label_words(battle):
        a = label_art(word, blue)
        lists.append(list(range(len(cells), len(cells) + a.shape[1] // 32)))
        cells += [a[:, x:x + 32] for x in range(0, a.shape[1], 32)]
    assert len(cells) <= 64, f"G9 labels need {len(cells)} cells > 64"
    return cells, lists


def split_sheet(b, battle):
    """split.tim bytes -> same TIM with every cell redrawn (unused cells transparent)."""
    assert struct.unpack_from("<II", b) == (0x10, 8)
    p = 8 + struct.unpack_from("<I", b, 8)[0]
    assert struct.unpack_from("<I4H", b, p)[1:] == (384, 256, 64, 256)
    a = np.full((256, 256), 15, np.uint8)
    for k, c in enumerate(label_layout(battle)[0]):
        a[k // 8 * 32:k // 8 * 32 + 32, k % 8 * 32:k % 8 * 32 + 32] = c
    return b[:p + 12] + (a[:, 0::2] | a[:, 1::2] << 4).astype(np.uint8).tobytes() + b[p + 12 + 128 * 256:]


def label_writes(battle):
    """[(BATTLE.BIN file offset, old bytes, new bytes)]: the cell lists (FF ends) and each record's +4 pointer."""
    lists = label_layout(battle)[1]
    blob = b"".join(bytes(x) + b"\xff" for x in lists)
    lo, hi = LABEL_LISTS
    assert len(blob) <= hi - lo, f"G9 lists {len(blob)} > {hi - lo} bytes"
    blob += b"\xff" * (hi - lo - len(blob))
    out = [(lo - DAY_BASE, battle[lo - DAY_BASE:hi - DAY_BASE], blob)]
    at = lo
    for n, x in enumerate(lists):
        o = LABEL_RECS + 12 * n + 4 - DAY_BASE
        out.append((o, battle[o:o + 4], struct.pack("<I", at)))
        at += len(x) + 1
    return out


def pack(cov, ink0=True):
    """4bpp, low nibble = left pixel. ink0 (title cards): CLUT 0 = white, 15 = black, 1-14 = dark to light grey
    (g17 TIM: ffff 8421 9084 .. f7bd 8000), so full ink -> 0, none -> 15, partial levels keep their index (15 - ink
    put 94% ink on near-black index 1: black specks inside letters). Else index = ink level."""
    idx = np.rint(cov.astype(np.float32) * 15 / 255).astype(np.uint8)
    if ink0:
        idx = np.where(idx == 15, 0, np.where(idx == 0, 15, idx)).astype(np.uint8)
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
    off = gr_index.toc(exe)[9][0] * SECTOR + ORB_REL
    d, end = tx03.decompress(unn, off)
    s = stream(orb_sheet(d), ORB_W)
    assert len(s) <= end - off, f"element orbs {len(s):#x} > {end - off:#x}"
    log("DATA/UNN.PAK", off, unn[off:off + len(s)], s, "gfx element orbs g09")
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
    battle_path = tree / "DATA/BATTLE.BIN"
    battle = bytearray(battle_path.read_bytes())
    for o, old, new in label_writes(bytes(battle)):
        log("DATA/BATTLE.BIN", o, old, new, "gfx battle labels G9")
        battle[o:o + len(new)] = new
    battle_path.write_bytes(battle)
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
    d = tx03.decompress(unn, gr_index.toc(exe)[9][0] * SECTOR + ORB_REL)[0]
    orb_preview(d, orb_sheet(d)).save(out / "orbs.png")
    for o, old, new in swap_layout(idx, (tree / "DATA/DAY.BIN").read_bytes()):
        print(f"DAY {o + DAY_BASE:08X}: {old.hex()} -> {new.hex()}")
    import tim
    for i, b in gretc_images((tree / "DATA/GRETC.RLZ").read_bytes(), (tree / "DATA/BATTLE.BIN").read_bytes()).items():
        bg = Image.new("RGBA", tim.read(b)[:2], (40, 40, 80, 255))
        bg.alpha_composite(tim.to_image(b))
        bg.convert("RGB").save(out / f"gretc_{i:03d}.png")
    print(out)
