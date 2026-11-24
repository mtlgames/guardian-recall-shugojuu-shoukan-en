"""build/strings.tsv for text coverage: `id<TAB>fnv32` per script string, the FNV-1a 32 of the bytes the build
writes (English if translated, else the original; status `data` records are skipped). tools/lua/textcover.lua logs
the same hash of every string the game reads, and the skill's textcover.py matches the two.

    python -X utf8 tools/strings_tsv.py [OUT]     (build.py writes it after each build)
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import script_io  # noqa: E402


def fnv32(b):
    h = 2166136261
    for x in b:
        h = ((h ^ x) * 16777619) & 0xFFFFFFFF
    return h


def encoded(f, s, qa=None):
    """The bytes the build writes for record s of script file f (no NUL)."""
    qa = qa or {}
    b = script_io.enc(qa[s["id"]]) if s["id"] in qa else script_io.enc(s["en"]) if s.get("en") else script_io.enc_jp(s)
    if f.parent.name == "exe" and s.get("en") and s["id"] not in qa:
        import insert  # the build pads centred EXE messages (insert.centre_pad)
        b = insert.centre_pad(s, b)
    return b


def rows(qa=None):
    for f in sorted((ROOT / "script").glob("*/*.json")):
        for s in json.loads(f.read_text(encoding="utf-8"))["strings"]:
            if s.get("status") == "data":
                continue
            b = encoded(f, s, qa)
            if b:
                yield s["id"], fnv32(b)


def write(out=ROOT / "build/strings.tsv", qa=None):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text("# id\tfnv32 (tools/strings_tsv.py)\n" + "".join(f"{i}\t{h:08x}\n" for i, h in rows(qa)),
                         encoding="utf-8")


assert fnv32(b"a") == 0xE40C292C  # FNV-1a 32 test vector

if __name__ == "__main__":
    write(*sys.argv[1:2])
