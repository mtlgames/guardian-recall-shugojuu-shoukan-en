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
- `tbl/jp.tbl` (generated: `tools/make_jptbl.py EXE tbl/jp.tbl`): decode -> encode byte-exact on all 4994 strings of
  UNN g23 + g13 blocks (verified). Only escape seen: SJIS ー 0x815B decodes as `[81][5B]` because single-byte 0xB0
  is also ー (phase 4: pick the canonical form per string or keep the escape).
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

## Markup text: GRETC.RLZ group txd (verified: decoded, `tools/gretc.py extract`; renderer not yet traced)
- 8 files (gd, cf, op, dic, day, rep, tu, save .txd), each RLE + XOR key 0x8F (containers.md). Layout: 0x1000-byte
  table of 1024 u32 offsets (from file start, 0 = unused slot), then NUL-terminated strings in the game encoding
  **plus printable ASCII** (cf.txd: "NATIVE TOKYO", op.txd: "1:MAIN THEME"), so this renderer already draws ASCII.
- Markup: `&s(x,y)` position, `&c(n)` colour, `&a(n,r,g,b)` palette, `&g(w,h)` glyph cell/spacing, `&f(w,h)` font
  size, `&e()`/`&d()` begin/end (centred or emphasis block), `&n()` newline, `&h()`, `&p(x,y)` (cf tab stops).
- Content: gd = guardian dictionary (203 slots), cf = character files (286), op = music titles (English romaji),
  dic = glossary dictionary (180), day = diary per episode (154: 天の章第一話 + episode title + summary), rep = replay
  list (252), tu = tutorial (28), save = memory-card messages (85, incl. boot "システムファイルが存在しません").

## EXE and overlay strings (verified: `tools/str_refs.py` finds a reference for each listed string)
- Pointer format: absolute u32 RAM pointers (EXE RAM = file + 0x8000F800) in tables/records, and lui/addiu (or
  lui/load) pairs in code. One encoding everywhere (scenario codec above).
- EXE text ranges: file 0x800-0x2F60 (RAM 0x80010000-0x80012760: file names, menus, system/debug messages,
  char/skill/item names, English option labels "BGM Volume"...) and 0xA4250-0xA6C00 (RAM 0x800B3A50-0x800B6400:
  monster/guardian/item name records, "Master"...). 379 + 303 strings with references (219+209 by word, 162+95 by
  pair); the rest of the EXE's "strings" are code noise. Event debug menu ("EVENT NO.%d", file 0xA24-0xA6A) for phase 2.
- Overlays load whole (id word included). Base 0x80166218 verified by RAM match (JAPAN, RSEL) and by references
  (ACTION 70, BATTLE 72, HEN 40, DAY 9 strings referenced at that base); TITLE.BIN at 0x80162F88 (RAM match).
  Text ranges (file offsets): ACTION 0xEC-0x10EC (field/map UI: リトライ, タイトルに戻る...), BATTLE 0x4-0x2E28 (skill
  names 誘眠 加護..., battle UI), HEN 0x4-0x320 (names), DAY 0x64-0x2C0 (+debug formats). BRAIN 0x4-~0x40 (menu:
  ＥＸＩＴ 用語辞典 守護獣図鑑 キャラファイル; base not found: no reference at 0x80166218), GD/DIC/CF/REP/TU only a
  "？？？？？？？？" placeholder; TITLE/TITLE2/MAP02/MENU/JAPAN/CALL02/RSEL: no text.
- UNN.PAK: real text only in groups 13 and 23 (strings scan of all 28 groups); g6/g7 hold "データに結合" leftovers
  inside model data (not shown).

## Free space (candidates; trap-fill and tour before use, phase 5)
- Disc: ~63k sectors free on disc 1, ~50k on disc 2 (containers.md); new files can be added.
- EXE image: loads 0x80010000-0x80166800, but RAM 0x800B6405-0x80162F88 is zero in the file (runtime buffers: glyph
  map 0x800C4E78, scenario 0x800D16F8, GRETC 0x80105DD0...) and overlays overwrite the tail from 0x80162F88/0x80166218.
  No free gap inside the code; new code goes in RAM below.
- RAM zero in two dumps (dialogue scene, route-select): **0x801B6DC8-0x801FF938 (0x48B70)** under the stack
  (sp 0x801FFFF0) - the main candidate; 0x8000E4F8-0x80010000 (0x1B08, above the kernel); 0x800CABFC-0x800D16F8
  (0x6AFC, just before the scenario buffer). Battle and menu scenes not yet checked.
- Scenario buffer 0x800D16F8: reads past +0x2800 hit other data (0x800D40C4); treat 0x2800 as the limit until traced.
