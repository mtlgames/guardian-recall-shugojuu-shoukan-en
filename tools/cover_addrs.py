"""VALS var for tools/lua/draw_sweep.lua: RAM addresses of the built EXE/overlay strings (code-referenced messages have
no pointer table, so draw_sweep's SLOTS can't reach them). Each string is found in the built binary of its file
(work/build/d1/tree, RAM base from the json `src`) or the relocation pool (work/asm/str_pool.bin at STR_POOL).

    python -X utf8 tools/cover_addrs.py STEM.. [--unshown LOGDIR]   -> one ','-list per stem, ';'-joined
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import cover_stats, insert, strings_tsv  # noqa: E402


def addrs(stem, unshown=None):
    f = ROOT / "script/exe" / f"{stem}.json"
    doc = json.loads(f.read_text(encoding="utf-8"))
    m = re.match(r"(\S+) \(RAM base (0x[0-9a-fA-F]+)\)", doc["src"])
    name, base = (m.group(1), int(m.group(2), 16)) if m else ("SLPS_012.97", 0x8000F800)
    img = (ROOT / "work/build/d1/tree" / name).read_bytes()
    if name == "SLPS_012.97":  # EXE: text ranges only; the payload copy past them is moved to STR_POOL at boot (docs/re/text.md)
        img = img[:0xA6C00]
    pool = (ROOT / "work/asm/str_pool.bin").read_bytes()
    out = []
    for s in doc["strings"]:
        if s.get("status") == "data":
            continue
        b = strings_tsv.encoded(f, s)
        if not b or (unshown is not None and f"{strings_tsv.fnv32(b):08x}" in unshown):
            continue
        for buf, at in ((img, base), (pool, insert.STR_POOL)):
            o = (b"\0" + buf).find(b"\0" + b + b"\0")  # leading NUL: a string at offset 0 counts too
            if o >= 0:
                out.append(at + o)
                break
        else:  # tail-shared: the ref points into a longer string ending the same way
            for buf, at in ((img, base), (pool, insert.STR_POOL)):
                o = buf.find(b + b"\0")
                if o >= 0:
                    out.append(at + o)
                    break
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stems", nargs="+")
    ap.add_argument("--unshown", help="LOGDIR: only strings its coverage logs haven't shown")
    a = ap.parse_args()
    seen = cover_stats.shown(a.unshown) if a.unshown else None
    print(";".join(",".join(f"{x:x}" for x in addrs(st, seen)) for st in a.stems))


if __name__ == "__main__":
    main()
