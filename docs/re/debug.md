# Debug tool: warps, mode switches, memory card

Tools: `tools/debug/warp.lua` (cold-boot warp, `--script`), `tools/debug/regen.py` (every scene in `scenes.tsv` in
parallel: proof sheet in `work/qa/warp/<name>/`, state in `work/states/<name>.sstate`), `tools/debug/overview.py`
(one labelled sheet over many runs), `tools/debug/cards/sys.mcd` (memory card with only the game-written system
file, so the boot skips the "create system file?" prompt; regen gives every run its own copy).

## Main loop, task and events (verified: warps to all of ev01-ev70 log "event N started", sheets in work/qa/warp)
- Main loop 0x800219F4 calls the u32 task fn at **0x8013CEE0** every frame, whatever overlay runs (route choice,
  JAPAN travel map, ACTION field). Idle task = 0x8001A5A0 (`jr ra`), set by every event start.
- Leftover event-select task 0x8001A3E8 ("EVENT NO.%d", LEFT/RIGHT, O starts, START = memory-card load, SELECT =
  0x80167C10) is never installed by the game; MENU.BIN (debug menu MODEL/SOUND/SE/EVENT/MEMORY CARD/XA/OPTION/
  CONTINUE/STR, fn table 0x80167DC0) is never loaded (no "MENU" string in the EXE).
- Event start: u16 event number (1..70) -> **0x8013CEE4**, task = **0x8001A25C**. The starter copies the number to
  gp+0xB2C and picks the next mode: events 47-49 and 51-69 -> field (0x8004C840); others -> DAY disc check
  (0x8004C900) when the disc id at **0x8013DE46** (0 = disc 1, 1 = disc 2; from DISK.ID at boot) is wrong for the
  event (1-20 and 50 want disc 1, 21-46 and 70 want disc 2), else field.
- Overlay id: u32 at **0x80166218** (overlays load whole, id word first): TITLE 5, BRAIN 7, JAPAN 0x0C (travel map
  that opens most events), ACTION 0x0D, RSEL 0x0E (天/地 choice), DAY 0x12, BATTLE 0x15, TITLE2 0x16 (title
  screen). Id 8 shows during the boot logos (no file has it). BRAIN.BIN loads at the TITLE base 0x80162F88 instead.
- Cold boot + START every 40 frames reaches the route choice (overlay 0x0E) on disc 1 in ~2770 frames; on disc 2
  New Game loads a field event directly. warp.lua waits until a probe task it swaps in for the idle task ticks
  (counter at 0x8000F0F0, code at 0x8000F040: RAM zero above the kernel) so it only warps into a running loop.
- **Starting a DAY-bound event from the route-choice screen crashes** (exception at 0x80166238 called from
  0x8006AC44: the RSEL overlay's tasks stay registered and DAY.BIN overwrites them). Hop first: target `7>2` starts
  event 7, waits for its JAPAN/ACTION overlay, then starts event 2.

## Mode setters (EXE 0x8004C000-0x8004CA40; mode list head 0x80136BF8)
| setter | first mode fn | screen |
|---|---|---|
| 0x8004C068 | 0x8004C280 | RSEL route choice (new game) |
| 0x8004C7E0 | 0x8004C788 | title OPTION path (garbled when called from a warp: use the title route) |
| 0x8004C840 | 0x8004C330 | field (event) |
| 0x8004C8A0 | 0x8004C3E4 | TITLE |
| 0x8004C900 | 0x8004C450 | DAY arg 0: disc check ("DISC 1/2を入れてください" screens) |
| 0x8004C960 | 0x8004C4CC | DAY arg 1: memory-card LOAD |
| 0x8004C9C0 | 0x8004C540 | BRAIN (= OPTION menu; from a warp its background is stale VRAM) |
Title returns 0..4 into a jump table at 0x80010398: 0 new game (C068), 1 load (0x8003BC4C + C960), 2 option
(C7E0), 3 BRAIN (C9C0), 4 0x8001AEF0. `call:ADDR` targets in warp.lua call a setter once from the main loop.

## Title (verified by shots: scenes title, title_menu, title_load, option)
- TITLE2 (0x16) loads at ~2040 frames with START mashing; its intro plays ~450 frames, then PUSH START; START
  opens LOAD / NEW GAME / OPTION (cursor on NEW GAME). START or ○ confirms, × backs out (title menu then reads
  NEW GAME / OPTION / CONTINUE). OPTION = the BRAIN menu: 守護獣戦術指南 守護獣図鑑 / イベント再現 用語辞典 /
  キャラファイル EXIT (2 columns), ○ enters, "PUSH ○ MUSIC MODE" bar (button not yet found).

## Memory card (verified: checksum matches the game-written system file)
- Files: `BISLPS-01297GRS` system file (1 block), `BISLPS-01297GRD` game save. Title "ＧＲ－００　ガーディアン
  リコール　システムファイル". Writer 0x8003B8C8..0x8003BB0C, data builder 0x8003B7F8.
- **Checksum**: byte 0x1FFE of the 8 KB block = sum of bytes 0x0000-0x1FFD & 0xFF (fn 0x8005EEFC; check 0x8005EF24
  is skipped while SELECT is held or u32 [0x80152600] != 0).
- GRS data: +0x200.. zero; +0x4CA 0x14 bytes; +0x4DE 0x180 bytes copied from 0x80157A90; +0x6D6 0x34 bytes of
  options from 0x8013DE00 (volumes 0x50...). The "si" struct printed by debug fn 0x8004ED84 lives at 0x80152258:
  tu_info[14].flag +0x00, rep_info.a[43] +0x0E, rep_info.b[41] +0x39, char_info[25] {flag, msg_no} +0x62,
  gd_info[54].msg_bit +0x94, dic_info[90].flag +0xCA, data_test_flag +0x124, day_entry_count +0x128,
  warp_entry_count +0x130, xa_entcnt +0x1FC. How si maps into the card file: open (guess: the 0x180 block).
- GRD load 0x8003BC4C: card buffer (u32 at 0x800B5F04) +0x214 (0x26) -> 0x80136BD0, +0x23A (0x3C) -> 0x80141398,
  +0x276 (0x230) -> 0x800C4A20 (first u16 = event number -> 0x8013CEE4; 25 x 4-byte unit stats), 0x800C4B50
  (0x100) -> 0x80140550. Saving happens inside ACTION (fn 0x8003B1E8 called 11x from ACTION; ACTION has
  SAVE_EXTRA/SAVE_ARRAY debug dumps: turn-based map state) - not yet triggered.
