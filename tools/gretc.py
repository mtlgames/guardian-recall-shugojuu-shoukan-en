"""GRETC.RLZ archive: directory (XOR-obfuscated) and entries. See docs/re/containers.md.

    python -X utf8 tools/gretc.py list GRETC.RLZ            # one line per entry
    python -X utf8 tools/gretc.py extract GRETC.RLZ OUTDIR   # every entry, expanded (packed ones via rlz)

Directory = first 7 sectors: byte i XOR (0x80 + 0xAA*i). Header 0xB0 bytes ("RLZ-G", RCS id, date; +0x80 u32 file
size, +0x84 u32 sectors, +0x88 u32 1, +0x8C u32 count), then count x 0x34-byte entries.
"""
import struct
import sys

HDR = 0xB0
ENT = 0x34
FIELDS = "name group packed b17 b18 b19 crc off size psize sector nsec stamp".split()


def unxor(b, start=0):
    return bytes(c ^ ((0x80 + 0xAA * (start + i)) & 0xFF) for i, c in enumerate(b))


def directory(data):
    head = unxor(data[:HDR])
    assert head[:5] == b"RLZ-G", "not an RLZ-G archive"
    count = struct.unpack_from("<I", head, 0x8C)[0]
    raw = unxor(data[:HDR + count * ENT])
    ents = []
    for i in range(count):
        e = raw[HDR + i * ENT:HDR + (i + 1) * ENT]
        name = e[:13].split(b"\0")[0].decode("ascii")
        group = e[13:22].split(b"\0")[0].decode("ascii")
        vals = struct.unpack_from("<4BH6I", e, 22)
        ents.append(dict(zip(FIELDS, (name, group) + vals)))
    return head, ents


def payload(data, e):
    """Stored bytes of an entry (still packed when e['packed'])."""
    return data[e["off"]:e["off"] + e["psize"]]


def expand(data, e):
    """An entry as the game sees it after loading: RLE-expanded (esc = b18), then XORed when b17 != 0."""
    from rlz import unpack, xor
    b = payload(data, e)
    if e["packed"]:
        b = unpack(b, e["b18"])
    assert len(b) == e["size"], (e["name"], len(b), e["size"])
    return xor(b, e["b17"]) if e["b17"] else b


def main(argv):
    if len(argv) < 2:
        sys.exit(__doc__)
    data = open(argv[1], "rb").read()
    head, ents = directory(data)
    if argv[0] == "list":
        print("\t".join(["i"] + FIELDS))
        for i, e in enumerate(ents):
            print("\t".join([str(i)] + [hex(e[k]) if isinstance(e[k], int) and k in ("off", "crc") else str(e[k])
                                        for k in FIELDS]))
    elif argv[0] == "extract":
        import os
        os.makedirs(argv[2], exist_ok=True)
        for i, e in enumerate(ents):
            b = expand(data, e)
            open(os.path.join(argv[2], f"{i:03d}_{e['group']}_{e['name']}"), "wb").write(b)
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv[1:])
