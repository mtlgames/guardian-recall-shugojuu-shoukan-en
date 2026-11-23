"""Translation batches (docs/translator-brief.md): split untranslated text, check translator output, merge it back.

    python -X utf8 tools/batches.py split [--size 3500] [--only REGEX]   work/tl/bNNN.tsv + build/terms_bNNN.txt
    python -X utf8 tools/batches.py check [bNNN ...]      a batch's .out.tsv; with no batch, all shipped English (for check.py)
    python -X utf8 tools/batches.py merge bNNN ... [--overwrite]   check, then write the English into script/
    python -X utf8 tools/batches.py fit "text" [--id g23.01.000]    dry-run: the stored form and its lint

Copied from the skill's assets/batches.py; the ADAPTER section fits this game. Batch TSV: id, speaker, form, limit, JP
(line breaks shown as " / "). Output: work/tl/bNNN.out.tsv, id<TAB>English, every id once, same order.

English as written by the translator vs. as stored (prepare()):
- scenario box records (g23, g13 quotes): the speaker name line is added from glossary.md (SPEAKERS), the body is
  word-wrapped to the box (tools/windows.py budget) and split into extra {wait} pages when a page runs past its lines.
  The translator writes the body only, {wait} between pages, `\\n` only for a forced break.
- other records: `\\n` = line break, kept as written (txd text carries its own &n()).
"""
import functools
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import font  # noqa: E402
import windows  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
TL = ROOT / "work/tl"
SCRIPT = ROOT / "script"
GLOSSARY = ROOT / "glossary.md"
MAX_ENTRIES = 150

# ---- ADAPTER: this game's text format ----
TOKEN = re.compile(r"\{[^}]*\}|&[a-z]\([^)]*\)")  # control codes and txd markup; must survive translation
PRINTF = re.compile(r"%[-+ 0#]*\d*(?:\.\d+)?[a-zA-Z]")
# HEN roster names drawn at a 76 px pitch: these use the given name only (D14), so the full-name glossary check skips
GIVEN_ONLY = {"hen.00048", "hen.00054", "hen.000c4", "hen.000d0"}
FREE = {"{wait}", "&n()"}  # page and line breaks the English may place freely
VARIABLE = r"\{var[^}]*\}"  # (this game draws no numbers inside text)
HONORIFICS = {"さん": "-san", "ちゃん": "-chan", "くん": "-kun", "君": "-kun", "様": "-sama", "先輩": "-senpai",
              "先生": "-sensei"}  # checked only right after a speaker name (glossary Speakers table)
GLYPHS = font.load_glyphs()


def docs():
    for path in sorted(SCRIPT.rglob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        yield path, doc, doc["strings"]


def needs_english(entry):
    """Data rows and ASCII-only rows (numbers, file names) stay as they are."""
    return (bool(entry.get("jp")) and not entry.get("en") and entry.get("status") != "data"
            and bool(re.search(r"[^\x00-\x7f]", entry["jp"])))


def group_of(entry):
    """evd unit names repeat per map: one batch row per distinct name (merge copies it to every id)."""
    return "evd:" + entry["jp"] if entry["id"].startswith("map") else entry["id"]


def entry_key(entry):
    return entry["id"]


def speaker_of(entry):
    """(JP name line, JP body) of a scenario-box record; name "" when the record has no name line."""
    v = windows.variant(entry)
    jp = entry["jp"]
    if is_named(entry):
        name, body = jp.split("\n", 1)
        return name, body
    return "", jp


def is_named(entry):
    v = windows.variant(entry)
    return bool(v and v["kind"] == "scenario" and windows.named_jp(entry["jp"]))


def limit_label(entry):
    v = windows.variant(entry)
    if not v:
        return "?"
    if "right" in v:  # diary page: each &s(x,y) segment gets right - x px
        return f"{v['name']}:right {v['right']}" + (f"x{v['lines']}" if v["lines"] < 99 else "")
    px = windows.jp_px(entry["jp"]) if v["px"] == "jp" else v.get("px", "")
    return f"{v['name']}:{px}px" + (f"x{v['lines']}" if v["lines"] < 99 else "")


@functools.lru_cache(maxsize=None)
def persons():
    """{JP name: EN} of the Speakers and Characters tables: honorifics are checked after these only."""
    return {j: ens[0] for jps, ens, _, notes in glossary(all_rows=True) if "(person)" in notes for j in jps}


@functools.lru_cache(maxsize=None)
def speakers():
    """{JP speaker label: EN} from every glossary table (first EN form)."""
    out = {}
    for jps, ens, _, _ in glossary(all_rows=True):
        for j in jps:
            out.setdefault(j, ens[0])
    return out


def wrap_page(text, px):
    """Greedy word wrap; `\\n` in the text forces a break. A one-word stub on the last line is avoided by wrapping
    narrower when that keeps the same line count."""
    lines = greedy(text, px)
    n, narrow = len(lines), px
    while n > 1 and font.width(lines[-1], GLYPHS) < 40 and narrow > px * 0.7:
        narrow -= 4
        trial = greedy(text, narrow)
        if len(trial) != n:
            break
        lines = trial
    return lines


def greedy(text, px):
    lines = []
    for para in text.split("\n"):
        cur = ""
        for word in para.split(" "):
            trial = f"{cur} {word}" if cur else word
            if cur and font.width(trial, GLYPHS) > px:
                lines.append(cur)
                cur = word
            else:
                cur = trial
        lines.append(cur)
    return lines


def prepare(entry, en):
    """Translator English -> stored English (see the module doc)."""
    en = en.replace("\\n", "\n").strip()
    v = windows.variant(entry)
    jp = entry["jp"]
    if v and v["kind"] == "txd":
        return windows.wrap_txd(v, en, GLYPHS)
    if not v or (v["kind"] == "lines" and not entry["id"].startswith("g13")):
        return en
    name, _ = speaker_of(entry)
    px = windows.jp_px(jp) if v["px"] == "jp" else v["px"]
    pages = []
    for page in en.split("{wait}"):
        page = page.strip()
        if not page:
            continue
        lines = wrap_page(page, px)
        if "{wait}" in jp:  # the box pages on {wait}: run long text onto extra pages
            pages += [lines[i:i + v["lines"]] for i in range(0, len(lines), v["lines"])]
        else:
            pages.append(lines)
    end = "\n{wait}" if jp.endswith("{wait}") else ("\n" if jp.endswith("\n") else "")
    sep = "\n{wait}" if "{wait}" in jp else "\n"
    body = sep.join("\n".join(p) for p in pages) + end
    if is_named(entry):
        body = (speakers()[name] if name else "") + "\n" + body
    return body


def width_problems(entry, en):
    v = windows.variant(entry)
    if not v:
        return ["no window budget (tools/windows.py)"]
    s = dict(entry, en=en)
    return windows.lint(s, v, GLYPHS)


CARD_TITLES = {"day.00250", "exe.01580", "exe.021d0", "action.006b4"}  # memory-card system file title: BIOS shows SJIS


def encodable(char, eid=""):
    return " " <= char <= "~" or (eid in CARD_TITLES and ("！" <= char <= "～" or char == "　"))
# ---- end of ADAPTER ----


def kind(char):
    if "぀" <= char <= "ゟ":
        return "hiragana"
    if "゠" <= char <= "ヿ":
        return "katakana"
    if "一" <= char <= "鿿" or char == "々":
        return "kanji"
    return "other"


def has_term(jp, term):
    """term occurs as a whole kana or kanji run: ミン isn't in タイミング, くも isn't in ぼくも."""
    jp = jp.replace(" / ", "")
    for m in re.finditer(re.escape(term), jp):
        a, b = m.start(), m.end()
        if (a == 0 or kind(jp[a - 1]) != kind(term[0])) and (b == len(jp) or kind(jp[b]) != kind(term[-1])):
            return True
    return False


def glossary(all_rows=False):
    """[(JP forms, EN forms, avoid forms, notes)] from glossary.md's | JP | EN | max | notes | Avoid | tables.
    Rows whose notes say "(no lint)" name speakers only (all_rows=True includes them)."""
    rows = []
    if not GLOSSARY.exists():
        return rows
    section = ""
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:]
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if line.startswith("|") and len(cells) >= 2 and cells[0] not in ("JP", "") and not set(cells[0]) <= set("-: "):
            notes = cells[3] if len(cells) > 3 else ""
            if section.startswith(("Speakers", "Characters")):
                notes += " (person)"
            if "(no lint)" in notes and not all_rows:
                continue
            avoid = [x.strip() for x in cells[4].split("/") if x.strip()] if len(cells) > 4 else []
            rows.append(([x.strip() for x in cells[0].split("/")], [x.strip() for x in cells[1].split("/")], avoid,
                         notes))
    return rows


def problems(entry, en, terms, stored=False):
    """Every rule, on one line of English (as written, or as stored when stored=True)."""
    jp = entry["jp"]
    if not en.strip():
        return ["empty English"]
    out = []
    plain = TOKEN.sub("", en)
    if bad := sorted({c for c in plain if not encodable(c, entry["id"]) and c != "\n"}):
        out.append(f"unencodable characters {bad}")
    if re.search(r"\\u[0-9a-fA-F]{4}", en) or "\t" in en:
        out.append("escape sequence or tab in the English")
    if entry["id"].split(".")[0] in ("cf", "gd", "rep", "tu", "day", "save", "op", "dic") and "&" in MARKUP_FREE(en):
        out.append("bare & in txd text (markup only)")
    free = lambda t: t in FREE or t.startswith("&g(")  # noqa: E731  &g = glyph pitch: English may tighten it to fit
    want = Counter(t for t in TOKEN.findall(jp) if not free(t))
    have = Counter(t for t in TOKEN.findall(en) if not free(t))
    if want != have:
        out.append(f"control codes differ: JP {dict(want)} EN {dict(have)}")
    # printf format strings (EXE/overlay): same conversions in order; flags/width may change (day.002a0 drops %-7s
    # padding). Text without conversions isn't printf'd: "100% of" drew as is in g13 help (phase 7 shot)
    if (jf := PRINTF.findall(jp)) and [f[-1] for f in jf] != [f[-1] for f in PRINTF.findall(en)]:
        out.append(f"printf conversions differ: JP {jf} EN {PRINTF.findall(en)}")
    name, body_jp = speaker_of(entry)
    if name and name not in speakers():
        out.append(f"speaker {name} not in glossary.md")
    jp_plain = TOKEN.sub("", body_jp)
    en_body = en.split("\n", 1)[1] if stored and is_named(entry) else en
    en_terms = " ".join(TOKEN.sub(" ", en_body).replace("\\n", " ").split()).lower()
    for jps, ens, avoid, _ in terms:
        if entry["id"] in GIVEN_ONLY:
            break
        if any(has_term(jp_plain, j) for j in jps) and not any(" ".join(e.split()).lower() in en_terms for e in ens):
            out.append(f"glossary: {jps[0]} -> {ens[0]}")
        out += [f"glossary Avoid: {a}" for a in avoid if re.search(rf"\b{re.escape(a)}\b", en)]
    names = persons()
    for jp_name, en_name in names.items():
        # a given name inside a listed full name (周防ちかな様) is checked as the full name only
        longer = [k for k in names if k != jp_name and k.endswith(jp_name)]
        for jp_form, en_form in HONORIFICS.items():
            hit = any((m.start() == 0 or kind(jp_plain[m.start() - 1]) != kind(jp_name[0]))
                      and not any(jp_plain[:m.start() + len(jp_name)].endswith(k) for k in longer)
                      for m in re.finditer(re.escape(jp_name + jp_form), jp_plain))
            if hit and (en_name + en_form).lower() not in en.lower():
                out.append(f"honorific {jp_name}{jp_form} needs {en_name}{en_form}")
    full = en if stored else prepare(entry, en)
    return out + width_problems(entry, full)


def MARKUP_FREE(en):
    return re.sub(r"&[a-z]\([^)]*\)", "", en)


def index():
    result = {}
    for _, _, entries in docs():
        for e in entries:
            key = entry_key(e)
            if key in result:
                raise ValueError(f"duplicate batch key {key!r}")
            result[key] = e
    return result


def read_tsv(path):
    return [line.split("\t") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def existing():
    return sorted(TL.glob("b[0-9][0-9][0-9].tsv"))


def show(text):
    return text.replace("\n", " / ")


def split(size, only=None):
    """Numbers on from the last batch and leaves out ids already batched, so a repeat run can't duplicate work."""
    index()
    TL.mkdir(parents=True, exist_ok=True)
    (ROOT / "build").mkdir(exist_ok=True)
    taken = {r[0] for p in existing() for r in read_tsv(p)}
    n = max((int(p.stem[1:]) for p in existing()), default=0)
    groups = {}
    for _, _, entries in docs():
        for e in entries:
            if needs_english(e) and entry_key(e) not in taken and (not only or re.match(only, e["id"])):
                groups.setdefault(group_of(e), []).append(e)
    batches, cur, chars = [], [], 0
    for group in groups.values():
        group = group[:1]  # one row per group; merge copies it to the rest
        c = sum(len(TOKEN.sub("", e["jp"])) for e in group)
        if cur and (chars + c > size or len(cur) + len(group) > MAX_ENTRIES):
            batches.append(cur)
            cur, chars = [], 0
        cur += group
        chars += c
    if cur:
        batches.append(cur)
    terms = glossary()
    for batch in batches:
        n += 1
        name = f"b{n:03d}"
        path = TL / f"{name}.tsv"
        if path.exists():
            sys.exit(f"{path} already exists")
        rows = []
        for e in batch:
            sp, body = speaker_of(e)
            rows.append(f"{entry_key(e)}\t{sp}\t{e['id'].split('.')[0]}\t{limit_label(e)}\t{show(body)}")
        path.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
        jps = " ".join(TOKEN.sub("", e["jp"]) for e in batch)
        used = [(j, ens[0]) for jpl, ens, _, _ in terms for j in jpl if has_term(jps, j)]
        (ROOT / f"build/terms_{name}.txt").write_text("".join(f"{j}\t{e}\n" for j, e in used)
                                                      or "(no glossary terms in this batch)\n", encoding="utf-8", newline="\n")
    print(f"{len(batches)} new batches in {TL}, {len(taken)} ids already batched")


def check_batch(batch, entries, terms):
    want = [r[0] for r in read_tsv(TL / f"{batch}.tsv")]
    rows = [(r[0], "\t".join(r[1:])) for r in read_tsv(TL / f"{batch}.out.tsv")]
    bad = []
    if [r[0] for r in rows] != want:
        got = [r[0] for r in rows]
        dup = sorted(i for i, c in Counter(got).items() if c > 1)
        bad.append(f"ids differ: missing {sorted(set(want) - set(got))[:8]} extra {sorted(set(got) - set(want))[:8]} "
                   f"duplicate {dup[:8]} (order must match too)")
    for eid, en in rows:
        if eid in entries:
            bad += [f"{eid}: {p}: {en!r}" for p in problems(entries[eid], en, terms)]
    return bad, dict(rows)


def merge(new, overwrite):
    """Refuses to replace different English unless told to, before anything is written. evd names go to every id
    with the same Japanese."""
    entries = index()
    stored = {}
    for k, en in new.items():
        e = entries[k]
        full = prepare(e, en)
        if e["id"].startswith("map"):
            for o in entries.values():
                if o["id"].startswith("map") and o["jp"] == e["jp"]:
                    stored[o["id"]] = full
        else:
            stored[k] = full
    if not overwrite:
        for k, full in stored.items():
            if entries[k].get("en") and entries[k]["en"] != full:
                sys.exit(f"{k} would lose {entries[k]['en']!r}: pass --overwrite if that is meant")
    changed = 0
    for path, doc, items in docs():
        touched = False
        for e in items:
            if entry_key(e) in stored and e.get("en") != stored[entry_key(e)]:
                e["en"], e["status"] = stored[entry_key(e)], "done"
                touched = True
                changed += 1
        if touched:
            path.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"merged: {changed} entries changed")


def main(argv):
    if not argv:
        sys.exit(__doc__)
    cmd, args = argv[0], argv[1:]
    if cmd == "split":
        return split(int(args[args.index("--size") + 1]) if "--size" in args else 3500,
                     args[args.index("--only") + 1] if "--only" in args else None)
    if cmd == "fit":
        eid = args[args.index("--id") + 1] if "--id" in args else "g23.01.000"
        e = index()[eid]
        full = prepare(e, args[0])
        print(full)
        print("\n".join(problems(e, args[0], glossary())) or "OK")
        return 0
    overwrite = "--overwrite" in args
    names = [a for a in args if a != "--overwrite"]
    entries, terms = index(), glossary()
    if cmd == "check" and not names:
        bad = [f"{i}: {p}: {e['en']!r}" for i, e in entries.items() if e.get("en") and e.get("status") != "data"
               for p in problems(e, e["en"], terms, stored=True)]
        print(f"{len(entries)} entries, {len(bad)} problems")
        print("\n".join(bad[:200]))
        return 1 if bad else 0
    if cmd not in ("check", "merge") or not names:
        sys.exit(__doc__)
    failed = 0
    for batch in names:
        bad, rows = check_batch(batch, entries, terms)
        failed += bool(bad)
        print(f"{batch}: " + ("OK" if not bad else f"{len(bad)} problems"))
        for line in bad:
            print("  " + line)
        if cmd == "merge" and not bad:
            merge(rows, overwrite)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1:]))
