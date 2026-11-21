"""GRETC.RLZ entry codec (EXE 0x800193C8 RLE, 0x80019504 XOR). See docs/re/containers.md.

RLE: byte == esc -> next two bytes (value, count): value written count times (count 0 writes nothing);
any other byte is a literal. esc is the entry's +0x18 byte.
XOR (entries whose +0x17 byte k != 0, after expanding): byte i ^= (k + 0xAA*i) & 0xFF.
"""


def unpack(b, esc):
    out = bytearray()
    i = 0
    while i < len(b):
        c = b[i]
        if c == esc:
            out += bytes([b[i + 1]]) * b[i + 2]
            i += 3
        else:
            out.append(c)
            i += 1
    return bytes(out)


def pack(b, esc):
    """Runs of 4+ (and every esc byte) become esc,value,count; the rest stay literal."""
    out = bytearray()
    i = 0
    while i < len(b):
        j = i
        while j < len(b) and b[j] == b[i] and j - i < 255:
            j += 1
        n = j - i
        if n >= 4 or b[i] == esc:
            out += bytes([esc, b[i], n])
        else:
            out += b[i:j]
        i = j
    return bytes(out)


def xor(b, k):
    return bytes(c ^ ((k + 0xAA * i) & 0xFF) for i, c in enumerate(b))


if __name__ == "__main__":
    for s in (b"", b"abc", b"\0" * 300 + b"xy\x07\x07z", bytes(range(256)) * 2):
        for e in (7, 0, 0xFF):
            assert unpack(pack(s, e), e) == s
    assert xor(xor(b"hello", 0x8F), 0x8F) == b"hello"
    print("rlz selftest ok")
