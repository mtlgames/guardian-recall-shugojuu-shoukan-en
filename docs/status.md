# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool in progress (warp + scene list working; save editor, battle/game-over/ending scenes
  left). Last build: none yet.
- **Done:**
  - Step 0: PCSX-Redux + SCPH-5500 BIOS in tools/ (original disc 1 boots, circle input + Lua probe verified),
    mkpsxiso/dumpsxiso 2.30, armips 0.11.0, xdelta3 3.1.0 in tools/; rom.sha1 pinned; pre-commit runs
    tools/check.py (failing test rejected: verified); guard hook active (blocked a heredoc); rulings D1-D7.
  - No earlier fan patch found (web search 2026-11-21).
  - Phase 1 recon (docs/re/): encoding + `tbl/jp.tbl`, renderer/glyph map, UNN.PAK index, TX03, scenario (g23) +
    battle quotes (g13); GRETC.RLZ decoded (txd markup text); EXE/overlay string ranges + pointers; free space;
    graphics survey G1-G16.
  - Phase 2 so far (docs/re/debug.md): `tools/debug/warp.lua` cold-boots and starts any event 1-70 through the
    game's own event starter (task 0x8013CEE0 / event no 0x8013CEE4), plus title menus, OPTION (= BRAIN menu)
    submenus, both disc-swap screens. `tools/debug/regen.py` runs the whole scene list in parallel (sheets in
    work/qa/warp/, states in work/states/); `tools/debug/mk_scenes.py` writes `tools/debug/scenes.tsv`;
    `overview.py` makes labelled sheets. Memory-card checksum found (byte sum at 0x1FFE); fixture card
    `tools/debug/cards/sys.mcd` (system file only).
- **Next (phase 2):**
  1. Read the last full regen (`python -X utf8 tools/debug/regen.py`, ~15 min, 85 scenes): fix any FAIL. Known:
     ev70 hangs on both discs (probably the ending: try `7>70` on disc 2), ev03 sits on NOW LOADING on disc 1,
     ev03/12/14/22/28/47/48 showed no lit frame in 1800 frames (give them more frames / ADVANCE=60).
  2. Label the unlabeled events in `mk_scenes.py` (overview.py over work/qa/warp/ev*), map each to its episode
     (day.txd 天/地/七龍/覚醒の章 第N話; 天 = ev1-9, 地 = ev10-19, 七龍 from ev20).
  3. Scenes still missing: a battle (BATTLE overlay 0x15: find the first event that reaches it, log shows
     "overlay 15"), game over (lose it: GOD/kill RAM via USD unit HP in ACTION's SAVE dumps), the ending and
     STAFF.STR credits, the day diary (day.txd), OPTION music mode (button unknown), field pause menu
     (リトライ / タイトルに戻る), the in-game save screen.
  4. Save editor `tools/debug/save.py`: needs a game-written GRD save (saver fn 0x8003B1E8 is called from ACTION,
     probably a field menu) and the system-file (GRS) layout for unlock-all flags (si struct 0x80152258; card
     +0x4DE block from 0x80157A90). Test: edited card boots, title LOAD shows it, no "壊れています".
  5. GOD / unlock-all options in warp.lua once the unit/flag RAM is known.
- **Open bugs:** none.
- **Waiting on the user:** (non-blocking) FMVs are voiced Japanese with no subtitles; default = no FMV subtitles,
  only the STAFF.STR credits get English (D3). Ask if subtitles are wanted.
- **Gotchas:** this PCSX-Redux nightly's `L.dump_ppu` writes 2 MB (first 1 MB = VRAM). Context-mode trims tool
  output > ~4 KB: read files with limit, keep command output short. Exec/read hooks need `emu.py --debugger`.
  `codex exec` hit its usage limit (until 2026-11-26): no codex reviews before then. Other repos' emulators share
  this machine: emu.py runs can be 10x slower under load; kill only PIDs whose command line has this repo.
  A game exception pauses PCSX (run ends 124): `work/probe_pause.lua` pattern logs the PC (docs/skill-gotchas.md).
