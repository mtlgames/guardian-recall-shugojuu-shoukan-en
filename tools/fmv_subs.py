"""FMV subtitles (D18): English burned into the voiced STR movies, white text with a dark outline, no box.

    python -X utf8 tools/fmv_subs.py STEM [--preview DIR] [--times 12.5,40]   frames with their subtitle, for checking
    python -X utf8 tools/fmv_subs.py [--preview DIR]      every movie: one built frame per page -> DIR/<STEM>/
    python -X utf8 tools/fmv_subs.py --check [BATCH]     times in order, every line English, pages readable
    python -X utf8 tools/fmv_subs.py --init | --batches N | --merge BATCH     ASR drafts -> gfx/fmv, translator batches

English: '-' = no subtitle for that row (ASR hallucination), '|' forces a line break, ' / ' starts a new page (sentence ends); a page longer than 2 lines goes on in
2-line pages by itself. A line's pages share its time by length.

gfx/fmv/<STEM>.tsv (start, end, ja, en; seconds of movie time = first sector of the frame / 150, the same clock as
the audio fmv_asr.py transcribed) lists the lines. Per frame that shows a line: decode (mdec, 304x160), draw the
English centred at the bottom, re-encode only the macroblocks the lettering touches at the frame's qscale, raised
until the frame fits its own sectors (staff_str helpers). Audio sectors and every other frame stay as they are.

`patch(tree_file, log)` (insert.patch_tree) writes the cached result (work/fmv/cache/, keyed by a hash of the inputs)
over the dumped file and logs each changed sector."""
import argparse
import csv
import hashlib
import inspect
import struct
import sys
from multiprocessing import Pool
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
import mdec  # noqa: E402
import staff_str  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SUBS = ROOT / "gfx/fmv"
FONT = ROOT / "fonts/LiberationSans-Bold.ttf"
CACHE = ROOT / "work/fmv/cache"
W, H = 304, 160                  # every voiced movie (STAFF.STR is 320x240 and has its own tool)
SS, SIZE, STROKE = 4, 12, 1.5    # supersampling, font px size, outline px
LINE_H, BOTTOM, MARGIN = 13, 5, 6   # line pitch, px below the last line box (descenders + outline fit), side margin
HOLD, MIN_SHOW = 0.3, 1.0        # seconds a line stays after its end; shortest time on screen
READ, CPS = 0.3, 30              # check(): shortest page time (a quick "Right." is 0.34 s), fastest chars/second
SECTORS_PER_S = 150              # 2x CD speed


WEAK = {"i", "a", "an", "the", "of", "to", "and", "or", "but", "my", "your", "our", "their", "his", "her", "its", "in",
        "on", "at", "for", "with", "from", "no", "not", "be", "is", "are", "was", "were", "you", "we", "they", "he",
        "she", "it", "i'm", "i'll", "i've", "you're", "we're", "they're", "it's", "that's", "has", "have", "had",
        "will", "would", "can", "could", "should", "every", "this", "that", "these", "those", "some", "any", "so",
        "as", "than", "if", "when", "because", "who", "which", "very", "just", "all"}
# word pairs and phrases a break never goes inside (glossary terms, phrasal verbs, set phrases)
KEEP = [p.split() for p in ("dragon vein", "dragon veins", "dragon wielder", "dragon wielders", "four gate generals",
                            "seven dragons", "emperor dragon", "hiryuki palace", "national diet building",
                            "all the time", "right now", "right away", "at once")]
PAGE, BRK = 3, 3.5   # pages(): cost of one more page, weight of a break's _brk cost (tuned on the visual-QA flags)
TAIL = {"up", "out", "off", "down", "away", "back", "over", "around"}   # shook / up: particle starting a line


def _end_cost(word):
    """How bad a page or line ending after word is: sentence end 0, clause end 1, mid-phrase 2, after a function word
    or a possessive 4."""
    w = word.rstrip('"\'')
    if w.endswith((".", "!", "?", "...")):
        return 0
    if w.endswith((",", ";", ":", "-")):
        return 1
    return 4 if word.lower().strip('"\'') in WEAK or w.endswith("'s") else 2


def _brk(ws, i):
    """Cost of a break between ws[i-1] and ws[i] (line or page)."""
    c = _end_cost(ws[i - 1])
    a, b = ws[i - 1], ws[i]
    if c == 2 and a[:1].isupper() and b[:1].isupper() and a != "I":
        c += 2                                          # inside a name: Seven / Dragons
    if c >= 2 and b.lower().strip(".,!?'\"") in TAIL:
        c += 2
    low = [w.lower().strip(".,!?;:'\"") for w in ws]
    for k in KEEP:
        for s in range(max(0, i - len(k) + 1), i):
            if low[s:s + len(k)] == k:
                c += 4
    return c


def _page(ws, f):
    """(cost, lines) of one page: one line costs 0; two lines cost their best break (ties: the more balanced);
    None if it needs 3+ lines."""
    if f.getlength(" ".join(ws)) <= ROOM:
        return 0, [" ".join(ws)]
    best = None
    for i in range(1, len(ws)):
        a, b = " ".join(ws[:i]), " ".join(ws[i:])
        wid = max(f.getlength(a), f.getlength(b))
        if wid <= ROOM:
            c = BRK * _brk(ws, i) + wid / ROOM
            if best is None or c < best[0]:
                best = (c, [a, b])
    return best


def pages(en, f=None):
    """Subtitle pages of one line ('|'-joined display lines): ' / ' starts a page; within a part, pages and line
    breaks are chosen together by dynamic programming over word positions: a page costs PAGE, a break BRK x _brk,
    so two clean pages beat one page broken mid-phrase."""
    f = f or _font()
    out = []
    for part in en.split(" / "):
        if "|" in part:                                 # forced line breaks: as written
            out.append(part)
            continue
        ws = part.split()
        best = {0: (0, [])}
        for i in range(1, len(ws) + 1):
            for j in range(i - 1, -1, -1):
                pg = _page(ws[j:i], f)
                if pg is None:
                    if len(_greedy(" ".join(ws[j:i]), f)) > 2:
                        break
                    continue
                c = best[j][0] + PAGE + pg[0] + (BRK * _brk(ws, i) if i < len(ws) else 0)
                if i not in best or c < best[i][0]:
                    best[i] = (c, best[j][1] + ["|".join(pg[1])])
        out += best[len(ws)][1]
    return out


def lines(stem):
    """[(start, end, en)] pages of gfx/fmv/<stem>.tsv with display times (held, never past the next line); a line
    of several pages shares its time between them by length."""
    rows = [(float(r["start"]), float(r["end"]), r["en"].strip()) for r in _rows(SUBS / f"{stem}.tsv")]
    rows = [r for r in rows if r[2] and r[2] != "-"]       # "-": no subtitle (a Whisper hallucination over music)
    out, fnt = [], _font()
    for i, (a, b, en) in enumerate(rows):
        nxt = rows[i + 1][0] if i + 1 < len(rows) else 1e9
        end = min(max(b + HOLD, a + MIN_SHOW), nxt)
        ps = pages(en, fnt)
        n = sum(len(p) for p in ps)
        t = a
        for p in ps:
            t1 = t + (end - a) * len(p) / n
            out.append((t, t1, p))
            t = t1
    return out


def _font():
    return ImageFont.truetype(str(FONT), SIZE * SS)


ROOM = (W - 2 * MARGIN) * SS


def _greedy(text, f):
    out, cur = [], ""
    for w in text.split():
        t = f"{cur} {w}".strip()
        if cur and f.getlength(t) > ROOM:
            out.append(cur)
            cur = w
        else:
            cur = t
    return out + [cur]


def wrap(en, f=None):
    """Display lines of one page: '|' forces a break; a part over one line is broken as pages() would."""
    f = f or _font()
    out = []
    for part in en.split("|"):
        pg = _page(part.split(), f) if part.split() else (0, [""])
        out += pg[1] if pg else _greedy(part, f)
    return out


def alphas(en, f=None):
    """(text, outline) alpha planes (H, W), 0..1, for one subtitle."""
    f = f or _font()
    ls = wrap(en, f)
    assert len(ls) <= 2, f"3+ lines: {en!r}"
    img_t, img_o = Image.new("L", (W * SS, H * SS)), Image.new("L", (W * SS, H * SS))
    dt, do = ImageDraw.Draw(img_t), ImageDraw.Draw(img_o)
    for k, t in enumerate(ls):
        y = (H - BOTTOM - LINE_H * (len(ls) - k)) * SS
        x = (W * SS - f.getlength(t)) / 2
        do.text((x, y), t, font=f, fill=255, stroke_width=round(STROKE * SS), stroke_fill=255)
        dt.text((x, y), t, font=f, fill=255)
    a = [np.asarray(i.resize((W, H), Image.BOX), float).clip(0, 255) / 255 for i in (img_t, img_o)]
    return a[0], a[1]


def draw(pix, a_t, a_o):
    pix = pix * (1 - a_o[..., None]) + 16 * a_o[..., None]
    return np.clip(np.rint(pix * (1 - a_t[..., None]) + 240 * a_t[..., None]), 0, 255)


def redraw(data, a_t, a_o, cap):
    """New frame bytes (fitting cap) with the subtitle drawn in."""
    q0, blocks = mdec.decode(data, W, H)[:2]
    new = draw(mdec.to_pixels(q0, blocks, W, H).astype(float), a_t, a_o)
    order = mdec.mb_order(W, H)
    redo = [i for i, (mx, my) in enumerate(order) if a_o[my * 16:my * 16 + 16, mx * 16:mx * 16 + 16].max() > 0.01]
    for q in range(q0, 64):
        out = list(blocks if q == q0 else staff_str._renum(staff_str.requant(blocks, q0, q)))
        for i in redo:
            mx, my = order[i]
            bl = staff_str.rgb_blocks(new[my * 16:my * 16 + 16, mx * 16:mx * 16 + 16], q)
            if bl is None:
                break
            out[6 * i:6 * i + 6] = bl
        else:
            data = mdec.encode(q, out)
            if len(data) <= cap:
                return data
    raise ValueError("frame does not fit at any qscale")


def times(s, fr):
    """{frame: movie time in seconds} (first sector of the frame / 150)."""
    return {f: secs[0] / SECTORS_PER_S for f, (secs, _) in fr.items()}


def plan(stem, fr, s):
    """{frame: subtitle index} and the subtitle list."""
    subs = lines(stem)
    t = times(s, fr)
    out = {}
    for f in fr:
        k = next((i for i, (a, b, _) in enumerate(subs) if a <= t[f] < b), None)
        if k is not None:
            out[f] = k
    return out, subs


_S = {}


def _init(path, stem):
    s = Path(path).read_bytes()
    fr = mdec.frames(s)
    todo, subs = plan(stem, fr, s)
    f = _font()
    _S.update(fr=fr, todo=todo, al=[alphas(en, f) for _, _, en in subs])


def _job(f):
    secs, data = _S["fr"][f]
    return f, redraw(data, *_S["al"][_S["todo"][f]], len(secs) * mdec.DATA)


def build(src, stem, frames=None):
    """{frame: new frame bytes} for every frame that shows a subtitle (or only `frames`)."""
    s = Path(src).read_bytes()
    todo = plan(stem, mdec.frames(s), s)[0]
    fs = [f for f in (frames or sorted(todo)) if f in todo]
    with Pool(initializer=_init, initargs=(str(src), stem)) as pool:
        return dict(pool.map(_job, fs, chunksize=8))


def _key(src, stem):
    """Hash of everything the encoded frames depend on (not the whole of this file: CLI changes keep the cache)."""
    h = hashlib.sha1()
    for p in (SUBS / f"{stem}.tsv", FONT, Path(mdec.__file__), Path(staff_str.__file__)):
        h.update(p.read_bytes())
    for fn in (_greedy, _brk, _page, _end_cost, wrap, pages, lines, _rows, _tsv, alphas, draw, redraw, times, plan, _font, _init, _job, build):
        h.update(inspect.getsource(fn).encode())
    h.update(repr((sorted(WEAK), KEEP, sorted(TAIL), PAGE, BRK, W, H, SS, SIZE, STROKE, LINE_H, BOTTOM, MARGIN, HOLD, MIN_SHOW, SECTORS_PER_S)).encode())
    h.update(str(Path(src).stat().st_size).encode())
    return h.hexdigest()[:16]


def cached(src, stem):
    out = CACHE / f"{stem}.{_key(src, stem)}.STR"
    if not out.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        for old in CACHE.glob(f"{stem}.*.STR"):
            old.unlink()
        out.write_bytes(staff_str.write(Path(src).read_bytes(), build(src, stem)))
    return out.read_bytes()


def stems():
    return sorted(p.stem for p in SUBS.glob("*.tsv"))


def patch(path, log):
    """Overwrite a dumped STR with its subtitled copy (if gfx/fmv has its lines); log every changed sector."""
    path = Path(path)
    if path.stem not in stems():
        return
    old, new = path.read_bytes(), cached(path, path.stem)
    assert len(new) == len(old)
    rel = f"STR/{path.name}"
    for o in range(0, len(old), mdec.SECTOR):
        if old[o:o + mdec.SECTOR] != new[o:o + mdec.SECTOR]:
            assert not old[o + 2] & 4, f"{rel}: audio sector {o // mdec.SECTOR} changed"
            log(rel, o, old[o:o + mdec.SECTOR], new[o:o + mdec.SECTOR], "D18 fmv subtitles")
    path.write_bytes(new)


def batch_stems(batch):
    return sorted({r[0].split(".")[1] for r in _tsv(ROOT / f"work/tl/{batch}.tsv")})


def check(only=None):
    """Errors: a line out of time order or ending before it starts, an untranslated line, a page on screen for less
    than READ s or faster than CPS characters a second (split it with ' / ' less, or say it shorter)."""
    errs = []
    for stem in only or stems():
        prev = -1
        for n, r in enumerate(_rows(SUBS / f"{stem}.tsv"), 2):
            a, b, en = float(r["start"]), float(r["end"]), r["en"].strip()
            if a <= prev or b <= a:
                errs.append(f"{stem}.tsv:{n}: times {a}-{b} out of order")
            if not en and r["ja"].strip():
                errs.append(f"{stem}.tsv:{n}: no English")
            prev = a
        for a, b, p in lines(stem):
            if any(len(_greedy(ln, _font())) > 1 for ln in p.split("|")):     # a forced '|' line wider than the frame
                errs.append(f"{stem} {a:.2f}s: line too wide: {p}")
            if b - a < READ or len(p) / (b - a) > CPS:
                errs.append(f"{stem} {a:.2f}s: {b - a:.1f} s for {len(p)} chars: {p}")
    return errs


def _tsv(path):
    """Rows of a tab-separated file, split as is: the csv module would eat a quote that starts a field."""
    return [ln.split("\t") for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln]


def _rows(path):
    head, *body = _tsv(path)
    return [dict(zip(head, r)) for r in body]


def _write(path, rows, cols=("start", "end", "ja", "en")):
    body = [[str(r[c]) for c in cols] for r in rows]
    assert not any("\t" in v or "\n" in v for r in body for v in r)
    Path(path).write_text("".join("\t".join(r) + "\n" for r in [list(cols)] + body), encoding="utf-8")


def init(order):
    """gfx/fmv/<STEM>.tsv from work/fmv/asr (missing files only). Whisper can hold a short line through a long music
    stretch, so a line ends at most 1.5 s + 0.25 s per character after it starts."""
    SUBS.mkdir(parents=True, exist_ok=True)
    for stem in order:
        dst = SUBS / f"{stem}.tsv"
        if dst.exists():
            continue
        rows = [{"start": r["start"], "end": f"{min(float(r['end']), float(r['start']) + 1.5 + 0.25 * len(r['ja'])):.2f}",
                 "ja": r["ja"], "en": ""} for r in _rows(ROOT / f"work/fmv/asr/{stem}.tsv")]
        _write(dst, rows)
        print(stem, len(rows))


def row_id(stem, r):
    """fmv.<STEM>.<start in 1/100 s>: stable when rows are added (no two lines of a movie start together)."""
    return f"fmv.{stem}.{round(float(r['start']) * 100):05d}"


def batches(order, per, first=1, todo=False):
    """work/tl/fmvNN.tsv (translator-brief columns: id, speaker, group, limit, JP) in story order, whole movies;
    todo: only rows without English."""
    out, cur = [], []
    for stem in order:
        rows = _rows(SUBS / f"{stem}.tsv")
        cur += [(row_id(stem, r), "", f"fmv {stem} {float(r['start']):.1f}s", "fmv:2x292px", r["ja"])
                for r in rows if not (todo and r["en"])]
        if len(cur) >= per:
            out.append(cur)
            cur = []
    out += [cur] if cur else []
    for k, b in enumerate(out, first):
        (ROOT / f"work/tl/fmv{k:02d}.tsv").write_text("".join("\t".join(r) + "\n" for r in b), encoding="utf-8")
        print(f"fmv{k:02d}", len(b), "lines", b[0][0], "-", b[-1][0])


def merge(batch):
    """work/tl/<batch>.out.tsv (id, English) into gfx/fmv/<STEM>.tsv en columns; every id of the batch once."""
    ids = [r[0] for r in _tsv(ROOT / f"work/tl/{batch}.tsv")]
    en = {r[0]: r[1] for r in _tsv(ROOT / f"work/tl/{batch}.out.tsv")}
    assert set(en) == set(ids), f"missing {sorted(set(ids) - set(en))[:5]}, extra {sorted(set(en) - set(ids))[:5]}"
    bad = [i for i, t in en.items() if not t.isascii() or any(c in t for c in "…“”")]
    assert not bad, f"non-ASCII: {bad[:5]}"
    for stem in batch_stems(batch):
        rows = _rows(SUBS / f"{stem}.tsv")
        for r in rows:
            r["en"] = en.get(row_id(stem, r), r["en"])
        _write(SUBS / f"{stem}.tsv", rows)


# story order: prologue, opening (song, no speech), episode movies M<episode>, ending, the two epilogues, then the
# summon incantations SYO01-07 (battle)
ORDER = ["PRO15", "OP_A4SND", "M0115", "M0415", "M0515", "M09A15", "M09B15", "M1015", "M1315", "M1515", "M1615",
         "M1915", "M20A15", "M20B15", "M20C15", "M2115", "M2215", "M2815", "M2915", "M3015", "M3115", "M3215", "M3615",
         "M3815", "M4015", "M4115", "M42A15", "M42B15", "MEND15", "EP_A115", "EP_A215", "EP_A315", "EP_A415",
         "EP_A515", "EP_B115", "EP_B215", "EP_B315", "EP_B415", "EP_B515", "SYO01", "SYO02", "SYO03", "SYO04", "SYO05",
         "SYO06", "SYO07"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stem", nargs="?")
    ap.add_argument("--preview", default="work/fmv/preview")
    ap.add_argument("--times", default=None, help="movie seconds to shoot (default: the middle of each line)")
    ap.add_argument("--check", nargs="?", const="all", default=None, help="all movies, or only BATCH's")
    ap.add_argument("--init", action="store_true", help="gfx/fmv/*.tsv from the ASR drafts (missing files only)")
    ap.add_argument("--batches", type=int, default=0, help="write work/tl/fmvNN.tsv of about N lines each")
    ap.add_argument("--first", type=int, default=1, help="--batches: number of the first batch")
    ap.add_argument("--todo", action="store_true", help="--batches: only lines without English")
    ap.add_argument("--merge", default=None, help="merge work/tl/BATCH.out.tsv into gfx/fmv")
    a = ap.parse_args()
    if a.init:
        return init([s for s in ORDER if (ROOT / f"work/fmv/asr/{s}.tsv").exists()])
    if a.batches:
        return batches([s for s in ORDER if s in stems()], a.batches, a.first, a.todo)
    if a.merge:
        return merge(a.merge)
    if a.check:
        errs = check(None if a.check == "all" else batch_stems(a.check))
        print("\n".join(errs) or "ok")
        sys.exit(1 if errs else 0)
    out = Path(a.preview)
    for stem in [a.stem] if a.stem else stems():
        src = next(p for d in ("d1", "d2") for p in [ROOT / f"work/iso/{d}/tree/STR/{stem}.STR"] if p.exists())
        s = src.read_bytes()
        fr = mdec.frames(s)
        t = times(s, fr)
        want = ([float(x) for x in a.times.split(",")] if a.times else [(x + y) / 2 for x, y, _ in lines(stem)])
        fs = sorted({min(fr, key=lambda f: abs(t[f] - w)) for w in want})
        # no stem: every movie from its cached (= built) copy, one frame per page; else a fresh encode of fs
        new = build(src, stem, fs) if a.stem else mdec.frames(cached(src, stem))
        (out / stem).mkdir(parents=True, exist_ok=True)
        for f in fs:
            data = new[f][1] if not a.stem else new.get(f, fr[f][1])
            q, blocks = mdec.decode(data, W, H)[:2]
            Image.fromarray(mdec.to_pixels(q, blocks, W, H)).save(out / stem / f"{stem}_{f:04d}.png")
        print(f"{stem}: {len(fs)} frames -> {out / stem}")


if __name__ == "__main__":
    main()
