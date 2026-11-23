import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARDS = ROOT / "tools/debug/cards"


def test_unlock_card_matches_save_py(tmp_path):
    # the committed unlock.mcd fixture is exactly sys.mcd + save.py --unlock-all, with a valid checksum
    out = tmp_path / "u.mcd"
    subprocess.run([sys.executable, str(ROOT / "tools/debug/save.py"), str(CARDS / "sys.mcd"), "--out", str(out),
                    "--unlock-all"], check=True, capture_output=True)
    new = out.read_bytes()
    assert new == (CARDS / "unlock.mcd").read_bytes()
    blk = new[0x2000:0x4000]  # GRS is block 1
    assert sum(blk[:0x1FFE]) & 0xFF == blk[0x1FFE]
    assert blk[0x244:0x276] == b"\x01" * 50 and blk[0x3A6:0x4A6] == b"\xff" * 0x100
    assert blk[0x214:0x23A] == b"\xff" * 0x26


def test_day_save_event(tmp_path):
    # day01.mcd: DAY save GRDA in block 2, event 1; --event rewrites its own field (+0x238), checksum fixed
    out = tmp_path / "d.mcd"
    p = subprocess.run([sys.executable, str(ROOT / "tools/debug/save.py"), str(CARDS / "day01.mcd"), "--file", "GRDA",
                        "--event", "5", "--out", str(out)], check=True, capture_output=True, text=True)
    assert "event 1" in p.stdout
    old, new = (CARDS / "day01.mcd").read_bytes(), out.read_bytes()
    blk = new[0x4000:0x6000]
    assert blk[0x238:0x23A] == b"\x05\x00" and sum(blk[:0x1FFE]) & 0xFF == blk[0x1FFE]
    assert [i for i in range(len(old)) if old[i] != new[i]] == [0x4238, 0x5FFE]
