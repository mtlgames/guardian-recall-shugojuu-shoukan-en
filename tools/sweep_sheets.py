"""sweep_sheets.py IDX PNGDIR OUTDIR: contact sheets of a tx03_sweep run, one set per UNN.PAK group
(OUTDIR/g<NN>_sheet*.png), via the skill's sheet.py. Extra args after OUTDIR go to sheet.py (e.g. --cols 8 --div 2)."""
import os
import subprocess
import sys

import gr_index
from skill import SCRIPTS

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    idx, pngdir, outdir, extra = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4:]
    exe = open(os.path.join(ROOT, "work/disc1/tree/SLPS_012.97"), "rb").read()
    toc = gr_index.toc(exe)
    groups = {}
    for line in open(idx):
        if line.startswith("#") or "FAIL" in line:
            continue
        o = int(line.split("\t")[0], 16)
        g = next(i for i, (s, n, _) in enumerate(toc) if s * 0x800 <= o < (s + n) * 0x800)
        groups.setdefault(g, []).append(os.path.join(pngdir, f"{o:08x}.png"))
    os.makedirs(outdir, exist_ok=True)
    for g, files in sorted(groups.items()):
        subprocess.run([sys.executable, "-X", "utf8", os.path.join(SCRIPTS, "sheet.py"), *files,
                        "--out", os.path.join(outdir, f"g{g:02d}_sheet.png"), *extra], check=True,
                       stdout=subprocess.DEVNULL)
        print(g, len(files))
