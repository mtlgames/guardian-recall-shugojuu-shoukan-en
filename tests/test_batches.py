"""tools/batches.py: shipped English passes the text lint; scenario English gets its speaker line and wraps."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import batches  # noqa: E402
import font  # noqa: E402


def test_shipped_english_lint_clean():
    assert batches.main(["check"]) == 0


def test_printf_conversions_must_match():
    e = {"id": "exe.x", "jp": "残り%dターン"}
    assert any("printf" in p for p in batches.problems(e, "Turns left", []))
    assert not any("printf" in p for p in batches.problems(e, "%-3d turns left", []))
    assert not any("printf" in p for p in batches.problems({"id": "g13.03.000", "jp": "１００％"}, "100% of", []))


def test_prepare_scenario_adds_speaker_wraps_and_pages():
    e = {"id": "g23.01.001", "jp": "富楼那\n「は、あ\n　い」\n{wait}「う」\n{wait}"}
    long = '"' + " ".join(["word"] * 60) + '"'
    out = batches.prepare(e, long + "{wait}" + '"End."')
    assert out.startswith("Furuna\n") and out.endswith('\n{wait}"End."\n{wait}')
    pages = out[len("Furuna\n"):].split("{wait}")
    for p in pages[:-1]:
        lines = [x for x in p.split("\n") if x]
        assert 1 <= len(lines) <= 3
        assert all(font.width(x, batches.GLYPHS) <= 224 for x in lines)


def test_prepare_keeps_forced_break_and_unnamed():
    e = {"id": "g23.01.149", "jp": "美由紀\n「あ」\n「い」\n{wait}"}
    assert batches.prepare(e, '"A"\\n"B"') == 'Miyuki\n"A"\n"B"\n{wait}'
    e = {"id": "g23.01.031", "jp": "　真由・・・\n{wait}"}
    assert batches.prepare(e, "Mayu...") == "Mayu...\n{wait}"
