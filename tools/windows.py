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
    # 02 item help (10-char lines), 07 ability / 10 think + reading (17-char lines): trigger not yet found in game
    # 02 records are 4 lines (category: / 2 description lines / stats)
    dict(name="item help", ids=r"g13\.02\.", kind="lines", px="jp", lines=4, status="jp width"),
    # 07 trait / 10 Tactic help: one box per group, so its widest JP line (17 chars, 221 px) is every record's floor
    dict(name="trait help", ids=r"g13\.(07|10)\.", kind="lines", px=221, lines=3, status="jp width (group max)"),
    dict(name="battle help", ids=r"g13\.", kind="lines", px="jp", lines=3, status="jp width"),
    dict(name="charfile profile", ids=r"cf\.", jp=r"^&s\(165,87\)", kind="txd", px=129, lines=5, status="measured"),
    # DIC.BIN wraps by itself once a glyph would start at col >= 100 (asm/hooks.asm): English is pre-wrapped at 100
    dict(name="dictionary entry", ids=r"dic\.", kind="txd", px=114, wrap=100, lines=99, status="measured"),
    # guardian page body `&g(14,24)&f(14,10)`: the JP auto-wraps at 14 chars x pitch 14 = 196 px; ASCII advance at
    # pitch 14 = width + 1, so English wraps at 180. Lines: 3 header (name, reading) + 10 body
    dict(name="guardian page", ids=r"gd\.", jp=r"^&s\(64,20\)", kind="txd", px=180, lines=13,
         status="derived (&f chars x &g pitch)"),
    # centred by byte count (start x = 159.5 - 3.25 * bytes), so bytes also keep it clear of the number column
    dict(name="replay list", ids=r"rep\.", kind="txd", px=223, lines=1, bytes=34, status="measured"),
    # one record = the whole diary page; each &s(x,y) segment gets right - x px (x 0 = &e() centred: right - left)
    dict(name="diary page", ids=r"day\.", jp=r"^&f\(32,32\)&s\(116,26\)", kind="txd", right=273, left=40, lines=5,
         status="measured"),
    dict(name="guardian list", ids=r"gd\.", jp=r"^[^&]", kind="txd", px=180, lines=1, status="measured"),
    dict(name="tutorial title", ids=r"tu\.", kind="txd", px=280, lines=1, status="measured"),
    # DAY SAVE/LOAD list row label (day_save): pen x 30, time at x 215 -> 180 px. Stages < 20 draw two labels on one
    # row ("%-6s %-6s ": Sky + Earth), so those two chapters keep the pair inside 180 (tests/test_batches.py)
    dict(name="save chapter label", ids=r"save\.(05(1[2-9]|[2-9]\d)|06\d\d|070[048])$", kind="txd", px=180, lines=1,
         status="measured"),
    dict(name="txd", ids=r"(cf|gd|rep|tu|day|save|op)\.[0-9a-f]{4}$", kind="txd", px="jp", lines=99,
         status="jp width"),
    # unit command menu (tac_unit_menu): fixed box, pen x 193, right border x 225 -> 30 px
    dict(name="unit command menu", ids=r"exe\.", jp=r"^(移動|情報|行動|思考|待機)$", kind="lines", px=30, lines=1,
         bytes="room", status="measured"),
    # floor: the Japanese's own ink width (13 px per full-width char), which its window holds by construction;
    # raise per screen with a measured row above when the English needs more
    dict(name="EXE/overlay string", ids=r"(exe|action|battle|hen|day|brain)\.[0-9a-f]{5}$", kind="lines", px="jp",
         lines=99, bytes="room", status="jp width"),
    # evd names go through the evd_name hook (any length); narrowest view = ring > UNIT list name column (x 25, Ali
    # values from x 103): 75 px. The 20-byte crash there was the 2D pool (asm/hooks.asm pool_grow), not the name.
    # 95 px = full English names ("Suzune Ichinomiya" 90 px, D4: no abbreviations). The ring > UNIT list holds 75 px
    # before the Ali column (x 103): phase 7 must widen that column or draw it condensed (docs/windows.md).
    dict(name="evd unit name", ids=r"map\d+\.", kind="lines", px=95, lines=1, status="engine pending (75 measured)"),
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
    named = v["kind"] == "scenario" and named_jp(s["jp"])
    for text, px in segments(v, s["en"], s["jp"]):
        for i, p in enumerate(pages(v, text)):
            body = p[1:] if named and i == 0 else p
            if len(body) > v["lines"]:
                errs.append(f"{len(body)} lines > {v['lines']}")
            for line in p:
                w = font.width(line, glyphs)
                if w > px:
                    errs.append(f"{w} px > {px}: {line!r}")
    return errs


def named_jp(jp):
    """A scenario record opens with a speaker name line: a short first line (<= 8 chars) with no sentence
    punctuation; tutorial narration lines (long, or with 。、) and 「（『/indented openings are not names."""
    if "\n" not in jp:
        return False
    first = jp.split("\n", 1)[0]
    return (len(first) <= 8 and first[:1] not in "「（『　" and not re.search(r"[。、！？・：「」（）『』]", first)
            and first[-1:] not in "はでがをに")  # tutorial text broken after a particle (ＭＰは, 今は先ほどの逆で)


def jp_px(jp):
    """Widest Japanese line in px as the original draws it: 13 per full-width char, 6 per ASCII byte."""
    text = re.sub(r"&[ns]\([^)]*\)|\{[^}]*\}", "\n", jp)  # new line / new position / control code
    text = MARKUP.sub("", text)  # colour, font, centring: no ink
    return max(sum(13 if ord(c) > 0x7F else 6 for c in line) for line in text.split("\n"))


def segments(v, text, jp=""):
    """[(text, px)]: the whole text at the variant's px, or (variants with `right`) one entry per &s(x,y) segment."""
    if "right" not in v:
        return [(text, jp_px(jp) if v["px"] == "jp" else v["px"])]
    parts = re.split(r"&s\((-?\d+),-?\d+\)", text)
    out = [(parts[0], v["right"] - v["left"])]
    for x, seg in zip(parts[1::2], parts[2::2]):
        out.append((seg, v["right"] - (int(x) if int(x) > 0 else v["left"])))
    return out


def wrap_txd(v, text, glyphs):
    """Word-wrap txd English to its variant: per &s(x,y) segment (`right` variants) or at `wrap` / `px`. Lines the
    translator broke with &n() stay; a "jp" floor (unmeasured) leaves the text as written."""
    if "right" in v:
        parts = re.split(r"(&s\(-?\d+,-?\d+\))", text)
        out = [wrap(parts[0], v["right"] - v["left"], glyphs)]
        for mark, seg in zip(parts[1::2], parts[2::2]):
            x = int(re.match(r"&s\((-?\d+)", mark).group(1))
            out += [mark, wrap(seg, v["right"] - (x if x > 0 else v["left"]), glyphs)]
        return "".join(out)
    px = v.get("wrap", v["px"])
    return text if px == "jp" else wrap(text, px, glyphs)


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
