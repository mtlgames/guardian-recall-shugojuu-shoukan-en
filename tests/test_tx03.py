import random
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import tx03  # noqa: E402


def roundtrip(w, h, data):
    s = tx03.compress(w, h, data)
    out, end = tx03.decompress(s)
    assert end == len(s)
    assert out == struct.pack("<hh", w, h) + bytes(data)
    return s


def test_roundtrip_synthetic():
    rnd = random.Random(1)
    w, h = 40, 30
    rows = [bytes(rnd.choice((0, 0xFF, 0x0F)) for _ in range(w)) for _ in range(4)]
    data = b"".join(rows[rnd.randrange(4)] for _ in range(h))
    roundtrip(w, h, data)
    roundtrip(w, h, bytes(rnd.randrange(256) for _ in range(w * h)))   # incompressible: literals only
    assert len(roundtrip(160, 240, bytes(160 * 240))) < 400            # blank card


def test_roundtrip_card():
    """A real title card recompresses no larger than ~5% over the original stream."""
    pak = Path(__file__).resolve().parents[1] / "work/disc1/tree/DATA/SUBTI.PAK"
    if not pak.exists():
        return
    d = pak.read_bytes()
    out, end = tx03.decompress(d, 0x2800)
    w, h = struct.unpack_from("<hh", out)
    s = roundtrip(w, h, out[4:])
    assert len(s) <= (end - 0x2800) * 1.05, (len(s), end - 0x2800)
