"""script_stats.py: strings per script/ folder: total, data, translated, still escaped ([XX]) text.

    python -X utf8 tools/script_stats.py [--esc]   # --esc lists text records whose jp still holds [XX]
"""
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    c = collections.defaultdict(collections.Counter)
    for f in sorted((ROOT / "script").glob("*/*.json")):
        for s in json.loads(f.read_text(encoding="utf-8"))["strings"]:
            k = c[f.parent.name]
            k["strings"] += 1
            k["data"] += s.get("status") == "data"
            k["en"] += bool(s.get("en"))
            esc = "[" in s["jp"] and s.get("status") != "data"
            k["escaped"] += esc
            if esc and "--esc" in sys.argv:
                print(f"{s['id']}\t{s['jp'][:60]!r}")
    for name, k in c.items():
        print(name, dict(k))
