# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 1. Research and recon in progress (Step 0 done). Last build: none yet.
- **Done:**
  - Step 0: PCSX-Redux + SCPH-5500 BIOS in tools/ (original disc 1 boots, circle input + Lua probe verified),
    mkpsxiso/dumpsxiso 2.30, armips 0.11.0, xdelta3 3.1.0 in tools/; rom.sha1 pinned; pre-commit runs
    tools/check.py (failing test rejected: verified); guard hook active (blocked a heredoc); rulings D1-D7.
  - No earlier fan patch found (web search 2026-11-21).
  - Recon (docs/re/): encoding + control codes, renderer and per-scene glyph map, UNN.PAK TOC/sub-tables in EXE,
    scenario (group 23) and battle quotes (group 13) block format, TX03 decoder, other string sites, graphics
    survey started (title cards, chapter cards, location cards, battle condition cards).
- **Next (phase 1 remainder):**
  1. Review the remaining sweep sheets (docs/re/graphics.md "Still to review"); rebuild with tx03_sweep.py +
     sweep_sheets.py. Keep image reads few: one sheet at a time.
  2. GRETC.RLZ format (loader 0x80014CCC, decompress/CRC); find title-screen and 天/地 graphics.
  3. Trace pointers for EXE/overlay strings (disasm.py xref; overlay load addresses) and record text ranges.
  4. Free space: EXE/RAM slack, scenario buffer size at 0x800D16F8.
  5. Tour menus/battle/save screens for graphics text (orig_dlg1 state onward); add rows to graphics.md.
- **Open bugs:** none.
- **Waiting on the user:** nothing.
- **Gotchas:** this PCSX-Redux nightly's `L.dump_ppu` writes 2 MB (first 1 MB = VRAM). Context-mode trims tool
  output > ~4 KB: read files with limit, keep command output short.
