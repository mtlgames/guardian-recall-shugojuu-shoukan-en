"""Show how a batch's JP differs from a near-copy entry already translated, to adapt its English.

    python -X utf8 tools/tl_diff.py bNNN SRC_ENTRY [--from N --to M] [--same OUT.tsv]

For each batch row g23.EE.NNN, the row g23.SRC.NNN: changed JP chunks (-src +batch), then the source English.
Quote style, commas and line breaks are ignored. --same writes `id<TAB>English` (translator form) for every row
that matches its source, ready for `tl_reuse.py bNNN --fill OUT.tsv`.
"""
import difflib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
from tl_reuse import translator_form  # noqa: E402

IGNORE = r"[\s　「」『』、。]|\{wait\}"


def main(argv):
    batch, src = argv[0], argv[1]
    lo = int(argv[argv.index("--from") + 1]) if "--from" in argv else 0
    hi = int(argv[argv.index("--to") + 1]) if "--to" in argv else 10**9
    d = json.loads((ROOT / "script" / "scenario" / f"{src}.json").read_text(encoding="utf8"))
    by = {e["id"]: e for e in (d if isinstance(d, list) else d["strings"])}
    rows = (ROOT / "work" / "tl" / f"{batch}.tsv").read_text(encoding="utf8").splitlines()[lo:hi]
    same = []
    for line in rows:
        i, _sp, _g, _l, jp = line.split("\t")
        e = by.get(re.sub(r"^g23\.\d+", f"g23.{src}", i))
        if not e or not e.get("en"):
            print(f"{i}: no source\n  {jp}")
            continue
        a, b = re.sub(IGNORE, "", e["jp"]), re.sub(IGNORE, "", jp.replace(" / ", "\n"))
        sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
        ch = [f"-{a[i1:i2]}+{b[j1:j2]}" for op, i1, i2, j1, j2 in sm.get_opcodes() if op != "equal"]
        print(f"{i} <- {e['id']}: {' '.join(ch) if ch else 'same'}")
        if ch:
            print("  EN:", translator_form(e))
        else:
            same.append(f"{i}\t{translator_form(e)}\n")
    if "--same" in argv:
        Path(argv[argv.index("--same") + 1]).write_text("".join(same), encoding="utf8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
