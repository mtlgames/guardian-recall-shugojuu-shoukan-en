"""Insert script/ text into a disc file tree (called by build.patch).

Modes: "en" = each record's `en` (records without one keep their original bytes); "marker" = every record replaced by
its id + filler of the same line/page shape (phase 5 marker build, docs/re/text.md "Marker build").

Limits (asm/hooks.asm): scenario blocks (UNN g23) load into SCEN_BUF (0x8000 bytes), battle-quote blocks (g13) into
malloc(G13_MAX = 0x4000)."""
import json
import os
import re
import struct
import subprocess
from pathlib import Path

import font
import script_io

ROOT = Path(__file__).resolve().parents[1]
ARMIPS = ROOT / "tools/armips/armips.exe"
LIMITS = {23: 0x8000, 13: 0x4000}
DIRS = {23: "scenario", 13: "battle"}
FILLER = "The quick brown fox jumps over the lazy dog. 0123456789 Ready? Go!"
RULER = "".join(str(i % 10) for i in range(80))  # digits: 6 px each, so the last one shown gives the width


def fit(text, px, glyphs):
    out = ""
    for ch in text:
        if font.width(out + ch, glyphs) > px:
            break
        out += ch
    return out


def marker_text(s, glyphs, px=300):
    """Same pages / lines as the Japanese; first line = id, the others = numbered filler past any box width."""
    short = s["id"].split(".", 1)[1] if s["id"].startswith("g") else s["id"]
    pages = s["jp"].split("{wait}")
    out, n = [], 0
    for p, page in enumerate(pages):
        lines = page.split("\n")
        new = []
        for i, line in enumerate(lines):
            if not line:
                new.append("")
                continue
            n += 1
            if p == 0 and i == 0:
                new.append(f"[{short}]")
            elif n % 2:
                new.append(fit(f"{n}:{RULER}", px, glyphs))
            else:
                new.append(fit(f"{n}:{FILLER}", px, glyphs))
        out.append("\n".join(new))
    return "{wait}".join(out)


MARKUP = re.compile(r"(&[a-z]\([^)]*\))")
JP_CHAR = re.compile(r"[^\x00-\x7f]")


def ascii_fill(tag, n):
    """tag + filler, exactly n ASCII chars (n = the Japanese byte count, so the record keeps its size)."""
    return (tag + ":" + FILLER * 4)[:n] if n > len(tag) else tag[:n]


B36 = "0123456789abcdefghijklmnopqrstuvwxyz"
PREFIX = {"exe": "E", "action": "A", "battle": "B", "hen": "H", "day": "D", "brain": "R"}
TAGS = {}  # marker tag -> id, written to work/marker_tags.tsv by a marker build
KEEP = os.environ.get("MARKER_KEEP")  # bisecting a marker-build bug: ids matching this regex keep the Japanese


def b36(n):
    return (b36(n // 36) if n >= 36 else "") + B36[n % 36]


def short_id(s):
    """Marker tag: scenario/battle `xx.yyy`, txd `cf27`; EXE/overlay strings and evd names get a short tag (their
    room is a few bytes): file letter + base-36 index (`E1a`, `A2`), `u` + base-36 index over all evd names."""
    if "tag" in s:
        return s["tag"]
    if re.match(r"g\d+\.", s["id"]):
        return s["id"].split(".", 1)[1]
    name, slot = s["id"].split(".")
    return f"{name}{int(slot)}"


def tag(s, t):
    s["tag"] = t
    TAGS[t] = s["id"]


def marker_txd(s):
    """Markup kept; each run holding Japanese -> filler of its byte length, the first one tagged with the id."""
    parts, tagged = MARKUP.split(s["jp"]), False
    for i, p in enumerate(parts):
        if i % 2 == 0 and JP_CHAR.search(p):
            parts[i] = ascii_fill("" if tagged else f"[{short_id(s)}]", len(script_io.enc_jp({**s, "jp": p})))
            tagged = True
    return "".join(parts)


def marker_lines(s):
    """Each line -> filler of its byte length (first line tagged); for in-place records (EXE strings, evd names)."""
    tbl = script_io.TABLES[s.get("tbl", "jp")]
    fmt = re.findall(r"%[-+ 0#]*\d*(?:\.\d+)?[a-zA-Z]", s["jp"])
    if fmt:  # printf format: keep the conversions, in order
        n = len(script_io.enc(s["jp"], tbl))
        t, f = short_id(s), "".join(fmt)
        return t[:max(0, n - len(f))] + f
    lines = s["jp"].split("\n")
    out = [ascii_fill(short_id(s) if i == 0 else "", len(script_io.enc(l, tbl))) for i, l in enumerate(lines)]
    return "\n".join(out)


def encoder(mode, glyphs):
    def enc(s):
        if mode == "marker" and not (KEEP and re.match(KEEP, s["id"])):
            return script_io.enc(marker_text(s, glyphs))
        if mode == "marker":
            return script_io.enc_jp(s)
        if s.get("en"):
            return script_io.enc(s["en"])
        return script_io.enc_jp(s)
    return enc


def text_groups(mode):
    glyphs = font.load_glyphs()
    enc = encoder(mode, glyphs)
    groups = {}
    for g, d in DIRS.items():
        blocks = []
        for f in sorted((ROOT / "script" / d).glob("*.json")):
            b = script_io.build_slots(json.loads(f.read_text(encoding="utf-8")), enc)
            assert len(b) <= LIMITS[g], f"{f.name}: block {len(b):#x} > buffer {LIMITS[g]:#x}"
            blocks.append(b)
        groups[g] = blocks
    return groups


def record_bytes(s, mode, marker):
    """Encoded text of a record (no NUL), or None to keep the original."""
    if s.get("status") == "data":
        return None
    if mode == "marker" and KEEP and re.match(KEEP, s["id"]):
        return None
    if mode == "marker":
        return script_io.enc(marker(s))
    return script_io.enc(s["en"]) if s.get("en") else None


def entry_index(doc):
    return int(re.match(r"GRETC\.RLZ entry (\d+)", doc["src"]).group(1))


def gretc_files(rlz, mode):
    """{GRETC entry: new plain bytes} for txd (rebuilt slot files) and evd (names in place, same length)."""
    import gretc
    ents = script_io.gretc_entries(rlz)
    new = {}
    for f in sorted((ROOT / "script/txd").glob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))

        def enc(s):
            b = record_bytes(s, mode, marker_txd)
            return script_io.enc_jp(s) if b is None else b
        new[entry_index(doc)] = script_io.build_slots(doc, enc)
    k = 0
    for f in sorted((ROOT / "script/evd").glob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        i = entry_index(doc)
        b = bytearray(gretc.expand(rlz, ents[i]))
        for s in doc["strings"]:
            tag(s, "u" + b36(k))
            k += 1
            t = record_bytes(s, mode, marker_lines)
            if t is None:
                continue
            n = b[s["off"] - 1] - 1  # op 34 idx len text 00
            # shortcut: names stay in place (len byte unchanged); growing them needs evd jump fix-ups (phase 7)
            assert len(t) <= n, f"{s['id']}: {len(t)} > {n} bytes"
            b[s["off"]:s["off"] + n] = t + bytes(n - len(t))
        new[i] = bytes(b)
    return new


def patch_images(tree, exe_path, mode):
    """EXE/overlay strings, in place (each record's `room` holds the text + NUL)."""
    for key, (f, base, _) in script_io.IMAGES.items():
        doc = json.loads((ROOT / f"script/exe/{key}.json").read_text(encoding="utf-8"))
        path = exe_path if key == "exe" else tree / f
        img = bytearray(path.read_bytes())
        for k, s in enumerate(doc["strings"]):
            tag(s, PREFIX[key] + b36(k))
            t = record_bytes(s, mode, marker_lines)
            if t is None:
                continue
            # shortcut: in place only; longer text needs relocation + repointing `refs` (phase 7)
            assert len(t) < s["room"], f"{s['id']}: {len(t)} bytes, room {s['room']}"
            img[s["off"]:s["off"] + s["room"]] = t + bytes(s["room"] - len(t))
        path.write_bytes(img)


def patch_tree(tree, mode="en"):
    """Font + hooks + text into the dumped file tree (EXE name differs per disc)."""
    tree = Path(tree)
    exe_path = next(p for p in tree.glob("SLPS_*"))
    unn_path = tree / "DATA/UNN.PAK"
    exe, unn = exe_path.read_bytes(), bytearray(unn_path.read_bytes())
    tables = font.patch_unn(exe, unn)                      # same size: before the repack moves groups
    exe, unn = script_io.unn_repack(exe, bytes(unn), text_groups(mode))
    exe_path.write_bytes(exe)
    unn_path.write_bytes(unn)
    rlz_path = tree / "DATA/GRETC.RLZ"
    rlz = rlz_path.read_bytes()
    rlz_path.write_bytes(script_io.gretc_repack(rlz, gretc_files(rlz, mode)))
    patch_images(tree, exe_path, mode)
    if mode == "marker":
        (ROOT / "work").mkdir(exist_ok=True)
        (ROOT / "work/marker_tags.tsv").write_text("".join(f"{t}\t{i}\n" for t, i in TAGS.items()), encoding="utf-8")
    work = ROOT / "work/asm"
    work.mkdir(parents=True, exist_ok=True)
    (work / "font_tables.bin").write_bytes(tables)
    subprocess.run([ARMIPS, ROOT / "asm/hooks.asm", "-strequ", "EXE", exe_path, "-strequ", "TABLES",
                    work / "font_tables.bin", "-strequ", "DIC", tree / "DATA/DIC.BIN"], check=True)
