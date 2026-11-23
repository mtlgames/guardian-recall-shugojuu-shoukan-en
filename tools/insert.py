"""Insert script/ text into a disc file tree (called by build.patch).

Modes: "en" = each record's `en` (records without one keep their original bytes); "marker" = every record replaced by
its id + filler of the same line/page shape (phase 5 marker build, docs/re/text.md "Marker build").

Limits (asm/hooks.asm): scenario blocks (UNN g23) load into SCEN_BUF (0x8000 bytes), battle-quote blocks (g13) into
malloc(G13_MAX = 0x4000)."""
import json
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


def encoder(mode, glyphs):
    def enc(s):
        if mode == "marker":
            return script_io.enc(marker_text(s, glyphs))
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
    work = ROOT / "work/asm"
    work.mkdir(parents=True, exist_ok=True)
    (work / "font_tables.bin").write_bytes(tables)
    subprocess.run([ARMIPS, ROOT / "asm/hooks.asm", "-strequ", "EXE", exe_path, "-strequ", "TABLES",
                    work / "font_tables.bin"], check=True)
