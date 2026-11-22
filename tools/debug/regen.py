"""Warp to every scene in tools/debug/scenes.tsv from a cold boot; save a proof shot sheet and a savestate per scene.

    python -X utf8 tools/debug/regen.py [--orig] [--only NAME ..] [--events 21-70 --disc 2] [--jobs 4] [--var V=..]

Each scene boots its disc (build/disc<N>/*.cue, or rom/ with --orig or when there is no build). Per scene:
work/qa/warp/<name>/ (shots every 150 frames, sheet.png, log.txt) and work/states/<name>.sstate. A scene passes
when warp.lua logged "<event|call> N started". --events A-B warps raw event numbers (names ev<N>) to map new ones.
An optional 8th scenes.tsv column names the scene's memory card in tools/debug/cards/ (default sys.mcd).
Exit 1 if any scene failed.
"""
import argparse, concurrent.futures as cf, glob, os, re, subprocess, sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, 'tools'))
from skill import SKILL  # noqa: E402

WARP_BOOT = 2800  # frames a cold boot takes to reach the route choice, where the warp happens


def scenes():
    rows = []
    with open(os.path.join(REPO, 'tools/debug/scenes.tsv'), encoding='utf-8') as f:
        for line in f:
            if line.startswith('#') or not line.strip():
                continue
            c = line.rstrip('\n').split('\t')
            assert len(c) in (7, 8), f'scenes.tsv row needs 7 columns (+ optional card): {line!r}'
            card = os.path.join(REPO, 'tools/debug/cards', c[7]) if len(c) == 8 and c[7] else None
            rows.append({'name': c[0], 'disc': int(c[1]), 'target': c[2], 'frames': int(c[5] or 1800), 'card': card})
    return rows


def cue_for(disc, orig):
    built = [] if orig else glob.glob(os.path.join(REPO, f'build/disc{disc}/*.cue'))
    return (built + glob.glob(os.path.join(REPO, f'rom/*(Disc {disc}).cue')))[0]


def run(sc, args):
    out = os.path.join(REPO, 'work/qa/warp', sc['name'])
    cmd = [sys.executable, '-X', 'utf8', os.path.join(SKILL, 'scripts/emu.py'), cue_for(sc['disc'], args.orig),
           '--out', out, '--script', os.path.join(REPO, 'tools/debug/warp.lua'),
           '--frames', str(WARP_BOOT + (args.frames or sc['frames'])), '--shot-every', '150', '--sheet',
           '--timeout', str(args.timeout), '--state-out', os.path.join(REPO, 'work/states', sc['name'] + '.sstate'),
           '--sav', sc.get('card') or args.card]  # own copy per run: the shared portable card would race between parallel runs
    cmd += ['--var', f"EVENT={sc['target']}"] if sc.get('raw') else ['--var', f"SCENE='{sc['name']}'"]
    for v in args.var or []:
        cmd += ['--var', v]
    p = subprocess.run(cmd, capture_output=True, text=True)
    logp = os.path.join(out, 'log.txt')
    log = open(logp, encoding='utf-8', errors='replace').read() if os.path.exists(logp) else ''
    ok = (p.returncode == 0 and 'final frame' in log
          and re.search(r'(event|call) \d+ started|idle scene ready|boot scene|overlay scene', log))
    return sc['name'], bool(ok), p.returncode


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--orig', action='store_true', help='boot rom/ even when build/ exists')
    ap.add_argument('--only', nargs='*')
    ap.add_argument('--events')
    ap.add_argument('--disc', type=int, default=1, help='disc for --events')
    ap.add_argument('--jobs', type=int, default=4)
    ap.add_argument('--frames', type=int, help='frames after the warp (default: scenes.tsv column)')
    ap.add_argument('--timeout', type=int, default=300)
    ap.add_argument('--var', action='append', help='extra --var for warp.lua, e.g. ADVANCE=90')
    ap.add_argument('--card', default=os.path.join(REPO, 'tools/debug/cards/sys.mcd'),
                    help='memory card (default: system file only, so the boot skips the create prompt)')
    args = ap.parse_args()
    if args.events:
        a, b = map(int, args.events.split('-'))
        todo = [{'name': f'ev{n:02d}', 'disc': args.disc, 'target': str(n), 'frames': 1800, 'raw': True}
                for n in range(a, b + 1)]
    else:
        todo = [s for s in scenes() if not args.only or s['name'] in args.only]
        missing = set(args.only or []) - {s['name'] for s in todo}
        assert not missing, f'not in scenes.tsv: {missing}'
    print('scenes:', len(todo), '| disc 1:', cue_for(1, args.orig))
    bad = []
    with cf.ThreadPoolExecutor(args.jobs) as ex:
        for name, ok, rc in ex.map(lambda s: run(s, args), todo):
            print(('ok  ' if ok else 'FAIL'), name, rc, flush=True)
            if not ok:
                bad.append(name)
    print(f'{len(todo) - len(bad)}/{len(todo)} ok', *(['failed:'] + bad if bad else []))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
