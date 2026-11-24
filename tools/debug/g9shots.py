"""Shoot every G9 battle label (29 records) from work/states/battle.sstate (made by `regen.py --only battle` on the
current build: cold boot, so it carries the new BATTLE code and split.tim): 15 runs of 2 labels (the two watcher
scans at state frames ~220 and ~457), 5 in parallel, then one zoomed sheet work/qa/g9/labels.png.
    python -X utf8 tools/debug/g9shots.py"""
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "tools"))
from skill import SKILL  # noqa: E402

CUE = os.path.join(REPO, "build/disc1/Guardian Recall - Shugojuu Shoukan (English) (Disc 1).cue")
OUT = os.path.join(REPO, "work/qa/g9")


def run(start):
    out = os.path.join(OUT, f"r{start:02d}")
    cmd = [sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts/emu.py"), CUE, "--out", out, "--state-in",
           os.path.join(REPO, "work/states/battle.sstate"), "--debugger", "--frames", "620", "--shots", "330,600",
           "--script", os.path.join(REPO, "tools/lua/g9labels.lua"), "--var", "FROM=0", "--var", "EVERY=100",
           "--var", f"START={start}", "--timeout", "900"]
    return start, subprocess.run(cmd, capture_output=True, text=True).returncode


with ThreadPoolExecutor(5) as ex:
    res = list(ex.map(run, range(0, 29, 2)))
print("runs:", res)
shots = []
for s, _ in res:
    for f in ("f000330.png", "f000600.png"):
        p = os.path.join(OUT, f"r{s:02d}", f)
        if os.path.exists(p):
            shots.append(p)
subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts/sheet.py"), *shots[:29], "--crop",
                "0,80,320,72", "--out", os.path.join(OUT, "labels.png")])
