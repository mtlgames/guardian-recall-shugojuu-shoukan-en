import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import mdec  # noqa: E402
import staff_str  # noqa: E402


def test_staff_lines():
    """gfx/staff.tsv: same display-line count in jp and en (asserted in lines()), no draft markers, every redrawn line
    fits the 160-px column without squeezing below 0.75."""
    ls = staff_str.lines()
    assert len(ls) == 205
    f, fc = staff_str._font(), staff_str._font(staff_str.CAP - 1)
    csq = staff_str.cast_squeeze(ls, fc)
    assert csq >= 0.75
    for kind, jp, en in ls:
        assert "?" not in en and "(glossary)" not in en, en
        if jp != en:
            alpha, sq = staff_str.line_alpha(kind, en, f, fc, csq)
            assert sq >= 0.75, en
            assert alpha.max() > 0.9 and not alpha[:, 0].any() and not alpha[:, -1].any(), en


def test_rgb_blocks_roundtrip():
    """Forward path: a white glyph-like patch on black survives encode -> decode within a few levels."""
    patch = np.zeros((16, 16, 3))
    patch[4:12, 3:5] = 255
    patch[4:6, 3:12] = 255
    for q in (1, 2, 4):
        bl = staff_str.rgb_blocks(patch, q)
        blocks = bl + [(0, [])] * (6 * 299)
        pix = mdec.to_pixels(*mdec.decode(mdec.encode(q, blocks))[:2])[:16, :16].mean(-1)
        assert np.abs(pix - patch.mean(-1)).max() < 4 * q + 4


@pytest.mark.slow
@pytest.mark.skipif(not staff_str.staff_strip.STR.exists(), reason="needs dumped disc 2 (build.py)")
def test_staff_bands_match_lines():
    """Every staff.tsv display line has its own ink band in the stitched strip."""
    strip = staff_str.staff_strip.scan()[1]
    assert len(staff_str.bands(strip)) == len(staff_str.lines())
