# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 2. Debug tool next (phase 1 recon done 2026-11-21). Last build: none yet.
- **Done:**
  - Step 0: PCSX-Redux + SCPH-5500 BIOS in tools/ (original disc 1 boots, circle input + Lua probe verified),
    mkpsxiso/dumpsxiso 2.30, armips 0.11.0, xdelta3 3.1.0 in tools/; rom.sha1 pinned; pre-commit runs
    tools/check.py (failing test rejected: verified); guard hook active (blocked a heredoc); rulings D1-D7.
  - No earlier fan patch found (web search 2026-11-21).
  - Phase 1 recon (docs/re/): encoding + `tbl/jp.tbl` (roundtrip on 4994 strings), renderer/glyph map, UNN.PAK
    index, TX03, scenario (g23) + battle quotes (g13); **GRETC.RLZ fully decoded** (XOR directory, RLE, XOR'd .txd
    markup text for dictionary/character files/diary/replay/tutorial/save messages); EXE/overlay string ranges +
    pointer format (abs u32 + lui/addiu), overlay base 0x80166218 (TITLE 0x80162F88); free-space candidates
    (RAM 0x801B6DC8-0x801FF938 main one); graphics survey static sweep complete G1-G16 (UNN, SUBTI, BTL, GRETC TIMs,
    STR movies: only STAFF.STR credits have burned-in text).
- **Next (phase 2, debug tool):** reach every scene from a cold boot without a save.
  1. Leftover event debug menu in the EXE ("EVENT NO.%d", "EVENT NUMBER CHANGE: LEFT OR RIGHT", "START:MEMORY
     CARD LOAD", file 0xA24-0xA6A): find the code that draws it and how to enable it (RAM flag / button combo).
  2. Otherwise a warp.lua that sets the event/stage number (find it by RAM search across two scenes) and story flags.
  3. Scene list `tools/debug/scenes.tsv`: each episode (天/地 routes, 52 episodes), chapter cards, a battle, map,
     menus (BRAIN: 用語辞典/守護獣図鑑/キャラファイル, day diary, save/load, option), disc swap, game over, ending, credits.
  4. Save editor `save.py` for the memory-card save (stage, route, names).
  5. Also open from phase 1: battle/menu tour for runtime-composed graphics (G9 kanji labels, G8 disc swap);
     txd renderer address; BRAIN.BIN load address; GRETC checksum algorithm (non-fatal); confirm free RAM in battle.
- **Open bugs:** none.
- **Waiting on the user:** (non-blocking) FMVs are voiced Japanese with no subtitles; default = no FMV subtitles,
  only the STAFF.STR credits get English (D3). Ask if subtitles are wanted.
- **Gotchas:** this PCSX-Redux nightly's `L.dump_ppu` writes 2 MB (first 1 MB = VRAM). Context-mode trims tool
  output > ~4 KB: read files with limit, keep command output short. Exec/read hooks need `emu.py --debugger`.
  `codex exec` hit its usage limit (until 2026-11-26): no codex reviews before then.
