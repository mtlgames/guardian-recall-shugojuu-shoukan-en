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
    print(out)
