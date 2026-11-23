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
    assert windows.variant({"id": "day.0600", "jp": "あ"})["name"] == "txd"  # 4-digit txd ids, not DAY.BIN strings


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
    assert [px for _, px in segs] == [233, 157, 233, 108, 233]
    s = {"id": "day.0000", "jp": jp, "en": "&s(165,65)" + "M" * 40}
    assert windows.lint(s, v, G)[0].endswith("px > 108: '" + "M" * 40 + "'")


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
