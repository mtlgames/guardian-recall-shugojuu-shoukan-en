"""Write docs/text_unshown.tsv (`id<TAB>reason`), the textcover waivers, from rules over script/ plus MANUAL rows.
Only strings no run can show belong here; strings a run could reach get a scene instead.

    python -X utf8 tools/cover_waive.py [LOGDIR]     (LOGDIR: only waive ids its logs haven't shown; default work/qa/cover)
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import cover_stats, strings_tsv  # noqa: E402

JP = re.compile(r"[^\x00-\x7f]")
DATA = re.compile(r"[-0-9,]*")

# id prefix or id -> reason, for strings checked by hand
MANUAL = {
    "day.0029c": ("separator in the memory-card header title (DAY 0x8016AB3C: sprintf day.002a0 %s args, '/' only when the "
                  "save holds two episodes); shown by the console's card manager, never drawn by the game"),
}


def reason(s):
    jp, en = s["jp"], s.get("en") or ""
    if re.match(r"(攻撃|防御)側：", jp):
        return ("battle rule-record name (+0x1C of the 0x20-byte records from BATTLE 0x80171544): never read while "
                "rules fired in the battle runs (read BP on the overlay text range)")
    if DATA.fullmatch(en or jp):
        return "numeric data record (index/flag list parsed by the overlay, never drawn)"
    if not en and not JP.search(jp):
        return "untranslated record with no Japanese (markup only / original English): the build writes the original bytes"
    for k, r in MANUAL.items():
        if s["id"].startswith(k):
            return r


def main():
    logdir = sys.argv[1] if len(sys.argv) > 1 else str(ROOT / "work/qa/cover")
    seen = cover_stats.shown(logdir)
    hashes = {i: f"{h:08x}" for i, h in strings_tsv.rows()}
    rows = []
    for f in sorted((ROOT / "script").glob("*/*.json")):
        for s in json.loads(f.read_text(encoding="utf-8"))["strings"]:
            if s["id"] in hashes and hashes[s["id"]] not in seen:
                r = reason(s)
                if r:
                    rows.append(f"{s['id']}\t{r}\n")
    out = ROOT / "docs/text_unshown.tsv"
    out.write_text("# id\treason (tools/cover_waive.py)\n" + "".join(rows), encoding="utf-8", newline="\n")
    print(f"{len(rows)} waivers -> {out}")


if __name__ == "__main__":
    main()
