from pathlib import Path

import pytest

import gr_text
import gretc
import rlz
import tx03

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "work/disc1/tree/DATA"


def test_decode_hiragana_and_codes():
    # 真由 「そう」 [01][00]: SJIS pair, half-width-as-hiragana (ｿ=0xBF, ｳ=0xB3), control codes
    assert gr_text.decode(b"\x90\x5e\x97\x52\x0a\x81\x75\xbf\xb3\x81\x76\x0a\x01\x00") == "真由\n「そう」\n[01][00]"


def test_tx03_literal_and_refs():
    # 2x2 image: raw bytes 1,2 then literal 3 then back-ref (o=0 -> previous byte) of 1 byte
    src = b"TX03" + (2).to_bytes(2, "little") + (2).to_bytes(2, "little") + b"\x01\x02" + b"\xe0\x03" + b"\x00"
    out, end = tx03.decompress(src)
    assert out[4:] == b"\x01\x02\x03\x03" and end == len(src)


@pytest.mark.skipif(not (DATA / "SUBTI.PAK").is_file(), reason="disc not extracted (work/disc1)")
def test_tx03_subti_first_card():
    out, end = tx03.decompress((DATA / "SUBTI.PAK").read_bytes(), 0)
    assert len(out) == 4 + 160 * 240 and end == 0x2065


def test_rlz_roundtrip_and_xor():
    for s in (b"", b"abc", b"\0" * 300 + b"xy\x07\x07z", bytes(range(256)) * 2):
        for esc in (7, 0, 0xFF):
            assert rlz.unpack(rlz.pack(s, esc), esc) == s
    assert rlz.unpack(b"a\x05\x00\x03b", 5) == b"a\0\0\0b"
    assert rlz.xor(b"\x00\x00", 0x80) == b"\x80\x2a"


@pytest.mark.skipif(not (DATA / "GRETC.RLZ").is_file(), reason="disc not extracted (work/disc1)")
def test_gretc_directory_and_entries():
    data = (DATA / "GRETC.RLZ").read_bytes()
    head, ents = gretc.directory(data)
    assert len(ents) == 255 and ents[0]["name"] == "tea.tim" and ents[-1]["name"] == "save.txd"
    for e in ents:
        b = gretc.expand(data, e)  # asserts the directory size
        if e["name"].endswith(".tim"):
            assert b[:4] == b"\x10\0\0\0", e["name"]
    assert "メモリーカード".encode("cp932") in gretc.expand(data, ents[-1])
