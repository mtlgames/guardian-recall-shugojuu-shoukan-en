"""Phase 4 extraction: script/ re-encodes to the original bytes, containers repack byte-identical, ranges covered."""
import json
import re
from pathlib import Path

import pytest

import extract
import gretc
import script_io as S

ROOT = Path(__file__).resolve().parents[1]
TREE = ROOT / "work/iso/d1/tree"
need_dump = pytest.mark.skipif(not (TREE / "DATA/UNN.PAK").is_file(), reason="no dump (python build.py --identity)")


def docs(sub):
    return {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((ROOT / "script" / sub).glob("*.json"))}


def test_tables_roundtrip_both_kana_forms():
    for b in (b"\xbf\xb3\xb0", b"\xbf\xb3\x81\x5b", "そうー".encode("cp932")):  # single kana + either ー; SJIS
        t = S.rec(b)
        assert t["jp"] == "そうー" and S.enc_jp(t) == b
    mixed = b"\xb0\x81\x5b"
    assert "[" in S.rec(mixed)["jp"] and S.enc_jp(S.rec(mixed)) == mixed  # both ー forms: escaped, still exact


def test_records_have_unique_ids_and_en_field():
    seen = set()
    for p in (ROOT / "script").glob("*/*.json"):
        for s in json.loads(p.read_text(encoding="utf-8"))["strings"]:
            assert s["id"] not in seen and "en" in s, s["id"]
            seen.add(s["id"])
    assert len(seen) > 7000


@pytest.fixture(scope="module")
def disc():
    exe = (TREE / "SLPS_012.97").read_bytes()
    return exe, (TREE / "DATA/UNN.PAK").read_bytes(), (TREE / "DATA/GRETC.RLZ").read_bytes()


@need_dump
def test_unn_blocks_and_pak_rebuild_identical(disc):
    exe, unn, _ = disc
    groups = S.unn_groups(exe, unn)
    built = {}
    for g, sub in ((23, "scenario"), (13, "battle")):
        d = docs(sub)
        built[g] = []
        for i, orig in enumerate(groups[g]):
            if (g, i) in S.NONTEXT:
                assert f"{i:02d}" not in d
                built[g].append(orig)
                continue
            b = S.build_slots(d[f"{i:02d}"])
            assert b == orig, (g, i)
            built[g].append(b)
    assert S.unn_repack(exe, unn, built) == (exe, unn)


@need_dump
def test_gretc_txd_evd_rebuild_identical(disc):
    _, _, rlz = disc
    ents = S.gretc_entries(rlz)
    txd, evd = docs("txd"), docs("evd")
    new = {}
    for i, e in enumerate(ents):
        name = e["name"].rsplit(".", 1)[0]
        plain = gretc.expand(rlz, e)
        if e["group"] == "txd":
            new[i] = S.build_slots(txd.pop(name))
            assert new[i] == plain, name
        elif name in evd:
            for s in evd.pop(name)["strings"]:
                b = S.enc_jp(s) + b"\0"
                assert plain[s["off"] - 3] == 0x34 and plain[s["off"] - 1] == len(b) and plain[s["off"]:s["off"] + len(b)] == b
            new[i] = plain
    assert not txd and not evd, "script files with no container"
    assert S.gretc_repack(rlz, new) == rlz


@need_dump
def test_evd_every_japanese_run_is_a_unit_name(disc):
    """No Japanese in evd scripts outside op 0x34 names (single kana bytes there are operands)."""
    rlz = disc[2]
    for e in S.gretc_entries(rlz):
        if e["group"] == "evd":
            d = gretc.expand(rlz, e)
            ends = {s["off"] + len(S.enc_jp(s)) for s in S.parse_evd(d)}
            for m in re.finditer(rb"(?:[\x81-\x9f\xe0-\xef][\x40-\x7e\x80-\xfc]|[\xa1-\xdf]){2,}\x00", d):
                assert m.end() - 1 in ends, (e["name"], hex(m.start()))


@need_dump
def test_exe_strings_exact_and_ranges_covered():
    d = docs("exe")
    for key, (f, base, ranges) in S.IMAGES.items():
        img = (TREE / f).read_bytes()
        spans = []
        for s in d[key]["strings"]:
            b = S.enc_jp(s)
            o = s["off"]
            assert img[o:o + len(b)] == b and not any(img[o + len(b):o + s["room"]]), s["id"]
            spans.append((o, o + len(b)))
        spans.sort()
        assert all(a[1] < b[0] for a, b in zip(spans, spans[1:])), f"{key}: overlapping strings"
        # coverage: every NUL-ended run of valid text holding Japanese inside a range ends in a record
        ends = {e for _, e in spans}
        for a, b in ranges:
            for m in re.finditer(rb"[^\x00]+", img[a:b]):
                r = m.group()
                if S.TEXT_RUN.fullmatch(r) and S.HAS_JP.search(r):
                    assert a + m.end() in ends, f"{key} {a + m.start():#x} {r[:20]!r} not extracted"


@need_dump
def test_no_referenced_japanese_outside_ranges():
    """A word or lui pair in the EXE or any code overlay pointing at a Japanese string no range holds (phase-7
    review: ACTION/HEN/BATTLE/DAY strings sat just past their range end)."""
    import jp_refs
    new = [h[:3] for h in jp_refs.hits(TREE) if (h[0], h[1]) not in jp_refs.KNOWN]
    assert not new, new


@need_dump
def test_script_matches_disc():
    """script/ jp text and layout equal a fresh extraction (catches hand edits of jp or layout fields)."""
    for rel, doc in extract.files(TREE):
        cur = json.loads((ROOT / "script" / rel).read_text(encoding="utf-8"))
        strip = lambda ss: [{k: v for k, v in s.items() if k not in extract.KEEP} for s in ss]  # noqa: E731
        assert strip(cur["strings"]) == strip(doc["strings"]), rel
