"""Window budgets (phase 5 width gate) and the fit lint over script/ (docs/windows.md has the evidence per row).

Each record gets the first VARIANTS row whose `ids` regex matches its id (re.match) and, if set, whose `jp` regex
matches its Japanese. Budget = px per line and lines per page; `status` is "measured" (shot in docs/windows.md) or
"guess". English lines are measured with fonts/vwf12.txt advances (font.width).

    python -X utf8 tools/windows.py            # lint every record with `en`; exit 1 on an overflow
    python -X utf8 tools/windows.py --cover    # records per variant, and records no variant covers
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

import font
import script_io

ROOT = Path(__file__).resolve().parents[1]
MARKUP = re.compile(r"&[a-z]\([^)]*\)")

# kind: scenario = "Name\nline\nline{wait}..." (first line of a page may be the speaker name);
#       lines = text split on \n and {wait};  txd = markup, lines split on &n() (English must carry its own &n()).
VARIANTS = [
    dict(name="scenario", ids=r"g23\.", kind="scenario", px=224, lines=3, status="measured"),
    dict(name="battle quote", ids=r"g13\.(00|01|08|09|11|12|15|16)\.", kind="scenario", px=224, lines=3,
         status="measured"),
    dict(name="battle comment", ids=r"g13\.1[34]\.", kind="lines", px=224, lines=3, status="measured"),
    dict(name="power help", ids=r"g13\.03\.", kind="lines", px=232, lines=3, status="measured"),
    dict(name="think help", ids=r"g13\.04\.", kind="lines", px=117, lines=4, status="measured"),
    dict(name="field help", ids=r"g13\.(05|06|17|18)\.", kind="lines", px=220, lines=3, status="measured"),
    dict(name="battle help", ids=r"g13\.", kind="lines", px=220, lines=3, status="guess"),
    dict(name="charfile profile", ids=r"cf\.", jp=r"^&s\(165,87\)", kind="txd", px=129, lines=5, status="measured"),
    dict(name="dictionary entry", ids=r"dic\.", kind="txd", px=114, lines=99, status="measured"),
    # centred by byte count (start x = 159.5 - 3.25 * bytes), so bytes also keep it clear of the number column
    dict(name="replay list", ids=r"rep\.", kind="txd", px=223, lines=1, bytes=34, status="measured"),
    dict(name="txd", ids=r"(cf|gd|rep|tu|day|save|op)\.[0-9a-f]{4}$", kind="txd", px=200, lines=99, status="guess"),
    dict(name="EXE/overlay string", ids=r"(exe|action|battle|hen|day|brain)\.[0-9a-f]{5}$", kind="lines", px=200, lines=99,
         bytes="room", status="guess"),
    # evd names go through the evd_name hook (any length); narrowest view = ring > UNIT list name column (x 25, Ali
    # values from x 103): 75 px. The 20-byte crash there was the 2D pool (asm/hooks.asm pool_grow), not the name.
    dict(name="evd unit name", ids=r"map\d+\.", kind="lines", px=75, lines=1, status="measured"),
]


def wrap(text, px, glyphs, nl="&n()"):
    """Break English text at spaces so no line is wider than px: the txd renderers never auto-wrap ASCII
    (docs/re/text.md). Markup is zero width; an existing `nl` starts a new line."""
    out, w = [], 0
    for tok in re.split(r"(&[a-z]\([^)]*\)| )", text):
        if not tok:
            continue
        if tok == nl:
            out.append(tok)
            w = 0
        elif MARKUP.fullmatch(tok):
            out.append(tok)
        elif tok == " ":
            out.append(tok)
            w += font.width(" ", glyphs)
        else:
            tw = font.width(tok, glyphs)
            if w and w + tw > px:
                while out and out[-1] == " ":  # the break replaces the space(s) before the word
                    out.pop()
                    w -= font.width(" ", glyphs)
                out.append(nl)
                w = 0
            out.append(tok)
            w += tw
    return "".join(out)


def variant(s):
    for v in VARIANTS:
        if re.match(v["ids"], s["id"]) and (not v.get("jp") or re.search(v["jp"], s["jp"])):
            return v
    return None


def pages(v, text):
    """[[line, ...] per page] in display form (markup removed)."""
    if v["kind"] == "txd":
        text = text.replace("&n()", "\n")
        text = MARKUP.sub("", text)
    out = []
    for page in text.split("{wait}"):
        lines = page.split("\n")
        while lines and lines[-1] == "":
            lines.pop()
        if lines:
            out.append(lines)
    return out


def lint(s, v, glyphs):
    """Error strings for one record's `en` against its variant."""
    errs = []
    if v.get("bytes") and not (v["bytes"] == "room" and s.get("refs")):  # strings with refs move to STR_POOL; "room" (EXE/overlay slot, NUL included), "jp" (Japanese length) or a fixed cap
        n = {"room": lambda: s["room"] - 1, "jp": lambda: len(script_io.enc_jp(s))}.get(v["bytes"], lambda: v["bytes"])()
        b = len(script_io.enc(s["en"]))
        if b > n:
            errs.append(f"{b} bytes > {n} in place")
    # a scenario record opens with the speaker's name line when the Japanese does (not 「 （ 『 or an indent)
    named = v["kind"] == "scenario" and "\n" in s["jp"] and s["jp"][0] not in "「（『　"
    for i, p in enumerate(pages(v, s["en"])):
        body = p[1:] if named and i == 0 else p
        if len(body) > v["lines"]:
            errs.append(f"{len(body)} lines > {v['lines']}")
        for line in p:
            w = font.width(line, glyphs)
            if w > v["px"]:
                errs.append(f"{w} px > {v['px']}: {line!r}")
    return errs


def records():
    for f in sorted((ROOT / "script").glob("*/*.json")):
        for s in json.loads(f.read_text(encoding="utf-8"))["strings"]:
            if s.get("status") != "data" and re.search(r"[^\x00-\x7f]", s["jp"]):  # skip ASCII data rows
                yield s


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cover", action="store_true")
    a = ap.parse_args(argv)
    glyphs = font.load_glyphs()
    if a.cover:
        c, none = Counter(), Counter()
        for s in records():
            v = variant(s)
            if v:
                c[f"{v['name']} ({v['status']})"] += 1
            else:
                none[s["id"].split(".")[0]] += 1
        for k, n in c.most_common():
            print(f"{n:6d}  {k}")
        for k, n in none.most_common():
            print(f"{n:6d}  NO BUDGET: {k}")
        return 0
    bad = 0
    for s in records():
        if not s.get("en"):
            continue
        v = variant(s)
        if not v:
            print(f"{s['id']}: no window budget (docs/windows.md)")
            bad += 1
            continue
        for e in lint(s, v, glyphs):
            print(f"{s['id']} [{v['name']}]: {e}")
            bad += 1
    print(f"fit lint: {bad} error(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
