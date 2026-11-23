"""Review pairs per batch (phase 6 review, docs/review.md).

    python -X utf8 tools/pairs.py bNNN [bNNN ..]     -> work/qa/review/pairs/bNNN.txt
    python -X utf8 tools/pairs.py --drift             batches whose .out.tsv no longer gives script/'s English

Rows: `>> id | speaker | JP` then the English as written in work/tl/bNNN.out.tsv (what a fix edits; `merge
--overwrite` stores it). Page breaks show as " ¦ ". A row whose JP and English both appeared in an earlier batch is
listed once as `== id = earlier id` (copies of chapter 00 and the tutorials).
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import batches  # noqa: E402

OUT = batches.ROOT / "work/qa/review/pairs"


def flat_jp(text):
    return text.replace(" / {wait}", " ¦ ").replace("{wait}", " ¦ ").replace(" / 　", "").replace(" / ", "").strip(" ¦")


def flat_en(text):
    return text.replace("{wait}", " ¦ ").replace("\\n", " / ")


def rows(batch):
    out = dict(r[:2] if len(r) > 1 else (r[0], "") for r in batches.read_tsv(batches.TL / f"{batch}.out.tsv"))
    for r in batches.read_tsv(batches.TL / f"{batch}.tsv"):
        yield r[0], r[1], r[4], out.get(r[0], "")


def write(names):
    OUT.mkdir(parents=True, exist_ok=True)
    seen = {}
    for p in batches.existing():
        name = p.stem
        lines = []
        for eid, sp, jp, en in rows(name):
            key = (jp, en)
            if key in seen and name in names:
                lines.append(f"== {eid} = {seen[key]}")
            elif name in names:
                lines.append(f">> {eid} | {sp} | {flat_jp(jp)}\n   {flat_en(en)}")
            seen.setdefault(key, eid)
        if name in names:
            (OUT / f"{name}.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
            print(OUT / f"{name}.txt", len(lines))


def drift():
    entries = batches.index()
    for p in batches.existing():
        bad = [eid for eid, _, _, en in rows(p.stem)
               if eid in entries and en and batches.prepare(entries[eid], en) != entries[eid].get("en")]
        if bad:
            print(p.stem, len(bad), bad[:5])


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["--drift"]:
        drift()
    elif args:
        write(set(args))
    else:
        sys.exit(__doc__)
