import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import font  # noqa: E402
import windows  # noqa: E402

G = font.load_glyphs()


def test_wrap_breaks_at_spaces_and_keeps_markup():
    px = font.width("aaa bbb", G)
    assert windows.wrap("aaa bbb ccc", px, G) == "aaa bbb&n()ccc"
    assert windows.wrap("&c(2)aaa&c(0) bbb ccc", px, G) == "&c(2)aaa&c(0) bbb&n()ccc"
    assert windows.wrap("aaa&n()bbb ccc", px, G) == "aaa&n()bbb ccc"
    for line in windows.wrap("The quick brown fox jumps over the lazy dog " * 5, 100, G).split("&n()"):
        assert font.width(line, G) <= 100


def test_pitch_and_narrow_first_lines():
    jp = "&g(14,0)&s(200,20)&c(7)名&s(230,206)&c(7)&g(14,0)声&s(165,40)&c(7)&g(16,8)&h()&f(32,6)NATIVE&h()"
    v = windows.variant({"id": "cf.0040", "jp": jp})
    name = "Chinami Nishimura"  # 85 px at pitch 13: one px less per glyph at pitch 12
    en = "&g(13,0)&s(200,20)&c(7)Miyuki&s(230,206)&c(7)&g({p},0)" + name + "&s(165,40)&g(16,8)&h()NATIVE&h()"
    assert windows.lint({"id": "cf.0040", "jp": jp, "en": en.format(p=12)}, v, G) == []
    assert windows.lint({"id": "cf.0040", "jp": jp, "en": en.format(p=13)}, v, G) == [f"85 px > 69: '{name}'"]
    assert windows.wrap("aaa bbb ccc", 1000, G, first=(font.width("aaa", G),)) == "aaa&n()bbb ccc"


def test_adv_and_dictionary_list():
    # guardian page: +1 px per glyph (pitch 14), so a line that fits by width alone can still break
    px = font.width("aaa bbb", G)
    assert windows.wrap("aaa bbb", px, G) == "aaa bbb"
    assert windows.wrap("aaa bbb", px, G, adv=1) == "aaa&n()bbb"
    gd = windows.variant({"id": "gd.0010", "jp": "&s(64,20)&g(14,32)x"})
    assert gd["name"] == "guardian page" and gd["adv"] == 1
    # dictionary headings in the list are one row (never wrapped); pages wrap at 100
    assert windows.variant({"id": "dic.0186", "jp": "東京第二国際空港"})["name"] == "dictionary list"
    assert windows.variant({"id": "dic.0187", "jp": "東京&n()&n()本文"})["name"] == "dictionary entry"


def test_scenario_lint_counts_lines_after_the_name():
    v = windows.VARIANTS[0]
    s = {"id": "g23.00.000", "jp": "名\n「あ\n　い」\n{wait}", "en": "Name\n\"One\ntwo\nthree\"{wait}"}
    assert windows.lint(s, v, G) == []
    s["en"] = "Name\none\ntwo\nthree\nfour{wait}"
    assert windows.lint(s, v, G) == ["4 lines > 3"]


def test_in_place_records_get_a_byte_budget():
    v = windows.variant({"id": "exe.00824", "jp": "ファイル"})
    s = {"id": "exe.00824", "jp": "ファイル", "room": 8, "en": "File"}
    assert windows.lint(s, v, G) == []
    s["en"] = "Filename"
    assert windows.lint(s, v, G) == ["8 bytes > 7 in place"]
    assert windows.variant({"id": "day.0200", "jp": "あ"})["name"] == "txd"  # 4-digit txd ids, not DAY.BIN strings
    assert windows.variant({"id": "day.0600", "jp": "あ"})["name"] == "day chapter label"


def test_exe_floor_is_the_japanese_width():
    s = {"id": "exe.00900", "jp": "暴走警告", "room": 99, "en": "Rampage alert!"}
    v = windows.variant(s)
    assert v["px"] == "jp" and windows.segments(v, s["en"], s["jp"]) == [(s["en"], 52)]
    assert windows.lint(s, v, G) == [f"{font.width(s['en'], G)} px > 52: 'Rampage alert!'"]


def test_txd_segments_get_right_minus_x():
    jp = "&f(32,32)&s(116,26)&c(0)天"
    v = windows.variant({"id": "day.0000", "jp": jp})
    assert v["name"] == "diary page"
    segs = windows.segments(v, "&f(32,32)&s(116,26)Ch. 1&s(0,43)&e()Title&d()&s(165,65)Miyuki&s(40,120)Body")
    assert [px for _, px in segs] == [233, [157], [233], [108], [194, 194, 233]]  # body: LOAD button on lines 1-2
    s = {"id": "day.0000", "jp": jp, "en": "&s(165,65)" + "M" * 40}
    assert windows.lint(s, v, G)[0].endswith("px > 108: '" + "M" * 40 + "'")


def test_wrap_txd_per_segment_and_px():
    diary = windows.VARIANTS[[v["name"] for v in windows.VARIANTS].index("diary page")]
    long = " ".join(["word"] * 30)
    out = windows.wrap_txd(diary, "&s(165,65)&c(7)Name&s(40,120)&c(0)" + long, G)
    head, body = out.split("&s(40,120)")
    assert "&n()" not in head and body.count("&n()") >= 2
    assert all(font.width(windows.MARKUP.sub("", x), G) <= 233 for x in body.split("&n()"))
    dic = windows.variant({"id": "dic.0001", "jp": "x&n()"})
    assert all(font.width(windows.MARKUP.sub("", x), G) <= 100 for x in windows.wrap_txd(dic, long, G).split("&n()"))


def test_save_label_pair_fits():
    # DAY save list, stages < 20: "%-6s %-6s " = Sky label + Earth label on one 180 px row (docs/windows.md)
    en = {}
    for s in windows.records():
        if s["id"].startswith("save.") and s.get("en") and s["jp"][:2] in ("天の", "地の"):
            en.setdefault(s["jp"][:2], []).append(font.width(s["en"], G))
    if en:
        assert max(en["天の"]) + font.width(" ", G) + max(en["地の"]) <= 180


def test_every_en_fits():
    assert windows.main([]) == 0
