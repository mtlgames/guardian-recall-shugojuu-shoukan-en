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
