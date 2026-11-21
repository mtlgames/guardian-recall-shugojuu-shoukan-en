# Text engine and script

Dump: `rom.sha1`. EXE `SLPS_012.97` (disc 1) and `SLPS_012.98` (disc 2) are byte-identical; every `DATA/` file is
identical on both discs (disc 1 alone has `DATA/32KAKU.XA`; STR movies differ). One set of text serves both discs.
EXE RAM = file offset + 0x8000F800 (t_addr 0x80010000, header 0x800; text size 0x156800).

## Encoding (verified: decoded readable dialogue, `tools/gr_text.py`; renderer read in disassembly)
- 0x81-0x9F, 0xE0-0xEF lead a Shift-JIS pair (renderer subtracts 0x4000 from codes > 0xDFFF before lookup).
- 0xA6-0xDD single byte = hiragana, via EXE table at RAM 0x8001130C (file 0x1B0C, 0x38 x u16 SJIS codes,
  order = half-width katakana order ｦｧｨ... mapped to をぁぃ...). 0xA1-0xA5, 0xDE, 0xDF are not mapped.
- Control: 0x00 end of string, 0x01 wait for button (page end), 0x0A newline, 0x0D ignored. Full-width space 0x8140
  advances 13 px without a glyph. Nothing else appears in scenario text (`tools/gr_codes.py`: only 00/01/0A).
- **No ASCII**: bytes < 0x81 other than the codes above index the glyph map with a negative offset. English needs a
  font/renderer change (phase 5).
- Message layout (scenario): `Name\n「line\n　line」\n[01][00]`; names are a separate first line; continuation lines start
  with 0x8140. Lines seen up to 17 full-width chars; box size not yet measured (phase 5 width gate).

## Renderer (verified by read breakpoint on the script buffer, `tools/lua/` + watch.lua, state `work/states/orig_dlg1.sstate`)
- Text interpreter loop at 0x80043E18 reads bytes (pc 0x80043E24/0x80043E58). Glyph lookup 0x80044C48(code, &out):
  index = code - 0x813F into u16 map at RAM 0x800C4E78; entry 0 = no glyph; entry bits 15-9 row (x14 px),
  bits 8-2 col (x12 px), bits 1-0 = bit plane. Glyphs are 12x14 cells, 1bpp, packed 4 per pixel in a 4bpp texture
  (21 cols x 18 rows x 4 planes); scene 1 map holds 1445 glyphs. Glyphs are drawn as GPU sprite packets.
- The glyph map is **per-scene**: 0x80044D7C(n) TX03-decompresses entry n of an archive loaded at RAM 0x80105DD0
  (from `data\gretc.rlz` group loader 0x80014CCC, max 0x30D40 bytes) and copies it to 0x800C4E78. The font texture
  presumably comes from the same set (guess; find in phase 5).

## Scenario script: UNN.PAK group 23 (verified: decoded, RAM match)
- Group 23 = UNN.PAK 0x1B87000, 0x60000 bytes. Sub-table (69 entries) at EXE RAM 0x80092734 (see containers.md).
- Each block: `u32 count, u32 0, count x u32 offset` (from block start; 0 = unused slot), then strings. Offsets point
  at the name line (just past the 0x0A that follows the previous string's 0x00).
- Block for the first Earth-route scene (+0xF000) is loaded to RAM 0x800D16F8 (buffer ref'd at 0x80044B4C etc.,
  loader 0x80044B24(index) -> 0x8004B044(buf, filedesc 0x8009295C, index)). Buffer size: not yet known; reads
  past +0x2800 belong to other data (0x800D40C4), so assume <= 0x2800 until proven (phase 5).
- +0x41000-0x44000 holds headerless text (starts mid-message at +0x4118B): probably dead; confirm with textcover.
- `tools/gr_scan_blocks.py UNN.PAK 0x1B87000 0x60000` lists blocks.

## Battle / map quotes: UNN.PAK group 13 (verified: decoded)
- Group 13 = 0x6DE000, 0xD800 bytes, 19 sub-entries (sub-table RAM 0x8009296C); same block format. Victory quotes per
  character etc. (`gr_scan_blocks.py UNN.PAK 0x6DE000 0xD800`).

## Other text (found by `tools/gr_strings.py`; pointers not yet traced)
| Where | Strings | Notes |
|---|---|---|
| EXE 0x800-0x2900 | ~100 | menus, system messages, char/monster/item names (fixed-stride records, e.g. 0x48), `%s` formats |
| EXE 0xA6000-0xA7000 | ~60 | monster/item/guardian names, record tables |
| DATA/ACTION.BIN | 71 | overlay (u32 id + MIPS code); field/map UI |
| DATA/BATTLE.BIN | 55 | overlay; battle UI, debug strings |
| DATA/HEN.BIN | 39 | overlay; formation/party (names, e.g. 北斗めぐみ) |
| DATA/DAY.BIN, BRAIN.BIN, DIC.BIN | 10/6/4 | overlays |
| UNN.PAK 0x153F800, 0x1608000, groups 16/19 | some | not yet decoded (group 19 may be compressed) |
EXE also has English option labels ("BGM Volume", "Message Speed", "Window Color"...) and a leftover event debug
menu ("EVENT NO.%d", "EVENT NUMBER CHANGE: LEFT OR RIGHT", "START:MEMORY CARD LOAD", file 0xA24-0xA6A) for phase 2.
Overlay load addresses not yet found (code starts `lui 0x8016`).
