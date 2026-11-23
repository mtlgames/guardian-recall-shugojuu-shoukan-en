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
_pending = (ROOT / "tools" / "exe_pending.txt").read_text(encoding="utf8").split()
PENDING = r"(" + "|".join(re.escape(i) for i in _pending) + r")$" if _pending else r"(?!)"

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
    dict(name="charfile profile", ids=r"cf\.", jp=r"^&s\(165,87\)", kind="txd", px=129, lines=6, status="measured"),
    # page header: name &s(200,20), voice actor &s(230,206) (box right 299, CV icon ends x 225), stats in the &h()
    # small font (not measured). `pitch`: ASCII advance = width + (&g pitch - 13) per glyph; long names use &g(13,0)
    dict(name="charfile header", ids=r"cf\.", jp=r"^&g\(14,0\)&s\(200,20\)", kind="txd", right=299, left=165, lines=1,
         pitch=True, status="measured"),
    # list of names (opt_charfile_all): centred row, highlight bar x 20-300, numbers end x 45
    dict(name="charfile list", ids=r"cf\.", jp=r"^[^&]", kind="txd", px=180, lines=1, status="measured"),
    # DIC.BIN wraps by itself once a glyph would start at col >= 100 (asm/hooks.asm): English is pre-wrapped at 100
    # one entry per book page, 16 px rows from y 35: row 12 falls off the page (opt_dictionary_page; JP max 11)
    # list of headings (opt_dictionary_all): one row, same list renderer as the replay list (centred by byte count)
    dict(name="dictionary list", ids=r"dic\.", jp=r"^(?!.*&n\(\))", kind="txd", px=223, lines=1, bytes=34,
         status="measured"),
    dict(name="dictionary entry", ids=r"dic\.", kind="txd", px=114, wrap=100, lines=11, status="measured"),
    # guardian page body `&g(14,24)&f(14,10)` (opt_guardians_page): text from x 64, ASCII advance at pitch 14 = width
    # + 1 (adv); 24 px rows from y 99: row 6 runs into the bottom bar, row 5 must end before the △ Push icon (x 263).
    # JP: 14 chars (to x 259), max 4 rows. Lines: 3 header (name, gap, reading) + 5 body
    dict(name="guardian page", ids=r"gd\.", jp=r"^&s\(64,20\)", kind="txd", px=192, adv=1, lines=8,
         status="measured"),
    # centred by byte count (start x = 159.5 - 3.25 * bytes), so bytes also keep it clear of the number column
    dict(name="replay list", ids=r"rep\.", kind="txd", px=223, lines=1, bytes=34, status="measured"),
    # one record = the whole diary page; each &s(x,y) segment gets right - x px (x 0 = &e() centred: right - left)
    # narrow: body lines 1-2 stop before the LOAD button (x 236; the JP runs under it, English words got hidden)
    dict(name="diary page", ids=r"day\.", jp=r"^&f\(32,32\)&s\(116,26\)", kind="txd", right=273, left=40, lines=5,
         narrow={"&s(40,120)": (194, 194)}, status="measured"),
    dict(name="guardian list", ids=r"gd\.", jp=r"^[^&]", kind="txd", px=180, lines=1, status="measured"),
    dict(name="tutorial title", ids=r"tu\.", kind="txd", px=280, lines=1, status="measured"),
    # DAY SAVE/LOAD list row label (day_save): pen x 30, time at x 215 -> 180 px. Stages < 20 draw two labels on one
    # row ("%-6s %-6s ": Sky + Earth), so those two chapters keep the pair inside 180 (tests/test_batches.py)
    dict(name="save chapter label", ids=r"save\.(05(1[2-9]|[2-9]\d)|06\d\d|070[048])$", kind="txd", px=180, lines=1,
         status="measured"),
    # day.txd keeps a second copy of the save labels (slots 512-708, same layout); no reader found yet: same budget
    dict(name="day chapter label", ids=r"day\.(05(1[2-9]|[2-9]\d)|06\d\d|070[048])$", kind="txd", px=180, lines=1,
         status="guess (copy of save labels)"),
    dict(name="txd", ids=r"(cf|gd|rep|tu|day|save|op)\.[0-9a-f]{4}$", kind="txd", px="jp", lines=99,
         status="jp width"),
    # unit command menu (tac_unit_menu): fixed box, pen x 193, right border x 225 -> 30 px
    dict(name="unit command menu", ids=r"exe\.", jp=r"^(移動|情報|行動|思考|待機)$", kind="lines", px=30, lines=1,
         bytes="room", status="measured"),
    # floor: the Japanese's own ink width (13 px per full-width char), which its window holds by construction;
    # raise per screen with a measured row above when the English needs more
    # 2026-11-24 English build (b073-b076), shots vs work/qa/warp_orig (docs/windows.md "EXE screens")
    # tac_think list: pen x 175, cost numbers from x 293 (JP 8 chars to x 277); SEARCH list columns are as wide
    dict(name="tactic list", ids=r"exe\.02[45]", jp=r"(せよ|するな！|癒せ)$", kind="lines", px=115, lines=1,
         status="measured"),
    # tac_think: "Current Tactic:" box, pen x 26, border x 137
    dict(name="current tactic", ids=r"exe\.0137c$", kind="lines", px=107, lines=1, status="measured"),
    # tac_action: 行動 submenu, fixed box, pen x 240, border x 312
    dict(name="action submenu", ids=r"exe\.(a62b0|a62d0|a62d8|a62e0|a62e8|014a4)$", kind="lines", px=69, lines=1,
         status="measured"),
    # option: BRAIN menu labels, left column pen x 66 runs into the centre art past ~x 160, right column x 218
    dict(name="BRAIN menu", ids=r"brain\.", kind="lines", px=90, lines=1, status="measured"),
    # ev43 HEN roster: names left-aligned at x 16 + 76 k (4 columns, inkrows) -> 74 px with a 2 px gap; Kaoru,
    # Sayaka and the Ichinomiya twins (77-90 px) use given names here only (D14)
    dict(name="HEN roster name", ids=r"hen\.00(0[0-9a-f]{2}|10[0-8])$", kind="lines",
         px=74, lines=1,
         status="measured"),
    # HEN team prompts share one line; floor = the group's widest JP line (21 chars)
    dict(name="HEN team prompt", ids=r"hen\.00(1ec|208|224|250|278|2a4)$", kind="lines", px=273, lines=1,
         status="jp width (group max)"),
    # tac_break / tac_saved: message box x 54-249, pen x 68
    dict(name="map message box", ids=r"action\.00(c[c-f]|d[0-9a-f]|e[0-9a-f]|f[01])", kind="lines", px=176,
         lines=1, status="measured"),
    # Psi names (table 0x8009B990): tac_power list widened by PSI_W (asm/hooks.asm): name x 210, cost x 280;
    # 情報 Aura now one column: name x 224, cost x 289. "Demon Might" (62) + "Rock Shield" shot in both (phase 7)
    dict(name="Psi name", ids=r"exe\.a6(7[d-f]|8[0-9ab])[0-9a-f]$", kind="lines", px=64, lines=1, bytes="room",
         status="measured"),
    # ring > UNIT list element (Ali) column, widened in asm/hooks.asm "ACTION.BIN": Master tab x 121, Lv x 160;
    # Guardian tab x 157, Lv x 200 -> 42 px ("Emperor"; "Thunder" shot in the Guardian tab, phase 7)
    dict(name="UNIT list element", ids=r"action\.001[4-6][0-9a-f]$", kind="lines", px=42, lines=1, bytes="room",
         status="measured"),
    # ring > SEARCH tabs (asm/hooks.asm "SEARCH tabs"): labels x 46/86/120, selected box sized to each; "Tactic" 29
    dict(name="SEARCH tab", ids=r"action\.010(34|3c|44)$", kind="lines", px=30, lines=1, status="measured"),
    # 思考 submenu (tac_think_menu): pen x 240, box right now 313; Berserk Alert popup: text x 123, box right 193
    dict(name="think submenu", ids=r"exe\.01(38c|398|3a4)$", kind="lines", px=73, lines=1, status="measured"),
    dict(name="Berserk Alert popup", ids=r"exe\.01330$", kind="lines", px=70, lines=1, status="measured (code)"),
    # Retreat Proposal title (box x 108 w 96, text x 114) and TURN END prompt (box x 115 w 182, text x 125): code
    # card/slot labels (table 0x8009CB38: Spare A-D, Normal, Never Registered, For Yoshida-san): only printf'd by a
    # leftover debug table dump (0x8006AB40, "table[%d] = %2d .... [%s]"); never drawn
    dict(name="debug printf labels", ids=r"exe\.(a6b[c-f][0-9a-f]|0287[0c])$", kind="lines", px=200, lines=1,
         bytes="room", status="not drawn (debug printf)"),
    # Ap-cost popup row "Restore Sp": label x 193, stat name moved to x 236 (asm/hooks.asm)
    dict(name="Ap popup Restore", ids=r"exe\.a6288$", kind="lines", px=41, lines=1, status="measured (code)"),
    dict(name="Retreat title", ids=r"action\.01068$", kind="lines", px=88, lines=1, status="measured (code)"),
    dict(name="TURN END prompt", ids=r"action\.01094$", kind="lines", px=170, lines=1, status="measured (code)"),
    # Forms (type table 0x8009BC34, 1-26): 情報 type row x 88 -> "Df." label x 186 (tac_info_g + unit_type.lua:
    # "Overlord Guardian" 88 shot); ring > UNIT Guardian tab Type column draws the short form (type_short, D14)
    dict(name="Form name", ids=r"exe\.02(5[6-9a-f]|6[0-5])[0-9a-f]$", kind="lines", px=96, lines=1, bytes="room",
         status="measured"),
    # traits (type table 27-57): ring > SEARCH Trait tab, 3 columns x 28/110/190 (78 each); 情報 Tec. now one trait
    # per row at x 186 (134; "Seven Dragons" + "Rising Dragon" shot, tac_info_g with --qa)
    dict(name="trait name", ids=r"exe\.a69[0-9a-c][0-9a-f]$|exe\.a68[c-f][0-9a-f]$", kind="lines", px=78, lines=1,
         bytes="room", status="measured"),
    # unit type names (table 0x80095D08 -> unit+0x10, the default unit name): 情報 / status panel name x 28 to the
    # emblem x 142 (108). Allies also show in ring > UNIT (masters 94, guardians 80): master names <= 90
    # (species a6354-a6508 + 015b4-0192c; boss parts 026a0-0271c are set by code)
    dict(name="unit type name", ids=r"exe\.(a63[5-9a-f]|a64[0-9a-f]|a650|015[b-f]|01[6-8][0-9a-f]|019[0-2]|026[a-f]"
         r"|027[01])[0-9a-f]$", kind="lines", px=108, lines=1, bytes="room", status="measured (status panel)"),
    # item names (table 0x8009B4F8): drawn only by the equipment helper 0x80060688 (情報 + HEN detail, icon + name)
    # and in "Obtained '%s'" (map message box 176). Narrowest: HEN detail Foot row, name x 59 -> "Mv." x 170 (poked
    # equipment: hen_unit + tools/lua/poke.lua, "Vermilion Wing Necklace" 112 hit Mv.: now Scarlet, 104)
    dict(name="item name", ids=r"exe\.(a67[2-9a-c][0-9a-f]|02[23][0-9a-f]{2})$", kind="lines", px=110, lines=1,
         bytes="room", status="measured"),
    # widths the English needs beyond what the screen holds or was measured (tools/exe_pending.txt, one id per
    # line): phase 7 widens the box/column or condenses (D4, D13); a shot must replace each with a measured row
    dict(name="EXE engine pending", ids=PENDING, kind="lines", px=170, lines=1, bytes="room",
         status="engine pending / unmeasured"),
    dict(name="EXE/overlay string", ids=r"(exe|action|battle|hen|day|brain)\.[0-9a-f]{5}$", kind="lines", px="jp",
         lines=99, bytes="room", status="jp width"),
    # evd names go through the evd_name hook (any length); narrowest view = ring > UNIT list name column (x 25).
    # The 20-byte crash there was the 2D pool (asm/hooks.asm pool_grow), not the name. Phase 7 moved the Ali column
    # (asm/hooks.asm "ACTION.BIN"): Master tab Ali x 121 -> 94 px ("Suzune Ichinomiya" 90 shot whole); the Guardian
    # tab's Type column is at x 107 -> guardian names 80 px ("Thunder Dragon" 79 shot)
    dict(name="evd unit name", ids=r"map\d+\.", kind="lines", px=94, lines=1, status="measured"),
]


def wrap(text, px, glyphs, nl="&n()", first=(), adv=0):
    """Break English text at spaces so no line is wider than px (`first`: narrower widths for the first lines):
    the txd renderers never auto-wrap ASCII (docs/re/text.md). Markup is zero width; an existing `nl` starts a
    new line. `adv`: extra px per glyph (an &g pitch above 13)."""
    out, w, n = [], 0, 0
    lim = lambda: first[n] if n < len(first) else px  # noqa: E731
    _w = font.width
    font_width = lambda t, g: _w(t, g) + adv * len(t)  # noqa: E731
    for tok in re.split(r"(&[a-z]\([^)]*\)| )", text):
        if not tok:
            continue
        if tok == nl:
            out.append(tok)
            w, n = 0, n + 1
        elif MARKUP.fullmatch(tok):
            out.append(tok)
        elif tok == " ":
            out.append(tok)
            w += font_width(" ", glyphs)
        else:
            tw = font_width(tok, glyphs)
            if w and w + tw > lim():
                while out and out[-1] == " ":  # the break replaces the space(s) before the word
                    out.pop()
                    w -= font_width(" ", glyphs)
                out.append(nl)
                w, n = 0, n + 1
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
    pitch = 13
    for text, px in segments(v, s["en"], s["jp"]):
        if v.get("pitch"):
            text = re.sub(r"&h\(\).*?&h\(\)", "", text)  # small ASCII font (cf stats), not the VWF
            pitch = int((re.findall(r"&g\((\d+),", text) or [pitch])[-1])
        for i, p in enumerate(pages(v, text)):
            body = p[1:] if named and i == 0 else p
            if len(body) > v["lines"]:
                errs.append(f"{len(body)} lines > {v['lines']}")
            for j, line in enumerate(p):
                w = font.width(line, glyphs) + (pitch - 13 + v.get("adv", 0)) * len(line)
                lim = px[min(j, len(px) - 1)] if isinstance(px, list) else px
                if w > lim:
                    errs.append(f"{w} px > {lim}: {line!r}")
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
    parts = re.split(r"(&s\((-?\d+),-?\d+\))", text)
    out = [(parts[0], v["right"] - v["left"])]
    for mark, x, seg in zip(parts[1::3], parts[2::3], parts[3::3]):
        px = v["right"] - (int(x) if int(x) > 0 else v["left"])
        out.append((seg, [*v.get("narrow", {}).get(mark, ()), px]))  # px per line, the last one repeats
    return out


def wrap_txd(v, text, glyphs):
    """Word-wrap txd English to its variant: per &s(x,y) segment (`right` variants) or at `wrap` / `px`. Lines the
    translator broke with &n() stay; a "jp" floor (unmeasured) leaves the text as written."""
    if v.get("pitch"):  # one-line labels at a set &g pitch: never wrapped, the lint checks them
        return text
    if "right" in v:
        parts = re.split(r"(&s\(-?\d+,-?\d+\))", text)
        out = [wrap(parts[0], v["right"] - v["left"], glyphs)]
        for mark, seg in zip(parts[1::2], parts[2::2]):
            x = int(re.match(r"&s\((-?\d+)", mark).group(1))
            out += [mark, wrap(seg, v["right"] - (x if x > 0 else v["left"]), glyphs,
                               first=v.get("narrow", {}).get(mark, ()))]
        return "".join(out)
    px = v.get("wrap", v["px"])
    return text if px == "jp" else wrap(text, px, glyphs, adv=v.get("adv", 0))


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
