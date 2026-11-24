"""Slot list for tools/lua/txd_sweep.lua: per txd file, its built slot offsets and the slots whose text no coverage
log under LOGDIR has shown yet (numeric data records such as "0,28,0,25,.." are left out: parsed, never drawn).

    python -X utf8 tools/txd_sweep.py LOGDIR OUT.txt [--all]

OUT lines: `name s:o,s:o,..|w,w,..` (s:o = slot:offset of every used slot; w = wanted slots). --all wants every
text slot, not only the unshown ones.
"""
import argparse, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import cover_stats, insert, script_io, strings_tsv  # noqa: E402

DATA = re.compile(r"[-0-9,]*")


def rows(logdir, want_all=False):
    seen = cover_stats.shown(logdir)
    hashes = {i: h for i, h in strings_tsv.rows()}
    for f in sorted((ROOT / "script/txd").glob("*.json")):
        doc = json.loads(f.read_text(encoding="utf-8"))
        b = script_io.build_slots(doc, lambda s: insert.record_bytes(s, "en", None) or script_io.enc_jp(s))
        offs = script_io.struct.unpack_from(f"<{doc['count']}I", b, len(bytes.fromhex(doc["head"])))
        so = [(i, o) for i, o in enumerate(offs) if o]
        want = []
        for s in doc["strings"]:
            text = s.get("en") or s["jp"]
            if s.get("status") == "data" or DATA.fullmatch(text):
                continue
            if want_all or f"{hashes.get(s['id'], 0):08x}" not in seen:
                want.append(s["slots"][0])
        yield f.stem, so, sorted(want)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("logdir")
    ap.add_argument("out")
    ap.add_argument("--all", action="store_true")
    a = ap.parse_args()
    lines = []
    for name, so, want in rows(a.logdir, a.all):
        lines.append(f"{name} " + ",".join(f"{s}:{o}" for s, o in so) + "|" + ",".join(map(str, want)))
        print(f"{name}: {len(want)} wanted of {len(so)} slots")
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
