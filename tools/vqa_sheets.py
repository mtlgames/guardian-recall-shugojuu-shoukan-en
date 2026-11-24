"""Compact visual-QA sheets from a regen tour: one sheet set per scene, duplicate frames dropped, split by disc so each
disc's manifest records its own build.

    python -X utf8 tools/vqa_sheets.py [--tour work/qa/tour] [--out work/qa/vqa] [--changed 0.03] [--only NAME ..]
    then per disc: qa_gate.py init work/qa/vqa/d<N>/manifest.tsv work/qa/vqa/d<N> --build "build/disc<N>/<bin>"

Writes work/qa/vqa/d<N>/<scene>_sheet.png (+ _sheet_2.png ... when a scene has more than --max changed frames).
"""
import argparse
import glob
import os
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO, "tools"))
from skill import SKILL  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--tour", default="work/qa/tour")
ap.add_argument("--out", default="work/qa/vqa")
ap.add_argument("--changed", default="0.03")
ap.add_argument("--max", default="12")
ap.add_argument("--div", default="1", help="1 = full 320x240 tiles: dialogue glyphs are unreadable at 2")
ap.add_argument("--only", nargs="*")
a = ap.parse_args()
rows = [ln.split("\t") for ln in open(os.path.join(REPO, "tools/debug/scenes.tsv"), encoding="utf-8")
        if ln.strip() and not ln.startswith("#")]
n = 0
for r in rows:
    name, disc = r[0], r[1]
    src = os.path.join(REPO, a.tour, name)
    if (a.only and name not in a.only) or not glob.glob(os.path.join(src, "f*.png")):
        continue
    out = os.path.join(REPO, a.out, f"d{disc}", f"{name}_sheet.png")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    for old in glob.glob(out[:-4] + "*.png"):
        os.remove(old)
    subprocess.run([sys.executable, "-X", "utf8", os.path.join(SKILL, "scripts/sheet.py"), src, "--changed", a.changed,
                    "--max", a.max, "--div", a.div, "--out", out], check=True, capture_output=True)
    n += 1
print(n, "scenes ->", a.out)
