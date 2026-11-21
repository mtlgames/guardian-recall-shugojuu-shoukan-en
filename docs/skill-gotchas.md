# Skill gotchas (one line each: reference file, then the fact)

- references/emulator-qa.md + scripts/lua/pcsx_lib.lua: PCSX-Redux nightly 32338 (2026-11-21) `PCSX.GPU.getVRAM()` returns 2 MB; the first 1 MB is the 1024x512 VRAM, the rest 0xFFFF filler. The lib comment says 1 MB.
- references/emulator-qa.md: with default `--mash`/`--mash-hold`, Guardian Recall's dialogue never advanced (route choice and title did), while a route of `4 circle;40 -` presses did. Use press routes for dialogue, or tune `--mash-hold`.
- references/platform-ps1.md: dumpsxiso extracts mixed-mode STR files as 2336-byte sectors (subheader + data); ffmpeg's psxstr demuxer rejects them until each sector gets the 16-byte sync+header back (tools/str_frames.py). One frame sheet per disc found the only burned-in text (credits).
- references/emulator-qa.md: L.on_exec/on_read/on_write stop with "require emu.py --debugger" (exit 2); PCSX runs have no --headless flag (window already hidden).
