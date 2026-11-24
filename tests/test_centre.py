"""insert.centre_pad: EXE messages centred with leading full-width spaces keep their centre in English;
strings_tsv hashes what the build writes."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import font  # noqa: E402
import insert  # noqa: E402
import script_io  # noqa: E402
import strings_tsv  # noqa: E402


def test_saved_centred():
    s = {"id": "action.00d54", "jp": "　　セーブしました", "en": "Saved"}
    text = script_io.dec(insert.centre_pad(s, script_io.enc(s["en"])))[0]
    assert text.endswith("Saved")
    centre = font.width(text[:-5]) + font.width("Saved") / 2
    assert abs(centre - (26 + 7 * 13 / 2)) <= 2  # JP centre: 2 spaces + 7 glyphs


def test_left_aligned_and_printf_untouched():
    for jp in ("メモリーカードが差されていません　", "　「%s」をかけますか？"):
        s = {"id": "x", "jp": jp, "en": "Text"}
        assert insert.centre_pad(s, b"Text") == b"Text"


def test_fnv():
    assert strings_tsv.fnv32(b"") == 0x811C9DC5 and strings_tsv.fnv32(b"foobar") == 0xBF9CF968
