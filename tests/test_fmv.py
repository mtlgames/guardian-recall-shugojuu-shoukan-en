import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fmv_subs  # noqa: E402
import mdec  # noqa: E402


def test_fmv_lines():
    """gfx/fmv: every movie's lines are translated, in time order, ASCII, at most 2 display lines."""
    assert fmv_subs.check() == []
    for stem in fmv_subs.stems():
        for a, b, en in fmv_subs.lines(stem):
            assert en.isascii() and b > a, (stem, a, en)


def test_alphas_inside_frame():
    """The lettering sits in the bottom rows, clear of the frame edges, outline around the text."""
    a_t, a_o = fmv_subs.alphas("Now that I am here, I won't let you do as you please! Long enough to wrap twice.")
    rows = a_o.max(1).nonzero()[0]
    assert rows.min() > fmv_subs.H - 40 and rows.max() < fmv_subs.H - 1
    assert not a_o[:, :2].any() and not a_o[:, -2:].any()
    assert (a_o >= a_t - 0.01).all()


@pytest.mark.slow
@pytest.mark.skipif(not (ROOT / "work/iso/d1/tree/STR/M0115.STR").exists(), reason="needs dumped disc 1 (build.py)")
def test_redraw_fits_and_decodes():
    """A subtitled frame fits its sectors and decodes with white text where the subtitle is."""
    fr = mdec.frames((ROOT / "work/iso/d1/tree/STR/M0115.STR").read_bytes())
    secs, data = fr[600]
    a_t, a_o = fmv_subs.alphas("A Guardian?")
    new = fmv_subs.redraw(data, a_t, a_o, len(secs) * mdec.DATA)
    pix = mdec.to_pixels(*mdec.decode(new, fmv_subs.W, fmv_subs.H)[:2], fmv_subs.W, fmv_subs.H).mean(-1)
    assert pix[a_t > 0.9].mean() > 200 and len(new) <= len(secs) * mdec.DATA
