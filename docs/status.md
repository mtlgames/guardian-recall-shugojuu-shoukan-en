# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool in progress (warp + scene list + tactics menus + map save working; battle, save
  editor, game-over/ending scenes left). Last build: none yet.
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
- **Next (phase 2):**
  1. (tac_* done.) Note: a scene's run ends at 2800 + frames but the warp lands ~2944: give routes headroom.
  2. **Battle (overlay 0x15)**: on ev70 Turn 01 the turn never passes to the guardian/enemy phase (cursor stays on
     guardian 天龍 after master 待機). Try: move the master next to an enemy (移動) so "私を守護せよ" fires; other
     events' first maps (ev02 熊本支部 etc.) where enemies start close; or RE the loader 0x8002B054 (fn pointer
     at 0x8002CEA4) and the turn/phase state in the tactics overlay, then warp straight to a battle.
  3. Save editor `tools/debug/save.py`: CONTINUE of a warp-made map save hangs on NOW LOADING because the story
     blocks (+0x214/+0x23A/0x800C4A20/0x80140550) are zero after a warp. Need one played save (GRD via LOAD, or
     map save from a properly entered event) as the base; then map fields by diffing. The ev03 NOW LOADING hang
     may share this cause (zero story state).
  4. Label the unlabeled events in `mk_scenes.py` (overview.py over work/qa/warp/ev*); ev48 on disc 2 shows
     "DISC 1を入れてください" (it is a disc-1 event or a swap point: fix its disc column).
  5. Scenes still missing: game over, the ending and STAFF.STR credits, the day diary (day.txd), OPTION music
     mode, ring MAP/DIAGRAM/SEARCH/UNIT screens, ev70 hang/ending check (`7>70` on disc 2).
  6. GOD / unlock-all options in warp.lua once the unit/flag RAM is known.
- **Open bugs:** none.
- **Waiting on the user:** (non-blocking) FMVs are voiced Japanese with no subtitles; default = no FMV subtitles,
  only the STAFF.STR credits get English (D3). Ask if subtitles are wanted.
- **Gotchas:** this PCSX-Redux nightly's `L.dump_ppu` writes 2 MB (first 1 MB = VRAM). Context-mode trims tool
  output > ~4 KB: read files with limit, keep command output short. Exec/read hooks need `emu.py --debugger`.
  `codex exec` hit its usage limit (until 2026-11-26): no codex reviews before then. Other repos' emulators share
  this machine: emu.py runs can be 10x slower under load; kill only PIDs whose command line has this repo.
  A game exception pauses PCSX (run ends 124): `tools/lua/pc_log.lua` logs the PC. Yes/no prompts in this game
  often default to いいえ. play.py `--every` sheets are 12 full frames: expensive to read, prefer single shots.
