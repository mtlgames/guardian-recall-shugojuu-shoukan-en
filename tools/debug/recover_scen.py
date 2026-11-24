"""Re-cover changed scenario text after a rebuild: one short sweep per g23 block, only the changed slots.

    python -X utf8 tools/debug/recover_scen.py IDS_FILE OUTDIR [--jobs 3]

IDS_FILE: string ids, one per line (e.g. textcover's NEVER SHOWN ids); g23 ids are kept, the rest ignored. Each
block is forced into ev11 (tools/lua/setreg.lua on the loader 0x80044B24, as the work/qa/cover/blk runs) and
tools/lua/scen_sweep.lua sweeps just the ids' slots (--var SLOTS). Logs land in OUTDIR/bNN/ev11/log.txt, under
work/qa/cover so textcover counts them. About a minute per block.
"""
import argparse, concurrent.futures as cf, json, os, subprocess, sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def slots_by_block(ids):
    want, out = set(ids), defaultdict(list)
    for name in sorted(os.listdir(os.path.join(REPO, 'script/scenario'))):
        with open(os.path.join(REPO, 'script/scenario', name), encoding='utf-8') as f:
            for s in json.load(f)['strings']:
                if s['id'] in want:
                    out[int(s['id'].split('.')[1])] += s['slots']
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ids')
    ap.add_argument('outdir')
    ap.add_argument('--jobs', type=int, default=3)
    a = ap.parse_args()
    ids = [i for i in open(a.ids, encoding='utf-8').read().split() if i.startswith('g23.')]
    blocks = slots_by_block(ids)

    def one(b):
        cmd = [sys.executable, '-X', 'utf8', os.path.join(REPO, 'tools/debug/regen.py'), '--only', 'ev11', '--cover',
               '--sweep', '--lua', 'tools/lua/setreg.lua', '--var', f"HOOKS='0x80044B24:a0={b}'", '--var', 'FROM=2900',
               '--var', 'ADVANCE=20', '--var', "SLOTS='" + ','.join(map(str, sorted(set(blocks[b])))) + "'",
               '--frames', '16800', '--timeout', '1500', '--outdir', os.path.join(a.outdir, f'b{b:02d}')]
        r = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
        return b, r.returncode

    bad = 0
    with cf.ThreadPoolExecutor(a.jobs) as ex:
        for b, rc in ex.map(one, sorted(blocks)):
            print(f"{'ok  ' if rc == 0 else 'FAIL'} b{b:02d} slots {sorted(set(blocks[b]))}", flush=True)
            bad += rc != 0
    print(f"{len(blocks) - bad}/{len(blocks)} blocks ok")
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
