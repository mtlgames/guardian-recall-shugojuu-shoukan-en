"""Print a MARKER_KEEP regex (tools/insert.py) for bisecting a marker-build bug: every id of the given script files
except the slice [LO:HI) of the records matching --where (a regex on jp), which get markers.

    MARKER_KEEP="$(python -X utf8 tools/debug/keep_re.py txd/dic --where '&n' --lo 0 --hi 45)" python build.py --marker
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="+", help="script/<x>.json without .json, e.g. txd/dic")
ap.add_argument("--where", default="")
ap.add_argument("--lo", type=int, default=0)
ap.add_argument("--hi", type=int, default=10 ** 9)
a = ap.parse_args()
keep = []
for f in a.files:
    ss = json.loads((ROOT / "script" / f"{f}.json").read_text(encoding="utf-8"))["strings"]
    sel = [s for s in ss if re.search(a.where, s["jp"])][a.lo:a.hi]
    marked = {s["id"] for s in sel}
    keep += [s["id"] for s in ss if s["id"] not in marked]
print("(" + "|".join(re.escape(i) + "$" for i in keep) + ")" if keep else "(?!)")
