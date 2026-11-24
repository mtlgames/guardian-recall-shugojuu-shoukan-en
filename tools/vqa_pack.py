"""Pack the non-padding tiles of several vqa sheets into one image (4 per row), so a reviewer reads fewer pixels.

    python -X utf8 tools/vqa_pack.py OUT.png SHEET.png.. [--cols 4]

Prints which output tiles came from which sheet. Tiles are 320x240 on a 322x242 pitch (div 1 sheets); a tile that is
all contact-sheet purple is padding and is dropped. Sheets with 640x480 tiles (title-menu scenes) are copied whole.
"""
import argparse
import os

from PIL import Image

PURPLE = (64, 0, 64)

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("sheets", nargs="+")
ap.add_argument("--cols", type=int, default=4)
a = ap.parse_args()
tiles, legend = [], []
for s in a.sheets:
    im = Image.open(s).convert("RGB")
    cols, rows = im.size[0] // 320, (im.size[1] + 2) // 242
    first = len(tiles)
    for r in range(rows):
        for c in range(cols):
            t = im.crop((c * 322, r * 242, c * 322 + 320, r * 242 + 240))
            colours = t.getcolors(4)
            if colours and all(abs(v - p) < 12 for _, col in colours for v, p in zip(col, PURPLE)):
                continue
            tiles.append(t)
    legend.append(f"{os.path.basename(s)}: tiles {first}-{len(tiles) - 1}")
rows = (len(tiles) + a.cols - 1) // a.cols
out = Image.new("RGB", (a.cols * 322, rows * 242), PURPLE)
for i, t in enumerate(tiles):
    out.paste(t, ((i % a.cols) * 322, (i // a.cols) * 242))
out.save(a.out)
print("\n".join(legend))
