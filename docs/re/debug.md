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
  (= card +0x3A6, 0x100) -> 0x8013E550 (event flag array). Saving happens inside ACTION (fn 0x8003B1E8 called 11x from ACTION; ACTION has
  SAVE_EXTRA/SAVE_ARRAY debug dumps: turn-based map state) - not yet triggered.

## Save editor and OPTION unlocks (verified: scenes opt_*_all show every entry)
- `tools/debug/save.py CARD` lists the GRS/GRD fields; `--out NEW --unlock-all` (or `--poke OFF=HEX`, `--fill
  OFF:LEN=V`, `--event N`) edits a game-written card and fixes the +0x1FFE checksum. Fixture
  `tools/debug/cards/unlock.mcd` = sys.mcd + `--unlock-all`; boots with no card error.
- The OPTION encyclopedias don't keep their own flags: BRAIN.BIN (0x80163030, 0x80163140, 0x80163298, loaded at
  0x80162F88) rebuilds the si struct (0x80152258) on entry from the story blocks the card load fills:
  0x80141398 (card +0x23A; +0xA = 50 per-entry bytes), 0x8013E550 (card +0x3A6, 0x100-byte event-flag array),
  0x80136BD0 (card +0x214). Writing si or 0x80157A90 in RAM does nothing (rebuilt). --unlock-all sets
  +0x244..+0x275 = 1 and +0x3A6..+0x4A5 = 0xFF.
- The map save (BREAK) does not write si. Overlay ids: HEN.BIN 0x0B (編成 formation/equipment screen before a
  tactics map: × twice -> 編成を終了します。 はい), CALL02 9, MAP02 6, MENU 0x0A, DIC 0x0F, CF 0x10, GD 0x11, REP 0x13,
  TU 0x14.

## Tactics map (verified on ev70 by play.py session work/play/t70 and the tac_* scenes)
- Overlay id reads 0 on the tactics map. ○ on a master: 移動 情報 行動 思考 待機; 行動 -> 超力 アイテム 話す 送還;
  思考 -> 思考変更 対象確認 命令実行 (order list 私を守護せよ 03, 気力を癒せ 15, ... with a help box). Guardians show
  only 情報. △ opens the ring menu UNIT MAP MISSION DIAGRAM SEARCH CONFIG BREAK (↓ steps; R1/L1 rotate camera).
- BREAK = map save: "マップセーブを行いますか？" はい/いいえ, **cursor starts on いいえ** (press ↑ first); はい ->
  セーブ中です (~900 frames) -> セーブしました + "ゲームを終了しますか？" ゲームを続ける / タイトルに戻る (title
  return path). Code: prompt fn 0x80170FC4 (ACTION ovl), save state machine 0x8016FEBC, quit prompt 0x8016F110.
- The map save goes **into the GRS system file**, not a GRD file: card block +0x276 u16 = event number (0x46),
  map state at +0x342..+0x1B91, checksum +0x1FFE still the byte sum. Fixture: `tools/debug/cards/ev70_map.mcd`.
  With it the title menu gains CONTINUE (LOAD / NEW GAME / OPTION / CONTINUE; ↓↓ from NEW GAME); title LOAD
  still says "データファイルが存在しません" (needs a GRD). CONTINUE from a warp-made save hangs on NOW LOADING
  (>6500 frames, cold boot too): the story-state blocks it restores (+0x214 -> 0x80136BD0, +0x23A -> 0x80141398,
  0x800C4A20.., 0x80140550) are all zero after a warp, unlike a played game. Open: fill them, or make the save
  from a played route.
- **Turn flow** (verified on ev01, natural new game): after a master's action the cursor jumps to its guardian
  (only 情報); the turn does not pass until **every master** has acted: **L2** (R2 likely the other way) cycles to
  the next unit. After the last master: enemy phase (red M/G UNIT panels), then scripted dialog. The ev70 / warped
  ev02 "stall" was this, not missing state. Warped events give Lv 65 masters; a natural new game Lv 3-6.
- Natural new game: `route_choice` + ○ (天) starts event 1 (JAPAN map, story, then tactics map ~20000 frames of ○
  mashing). States: work/states/rc_ten.sstate (just after the choice), work/qa/nat1/s*.sstate.
- Battle: BATTLE.BIN (0x15) plays attack animations (G<guardian>_B<anim>, M<master>_B<anim> from BTL.PAK). Loader fn 0x8002B054 (loads BATTLE.BIN, string 0x80010B18), used as
  a fn pointer at 0x8002CEA4.
- GRD filename "BISLPS-01297GRD" at 0x8009B4D8, used in 0x8005DF34 / 0x8005E034 / 0x8005F02C (card lib wrappers;
  callers not found by direct jal: probably via a pointer).
- **Units (USD[65])**: array at **0x800C3050**, stride 0x64; +0 Lv, +4 unit_flag (1 = present), +6 unit_no,
  **+0x10 HP (current, the "Sp" bar)**, +0x12 AP, +0x14 MP (layout from ACTION's debug dump at 0x801690AC; HP
  verified: an enemy went 112 -> 51 in the `battle` scene). 0-24 = allies (USD_ST[25]), 25+ = enemies. BATTLE
  copies stats in and writes them back at the end, so poke HP on the map, not mid-battle. HP=1 then an enemy hit:
  the unit "retires" with a death line (ちかな まいったね。こんなとこでリタイアかい). Level table (Sp u16, Ap u8, Mp u8,
  8 bytes/level) at 0x80181490 (ev70 RAM).
- Conditions per map (ring > MISSION): ev70 勝利 真・龍鬼の戦闘不能 / 敗北 味方の全滅; **ev01 勝利 敵の全滅 / 敗北
  美由紀の戦闘不能** (unit 0). The check runs after a battle, not on HP alone: poking HP 0 or flag 2 on the map
  does nothing. **Game over verified** (work/qa/gover01c): 美由紀 at 1 HP, enemy hit -> "GameOver" graphic + defeat
  dialog -> 勝利/敗北条件 card -> the map restarts at Turn 01 with full HP. Scene `gameover` (new game, writes
  `0x800C3060<0x1` = clamp her HP, stops on her HP reaching 0). Unit +8 = order slot, +0x30/+0x34 -> sprite
  objects (world x/height/z at +0x48 halfwords, 100 per tile); ev01's leader (unit 26) never leaves its spot.
- **Stall after an ally master retires** (emulator): after ちかな's retire line u16 0x8013CEEE keeps bits 0x14
  (normal 0x20; bit 4 halts the event script) and the map ignores all buttons for good. Clearing them resumes
  the enemy phase: `tools/lua/unstick.lua`. Not a translation concern; likely an XA end PCSX-Redux never signals.
- Probes: `tools/lua/units.lua` (USD dump every N frames), `tools/lua/clamp_hp.lua` (ALLY_HP / ENEMY_HP).
- Defeat voice clips: XA001-003 `gr_xa\編集map\61ゲームオーバー`; quotes
  in UNN.PAK group 13 sub-entry 11 (ここは退いた方がいい ...).

## Event script interpreter (EXE; verified by exec_log)
- Buffer **0x800B68F0**, PC = u16 at gp+0xC6 (gp = **0x800B58E4**, so 0x800B59AA); gp+0xC4 = wait. Dispatcher
  0x8001B3xx reads an op byte: op < 0x20 -> fn table 0x8009328C[op], else 0x8009338C[op-0x20] (8-byte entries fn,
  flag). Args are little-endian u16 (0x8001D8EC). It is halted while u16 0x8013CEEE & 4 or 0x8013CEEC & 8.
- **op 0x23** = system call 0x8001EAE4(sub, a, b), sub 0..0x27 via jump table 0x80010650: 1 = end of episode ->
  DAY menu (installs mode fn 0x8002059C, which loads DAY.BIN and calls 0x80167C8C(0) = diary/save menu task
  0x80166508; 0x80167C8C(1) is the title LOAD path), 2 = load ACTION.BIN, 4 = DAY disc check (0x8016B998),
  19 = load JAPAN.BIN. warp.lua target `V>op:23010000000000` injects it at the PC inside event V.
- **DIARY reached naturally (2026-11-23 (4))**: ev01 won from `work/states/battle.sstate`: clamp_hp ENEMY_HP=1 +
  待機 loop (4 of 5 enemies die attacking, work/qa/win01/s040000), then the leader (unit 26, never moves) teleported
  next to the party by poking its sprite objects (0x8013E980/2/4 = 600,-100,300; 0x8013E9FC/E/A00 = 600,-100,200),
  enemy phase kills it, victory dialog, ○ mash: DAY overlay 0x12 at +3509 frames -> DIARY page (天の章第一話
  守護獣召喚, NAME 天城美由紀, PLACE 福岡 天神高校, 4-line entry). State: `work/states/diary.sstate`. Zeroing every
  enemy's HP on the map does not win: the leader must die in a battle.
- **DAY menu (no stall)**: Up/Down pick the tab (task +0x1A0, 0..5 = DIARY ROUTE SAVE LOAD CONFIG NEXT, label on
  the right edge), ○ opens it, × closes; ○ on DIARY does nothing visible (earlier "stall" = only ○ was tried).
  ROUTE = 地の章をプレイしますか？ (はい switches route), SAVE/LOAD = block list (save prompt defaults to いいえ),
  NEXT = 次のマップへ進みます. Tasks: DAY 0x80166508 (a0 0x8017C27C), menu subtask 0x8016681C (state +4: 0 idle,
  1/3 open/close), page handlers table 0x8016C058. Pad edge flags: u32 per button at 0x80152588 + 8*i (up
  0x80152598, down 0x801525A0, × 0x801525D0, ○ 0x801525D8); the page is drawn once, poking 0x8013CEE4 later
  changes nothing.
- **DAY save** (DAY > SAVE): file BISLPS-01297GRDA (block 2 on `tools/debug/cards/day01.mcd`, saved from
  diary.sstate). Title > LOAD of it opens the DAY menu on the DIARY page (tab cursor on LOAD) from a cold boot:
  scenes `day_*`. Loader 0x8005D9C4: +0x200 (0x34) -> 0x8013DE00, +0x234 (0x180) -> 0x80157A90, whose +4 u16 is the
  event -> 0x8013CEE4, so **GRDA +0x238 = episode** (`save.py --file GRDA --event N`; scenes.tsv card `day01.mcd@N`).
  Diary text = day.txd slot 4*(N-1) (event 5 = 天の章第五話, 12 = 地の章第一話); slots 512-708 not yet tied to events.
- **DAY menu via op warp** (older notes): the op runs and DAY.BIN loads, but from ev20 (ACTION) the task crashes ~8 frames
  later (returns to 0x8013DE00 with sp 0x801FFFD0: a clobbered stack ra); from ev7 (JAPAN map) the console resets
  during a CD read. Likely missing story state (the case also reads 0x80141398[event], card +0x23A, zero after a
  warp). Next: `tools/lua/write_val.lua` on the stack slot, or play ev01 to its end (natural op) and save a state.
- DAY enter modes (0x8016B998 a0 = disc id == 0): disc 2 -> 0 = "DISC 1を入れてください"; disc 1 -> (byte
  0x8013E57B & 1) + 1: 1 = DISC 2 screen (scene disc_swap2), 2 = second DISC 2 screen (heroine + logo, disc_swap3).
- Probes: `tools/lua/exec_range.lua` (exec hooks on every word of a small range), `tools/lua/write_val.lua` (who
  stores VALUE into a range), `tools/lua/dumpram_at.lua` (several frames: `DUMP_AT='5,600'`).
- Probes: `tools/lua/exec_log.lua` (log hits on addresses, --debugger), `tools/lua/watch_u32.lua` (log u32 or
  *pointer changes per frame), `tools/lua/pc_log.lua` (pc/ra every N frames + pause catcher for hangs).
- **tac_search stall is not ours** (2026-11-23): on the cursor reaching SEARCH (~frame 4950, before ○) the game jumps
  to 0x6420 from the 3D primitive dispatch (0x80074C88, ra 0x80079C28; packet pointer 0x801617C0 = frame struct
  +0x211C). The **original disc** does the same with `one.py tac_search --orig` (twice, also with 120 more frames before
  ○); some marker builds pass, depending on build only (load timing). Marker-table bisect (MARKER_KEEP/MARKER_SAME)
  chased this for hours: when a scene stalls, run it with `--orig` first.
