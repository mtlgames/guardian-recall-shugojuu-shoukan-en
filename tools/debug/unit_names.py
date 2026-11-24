"""Stress check: ally unit names in ring > UNIT on every map whose evd names its units (script/evd/mapNN.json).
Warps event NN, opens ring > UNIT (Master tab), then R1 (Guardian tab), logging draws (tools/lua/draw_log.lua) into
work/qa/units/evNN; then lists each name drawn in the name column (x 25) with its width (font.width) against the room
before the next column (Master tab: Ali at x 121; Guardian tab: Type at x 107; docs/windows.md "evd unit names").
Exit 1 if any name doesn't fit.   python -X utf8 tools/debug/unit_names.py [NN..] [--jobs 4] [--no-run]
Shortcut: only the first page of each tab (7 rows) and only the units on the map at Turn 01."""
import argparse
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools"))
import font  # noqa: E402
from skill import SKILL  # noqa: E402

ROOM = {"Master": 121 - 25 - 2, "Guardian": 107 - 25 - 2}  # 2 px gap before the next column
# --mash N: N circle/cross cycles first (opening dialogue; on the map circle opens the unit menu, cross shuts it)
MASH = "8 circle;40 -;8 cross;40 -;8 cross;40 -"
ROUTE = "1750 -;6 triangle;60 -;6 circle;120 -;6 r1;120 -"
FRAMES = 5200


def disc_of(ev):
    for line in open(REPO / "tools/debug/scenes.tsv", encoding="utf-8"):
        c = line.split("\t")
        if c[0] == f"ev{ev:02d}":
            return int(c[1])
    return 2


def run(ev):
    out = REPO / f"work/qa/units/ev{ev:02d}"
    cue = next((REPO / f"build/disc{disc_of(ev)}").glob("*.cue"))
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts/emu.py"), str(cue), "--out", str(out),
           "--sav", str(REPO / "tools/debug/cards/sys.mcd"), "--debugger",
           "--script", str(REPO / "tools/debug/warp.lua"), "--var", f"EVENT='{ev}'", "--var", f"WROUTE='{ROUTE}'",
           "--script", str(REPO / "tools/lua/draw_log.lua"), "--var", "FROM=2000",
           "--frames", str(FRAMES), "--shot-every", "600", "--timeout", "1800"]
    return ev, subprocess.run(cmd, capture_output=True, text=True).returncode


def names(ev):
    """(tab, name) drawn in the name column (x 25); the tab = the row's next column: Ali x 121 (Master) or Type x 107
    (Guardian)."""
    log = REPO / f"work/qa/units/ev{ev:02d}/log.txt"
    pend, got = None, []
    for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"DRAW (\d+) (\d+) (.*)", line)
        if not m:
            continue
        x, y, text = int(m.group(1)), int(m.group(2)), m.group(3)
        if x == 25:
            pend = (y, text)
        elif pend and y == pend[0] and x in (121, 107):
            got.append(("Master" if x == 121 else "Guardian", pend[1]))
            pend = None
    return got


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("events", nargs="*", type=int)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--no-run", action="store_true")
    ap.add_argument("--mash", type=int, default=0)
    a = ap.parse_args()
    if a.mash:
        ROUTE = ";".join([MASH] * a.mash) + ";" + ROUTE
        FRAMES += 128 * a.mash
    evs = a.events or sorted(int(p.stem[3:]) for p in (REPO / "script/evd").glob("map*.json"))
    if not a.no_run:
        with ThreadPoolExecutor(a.jobs) as pool:
            for ev, rc in pool.map(run, evs):
                print(f"ev{ev:02d} exit {rc}", flush=True)
    bad, seen = 0, {}
    for ev in evs:
        for tab, n in names(ev):
            seen.setdefault((tab, n), []).append(ev)
    for (tab, n), e in sorted(seen.items(), key=lambda kv: -font.width(kv[0][1])):
        w = font.width(n)
        flag = "OVER" if w > ROOM[tab] else ""
        bad += bool(flag)
        print(f"{tab:8} {w:3}/{ROOM[tab]} {n:24} ev{','.join(map(str, e))} {flag}")
    sys.exit(1 if bad else 0)
