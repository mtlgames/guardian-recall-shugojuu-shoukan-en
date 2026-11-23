"""Find shipped English for a JP phrase (all script/ files): `id | JP excerpt | EN excerpt` per hit.

    python -X utf8 tools/find_en.py PHRASE [PHRASE..] [--max N]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main(argv):
    n = int(argv[argv.index("--max") + 1]) if "--max" in argv else 3
    phrases = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--max")]
    for p in phrases:
        hits = 0
        for f in sorted((ROOT / "script").glob("*/*.json")):
            d = json.loads(f.read_text(encoding="utf8"))
            for e in d if isinstance(d, list) else d["strings"]:
                jp = re.sub(r"[\s　]", "", e["jp"])
                if p in jp and e.get("en") and e["en"] != e["jp"] and hits < n:
                    i = jp.find(p)
                    print(f"{e['id']} | {jp[max(0, i - 10):i + 30]} | {e['en'][:300]!r}")
                    hits += 1
        if not hits:
            print(f"{p}: no English yet")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
