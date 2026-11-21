# Reverse-engineering notes

One file per subsystem (text engine, pointers, compression, font, graphics). Mark every finding with how far it is
proven, so a later session doesn't build on a guess:

- **verified** - and how: a decoded known string, a corrupt-and-boot test, a breakpoint hit on the drawing path, a
  passing roundtrip test. Name the test or savestate.
- **guess** - and why it seems likely (byte pattern, another game, an earlier patch's notes). Promote it to verified
  before code depends on it.

Addresses are for the dump in `rom.sha1` unless a note says otherwise.

| File | Covers | State |
|---|---|---|
| text.md | encoding, control codes, renderer + glyph map, scenario/battle text blocks, other string sites | encoding/blocks verified; buffer size, overlay addresses open |
| containers.md | disc layout, UNN.PAK TOC + sub-tables, TX03 codec, GRETC.RLZ, overlays | UNN/TX03 verified; GRETC unknown |
| graphics.md | graphics-text survey | in progress |

Tools: `tools/gr_text.py` (decode), `gr_scan_blocks.py`, `gr_codes.py`, `gr_strings.py`, `sjis_survey.py`,
`gr_index.py` (UNN index), `tx03.py`, `tx03_sweep.py`, `sweep_sheets.py`, `vram_view.py`, `tools/lua/dumpram_at.lua`.
Savestates (work/states/, regenerate from cold boot if lost): `orig_title` (title screen), `orig_tenchi`
(天/地 choice), `orig_dlg1` (first Earth-route dialogue). Dialogue advances on a circle *press*; `--mash` holds and
does not advance text.
