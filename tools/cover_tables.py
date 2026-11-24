"""SLOTS var for tools/lua/draw_sweep.lua: the word-pointer slots (`w` refs) of every script/exe string, grouped into
tables (consecutive slots of one file at most GAP bytes apart; stride-0x10 records in battle.json group too).

    python -X utf8 tools/cover_tables.py [--gap 0x40]     -> prints 'a,a,..;a,..'
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def groups(gap=0x40):
    out = []
    for f in sorted((ROOT / "script/exe").glob("*.json")):
        w = sorted({int(r[1:], 16) for s in json.loads(f.read_text(encoding="utf-8"))["strings"]
                    if s.get("status") != "data" for r in s.get("refs", []) if r[0] == "w"})
        for a in w:
            if out and out[-1][0] == f.stem and a - out[-1][1][-1] <= gap:
                out[-1][1].append(a)
            else:
                out.append((f.stem, [a]))
    return [g for _, g in out if len(g) > 1]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--gap", type=lambda x: int(x, 0), default=0x40)
    print(";".join(",".join(f"{a:x}" for a in g) for g in groups(ap.parse_args().gap)))
