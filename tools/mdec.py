"""PS1 STR movie video frames (MDEC bitstream version 2), for re-encoding the STAFF.STR credits (G15).

dumpsxiso extracts STR files as 2336-byte form-2 sectors: 8-byte subheader, then for a video sector a 0x20-byte
header (60 01 01 80, u16 chunk, u16 chunks, u32 frame, u32 frame bytes, u16 w, u16 h, ...) and 2016 bytes of frame
data. Audio sectors (subheader submode bit 2) are left alone.

Frame = 8-byte header (u16 MDEC code count / 2 rounded up to 32... see `encode`, u16 0x3800, u16 qscale, u16 version)
+ bitstream read as little-endian u16 words, MSB first. Per macroblock (column-major, 16x16): blocks Cr Cb Y1 Y2 Y3 Y4,
each a 10-bit signed DC then AC (run, level) VLCs (MPEG-1 table B.14; escape 000001 + 6-bit run + 10-bit level) and
EOB '10'.

    python -X utf8 tools/mdec.py STR [--frames 1-50]     decode + re-encode check, prints frames that differ
"""
import struct
import sys

import numpy as np

SECTOR = 2336
MAGIC = b"\x60\x01\x01\x80"
DATA = 2016

# (run, level) -> code bits (without the sign bit)
_TABLE = """11 0 1|011 1 1|0100 0 2|0101 2 1|00101 0 3|00110 4 1|00111 3 1|000100 7 1|000101 6 1|000110 1 2|000111 5 1|
0000100 2 2|0000101 9 1|0000110 0 4|0000111 8 1|00100000 13 1|00100001 0 6|00100010 12 1|00100011 11 1|00100100 3 2|
00100101 1 3|00100110 0 5|00100111 10 1|0000001000 16 1|0000001001 5 2|0000001010 0 7|0000001011 2 3|0000001100 1 4|
0000001101 15 1|0000001110 14 1|0000001111 4 2|000000010000 0 11|000000010001 8 2|000000010010 4 3|000000010011 0 10|
000000010100 2 4|000000010101 7 2|000000010110 21 1|000000010111 20 1|000000011000 0 9|000000011001 19 1|
000000011010 18 1|000000011011 1 5|000000011100 3 3|000000011101 0 8|000000011110 6 2|000000011111 17 1|
0000000010000 10 2|0000000010001 9 2|0000000010010 5 3|0000000010011 3 4|0000000010100 2 5|0000000010101 1 7|
0000000010110 1 6|0000000010111 0 15|0000000011000 0 14|0000000011001 0 13|0000000011010 0 12|0000000011011 26 1|
0000000011100 25 1|0000000011101 24 1|0000000011110 23 1|0000000011111 22 1|00000000010000 0 31|00000000010001 0 30|
00000000010010 0 29|00000000010011 0 28|00000000010100 0 27|00000000010101 0 26|00000000010110 0 25|
00000000010111 0 24|00000000011000 0 23|00000000011001 0 22|00000000011010 0 21|00000000011011 0 20|
00000000011100 0 19|00000000011101 0 18|00000000011110 0 17|00000000011111 0 16|000000000010000 0 40|
000000000010001 0 39|000000000010010 0 38|000000000010011 0 37|000000000010100 0 36|000000000010101 0 35|
000000000010110 0 34|000000000010111 0 33|000000000011000 0 32|000000000011001 1 14|000000000011010 1 13|
000000000011011 1 12|000000000011100 1 11|000000000011101 1 10|000000000011110 1 9|000000000011111 1 8|
0000000000010000 1 18|0000000000010001 1 17|0000000000010010 1 16|0000000000010011 1 15|0000000000010100 6 3|
0000000000010101 16 2|0000000000010110 15 2|0000000000010111 14 2|0000000000011000 13 2|0000000000011001 12 2|
0000000000011010 11 2|0000000000011011 31 1|0000000000011100 30 1|0000000000011101 29 1|0000000000011110 28 1|
0000000000011111 27 1"""
VLC = {}
for _e in _TABLE.replace("\n", "").split("|"):
    _c, _r, _l = _e.split()
    VLC[(int(_r), int(_l))] = _c
DECODE = {c: rl for rl, c in VLC.items()}
MAXLEN = max(map(len, DECODE))


def frames(s):
    """{frame number: (sector indices in order, frame bytes)} for every video frame of an STR (2336-byte sectors)."""
    out = {}
    for i in range(len(s) // SECTOR):
        o = i * SECTOR
        if s[o + 2] & 4 or s[o + 8:o + 12] != MAGIC:
            continue
        chunk, nchunks, frame, size = struct.unpack_from("<HHII", s, o + 12)
        secs = out.setdefault(frame, ([], size, nchunks))[0]
        assert chunk == len(secs), (frame, chunk)
        secs.append(i)
    return {f: (secs, b"".join(s[i * SECTOR + 0x28:i * SECTOR + 0x28 + DATA] for i in secs)[:size])
            for f, (secs, size, n) in out.items()}


class Bits:
    def __init__(self, data):
        n = len(data) // 2
        words = struct.unpack_from(f"<{n}H", data)
        self.s = "".join(f"{w:016b}" for w in words)
        self.p = 0

    def read(self, n):
        v = self.s[self.p:self.p + n]
        self.p += n
        return v


def _signed(v, n):
    v = int(v, 2)
    return v - (1 << n) if v & (1 << (n - 1)) else v


def decode(data, w=320, h=240):
    """(qscale, blocks): blocks = [(dc, [(run, level), ...])] in stream order, 6 per macroblock."""
    count, magic, q, ver = struct.unpack_from("<HHHH", data)
    assert magic == 0x3800 and ver == 2, (hex(magic), ver)
    b = Bits(data[8:])
    blocks = []
    for _ in range((w + 15) // 16 * ((h + 15) // 16) * 6):
        dc = _signed(b.read(10), 10)
        ac = []
        while True:
            if b.s.startswith("10", b.p):
                b.p += 2
                break
            if b.s.startswith("000001", b.p):
                b.p += 6
                ac.append((int(b.read(6), 2), _signed(b.read(10), 10)))
                continue
            for n in range(2, MAXLEN + 1):
                rl = DECODE.get(b.s[b.p:b.p + n])
                if rl:
                    b.p += n
                    ac.append((rl[0], -rl[1] if b.read(1) == "1" else rl[1]))
                    break
            else:
                raise ValueError(f"bad VLC at bit {b.p}")
        blocks.append((dc, ac))
    return q, blocks, b.p, count


def encode(q, blocks, end=True):
    """Frame bytes for (qscale, blocks): header + bitstream (+ end code), padded to 32 bits. An AC item
    (run, level, True) is written as an escape code even when a VLC exists (bit padding, see block_bits)."""
    out, codes = [], 0
    for dc, ac in blocks:
        out.append(f"{dc & 0x3FF:010b}")
        for r, l, *esc in ac:
            c = None if esc else VLC.get((r, abs(l)))
            out.append(c + ("1" if l < 0 else "0") if c else f"000001{r:06b}{l & 0x3FF:010b}")
        out.append("10")
        codes += len(ac) + 2
    if end:
        out.append("0111111111")
    s = "".join(out)
    s += "0" * (-len(s) % 32)
    words = [int(s[i:i + 16], 2) for i in range(0, len(s), 16)]
    head = struct.pack("<HHHH", (codes + 63) // 64 * 32, 0x3800, q, 2)
    return head + struct.pack(f"<{len(words)}H", *words)


def block_bits(block):
    """Bits encode() spends on one block: DC + each AC code (+ sign) or 22-bit escape + end of block."""
    dc, ac = block
    return 12 + sum(22 if esc or (r, abs(l)) not in VLC else len(VLC[(r, abs(l))]) + 1 for r, l, *esc in ac)


QUANT = np.array([2, 16, 19, 22, 26, 27, 29, 34, 16, 16, 22, 24, 27, 29, 34, 37, 19, 22, 26, 27, 29, 34, 34, 38,
                  22, 22, 26, 27, 29, 34, 37, 40, 22, 26, 27, 29, 32, 35, 40, 48, 26, 27, 29, 32, 35, 40, 48, 58,
                  26, 27, 29, 34, 38, 46, 56, 69, 27, 29, 35, 38, 46, 56, 69, 83], float).reshape(8, 8)
ZIGZAG = sorted(((y, x) for y in range(8) for x in range(8)),
                key=lambda p: (p[0] + p[1], p[0] if (p[0] + p[1]) % 2 else p[1]))   # scan order -> (row, col)
_C = np.array([[np.sqrt((1 if u else 0.5) / 4) * np.cos((2 * x + 1) * u * np.pi / 16) for x in range(8)]
               for u in range(8)])                                                # orthonormal DCT-II basis


def block_coefs(dc, ac, q):
    """Dequantised 8x8 DCT coefficients of one block."""
    F = np.zeros((8, 8))
    F[0, 0] = dc * QUANT[0, 0]
    k = 0
    for r, l in ac:
        k += r + 1
        y, x = ZIGZAG[k]
        F[y, x] = l * q * QUANT[y, x] / 8
    return F


def block_levels(pix, q, dc_only=False):
    """(dc, [(run, level)]) for an 8x8 block of signed samples (-128..127): forward DCT + PSX quantisation."""
    F = _C @ pix @ _C.T
    dc = int(np.clip(round(F[0, 0] / QUANT[0, 0]), -512, 511))
    ac, run = [], 0
    for y, x in ZIGZAG[1:]:
        l = 0 if dc_only else int(np.clip(round(F[y, x] * 8 / (q * QUANT[y, x])), -511, 511))
        if l:
            ac.append((run, l))
            run = 0
        else:
            run += 1
    return dc, ac


def mb_order(w=320, h=240):
    """(mx, my) of each macroblock in stream order (column-major)."""
    return [(mx, my) for mx in range((w + 15) // 16) for my in range((h + 15) // 16)]


def to_pixels(q, blocks, w=320, h=240):
    """RGB uint8 (h, w, 3) of a decoded frame."""
    Y = np.zeros(((h + 15) // 16 * 16, (w + 15) // 16 * 16))
    Cr, Cb = np.zeros((Y.shape[0] // 2, Y.shape[1] // 2)), np.zeros((Y.shape[0] // 2, Y.shape[1] // 2))
    for i, (mx, my) in enumerate(mb_order(w, h)):
        b = [_C.T @ block_coefs(*blocks[6 * i + j], q) @ _C for j in range(6)]
        Cr[my * 8:my * 8 + 8, mx * 8:mx * 8 + 8] = b[0]
        Cb[my * 8:my * 8 + 8, mx * 8:mx * 8 + 8] = b[1]
        for j, (dy, dx) in enumerate(((0, 0), (0, 8), (8, 0), (8, 8))):
            Y[my * 16 + dy:my * 16 + dy + 8, mx * 16 + dx:mx * 16 + dx + 8] = b[2 + j]
    cr, cb = (np.repeat(np.repeat(c, 2, 0), 2, 1) for c in (Cr, Cb))
    Y += 128
    rgb = np.stack([Y + 1.402 * cr, Y - 0.3437 * cb - 0.7143 * cr, Y + 1.772 * cb], -1)
    return np.clip(np.rint(rgb), 0, 255).astype(np.uint8)[:h, :w]


def gray_mb(lum, q):
    """6 blocks (Cr, Cb, Y1-Y4) for a 16x16 greyscale patch (0..255): neutral chroma."""
    out = [(0, []), (0, [])]
    for dy, dx in ((0, 0), (0, 8), (8, 0), (8, 8)):
        out.append(block_levels(lum[dy:dy + 8, dx:dx + 8].astype(float) - 128, q))
    return out


if __name__ == "__main__":
    s = open(sys.argv[1], "rb").read()
    fr = frames(s)
    lo, hi = 1, max(fr)
    if "--frames" in sys.argv:
        lo, hi = map(int, sys.argv[sys.argv.index("--frames") + 1].split("-"))
    bad = 0
    for f in range(lo, hi + 1):
        data = fr[f][1]
        q, blocks, bits, count = decode(data)
        new = encode(q, blocks)
        if new != data[:len(new)] or any(data[len(new):]):
            bad += 1
            if bad <= 5:
                k = next((i for i in range(min(len(new), len(data))) if new[i] != data[i]), None)
                print(f"frame {f}: differs at byte {k} (new {len(new)}, old {len(data)}, header {count}, "
                      f"bits {bits}, tail {data[len(new):len(new) + 8].hex()})")
    print(f"{hi - lo + 1} frames, {bad} differ")
