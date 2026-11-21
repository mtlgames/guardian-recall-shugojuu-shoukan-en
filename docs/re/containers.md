# Disc, archives, compression

## Disc (verified: dumpsxiso, both discs)
- Two discs, MODE2/2352 single track. `dumpsxiso -x tree -s layout.xml` works (work/disc{1,2}/). Disc 1 = 296,880
  sectors (~66 min): ~63k sectors free before 80 min; disc 2 = 310,101 sectors: ~50k free.
- `DATA/` identical on both discs except disc 1's `32KAKU.XA`. EXE identical. STR movies differ per disc.
- XA voice (`XA000-XA039.XA`), VB/VH sound banks, STR movies (no burned subtitles seen in the opening).

## UNN.PAK (verified: TOC sums to file size; group 23/13 text found where the tables say)
- 28 groups. TOC at EXE RAM 0x800914DC (file 0x81CDC): `{u16 sector, u16 nsec, u32 bytes}`; header after it at
  0x800915BC: `{0, -1, char* "DATA\UNN.PAK", toc}`.
- Groups have sub-tables in the EXE, same entry format (sector relative to group start), each followed by a
  header `{u32 lba (set at runtime), -1, 0, table_start}`. Sub-table span = group nsec - 1 (one spare sector).
  `tools/gr_index.py EXE` lists them: g0 0x80092A14(95) g9 0x80092D1C(14) g10 0x80091B44(55) g11 0x800924D4(28)
  g12 0x800925C4(32) g13 0x8009296C(19) g14 0x8009169C(147) g15 0x80091D0C(55) g16 0x80091ED4(128)
  g17 0x800922E4(53) g18 0x800915CC(24) g19 0x80093694(184) g20 0x80093C64(60) g21 0x8009249C(5)
  g22 0x800926D4(10) g23 0x80092734(69) g24 0x80092D9C(83) g25 0x80093044(16) g26 0x800930D4(12)
  g27 0x80093144(23). Groups 1-8 have none matched yet (g3, g8 have candidate tables at 0x80095xxx; check).
- So any group can grow or move: rewrite the TOC + its sub-table (phase 3 rebuild).
- Group contents (first guess from sweep): 1/2 strips (504x12 etc.), 3 strips 1459x16, 10 55x 42x50 images,
  13 battle quotes, 17 = copy of SUBTI.PAK (title cards, +64), 18 24x 128x240 images, 23 scenario, 24 66x 160x240.

## TX03 compression (verified: decoder `tools/tx03.py` decodes 1103 streams with consistent sizes)
- EXE 0x8005D5DC. `"TX03", s16 w, s16 h, 2 raw bytes, commands` -> `w, h, w*h bytes`. Commands in tx03.py docstring
  (literal run, back-ref, up-1 row, up-2 rows, up-4 rows with -4..+3 offset). Used for images and the glyph maps.
- Counts: UNN.PAK 1065 "TX03" (1050 decode, 15 false hits listed in work/gfx/sweep/UNN.idx), SUBTI.PAK 53,
  BTL.PAK 6965 (battle sprites, not yet swept). No compressor yet (phase 3: write one, roundtrip-test).

## GRETC.RLZ (verified: probe `tools/lua/gretc_probe.lua` dumped the directory at lookup; `tools/gretc.py extract`
expands all 255 entries to their directory sizes, every .tim parses as a TIM, .txd decode to readable text)
- Directory = first 7 sectors, obfuscated: byte i XOR (0x80 + 0xAA*i). Header 0xB0: "RLZ-G", RCS id
  "rle.c 1.33 98/06/17 ikeda", "Jun 21 1998"; +0x80 u32 file size 0x32A800, +0x84 u32 sectors, +0x88 u32 method (1),
  +0x8C u32 count (255). Entries 0x34: name[13], group[9], +0x16 u8 packed, +0x17 u8 xor key (0 = none),
  +0x18 u8 RLE escape byte, +0x19 0xFF, +0x1A u16 checksum (CRC16 poly 0x1021 init 0 per byte, fn 0x80019560 from 0x800190BC; a plain CRC-16/XMODEM
  over stored/expanded/xored bytes does not match yet; a mismatch only printfs "(CRC-ERROR)", not fatal),
  +0x1C u32 offset, +0x20 u32 size, +0x24 u32 packed size, +0x28 u32 sector, +0x2C u32 sectors, +0x30 u32 stamp.
- Loader 0x80014CCC(req): looks up by group name, loads into RAM 0x80105DD0 (max 0x30D40). Method from header +0x88:
  0 -> 0x8001932C, 1 -> 0x800193C8 (RLE: byte == esc -> value, count), 2 -> 0x8001925C. Then if xor key != 0:
  0x80019504 XORs the expanded bytes with key, key += 0xAA per byte. Codec: `tools/rlz.py` (unpack/pack/xor, selftest).
- Groups: mill (battle digits, split.tim kanji glyphs), btbg (battle bgs), gd2/gd (guardian dictionary art),
  cf2/cf (character files), evd (70 event scripts map*.evd, 2 packed), dic, rsel (天/地 route select), opt, mus, day,
  brain, **txd** (8 text files, xor key 0x8F: see text.md).
- Rebuild: entries are sector-aligned; a repack must rewrite the directory (re-XOR), sizes and sectors; the u16
  checksum only feeds a debug printf (still worth matching: corrupt-and-boot test in phase 3).

## Overlays
`DATA/*.BIN`: u32 id then MIPS code (TITLE, TITLE2, ACTION, BATTLE, MENU, MAP02, CALL02, JAPAN, HEN, DAY, ...).
Loaded whole (id word included) - verified by RAM match: TITLE.BIN at 0x80162F88; JAPAN.BIN and RSEL.BIN at
0x80166218. Guess (lui/addiu targets landing on string starts): ACTION.BIN 0x80166218. Others: see text.md.
