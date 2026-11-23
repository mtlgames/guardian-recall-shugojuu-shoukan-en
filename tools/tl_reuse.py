"""Prefill a batch from English already in script/: same JP body (speaker line, line breaks and spaces ignored).

    python -X utf8 tools/tl_reuse.py bNNN [--write]
    python -X utf8 tools/tl_reuse.py bNNN --fill FILLS.tsv

Prints `id<TAB>source id<TAB>English` per hit (stored English with the speaker line and trailing {wait} removed, so
it is in translator form). --write creates work/tl/bNNN.out.tsv with the hits filled and `TODO` for the rest (refuses
to overwrite). --fill replaces rows of bNNN.out.tsv with the `id<TAB>English` rows of FILLS.tsv and lists the TODOs
left. Check every reused line in context: the same words can need a different English.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import windows  # noqa: E402


def has_speaker(jp: str) -> bool:
    """First line is a name line (same test as batches.py / windows.py)."""
    return bool(windows.named_jp(jp))


def norm(jp: str) -> str:
    """JP body without the speaker line, line breaks or spaces."""
    if has_speaker(jp):
        jp = jp.split("\n", 1)[1]
    return re.sub(r"[\s　]", "", jp)


def translator_form(entry: dict) -> str:
    en = entry["en"]
    if has_speaker(entry["jp"]) and "\n" in en:
        en = en.split("\n", 1)[1]  # speaker line added by batches.prepare
    en = re.sub(r"\n?\{wait\}$", "", en)
    return en.replace("\n{wait}", "{wait}").replace("\n", " ")


def index(skip_prefix: str = "") -> dict:
    idx = {}
    for f in sorted((ROOT / "script").glob("*/*.json")):
        d = json.loads(f.read_text(encoding="utf8"))
        for e in d if isinstance(d, list) else d["strings"]:
            if e.get("en") and e["en"] != e["jp"] and not (skip_prefix and e["id"].startswith(skip_prefix)):
                idx.setdefault(norm(e["jp"]), e)
    return idx


def fill(batch: str, fills: Path) -> int:
    new = dict(l.split("\t", 1) for l in fills.read_text(encoding="utf8").splitlines() if "\t" in l)
    out = ROOT / "work" / "tl" / f"{batch}.out.tsv"
    rows = [l.split("\t", 1) for l in out.read_text(encoding="utf8").splitlines() if l.strip()]
    rows = [(i, new.pop(i, en)) for i, en in rows]
    out.write_text("".join(f"{i}\t{en}\n" for i, en in rows), encoding="utf8")
    left = [i for i, en in rows if en == "TODO"]
    print(f"unknown ids: {list(new)}  TODO left: {left}")
    return 1 if new or left else 0


def main(argv):
    if "--fill" in argv:
        return fill(argv[0], Path(argv[argv.index("--fill") + 1]))
    batch, write = argv[0], "--write" in argv
    idx = index()
    rows = []
    for line in (ROOT / "work" / "tl" / f"{batch}.tsv").read_text(encoding="utf8").splitlines():
        i, sp, _g, _l, jp = line.split("\t")
        e = idx.get(norm((sp + "\n" if sp else "") + jp.replace(" / ", "\n")))
        if e and e["id"] != i:
            print(f"{i}\t{e['id']}\t{translator_form(e)}")
        rows.append((i, translator_form(e) if e and e["id"] != i else "TODO"))
    print(f"{sum(r[1] != 'TODO' for r in rows)} / {len(rows)} reused")
    if write:
        out = ROOT / "work" / "tl" / f"{batch}.out.tsv"
        if out.exists():
            sys.exit(f"{out} exists")
        out.write_text("".join(f"{i}\t{en}\n" for i, en in rows), encoding="utf8")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
