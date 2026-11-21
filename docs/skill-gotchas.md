# Skill gotchas (one line each: reference file, then the fact)

- references/emulator-qa.md + scripts/lua/pcsx_lib.lua: PCSX-Redux nightly 32338 (2026-11-21) `PCSX.GPU.getVRAM()` returns 2 MB; the first 1 MB is the 1024x512 VRAM, the rest 0xFFFF filler. The lib comment says 1 MB.
- references/emulator-qa.md: with default `--mash`/`--mash-hold`, Guardian Recall's dialogue never advanced (route choice and title did), while a route of `4 circle;40 -` presses did. Use press routes for dialogue, or tune `--mash-hold`.
