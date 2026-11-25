import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fmv_subs  # noqa: E402
import mdec  # noqa: E402
import staff_str  # noqa: E402


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


def test_pad_keeps_picture_and_aligns():
    """_pad adds bits (escape rewrites, zero-level escapes) to any residue mod 16 without changing the decoded
    coefficients; _dead drops small levels keeping positions."""
    import numpy as np
    blocks = [(5, [(0, 3), (2, -1), (0, 1)]), (-2, [(1, 2)]), (0, []), (0, []), (7, [(0, 1)]), (0, [])]
    want = [mdec.block_coefs(*b, 8) for b in blocks]
    base = sum(map(mdec.block_bits, blocks))
    for p in range(1, 16):
        seg = list(blocks)
        assert staff_str.pad(seg, p)
        assert (sum(map(mdec.block_bits, seg)) - base) % 16 == p
        q, dec = mdec.decode(mdec.encode(8, seg * 190), 304, 160)[:2]
        assert all(np.array_equal(mdec.block_coefs(*d, 8), w) for d, w in zip(dec[:6], want))
    assert staff_str.dead((1, [(0, 1), (2, 5), (0, -2)]), 2) == (1, [(3, 5)])


def test_sync_snaps_to_voice():
    """fmv_sync.sync: a start in silence moves to the voice onset, ends never shrink, a short line before the next
    one keeps reading time, '-' rows are not moved."""
    import numpy as np
    import fmv_sync
    sr = fmv_sync.SR
    pcm = np.zeros(sr * 10, np.float32)
    pcm[int(1.4 * sr):int(3 * sr)] = 0.3                # voice 1.4-3.0 (Whisper said 1.0)
    pcm[int(4.5 * sr):int(5 * sr)] = 0.3                # short line voiced 4.5-5.0, next line at 4.8
    pcm[int(6.5 * sr):int(7 * sr)] = 0.3
    rows = [{"start": "1.00", "end": "3.20", "ja": "あ", "en": "Hello there."},
            {"start": "3.10", "end": "3.60", "ja": "い", "en": "-"},       # not shown: no cap on the line before
            {"start": "4.30", "end": "4.80", "ja": "う", "en": "You and me."},
            {"start": "4.80", "end": "5.50", "ja": "え", "en": "Hi."},
            {"start": "6.00", "end": "7.00", "ja": "お", "en": "-"}]
    new = fmv_sync.sync(rows, [(1.4, 3.0), (4.5, 5.0), (6.5, 7.0)], pcm, {})
    assert new[0] == (1.4, 3.2) and new[1] == (3.1, 3.6) and new[4] == (6.0, 7.0)
    assert new[2] == (4.38, 4.8)                        # leads its voice: 11 chars need 0.37 s before 4.8
    assert new[3] == (4.8, 5.5)
