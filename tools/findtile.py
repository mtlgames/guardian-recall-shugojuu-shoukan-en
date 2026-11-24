"""Find the tour frame behind one tile of a vqa sheet, and the original-disc frame showing the same screen.

    python -X utf8 tools/findtile.py work/qa/vqa/d1/battle_sheet_17.png 0 [--jp]

Tile index counts row-major from 0 (tiles are 320x240 on a 322x242 pitch). Prints the best tour frame; with --jp also
the closest work/qa/tour_jp/<scene>/ frame (by image, then by number) for `sheet.py EN --compare JP`.
"""
import argparse
import glob
import os
import re

from PIL import Image, ImageChops, ImageStat

ap = argparse.ArgumentParser()
ap.add_argument("sheet")
ap.add_argument("tile", type=int)
ap.add_argument("--jp", action="store_true")
a = ap.parse_args()
scene = re.sub(r"_sheet(_\d+)?\.png$", "", os.path.basename(a.sheet))
sh = Image.open(a.sheet).convert("RGB")
cols = sh.size[0] // 320
x, y = (a.tile % cols) * 322, (a.tile // cols) * 242
tile = sh.crop((x, y, x + 320, y + 240))


def rank(d):
    out = []
    for f in sorted(glob.glob(f"work/qa/{d}/{scene}/f*.png")):
        im = Image.open(f).convert("RGB")
        if im.size == (320, 240):
            out.append((sum(ImageStat.Stat(ImageChops.difference(im, tile)).mean), f))
    return sorted(out)


en = rank("tour")
print("tour:", en[0][1], f"diff {en[0][0]:.1f}")
if a.jp:
    jp = rank("tour_jp")
    print("tour_jp best image:", jp[0][1], f"diff {jp[0][0]:.1f}")
    same = en[0][1].replace("/tour/", "/tour_jp/").replace("\\tour\\", "\\tour_jp\\")
    if os.path.exists(same):
        print("tour_jp same frame:", same)
