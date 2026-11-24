"""tx03.py: the game's "TX03" compression (EXE 0x8005D5DC), used for images, font maps and other resources.

Stream: b"TX03", s16 w, s16 h (bytes per row, rows), then 2 raw bytes, then commands until w*h bytes are out.
Output = s16 w, s16 h, w*h data bytes (what the game writes). Commands (n = count field, copy n+1 bytes):
  111nnnnn            literal: n+1 bytes follow
  110ooonn [n8]       copy from out[pos - 4w + o - 4]   (n==3: next byte is n; n==0xFF copies nothing)
  00ooonnn [n8]       copy from out[pos - o - 1]        (n==7: next byte is n)
  01ooonnn [n8]       copy from out[pos - w + o - 4]
  10ooonnn [n8]       copy from out[pos - 2w + o - 4]
Positions count the 4-byte header, as the game's loop does (it starts at 6 and stops at w*h + 4).
CLI: python tools/tx03.py FILE OFFSET -> prints w, h, compressed size.
"""
import struct
import sys


def decompress(src, off=0):
    """Return (out, end): out = header + data (bytes), end = offset just past the stream in src."""
    if src[off:off + 4] != b"TX03":
        raise ValueError(f"no TX03 at {off:#x}")
    i = off + 4
    w, h = struct.unpack_from("<hh", src, i)
    out = bytearray(src[i:i + 6])
    i += 6
    end = w * h + 4
    while len(out) < end:
        c = src[i]
        i += 1
        top3 = c & 0xE0
        if top3 == 0xE0:
            n = c & 0x1F
            out += src[i:i + n + 1]
            i += n + 1
            continue
        if top3 == 0xC0:
            o, n = (c >> 2) & 7, c & 3
            if n == 3:
                n, i = src[i], i + 1
            ref = len(out) - 4 - 4 * w + o
        else:
            o, n = (c >> 3) & 7, c & 7
            if n == 7:
                n, i = src[i], i + 1
            top2 = c & 0xC0
            ref = len(out) - (o + 1) if top2 == 0 else len(out) - 4 - (w if top2 == 0x40 else 2 * w) + o
        if n == 0xFF:
            continue
        for _ in range(n + 1):
            out.append(out[ref])
            ref += 1
    return bytes(out[:end]), i


def compress(w, h, data):
    """TX03 stream for w*h data bytes (w = bytes per row). Greedy longest match over all copy forms; a copy beats a
    literal even at length 1 (1 byte vs 2). decompress(compress(...)) == header + data (tests/test_tx03.py)."""
    assert len(data) == w * h and w * h >= 2
    t = struct.pack("<hh", w, h) + bytes(data)   # target, positions as the decoder counts them
    end = len(t)
    cands = ([(0x00 | o << 3, 7, -(o + 1)) for o in range(8)]
             + [(0x40 | o << 3, 7, -4 - w + o) for o in range(8)]
             + [(0x80 | o << 3, 7, -4 - 2 * w + o) for o in range(8)]
             + [(0xC0 | o << 2, 3, -4 - 4 * w + o) for o in range(8)])
    out = bytearray(b"TX03" + t[:6])
    lit = bytearray()

    def flush():
        for k in range(0, len(lit), 32):
            run = lit[k:k + 32]
            out.append(0xE0 | (len(run) - 1))
            out.extend(run)
        lit.clear()

    p = 6
    while p < end:
        best, bl = None, 0
        lim = min(255, end - p)
        for code, inl, d in cands:
            r = p + d
            if r < 4:   # never read the w/h header
                continue
            n = 0
            while n < lim and t[r + n] == t[p + n]:
                n += 1
            # tie: prefer the form that encodes the length inline (1 byte instead of 2)
            if n > bl or (n == bl and n and n - 1 < inl and best[1] <= n - 1):
                best, bl = (code, inl), n
        if bl == 0:
            lit.append(t[p])
            p += 1
            continue
        flush()
        code, inl = best
        if bl - 1 < inl:
            out.append(code | (bl - 1))
        else:
            out += bytes((code | inl, bl - 1))
        p += bl
    flush()
    return bytes(out)


if __name__ == "__main__":
    data = open(sys.argv[1], "rb").read()
    off = int(sys.argv[2], 0)
    out, end = decompress(data, off)
    w, h = struct.unpack_from("<hh", out)
    print(f"w {w} h {h} out {len(out)} packed {end - off:#x}")
