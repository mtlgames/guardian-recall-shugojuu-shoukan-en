"""Save editor for Guardian Recall memory cards (.mcd, 128 KB raw). Layout: docs/re/debug.md (Memory card).

    python -X utf8 tools/debug/save.py CARD                         list the game's files and their story fields
    python -X utf8 tools/debug/save.py CARD --out NEW [--file GRS] [--event N] [--poke OFF=HEX..] [--fill OFF:LEN=V..]
                                        [--unlock-all]

Offsets are inside the file's first 8 KB block (the one the checksum covers). Edits start from a game-written base
card, never zeros; the byte-sum checksum at +0x1FFE is fixed on write. --unlock-all sets every story flag the
OPTION encyclopedias read (char flags +0x244.., event flags +0x3A6..) so every entry shows.
"""
import argparse
import sys

BLOCK, FRAME = 0x2000, 0x80
SUM = 0x1FFE                     # checksum byte: sum of bytes 0x0000-0x1FFD & 0xFF (game fn 0x8005EEFC)
EVENT = 0x276                    # u16 event number (-> 0x8013CEE4 on load)
FIELDS = {                       # card offset: (length, RAM it loads into, meaning)
    0x214: (0x26, 0x80136BD0, 'story block A'),
    0x23A: (0x3C, 0x80141398, 'story block B; +0xA: 50 per-entry flags read by BRAIN (OPTION)'),
    0x276: (0x130, 0x800C4A20, 'event number u16 + unit stats'),
    0x3A6: (0x100, 0x8013E550, 'event flag array (BRAIN copies it into si)'),
    0x4DE: (0x180, 0x80157A90, 'system data (u32 time, u32 event, flags)'),
}
# DAY-menu save (GRDA..., written by DAY > SAVE; loader 0x8005D9C4): its own layout. Event u16 at +0x238 picks the
# episode the DAY menu (and its DIARY page) opens on after title > LOAD.
GRD_EVENT = 0x238
GRD_FIELDS = {
    0x200: (0x34, 0x8013DE00, 'options area'),
    0x234: (0x180, 0x80157A90, 'system data (u32, u16 event at +4 -> 0x8013CEE4, flags)'),
}
# block A (all 0xFF) unlocks the epilogue replays; BRAIN also copies its +6..+0x26 to 0x8013DE14 (options area)
UNLOCK = [(0x214, 0x26, 0xFF), (0x23A + 0xA, 50, 0x01), (0x3A6, 0x100, 0xFF)]


def files(card):
    """{name: block index} from the directory frames (frame 1-15 = block 1-15)."""
    out = {}
    for i in range(1, 16):
        f = card[i * FRAME:(i + 1) * FRAME]
        if f[0] == 0x51:  # first block of a file in use
            out[f[0x0A:0x1E].split(b'\0')[0].decode('ascii', 'replace')] = i
    return out


def checksum(blk):
    return sum(blk[:SUM]) & 0xFF


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('card')
    ap.add_argument('--out')
    ap.add_argument('--file', default='GRS', help='file name suffix: GRS (system file + map save) or GRDA (DAY-menu save, day01.mcd)')
    ap.add_argument('--event', type=int)
    ap.add_argument('--poke', nargs='*', default=[], help='OFF=HEXBYTES, e.g. 0x276=4600')
    ap.add_argument('--fill', nargs='*', default=[], help='OFF:LEN=BYTE, e.g. 0x3A6:0x100=0xFF')
    ap.add_argument('--unlock-all', action='store_true')
    a = ap.parse_args()
    card = bytearray(open(a.card, 'rb').read())
    assert len(card) == 0x20000, f'{a.card}: not a raw 128 KB card'
    fs = files(card)
    name = next((n for n in fs if n.endswith(a.file)), None)
    if not name:
        sys.exit(f'no *{a.file} file on {a.card} (files: {", ".join(fs) or "none"})')
    at = fs[name] * BLOCK
    blk = card[at:at + BLOCK]
    ok = checksum(blk) == blk[SUM]
    grs = name.endswith('GRS')
    ev, fields = (EVENT, FIELDS) if grs else (GRD_EVENT, GRD_FIELDS)
    print(f'{name}: block {fs[name]}, checksum {"ok" if ok else "BAD"}, event {int.from_bytes(blk[ev:ev + 2], "little")}')
    for off, (n, ram, what) in fields.items():
        print(f'  +0x{off:03X} {n:#6x} -> {ram:08X} {sum(1 for x in blk[off:off + n] if x):4d} non-zero  {what}')
    if not a.out:
        return 0
    assert ok, 'base save has a bad checksum: start from a game-written card'
    assert grs or not a.unlock_all, '--unlock-all edits the GRS system file'
    edits = list(UNLOCK) if a.unlock_all else []
    for f in a.fill:
        o, rest = f.split(':')
        n, v = rest.split('=')
        edits.append((int(o, 0), int(n, 0), int(v, 0)))
    for off, n, v in edits:
        assert 0x200 <= off and off + n <= SUM, f'fill outside the data area: {off:#x}+{n:#x}'
        blk[off:off + n] = bytes([v]) * n
    for p in a.poke:
        o, hx = p.split('=')
        b = bytes.fromhex(hx)
        assert 0x200 <= int(o, 0) and int(o, 0) + len(b) <= SUM, f'poke outside the data area: {p}'
        blk[int(o, 0):int(o, 0) + len(b)] = b
    if a.event is not None:
        blk[ev:ev + 2] = a.event.to_bytes(2, 'little')
    blk[SUM] = checksum(blk)
    card[at:at + BLOCK] = blk
    open(a.out, 'wb').write(card)
    print(f'wrote {a.out} ({len(edits)} fills, {len(a.poke)} pokes, checksum {blk[SUM]:#04x})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
