import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import mdec  # noqa: E402

STAFF = ROOT / "work/iso/d2/tree/STR/STAFF.STR"


@pytest.mark.skipif(not STAFF.exists(), reason="needs dumped disc 2 (build.py)")
def test_staff_frames_roundtrip():
    """MDEC v2 decode -> encode gives the original frame bytes (zero padding after); full run: tools/mdec.py STR."""
    fr = mdec.frames(STAFF.read_bytes())
    assert len(fr) == 4797
    for f in (1, 300, 2000, 4500):
        data = fr[f][1]
        new = mdec.encode(*mdec.decode(data)[:2])
        assert new == data[:len(new)] and not any(data[len(new):]), f
