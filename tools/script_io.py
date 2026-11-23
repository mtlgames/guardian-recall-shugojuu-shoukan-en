"""Text containers of Guardian Recall: parse to string records and rebuild to bytes (docs/re/text.md).

Every parser returns the layout needed to rebuild the container byte for byte, so `build(parse(b)) == b` holds for
the original (tests/test_script.py) and the same builders insert the translation later (phase 7).

- slot blocks: UNN.PAK groups 23 (scenario) and 13 (battle quotes): `u32 count, u32 0, count x u32 offset`; txd files
  (GRETC.RLZ group txd): 1024 x u32 offset. Strings follow in slot order of first use, each `text 00`, optionally
  preceded by 0x0A filler (`pre`); the block ends in `tail` (0x0A + zero padding).
- evd scripts (GRETC.RLZ group evd): op 0x34 `34 idx len text 00` (len counts text + NUL) = unit name.
- EXE / overlay strings: NUL-terminated, in place; reached by u32 pointers and lui/addiu pairs.
- UNN.PAK: TOC in the EXE `{u16 sector, u16 nsec, u32 bytes}` per group; sub-tables per group (gr_index.py).
- GRETC.RLZ: directory + entries (gretc.py); entries are stored pack(xor(plain)).

Text form: tbl/jp.tbl decode with `{nl}` shown as a real newline and the final `{end}` left off.
"""
import re
import struct
from pathlib import Path

import gr_index
import gretc
import rlz
from tbl import Table

ROOT = Path(__file__).resolve().parents[1]
JP = Table.load(ROOT / "tbl/jp.tbl")
# Same codes, but hiragana and ー encode to their Shift-JIS pairs: EXE/overlay strings (C source) use those, the
# scenario uses the single bytes. tbl.py escapes the non-canonical form as [XX], so each string picks one table.
# Most scenario lines mix single-byte hiragana with the SJIS ー (815B), so ー gets its own variant too.
_lines = (ROOT / "tbl/jp.tbl").read_text(encoding="utf-8").splitlines()
_single = [l for l in _lines if re.match(r"(A[6-9A-F]|[BC][0-9A-F]|D[0-9A-D])=", l)]
_long = ["815B=ー"]
TABLES = {"jp": JP,
          "jp-": Table(_long + _lines),
          "sjis": Table([l for l in _lines if l not in _single] + _single)}
SECTOR = 0x800
TXD_SLOTS = 1024


def dec(b):
    """Bytes of one string without its 00 -> (text, table name): the table needing fewer [XX] escapes."""
    best = None
    for name, t in TABLES.items():
        s = t.decode(b, 0, len(b))[0].replace("{nl}", "\n")
        if best is None or s.count("[") < best[0].count("["):
            best = (s, name)
    return best


def enc(t, table=JP):
    return table.encode(t.replace("\n", "{nl}"))


def rec(b):
    """{"jp": text} (+ "tbl": "sjis" when the string uses Shift-JIS kana)."""
    t, name = dec(b)
    return {"jp": t} if name == "jp" else {"jp": t, "tbl": name}


def enc_jp(s):
    """Original bytes of a record (without the 00)."""
    return enc(s["jp"], TABLES[s.get("tbl", "jp")])


# ---- slot blocks (UNN text blocks, txd) ----

def parse_slots(b, txd=False):
    """txd: 1024 offsets at 0. Else `u32 count, u32 0, offsets`; g23 entry 43 has count 0 and g13 entry 2 (item
    help) `u32 80` with no 0 word: there the offsets run up to the first string."""
    if txd:
        count, hdr = TXD_SLOTS, 0
    else:
        n, z = struct.unpack_from("<II", b)
        hdr = 8 if z == 0 else 4
        count = n if z == 0 and n else None
    if count is None:
        count, first = 0, len(b)
        while hdr + 4 * (count + 1) <= first:
            x = struct.unpack_from("<I", b, hdr + 4 * count)[0]
            if x == 0x0A0A0A0A:  # 0x0A filler before the first string (entry 43: 254 slots)
                break
            first = min(first, x) if x else first
            count += 1
    offs = struct.unpack_from(f"<{count}I", b, hdr)
    pos = hdr + 4 * count
    strings = []
    for o in sorted(set(x for x in offs if x)):
        assert o >= pos, f"overlapping string at {o:#x}"
        gap = b[pos:o]  # 0x0A filler; a few blocks also hold unreferenced staging notes here (kept as hex)
        end = b.index(b"\0", o)
        strings.append({"slots": [i for i, x in enumerate(offs) if x == o],
                        "pre": len(gap) if set(gap) <= {0x0A} else gap.hex(), **rec(b[o:end])})
        pos = end + 1
    return {"head": b[:hdr].hex(), "count": count, "tail": b[pos:].hex(), "strings": strings}


def build_slots(blk, encode=enc_jp):
    """encode(record) -> bytes without the 00; the default rebuilds the original."""
    count = blk["count"]
    offs = [0] * count
    pre = bytes.fromhex(blk["head"])
    head = len(pre) + 4 * count
    body = bytearray()
    for s in blk["strings"]:
        body += b"\x0a" * s["pre"] if isinstance(s["pre"], int) else bytes.fromhex(s["pre"])
        for i in s["slots"]:
            offs[i] = head + len(body)
        body += encode(s) + b"\0"
    return pre + struct.pack(f"<{count}I", *offs) + bytes(body) + bytes.fromhex(blk["tail"])


# ---- evd unit names ----

NAME_RE = re.compile(rb"\x34(?=[\x00-\xff][\x02-\xff])")  # lookahead: `34 05 34 00 0b` holds a name at the 2nd 34
CHARS = re.compile(rb"(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\xa1-\xdf]|[\x20-\x7e])+")


def parse_evd(b):
    """op 0x34 names whose bytes are valid text holding at least one Japanese character."""
    out = []
    for m in NAME_RE.finditer(b):
        o, n = m.start() + 3, b[m.start() + 2]
        s = b[o:o + n]
        if len(s) == n and s[-1] == 0 and CHARS.fullmatch(s[:-1]) and re.search(rb"[\x81-\x9f\xe0-\xef\xa1-\xdf]", s):
            out.append({"off": o, "idx": b[m.start() + 1], **rec(s[:-1])})
    return out


# ---- UNN.PAK ----

def unn_groups(exe, unn):
    """{group: [sub-entry bytes]} for the text groups, plus the index needed to rebuild."""
    toc = gr_index.toc(exe)
    subs = {t: ents for _, t, ents in gr_index.subtables(exe)}
    out = {}
    for g, tab in TEXT_GROUPS.items():
        gs = toc[g][0]
        out[g] = [unn[(gs + s) * SECTOR:(gs + s) * SECTOR + size] for s, n, size in subs[tab]]
    return out


TEXT_GROUPS = {23: 0x80092734, 13: 0x8009296C}  # group -> sub-table RAM address
NONTEXT = set()  # (group, entry) of sub-entries that are not text blocks: none


def unn_repack(exe, unn, groups):
    """New (exe, unn) with the text groups' sub-entries replaced by `groups` {g: [bytes]}.

    Each sub-entry starts on a sector; a group keeps its sector count while it fits (plus the spare sector the
    original carries), and later groups move up when one grows. TOC and sub-tables in the EXE are rewritten."""
    exe = bytearray(exe)
    toc = gr_index.toc(exe)
    order = sorted(range(len(toc)), key=lambda g: toc[g][0])
    out = bytearray(unn[:toc[order[0]][0] * SECTOR])
    for g in order:
        s0, n0, b0 = toc[g]
        old = unn[s0 * SECTOR:(s0 + n0) * SECTOR]
        if g in groups:
            tab = TEXT_GROUPS[g]
            ents = struct.iter_unpack("<HHI", exe[tab - gr_index.BASE:tab - gr_index.BASE + 8 * len(groups[g])])
            data = bytearray()
            for i, ((s, n, size), new) in enumerate(zip(ents, groups[g])):
                assert len(data) <= s * SECTOR or len(data) % SECTOR == 0
                s_new = len(data) // SECTOR
                # keep the original sector span (and its padding bytes) while the entry fits
                pad = old[s * SECTOR + len(new):(s + n) * SECTOR] if len(new) <= n * SECTOR else b""
                blob = new + pad
                blob += bytes(-len(blob) % SECTOR)
                struct.pack_into("<HHI", exe, tab - gr_index.BASE + 8 * i, s_new, len(blob) // SECTOR, len(new))
                data += blob
            need = len(data) // SECTOR + 1  # spare sector
            n_new = max(n0, need)
            data += old[len(data):n_new * SECTOR] if len(data) < len(old) else b""
            data += bytes(n_new * SECTOR - len(data))
            b_new = b0 if n_new == n0 else (n_new - 1) * SECTOR
        else:
            data, n_new, b_new = old, n0, b0
        struct.pack_into("<HHI", exe, gr_index.TOC - gr_index.BASE + 8 * g, len(out) // SECTOR, n_new, b_new)
        out += data
    end = (toc[order[-1]][0] + toc[order[-1]][1]) * SECTOR
    out += unn[end:]
    return bytes(exe), bytes(out)


# ---- GRETC.RLZ ----

def gretc_entries(data):
    _, ents = gretc.directory(data)
    return ents


def gretc_repack(data, new):
    """New GRETC.RLZ with entries `new` {index: plain bytes} replaced (stored = pack(xor(plain)) when packed).

    Entries stay in directory order, each on its own sectors; crc and stamp are kept (a crc mismatch only prints
    "(CRC-ERROR)", docs/re/containers.md)."""
    head, ents = gretc.directory(data)
    hdr_len = 0xB0 + len(ents) * 0x34
    dirx = bytearray(gretc.unxor(data[:hdr_len]))
    body = bytearray(data[:ents[0]["sector"] * SECTOR])
    for i, e in enumerate(ents):
        if i in new:
            plain = new[i]
            b = rlz.xor(plain, e["b17"]) if e["b17"] else plain
            stored = rlz.pack(b, e["b18"]) if e["packed"] else b
            old = data[e["sector"] * SECTOR:(e["sector"] + e["nsec"]) * SECTOR]
            blob = stored + (old[len(stored):] if len(stored) <= len(old) else b"")  # padding holds stale bytes
            blob += bytes(-len(blob) % SECTOR)
            size, psize = len(plain), len(stored)
        else:
            blob = data[e["sector"] * SECTOR:(e["sector"] + e["nsec"]) * SECTOR]
            size, psize = e["size"], e["psize"]
        sec = len(body) // SECTOR
        p = 0xB0 + i * 0x34
        struct.pack_into("<IIIII", dirx, p + 0x1C, sec * SECTOR, size, psize, sec, len(blob) // SECTOR)
        body += blob
    struct.pack_into("<II", dirx, 0x80, len(body), len(body) // SECTOR)
    body[:hdr_len] = gretc.unxor(bytes(dirx))
    return bytes(body)


# ---- EXE / overlay strings ----

EXE_BASE = 0x8000F800
# file, RAM base of file offset 0, text ranges (file offsets) - docs/re/text.md
IMAGES = {
    "exe": ("SLPS_012.97", EXE_BASE, [(0x800, 0x2F60), (0xA4250, 0xA6C00)]),
    "action": ("DATA/ACTION.BIN", 0x80166218, [(0xEC, 0x10EC)]),
    "battle": ("DATA/BATTLE.BIN", 0x80166218, [(0x4, 0x2E28)]),
    "hen": ("DATA/HEN.BIN", 0x80166218, [(0x4, 0x320)]),
    "day": ("DATA/DAY.BIN", 0x80166218, [(0x64, 0x2C0)]),
    # BRAIN loads at the TITLE base (docs/re/debug.md); menu label pointers at file 0x2AF4.. (stride 20)
    "brain": ("DATA/BRAIN.BIN", 0x80162F88, [(0x4, 0x60)]),
}
TEXT_RUN = re.compile(rb"(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\xa1-\xdf]|[\x0a\x01\x20-\x7e])+")
HAS_JP = re.compile(rb"[\x81-\x9f\xe0-\xef\xa1-\xdf]")


def refs(img, base):
    """{ram: [(kind, ram of the reference)]} from u32 words and lui pairs (str_refs.py)."""
    import str_refs
    out = {}
    for k, v in str_refs.words(img, base).items():
        out.setdefault(k, []).extend(("w", a) for a in v)
    for k, v in str_refs.pairs(img, base).items():
        out.setdefault(k, []).extend(("p", a) for a in v)
    return out


def image_strings(img, base, ranges, rf):
    """Strings in the text ranges: every NUL-ended run of valid text holding Japanese, and every referenced
    address inside a range that starts such a string (also inside a longer run of other bytes)."""
    found = {}
    for a, b in ranges:
        for m in re.finditer(rb"[^\x00]+", img[a:b]):
            r, o = m.group(), a + m.start()
            if TEXT_RUN.fullmatch(r) and HAS_JP.search(r):
                found[o] = len(r)
        for ram in rf:
            o = ram - base
            if a <= o < b and o not in found and img[o]:
                end = img.index(b"\0", o)
                r = img[o:end]
                inside = [s for s, n in found.items() if s < o < s + n]
                if not inside and TEXT_RUN.fullmatch(r) and HAS_JP.search(r):
                    found[o] = len(r)
    import bisect
    keys = sorted(rf)
    for o in list(found):
        # a run whose start nobody references but whose tail is referenced: the string starts at the reference
        # (ACTION 0x107: a stray 0xEE byte before the referenced "Ｓ")
        n = found[o]
        if base + o not in rf:
            inner = keys[bisect.bisect_right(keys, base + o):bisect.bisect_left(keys, base + o + n)]
            tail = img[inner[0] - base:o + n] if inner else b""
            if inner and TEXT_RUN.fullmatch(tail) and HAS_JP.search(tail):
                del found[o]
                found[inner[0] - base] = o + n - (inner[0] - base)
    out = []
    for o in sorted(found):
        n = found[o]
        room = n + 1
        while o + room < len(img) and img[o + room] == 0 and (o + room) % 4:
            room += 1  # zero padding up to the next word boundary
        start = [f"{k}{a:08X}" for k, a in rf.get(base + o, [])]
        lo, hi = bisect.bisect_right(keys, base + o), bisect.bisect_left(keys, base + o + n)
        inner = [f"+{x - base - o}" for x in keys[lo:hi]]
        out.append({"off": o, "room": room, "refs": start, "inner": inner, **rec(img[o:o + n])})
    return out
