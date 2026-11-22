# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool in progress (warp, scene list, tactics menus, battle, save editor, ending/credits,
  music mode done; game over and day diary left). Last build: none yet.
- **Done:**
  - Step 0: PCSX-Redux + SCPH-5500 BIOS in tools/ (original disc 1 boots, circle input + Lua probe verified),
    mkpsxiso/dumpsxiso 2.30, armips 0.11.0, xdelta3 3.1.0 in tools/; rom.sha1 pinned; pre-commit runs
    tools/check.py (failing test rejected: verified); guard hook active (blocked a heredoc); rulings D1-D7.
  - No earlier fan patch found (web search 2026-11-21).
  - Phase 1 recon (docs/re/): encoding + `tbl/jp.tbl`, renderer/glyph map, UNN.PAK index, TX03, scenario (g23) +
    battle quotes (g13); GRETC.RLZ decoded (txd markup text); EXE/overlay string ranges + pointers; free space;
    graphics survey G1-G16.
  - Phase 2 so far (docs/re/debug.md): `tools/debug/warp.lua` cold-boots and starts any event 1-70 through the
    game's own event starter, plus title menus, OPTION (= BRAIN menu) submenus, both disc-swap screens.
    `tools/debug/regen.py` runs the scene list in parallel (sheets in work/qa/warp/, states in work/states/);
    `tools/debug/mk_scenes.py` writes `tools/debug/scenes.tsv`; `overview.py` makes labelled sheets.
    Memory-card checksum known (byte sum at 0x1FFE); fixture `tools/debug/cards/sys.mcd` (system file only).
  - 2026-11-23: tactics map controls mapped (ev70): unit menu, 行動/超力/思考 submenus, △ ring menu (UNIT MAP
    MISSION DIAGRAM SEARCH CONFIG BREAK), BREAK = map save + quit prompt (= field pause/save screen). Scenes
    `tac_*` in scenes.tsv (unit menu, 行動, 超力, 思考, 情報, 待機, ring, CONFIG, MISSION = 勝利/敗北条件, BREAK
    prompt, セーブしました+quit prompt): all 11 regen ok and every final shot checked. Map save lands in the GRS system file (layout in debug.md); fixture
    `tools/debug/cards/ev70_map.mcd` (title gains CONTINUE). New probes tools/lua/{exec_log,watch_u32,pc_log}.lua.
  - 2026-11-23 (2): save editor `tools/debug/save.py` (lists fields; --unlock-all/--poke/--fill/--event; fixes the
    checksum; tests/test_save.py) + fixture `tools/debug/cards/unlock.mcd` (boots clean; every OPTION
    encyclopedia/replay entry incl. epilogues unlocked). scenes.tsv optional 8th column = card. New scenes:
    opt_*_all (5), tac_unit/map/diagram/search, replay_d2, ending (disc 2 イベント再現 > エンディング = ending +
    full STAFF.STR credits), epilogue_miyuki/yuko, opt_music(_track) (OPTION △ = MUSIC MODE, R2 = next track),
    **battle** (cold boot -> 天 new game -> ev01 tactics map, turn-cycle route, stops 500 frames into BATTLE 0x15
    at ~39500 frames: `regen.py --only battle --timeout 2400`). warp.lua: `0xADDR=0xV*N` fill writes, writes on
    ovl: scenes, route step `stop:X+N`. Turn flow: the turn passes only after **every master** acted (L2 = next
    unit); the ev70 "guardian stall" was that. ev48 = swap screen on both discs (labelled). Probes
    tools/lua/{story_blocks,poke}.lua.
- **Next (phase 2):**
  1. Full `regen.py --orig --timeout 2400` (110 scenes) and confirm all ok; look at any sheet not yet checked.
     epilogue_miyuki and epilogue_yuko end on the same motorbike frame: check their sheets differ later on
     (shared opening?) or lengthen them.
  2. **Game over**: needs a defeat. Unit HP is not a plain u16 next to the shown Sp/Mp/Ap (searched a RAM dump
     for 145/111/91/50). Try: diff RAM before/after the battle (work/qa/turns2 s000500 vs s002500 states) for the
     damaged unit, poke a master's HP low in the battle state and let the enemy phase run; or find the 敗北条件
     check near the "OldTurn"/"turn_chg_flag" prints (ACTION.BIN). Then GOD (pin HP) in warp.lua.
  3. **Day diary (day.txd)**: DAY entry 0x8016B998 (a0 = disc id == 0) from mode fn 0x8004C450; likely shown in
     the natural intermission after an event. Try finishing ev01 from the battle state (turn-cycle route), watch
     for overlay 0x12; or RE DAY's mode switch.
  4. Label the unlabeled events in `mk_scenes.py` (overview.py over work/qa/warp/ev*).
  5. Low priority: CONTINUE of a warp-made map save hangs on NOW LOADING (zero story blocks).
- **Open bugs:** none.
- **Waiting on the user:** (non-blocking) FMVs are voiced Japanese with no subtitles; default = no FMV subtitles,
  only the STAFF.STR credits get English (D3). Ask if subtitles are wanted.
- **Gotchas:** this PCSX-Redux nightly's `L.dump_ppu` writes 2 MB (first 1 MB = VRAM). Context-mode trims tool
  output > ~4 KB: read files with limit, keep command output short. Exec/read hooks need `emu.py --debugger`.
  `codex exec` hit its usage limit (until 2026-11-26): no codex reviews before then. Other repos' emulators share
  this machine: emu.py runs can be 10x slower under load; kill only PIDs whose command line has this repo.
  A game exception pauses PCSX (run ends 124): `tools/lua/pc_log.lua` logs the PC. Yes/no prompts in this game
  often default to いいえ. play.py `--every` sheets are 12 full frames: expensive to read, prefer single shots.
