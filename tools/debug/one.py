"""Run one scenes.tsv scene from a cold boot on build/ (like regen.py --only NAME) into work/qa/one/<NAME>/, with extra
emu.py args (probes): python -X utf8 tools/debug/one.py NAME [--frames N] [-- --script tools/lua/pc_log.lua --var FROM=1]"""
import argparse
import os
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools"))
from skill import SKILL  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("name")
ap.add_argument("--frames", type=int)
ap.add_argument("--orig", action="store_true")
ap.add_argument("--timeout", default="400")
ap.add_argument("--out", help="run dir name under work/qa/one (default NAME)")
ap.add_argument("--card", help="card in tools/debug/cards (default the scene's)")
ap.add_argument("rest", nargs=argparse.REMAINDER)
a = ap.parse_args()
row = next(r.split("\t") for r in open(os.path.join(REPO, "tools/debug/scenes.tsv"), encoding="utf-8")
           if r.split("\t")[0] == a.name)
disc, frames, card = int(row[1]), int(row[5] or 1800), a.card or (row[7].strip() if len(row) > 7 else "") or "sys.mcd"
assert "@" not in card, "CARD@N scenes: use regen.py"
root = "rom" if a.orig else f"build/disc{disc}"
cue = next(os.path.join(REPO, root, f) for f in os.listdir(os.path.join(REPO, root))
           if f.endswith(".cue") and (a.orig is False or f"Disc {disc}" in f))
out = os.path.join(REPO, "work/qa/one", a.out or a.name)
os.makedirs(os.path.join(REPO, "work/cards"), exist_ok=True)
sav = os.path.join(REPO, "work/cards", f"one_{a.out or a.name}.mcd")
shutil.copy(os.path.join(REPO, "tools/debug/cards", card), sav)
cmd = [sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts/emu.py"), cue, "--out", out,
       "--script", os.path.join(REPO, "tools/debug/warp.lua"), "--var", f"SCENE='{a.name}'", "--sav", sav,
       "--frames", str(2800 + (a.frames or frames)), "--shot-every", "150", "--timeout", a.timeout]
cmd += [x for x in a.rest if x != "--"]
r = subprocess.run(cmd)
print(out, "exit", r.returncode)
