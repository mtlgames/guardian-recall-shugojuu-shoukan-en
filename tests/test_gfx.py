import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import gfx  # noqa: E402
import gretc  # noqa: E402

RLZ = ROOT / "work/iso/d1/tree/DATA/GRETC.RLZ"
BATTLE = ROOT / "work/iso/d1/tree/DATA/BATTLE.BIN"


@pytest.mark.skipif(not RLZ.exists(), reason="needs a dumped disc (build.py)")
def test_gretc_images_keep_tim_layout():
    """Redrawn GRETC TIMs keep header + CLUT and size; only pixels change, and every one changes something."""
    rlz = RLZ.read_bytes()
    ents = gretc.directory(rlz)[1]
    for i, new in gfx.gretc_images(rlz, BATTLE.read_bytes()).items():
        old = gretc.expand(rlz, ents[i])
        p, w, h = gfx.tim_pixels(old) if i != gfx.SPLIT else (8 + 0x2C + 12, 128, 256)   # split.tim: 4bpp
        assert len(new) == len(old) and new[:p] == old[:p], i
        assert new[p:p + w * h] != old[p:p + w * h], i


@pytest.mark.skipif(not RLZ.exists(), reason="needs a dumped disc (build.py)")
def test_battle_labels_fit():
    """G9: every label word gets whole cells (<= 64 in all, <= 4 per label: 128 px), the lists fit their 116 bytes,
    and the pointer writes land on the 29 records' +4 words inside the list range."""
    import struct
    battle = BATTLE.read_bytes()
    cells, lists = gfx.label_layout(battle)
    assert len(cells) <= 64 and max(map(len, lists)) <= 4 and len(lists) == gfx.NLABELS
    assert [w for w, _ in gfx.label_words(battle)][:3] == ["Barbarian", "Oni", "Knight"]
    writes = gfx.label_writes(battle)
    lo, hi = gfx.LABEL_LISTS
    blob = writes[0][2]
    for (o, old, new), cl in zip(writes[1:], lists):
        p = struct.unpack("<I", new)[0]
        assert lo <= p < hi and list(blob[p - lo:p - lo + len(cl) + 1]) == cl + [0xFF]


@pytest.mark.skipif(not RLZ.exists(), reason="needs a dumped disc (build.py)")
def test_orbs_keep_layout_and_fit():
    """G17: the orb TIM keeps its size, headers and CLUTs; each word fits the orb's inner 37 px; outside pixels stay."""
    import gr_index
    import numpy as np
    import tx03
    tree = RLZ.parents[1]
    exe = next(tree.glob("SLPS_*")).read_bytes()
    d = tx03.decompress((tree / "DATA/UNN.PAK").read_bytes(), gr_index.toc(exe)[9][0] * gfx.SECTOR + gfx.ORB_REL)[0]
    new = gfx.orb_sheet(d)
    old = d[4:]
    assert len(new) == len(old) and new[:20] == old[:20] and new[27668:27680] == old[27668:27680]
    for k in range(10):
        o = 20 + 128 * k + 96
        assert new[o:o + 32] == old[o:o + 32], k                    # CLUT untouched
    assert all(gfx._orb_word(w).shape[1] <= 35 for w in gfx.ORB_WORDS)
    cb_old, cb_new = (gfx.unpack(bytes(t[20:20 + 128 * 216]), 128) for t in (old, new))
    assert (cb_old[40:] == cb_new[40:]).all() and (cb_old[:40, 160:] == cb_new[:40, 160:]).all()
    ib_old, ib_new = (gfx.unpack(bytes(t[27680:27680 + 120 * 255]), 120) for t in (old, new))
    assert (ib_old[40:] == ib_new[40:]).all() and not np.array_equal(ib_old[:40], ib_new[:40])
