"""Leftover-Japanese scan of the built discs (release gate; references/pipeline.md §Checks).

    python -X utf8 tools/jp_scan.py        exit 1 if anything is found

1. Re-extracts every text container (UNN g23/g13 blocks, GRETC txd/evd, EXE + overlays) from the *built* tree of
   each disc (work/build/d<N>/tree) and reports any slot whose decoded text still holds kana/kanji, except records
   script/ marks `status: data` (not shown) or keeps Japanese on purpose (KEEP below).
2. Reports Shift-JIS runs in every changed non-media file of the built tree that the pristine file doesn't hold:
   Japanese the build itself wrote. (Not `jp_left.py`: its --orig keeps *unchanged* runs, and every repointed EXE
   string leaves its old Japanese in place; step 1 and jp_refs.hits judge those.)
   Unchanged Japanese outside the extractor's list is the recon's job (docs/re/text.md, jp_refs.py, textcover).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import extract  # noqa: E402
import jp_refs  # noqa: E402
import sjis_survey  # noqa: E402

ROOT = extract.ROOT
JP = re.compile(r"[぀-ヿ一-鿿]")
MEDIA = {".XA", ".STR", ".VB", ".VH", ".TIM", ".DA"}
KEEP = set()  # ids whose Japanese is kept on purpose (none)


def script_status():
    out = {}
    for p in (ROOT / "script").rglob("*.json"):
        for s in json.loads(p.read_text(encoding="utf-8"))["strings"]:
            out[s["id"]] = (s.get("status", ""), s.get("en", ""))
    return out


def slots(tree, status):
    for rel, doc in extract.files(tree):
        for s in doc["strings"]:
            st, en = status.get(s["id"], ("missing", ""))
            if rel.startswith("exe/"):
                continue  # in-place EXE strings are stale after repointing: jp_refs below
            if JP.search(s["jp"]) and st != "data" and s["id"] not in KEEP:
                yield f"{rel} {s['id']} [{st}] {s['jp'][:40]!r}"


def raw_new(tree, orig):
    """Shift-JIS runs (sjis_survey's rule) in a built file that the pristine file doesn't hold anywhere."""
    for f in sorted(p for p in tree.rglob("*") if p.is_file() and p.suffix.upper() not in MEDIA):
        o = orig / f.relative_to(tree)
        old = o.read_bytes() if o.is_file() else b""
        new = f.read_bytes()
        if old == new:
            continue
        for off, text in sjis_survey.runs(new, 4):
            if text.encode("cp932") not in old:
                yield f"{f.relative_to(tree)} {off:#x} {text[:40]!r}"


def main():
    status = script_status()
    t1, t2 = (ROOT / f"work/build/d{n}/tree" for n in (1, 2))
    bad = [f"d1 slot {line}" for line in slots(t1, status)]
    # disc 2 shares every DATA file (insert.py): same bytes = same scan
    bad += [f"d2 DATA differs from d1: {p.relative_to(t2)}" for p in sorted((t2 / "DATA").rglob("*"))
            if p.is_file() and p.read_bytes() != (t1 / p.relative_to(t2)).read_bytes()]
    # EXE/overlay strings are relocated, the old Japanese stays in place: count only what a pointer still reaches
    for n, t in ((1, t1), (2, t2)):
        bad += [f"d{n} jp ref {k} {o:#x} {s!r}" for k, o, s, r in jp_refs.hits(t, built=True)]
        bad += [f"d{n} raw {line}" for line in raw_new(t, ROOT / f"work/iso/d{n}/tree")]
    print("\n".join(bad) or "clean")
    print(f"{len(bad)} findings")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
