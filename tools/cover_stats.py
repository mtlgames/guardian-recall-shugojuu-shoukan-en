"""Text coverage by script file: shown/total per file group, from TEXT lines (tools/lua/textcover.lua) under LOGDIR.

    python -X utf8 tools/cover_stats.py LOGDIR [build/strings.tsv] [--waive docs/text_unshown.tsv] [--files] [--missing PREFIX]

--files: one line per script file; --missing PREFIX: print the unshown ids starting with PREFIX (with their text).
The release gate itself is the skill's textcover.py; this is the per-area view for closing gaps.
"""
import argparse, collections, glob, json, os, re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def shown(logdir):
    out = set()
    for log in glob.glob(os.path.join(logdir, "**", "log.txt"), recursive=True):
        out.update(re.findall(r"^TEXT ([0-9a-f]+)", open(log, encoding="utf-8", errors="replace").read(), re.M))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logdir")
    ap.add_argument("strings", nargs="?", default=str(ROOT / "build/strings.tsv"))
    ap.add_argument("--waive", default=str(ROOT / "docs/text_unshown.tsv"))
    ap.add_argument("--files", action="store_true")
    ap.add_argument("--missing")
    a = ap.parse_args()
    tab = [l.rstrip("\n").split("\t") for l in open(a.strings, encoding="utf-8") if not l.startswith("#")]
    waived = set()
    if os.path.exists(a.waive):
        waived = {r[0] for r in (l.rstrip("\n").split("\t") for l in open(a.waive, encoding="utf-8"))
                  if len(r) > 1 and r[1].strip() and not r[0].startswith("#")}
    seen = shown(a.logdir)
    stat = collections.defaultdict(lambda: [0, 0, 0])
    miss = []
    for i, h in tab:
        k = i.split(".")[0] if a.files else re.sub(r"\d+$", "", i.split(".")[0])
        st = stat[k]
        st[0] += 1
        if h in seen:
            st[1] += 1
        elif i in waived:
            st[2] += 1
        elif a.missing and i.startswith(a.missing):
            miss.append(i)
    for k, (n, s, w) in sorted(stat.items()):
        print(f"{k:12} {s:5}/{n:<5} waived {w:<4} left {n - s - w}")
    t = [sum(x) for x in zip(*stat.values())]
    print(f"{'total':12} {t[1]:5}/{t[0]:<5} waived {t[2]:<4} left {t[0] - t[1] - t[2]}")
    if miss:
        text = {}
        for f in (ROOT / "script").glob("*/*.json"):
            for s in json.loads(f.read_text(encoding="utf-8"))["strings"]:
                text[s["id"]] = (s.get("en") or s["jp"]).replace("\n", " / ")[:90]
        for i in miss:
            print(i, text.get(i, ""))


if __name__ == "__main__":
    main()
