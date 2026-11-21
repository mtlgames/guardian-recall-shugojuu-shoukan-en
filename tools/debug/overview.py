"""One contact sheet over many warp runs: per run, the N non-blank shots after the warp, labelled <run>_<frame>.

    python -X utf8 tools/debug/overview.py work/qa/warp/ev2* --per 3 --out work/qa/ov_ev2x.png [--from 2900]
"""
import argparse, glob, os, shutil, subprocess, sys, tempfile
from PIL import Image, ImageStat

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from skill import SKILL  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('runs', nargs='+')
    ap.add_argument('--per', type=int, default=3)
    ap.add_argument('--from', dest='start', type=int, default=2900)
    ap.add_argument('--out', required=True)
    ap.add_argument('--div', default='3')
    a = ap.parse_args()
    tmp = tempfile.mkdtemp()
    for run in sorted(a.runs):
        shots = [p for p in sorted(glob.glob(os.path.join(run, 'f[0-9]*.png')))
                 if int(os.path.basename(p)[1:7]) >= a.start]
        lit = [p for p in shots if ImageStat.Stat(Image.open(p).convert('L')).mean[0] > 12]
        pick = [lit[round(i * (len(lit) - 1) / max(1, a.per - 1))] for i in range(a.per)] if lit else []
        for p in dict.fromkeys(pick):
            shutil.copy(p, os.path.join(tmp, f'{os.path.basename(run)}_{os.path.basename(p)[1:7]}.png'))
    files = sorted(glob.glob(os.path.join(tmp, '*.png')))
    subprocess.run([sys.executable, '-X', 'utf8', os.path.join(SKILL, 'scripts/sheet.py'), *files,
                    '--div', a.div, '--cols', str(a.per * 2), '--out', a.out], check=True)


if __name__ == '__main__':
    main()
