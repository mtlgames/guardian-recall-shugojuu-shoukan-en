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

## English font and hooks (phase 5, verified in game: ev01-03 marker text drawn, `asm/hooks.asm`, `tools/font.py`)
- The glyph map is **global**, not per scene: UNN g9 sub-entry 0 is an archive (u32 offsets); item 10 = the map
  (TX03, 11966 entries, 1459 used), item 7 = the font TIM (4bpp, raw, VRAM 896,256, 64x256; CLUTs 896-959,511, one
  per plane: entries 0x800B6500 = 0x7FF8..0x7FFB), item 9 = a CLUT TIM. Loaded at boot by 0x8001A980.
  The 21x18x4 = 1512 cells hold 1459 glyphs; 52 cells are free (cell 0,0,0 can't be named: entry 0 = none).
- Renderers calling the lookup 0x80044C48: scenario box 0x80043DA4 (3 callers), generic string draw 0x80043A64
  (~200 callers: EXE menus, ACTION, HEN), 0x80044624, 0x80017F10, DIC.BIN 0xD04. Each sprite = glyph (rgb from a
  table) + black shadow at +1,+1, 12x14, tpage gp+0xC14 (0x1E). Scenario pen: x s3 (+13 per glyph, +13 for 8140),
  y s7 (+17 per 0A), origin x = box +0x20; fp = glyphs shown (typewriter).
- English: bytes 0x20-0x7E go through `cell_tab` (hook at 0x80044C48) to cells drawn from `fonts/vwf12.txt`:
  letters/digits replace the full-width Ａ-Ｚ ａ-ｚ ０-９ glyphs (now left-aligned), punctuation uses free cells. Every
  lookup stores the advance in `last_adv` (ASCII: width + 1; else 13); the scenario renderer adds it (0x80044480).
- RAM for new code/data: the malloc arena (descriptor 0x8015B608, init 0x8006A2C4(base [0x800120DC]+0x800, size
  0x801F7700 - [0x800120DC]) set in main 0x8001A6FC) is cut to end 0x801EBF00; ours = 0x801EC000-0x801F7FFF.
  Payload at 0x801F0000, copied there by a boot stub (new EXE entry, stored in the zero BSS at 0x800CAC00; startup
  clears BSS 0x800B6408-0x80162F88 afterwards). Heap walk: `tools/lua/heap.lua` (block header 0x1C: +0 next,
  +8 used, +0xC size; first block at desc+0x40); malloc log: `tools/lua/malloc_log.lua`. The HEN formation screen
  (ev43) uses the arena up to 0x801E1778 on the original (a 0x1A8FC block), the most seen so far.
- **ev43 crash (fixed 2026-11-23):** the arena cut was 0x10000 and the g13 malloc grown to 0x4000; with the 2D pool
  0x2800 bigger (pool_grow rounding) HEN's g13 malloc returned 0, the CD DMA loaded the block to address 0 and the
  kernel died (pause pc 0xF8 in a B0 call, ra 0x8008FF00). Now: scenario buffer in BSS, g13 buffer static.
- Scenario buffer: 0x800D16F8 was 0x2800 bytes (next symbol 0x800D3EF8, refs: 5 lui/addiu pairs 0x80044B4C-0x80044FEC)
  -> SCEN_BUF 0x800CAC00, 0x6A78 bytes (zero BSS after the glyph map up to vars at 0x800D1678; no code ref into it in
  the EXE or any overlay: `tools/xref_range.py`). Battle quotes (g13): loader 0x80044BB4 malloc(0x2800) -> static
  G13_BUF 0x801EC000 (0x4000); callers read it via gp+0xBF4 only, the release's free (0x80044C24) is nopped.
- Scenario box (measured, ev02/ev03 marker shots): pen x = 70 (top and bottom box), name line + up to 3 text lines,
  17 px apart; page cursor at x 296-301 between lines 2 and 3. JP lines end at 70 + 17 x 13. Budget: 224 px/line.

- Space (0x20) has a blank cell of its own (a lookup miss draws ？ in the txd renderer and doesn't advance in
  0x80044624). The hook also sets `last_sjis` (1 after a Shift-JIS lookup, 0 after ASCII).
- VWF per renderer (verified in game with the marker build, 2026-11-23): generic 0x80043A64 (pen s3; lookup miss and
  glyph both go through `gen_adv`), 0x80044624 (pen s2, `gen2_adv`; a miss now advances too), txd markup default
  font mode (`txd_adv` at 0x80017DC8: x += &g pitch + last_adv - 13).
- **txd markup renderer** 0x800133D4 (context struct: x +0x14, y +0x18, &g pitch +0x24, line height +0x28, &f chars
  per line +0x2C, lines +0x30, chars on the line +0x34). Handler table 0x800913EC ('c p s g f a n e d h y i m b').
  Auto-wrap 0x80017EAC: when +0x34 >= +0x2C (except before 、。) x = 0, y += +0x28. `txd_adv` counts Shift-JIS
  glyphs only, so English never auto-wraps: the inserter must wrap English with &n() at (+0x2C x +0x24) px.
  Glyph draw 0x80017F10 (lookup miss -> ？ 0x8148). Font modes +0x0/+0x8/+0xC (other advance paths, not hooked).
- **Dictionary pages** (DIC.BIN, overlay 0x80166218; 0xB38 = layout of one page into glyph records, 0x2708 =
  per page, 0x2600 = all 90 entries at list build, 0x1CEC = draw one glyph with the page-turn transform). Its own
  grid: x = col * 14 + 0x28 (left page) / 0xAE (right), y = row * 16 + 0x23, 8 columns; only &c and &n. Records
  were 26 bytes in the task workspace (0x36934 bytes, glyph array ws+0x49B0..ws+0x3688C = 7856 records; JP uses
  6045): English markers needed 11272 and overran into the next arena block (list pointers -> sprintf hang).
  Patched: col counts pixels (wrap when col >= 100), ASCII advance = width + 1, spaces keep no record, records 10
  bytes (corners rebuilt per draw by `dic_expand`): capacity 20444.

## Scenario script: UNN.PAK group 23 (verified: decoded, RAM match)
- Group 23 = UNN.PAK 0x1B87000, 0x60000 bytes. Sub-table (69 entries) at EXE RAM 0x80092734 (see containers.md).
- Each block: `u32 count, u32 0, count x u32 offset` (from block start; 0 = unused slot), then strings. Offsets point
  at the name line (just past the 0x0A that follows the previous string's 0x00).
- Block for the first Earth-route scene (+0xF000) is loaded to RAM 0x800D16F8 (buffer ref'd at 0x80044B4C etc.,
  loader 0x80044B24(index) -> 0x8004B044(buf, filedesc 0x8009295C, index)). Buffer size: not yet known; reads
  past +0x2800 belong to other data (0x800D40C4), so assume <= 0x2800 until proven (phase 5).
- Entry 43 (+0x41800) has count 0 and 254 slots (105 strings, SJIS kana, 白虎... lines); the text at +0x4118B is stale
  sector padding of entry 42. Whether the game reaches entry 43: textcover (phase 8).
- Layout (verified, tests/test_script.py rebuilds every block byte-exact): strings in order of first slot, each
  `text 00`, separated by 0x0A filler (1-5 bytes); 3 blocks (16, 29, ...) also hold **unreferenced staging notes**
  between strings ("キョロキョロするゆかり、... SR226出力。"), kept as hex `pre`. Block ends 0x0A + zero padding;
  the sector padding after a sub-entry's `bytes` holds stale data (kept on repack).
- `tools/gr_scan_blocks.py UNN.PAK 0x1B87000 0x60000` lists blocks.

## Battle / map quotes: UNN.PAK group 13 (verified: decoded)
- Group 13 = 0x6DE000, 0xD800 bytes, 19 sub-entries (sub-table RAM 0x8009296C); same block format. Victory quotes per
  character etc. (`gr_scan_blocks.py UNN.PAK 0x6DE000 0xD800`).
- Entry 2 = item help (帽子：... Ｄｆ＋２): `u32 80` then 81 offsets, no 0 word.

## Unit names in event scripts: GRETC.RLZ group evd (verified: every Japanese run in the 70 evd files is one)
- Op `34 idx len text 00` (len = text + NUL) names the map's units (大地裕子, 闘士, 鎌蜥蜴...). 564 names, 159 distinct;
  35 maps have them. Handler 0x8001E214 (EXE): script base 0x800B68F0, pc u16 at gp+0xC6; stores a pointer to the text
  (no copy) at unit +0x10, units at 0x8013E650 + idx * 0x7C. **Hooked** (evd_name_hook, asm/hooks.asm): insert.py writes
  key `7F hi lo` in place of the text and the hook points the unit at the English in a payload table, so the evd never
  grows. The ring > UNIT list (ACTION) crashed on 20-byte names: not a name buffer (only the generic draw reads the
  name) but the 2D primitive pool below.

## 2D primitive pool (verified 2026-11-23, fixed by pool_grow in asm/hooks.asm)
- Allocator 0x8004F664(size): struct at *0x8015238C (0x8017C210 on maps): +4/+8 slots (two heap buffers), +0xC
  current buffer, +0x10 frame base (= +0xC + cap * frame parity), +0x14 k (slot index), +0x18 cap, +0x1C minimum
  (0x2800), +0x20 failed bytes, +0x24 used, +0x30 demand, +0x34 failed calls. Generic draw = 0x20 bytes per glyph.
- Per frame 0x8004F2DC: demand = used + failed; if it exceeds the cap, 0x8004F43C reallocs slot[k&1] to 2 x demand
  (malloc 0x8006996C, or 0x800699BC = free + malloc), frees the other slot a frame later. **The game never checks
  the malloc result**: on failure base = 0 and glyph packets overwrite the kernel at 0x0 (exception, pc 0x641C ra
  0xD00, or pc 0x80000080 ra 0x80079C28 in the 3D dispatch). Our 0x10000 arena cut fragments the heap enough for
  20-byte names (demand 0x49E0 -> 0x93C0 bytes, no block that big). tac_search does it on the original too.
- Fix: pool_grow rounds demand above the minimum up to 0x2000 (one realloc to 0x6000 on the UNIT list) and on a
  failed malloc keeps the current buffer and cap (requests over the cap are skipped), zeroing the freed slot.
  Probe tools/lua/pool2d.lua (struct, peak use, `DUMP=frame` dumps it per frame).

## Extraction (phase 4, verified by tests/test_script.py)
- `tools/extract.py` -> `script/{scenario,battle,txd,evd,exe}/*.json` (7751 strings), library `tools/script_io.py`
  (parsers + builders + UNN/GRETC repack), `tools/script_stats.py` (counts). Tests: every block/txd rebuilds
  byte-exact, UNN.PAK + EXE TOC and GRETC.RLZ repack byte-identical, evd/EXE strings re-encode exactly, every
  Japanese text run in the EXE/overlay ranges and evd files is a record, script/ equals a fresh extraction.
- Two kana forms: scenario = single-byte hiragana (+ SJIS ー 815B in most lines, B0 in a few); EXE/overlays = SJIS
  hiragana pairs. One tbl can't encode both, so each record names its table variant (`tbl`: jp / jp- / sjis,
  script_io.TABLES); no text record keeps an [XX] escape.
- EXE/overlay records carry `off`, `room` (bytes in place incl. NUL + padding to the next word), `refs` (w = u32
  word, p = lui pair, RAM address of the reference), `inner` (refs landing inside). status `data` = printf debug
  output or unreferenced noise (57). The 0x800-0x2F60 range also holds ASCII file names and labels: not extracted.

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
- Relocation (tools/insert.py patch_images): a string longer than its room moves to STR_POOL (payload 0x801F4000,
  resident) and every ref is repointed (w: the word; p: lui + its first low op, each lui feeds one low op only).
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
