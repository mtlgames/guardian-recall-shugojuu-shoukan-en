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
    assert windows.variant({"id": "day.0000", "jp": "あ"})["name"] == "txd"  # 4-digit txd ids, not DAY.BIN strings


def test_every_en_fits():
    assert windows.main([]) == 0
