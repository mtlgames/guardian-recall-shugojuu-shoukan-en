"""Scenes whose sheets lack a current verdict (the newest qa_gate todo chunks): new scene (no work/qa/tour_prev run) or
changed, with a tools/framediff.py summary against tour_prev -> work/qa/vqa/todo_29.txt.
    python -X utf8 tools/vqa_todo.py"""
import csv, glob, os, re, subprocess, sys
out = []
for d in ('d1', 'd2'):
    todo = set()
    for c in glob.glob(f'work/qa/vqa/{d}/chunks/chunk_*.txt'):
        if os.path.getmtime(c) < os.path.getmtime(f'work/qa/vqa/{d}/manifest.tsv') - 5:
            continue
        for line in open(c, encoding='utf-8'):
            if '\t' in line:
                todo.add(line.split('\t')[0])
    scenes = sorted({re.sub(r'_sheet(_\d+)?$', '', t) for t in todo})
    for s in scenes:
        prev = f'work/qa/tour_prev/{s}'
        if not os.path.isdir(prev):
            out.append(f'{d} {s}: new scene (no previous tour run)')
            continue
        r = subprocess.run([sys.executable, '-X', 'utf8', 'tools/framediff.py', f'work/qa/tour/{s}', prev],
                           capture_output=True, text=True)
        lines = [l for l in r.stdout.splitlines() if l.strip()]
        out.append(f'{d} {s}: {len(lines)} framediff lines; ' + ' | '.join(lines[:3])[:300])
open('work/qa/vqa/todo_29.txt', 'w', encoding='utf-8').write('\n'.join(out) + '\n')
print(len(out), 'scenes;', sum('new scene' in o for o in out), 'new')
