import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402
import gretc  # noqa: E402

RLZ = ROOT / "work/iso/d1/tree/DATA/GRETC.RLZ"


@pytest.mark.skipif(not RLZ.exists(), reason="needs a dumped disc (build.py)")
def test_gretc_images_keep_tim_layout():
    """Redrawn GRETC TIMs keep header + CLUT and size; only pixels change, and every one changes something."""
    rlz = RLZ.read_bytes()
    ents = gretc.directory(rlz)[1]
    for i, new in gfx.gretc_images(rlz).items():
        old = gretc.expand(rlz, ents[i])
        p, w, h = gfx.tim_pixels(old)
        assert len(new) == len(old) and new[:p] == old[:p], i
        assert new[p:p + w * h] != old[p:p + w * h], i
