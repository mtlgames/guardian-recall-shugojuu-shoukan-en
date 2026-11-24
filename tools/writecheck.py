"""writecheck.py: the build's write check (phase 7). build.py calls verify() on every disc after insert.patch_tree.

Rules (errors fail the build):
  - only the files insert.py patches may differ from the pristine dump (FILES);
  - EXE and overlay images: every changed byte comes from a logged write (insert.LOG: in-place strings, repointed
    refs, UNN index rewrite, armips runs), each write's original bytes match the dump, no two writes overlap and no
    later write clobbers an earlier one (tools/romdiff.py --writes semantics);
  - armips runs (asm_writes) lie inside spans its -temp listing says it emitted, and a run longer than a hook
    patch (HOOK_MAX) only covers bytes that were zero in the dump (payload, boot stub: never live code or data);
  - UNN.PAK: every group but the text groups (13, 23) keeps its bytes; g9 differs only inside the font TIM pixels;
    logged in-place gfx writes (g17 title cards, tools/gfx.py) pass the same romdiff write checks;
  - GRETC.RLZ: entries insert.py did not rebuild keep their stored bytes; directory fields other than the
    offset/size/sector ones are unchanged.
What it misses: whether a write's *content* is right (text tests, emulator QA) and the text groups' own bytes
(tests/test_script.py roundtrips them)."""
import filecmp
import re
import struct
from pathlib import Path

import font
import gr_index
import gretc
import romdiff
import script_io

FILES = {"DATA/UNN.PAK", "DATA/GRETC.RLZ", "DATA/ACTION.BIN", "DATA/BATTLE.BIN", "DATA/HEN.BIN", "DATA/DAY.BIN",
         "DATA/BRAIN.BIN", "DATA/DIC.BIN", "DATA/SUBTI.PAK", "STR/STAFF.STR"}  # + the SLPS_* EXE
HOOK_MAX = 0x40  # longest hook-site patch is 6 instructions; anything longer must sit in the dump's zero area
BREAK = re.compile(r'\.(open|org|orga|close|headersize)\b\s*"?([^",;\s]*)"?,?(0x[0-9A-Fa-f]+)?')


def asm_blocks(listing):
    """{file name (upper case): [(lo, hi) file offsets]} armips emitted, from its -temp listing."""
    out, name, header, start = {}, None, 0, None
    for line in listing.splitlines():
        m = re.match(r"([0-9A-F]{8}) (.*)", line)
        if not m or m[1] == "FFFFFFFF" and not m[2].startswith(".open"):
            continue
        addr, brk = int(m[1], 16), BREAK.match(m[2])
        if not brk:
            if start is None:
                start = addr
            continue
        if name and start is not None and addr > start:
            out.setdefault(name, []).append((start - header, addr - header))
        start = None
        if brk[1] == "open":
            name, header = Path(brk[2]).name.upper(), int(brk[3], 16)
        elif brk[1] == "headersize":
            header = int(brk[2], 16)
    return out


def runs(a, b):
    """[(lo, hi)] spans where a and b differ (same length)."""
    out, i, n = [], 0, len(a)
    while i < n:
        if a[i:i + 2048] == b[i:i + 2048]:
            i += 2048
            continue
        end = min(i + 2048, n)
        while i < end:
            if a[i] != b[i]:
                j = i
                while j < n and a[j] != b[j]:
                    j += 1
                out.append((i, j))
                i = j
            else:
                i += 1
    return out


def asm_writes(name, pre, post, blocks):
    """(writes, errors) for the bytes armips changed in one file (pre = before armips, post = after). A write logged
    earlier under an asm run makes pre differ from the dump there: romdiff then reports the overlap."""
    assert len(pre) == len(post), f"{name}: armips changed the file size"
    merged = []  # adjacent hook sites (.org X, .org X+4) make one run
    for lo, hi in sorted(blocks):
        if merged and lo <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(hi, merged[-1][1]))
        else:
            merged.append((lo, hi))
    blocks = merged
    writes, errs = [], []
    for lo, hi in runs(pre, post):
        if not any(a <= lo and hi <= b for a, b in blocks):
            errs.append(f"{name} 0x{lo:06X}-0x{hi:06X}: changed by armips outside its listed output")
        elif hi - lo > HOOK_MAX and any(pre[lo:hi]):
            errs.append(f"{name} 0x{lo:06X}-0x{hi:06X}: asm block over non-zero original bytes")
        writes.append((lo, bytes(pre[lo:hi]), bytes(post[lo:hi]), "asm"))
    return writes, errs


def unn_errors(exe0, exe1, unn0, unn1, writes=()):
    """writes: logged in-place UNN writes [(pre-repack off, orig, new, who)] (gfx cards), allowed in their group."""
    errs = []
    toc0, toc1 = gr_index.toc(exe0), gr_index.toc(exe1)
    first = min(s for s, _, _ in toc0) * script_io.SECTOR
    if unn1[:first] != unn0[:first]:
        errs.append("UNN.PAK: header before the first group changed")
    off, a = font.g9_entry0(exe0, unn0)
    img = off + font.tim_image(a, 7)
    h = struct.unpack_from("<H", a, font.tim_image(a, 7) - 2)[0]
    for g, ((s0, n0, b0), (s1, n1, b1)) in enumerate(zip(toc0, toc1)):
        if g in script_io.TEXT_GROUPS:
            continue
        old = unn0[s0 * script_io.SECTOR:(s0 + n0) * script_io.SECTOR]
        new = unn1[s1 * script_io.SECTOR:(s1 + n1) * script_io.SECTOR]
        if (n0, b0) != (n1, b1) or len(old) != len(new):
            errs.append(f"UNN.PAK group {g}: size changed")
            continue
        lo = img - s0 * script_io.SECTOR
        allowed = [range(lo, lo + 128 * h)] if g == 9 else []
        base = s0 * script_io.SECTOR
        mine = [(o - base, a, b, w) for o, a, b, w in writes if base <= o < base + len(old)]
        errs += [f"UNN.PAK group {g}: {e}" for e in romdiff.check(old, new, allowed, mine)[0]]
    end0 = max(s + n for s, n, _ in toc0) * script_io.SECTOR
    end1 = max(s + n for s, n, _ in toc1) * script_io.SECTOR
    if unn1[end1:] != unn0[end0:]:
        errs.append("UNN.PAK: tail after the last group changed")
    return errs


def gretc_errors(rlz0, rlz1, rebuilt):
    errs = []
    h0, e0 = gretc.directory(rlz0)
    h1, e1 = gretc.directory(rlz1)
    if h0[:0x80] != h1[:0x80] or h0[0x88:] != h1[0x88:] or len(e0) != len(e1):
        errs.append("GRETC.RLZ: header changed")
    hdr = gretc.HDR + len(e0) * gretc.ENT
    if rlz1[hdr:e0[0]["sector"] * script_io.SECTOR] != rlz0[hdr:e0[0]["sector"] * script_io.SECTOR]:
        errs.append("GRETC.RLZ: bytes between directory and first entry changed")
    moved = {"off", "size", "psize", "sector", "nsec"}
    for i, (a, b) in enumerate(zip(e0, e1)):
        if any(a[k] != b[k] for k in a if k not in moved):
            errs.append(f"GRETC.RLZ entry {i} ({a['name']}): directory fields changed")
        if i not in rebuilt and gretc.payload(rlz0, a) != gretc.payload(rlz1, b):
            errs.append(f"GRETC.RLZ entry {i} ({a['name']}): stored bytes changed, not a rebuilt entry")
    return errs


def verify(orig_tree, tree, log, gretc_rebuilt):
    """Error lines for disc tree vs its pristine dump; log = {rel path: [(off, orig, new, writer)]}."""
    orig_tree, tree = Path(orig_tree), Path(tree)
    exe = next(p for p in orig_tree.glob("SLPS_*")).name
    errs, changed = [], []
    for p in sorted(orig_tree.rglob("*")):
        if p.is_file():
            rel = p.relative_to(orig_tree).as_posix()
            if not filecmp.cmp(p, tree / rel, shallow=False):
                changed.append(rel)
    if sorted(q.relative_to(tree).as_posix() for q in tree.rglob("*") if q.is_file()) != \
            sorted(p.relative_to(orig_tree).as_posix() for p in orig_tree.rglob("*") if p.is_file()):
        errs.append("file list differs from the dump")
    for rel in changed:
        if rel not in FILES and rel != exe:
            errs.append(f"{rel}: changed, but insert.py never patches it")
            continue
        if rel in ("DATA/UNN.PAK", "DATA/GRETC.RLZ"):
            continue
        a, b = (orig_tree / rel).read_bytes(), (tree / rel).read_bytes()
        if len(a) != len(b):
            errs.append(f"{rel}: size changed")
        errs += [f"{rel} {e}" for e in romdiff.check(a, b, [], log.get(rel, []))[0]]
    rd = lambda t, r: (t / r).read_bytes()  # noqa: E731
    errs += unn_errors(rd(orig_tree, exe), rd(tree, exe), rd(orig_tree, "DATA/UNN.PAK"), rd(tree, "DATA/UNN.PAK"),
                        log.get("DATA/UNN.PAK", []))
    errs += gretc_errors(rd(orig_tree, "DATA/GRETC.RLZ"), rd(tree, "DATA/GRETC.RLZ"), gretc_rebuilt)
    return errs
