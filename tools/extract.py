"""Dump every text container of disc 1 into script/ as JSON (one file per block / file / image).

    python -X utf8 tools/extract.py           # writes only missing files
    python -X utf8 tools/extract.py --force   # rewrites all, keeping en/notes/status of ids that still exist

Layout (all ids are address- or slot-based and stable):
  script/scenario/NN.json  UNN.PAK group 23 entry NN (scenario), ids g23.NN.SSS (SSS = first slot)
  script/battle/NN.json    UNN.PAK group 13 entry NN (battle quotes, item help), ids g13.NN.SSS
  script/txd/NAME.json     GRETC.RLZ txd files, ids NAME.SSSS
  script/evd/MAP.json      GRETC.RLZ evd unit names (op 0x34), ids MAP.OFFS
  script/exe/IMG.json      EXE / overlay strings in place, ids IMG.OFFSET
Records: jp (decoded, real newlines), en (empty until translated), plus the layout needed to rebuild the original
bytes (tests/test_script.py). status "data" = not shown text (debug printf, byte noise): leave en empty.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gretc  # noqa: E402
import script_io as S  # noqa: E402

ROOT = S.ROOT
OUT = ROOT / "script"
KEEP = ("en", "notes", "status")


def tree():
    sys.path.insert(0, str(ROOT))
    import build
    return build.dump(1) / "tree"


def is_data(img, s):
    """Not shown on screen: printf debug output, or unreferenced byte noise in the record range."""
    jp = s["jp"]
    if jp.endswith("\n"):
        return "printf"
    if not s["refs"] and (len(re.findall(r"[^\x00-\x7f]", jp)) < 2 or "{wait}" in jp or "[" in jp):
        return "noise"
    return None


def files(t):
    """Yield (relative path, document) for every container."""
    exe = (t / "SLPS_012.97").read_bytes()
    unn = (t / "DATA/UNN.PAK").read_bytes()
    for g, blocks in S.unn_groups(exe, unn).items():
        sub = {23: "scenario", 13: "battle"}[g]
        for i, b in enumerate(blocks):
            if (g, i) in S.NONTEXT:
                continue
            blk = S.parse_slots(b)
            for s in blk["strings"]:
                s["id"] = f"g{g}.{i:02d}.{s['slots'][0]:03d}"
            yield f"{sub}/{i:02d}.json", {"src": f"UNN.PAK group {g} entry {i}", **blk}
    rlz = (t / "DATA/GRETC.RLZ").read_bytes()
    for i, e in enumerate(S.gretc_entries(rlz)):
        name = e["name"].rsplit(".", 1)[0]
        if e["group"] == "txd":
            blk = S.parse_slots(gretc.expand(rlz, e), txd=True)
            for s in blk["strings"]:
                s["id"] = f"{name}.{s['slots'][0]:04d}"
            yield f"txd/{name}.json", {"src": f"GRETC.RLZ entry {i} {e['name']}", **blk}
        elif e["group"] == "evd":
            ss = S.parse_evd(gretc.expand(rlz, e))
            for s in ss:
                s["id"] = f"{name}.{s['off']:04x}"
            if ss:
                yield f"evd/{name}.json", {"src": f"GRETC.RLZ entry {i} {e['name']}", "strings": ss}
    for key, (f, base, ranges) in S.IMAGES.items():
        img = (t / f).read_bytes()
        ss = S.image_strings(img, base, ranges, S.refs(img, base))
        for s in ss:
            s["id"] = f"{key}.{s['off']:05x}"
            why = is_data(img, s)
            if why:
                s["status"] = "data"
                s["notes"] = why
        yield f"exe/{key}.json", {"src": f"{f} (RAM base {base:#x})", "strings": ss}


def order(s):
    """id first, then jp/en, then layout fields."""
    head = {k: s[k] for k in ("id", "jp") if k in s}
    head["en"] = s.get("en", "")
    return {**head, **{k: v for k, v in s.items() if k not in head}}


def write(path, doc, force):
    if path.exists():
        if not force:
            return False
        old = {s["id"]: s for s in json.loads(path.read_text(encoding="utf-8"))["strings"]}
        for s in doc["strings"]:
            for k in KEEP:
                if k in old.get(s["id"], {}) and (k != "status" or s.get("status") != "data"):
                    s[k] = old[s["id"]][k]
    doc["strings"] = [order(s) for s in doc["strings"]]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return True


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    n = w = strings = 0
    for rel, doc in files(tree()):
        n += 1
        strings += len(doc["strings"])
        w += write(OUT / rel, doc, a.force)
    print(f"{n} files, {strings} strings, {w} written")


if __name__ == "__main__":
    main()
