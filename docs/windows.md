# Window budgets (phase 5 width gate)

Machine-readable rows: `tools/windows.py` (VARIANTS; `--cover` lists records per variant and records with no budget;
without flags it lints every `en`). This file holds the evidence. Widths are measured in pixels on marker-build shots
(build.py --marker, `work/qa/warp/<scene>/final.png`) against the original's shot of the same scene (`--orig`):
px = last column a glyph may reach minus the line's x origin. English widths = fonts/vwf12.txt advances (glyph width
+ 1 px gap; space 4 px).

**Glyph torture line** (2026-11-23, scenario renderer): `build.py --marker --qa 'g23.01.000=Yumi\n!"#$%&...K\nL...s\ntuvwxyz{|}~  a  b\n{wait}'`
(all printable ASCII split to 222/223/85 px, i.e. lines that fill the 224 px box), `one.py ev02 -- --frames 5400`:
every glyph distinct and correct, double spaces visible, y/g/p descenders inside the box, page cursor clear of a
223 px line. Still to torture: the txd renderer (0x800133D4), generic UI (0x80043A64/0x80044624), DIC grid.

| Variant | Ids | px/line | lines | Status | Evidence |
|---|---|---|---|---|---|
| scenario box | g23.* | 224 | name + 3 per page | measured | ev02/ev03 marker shots: pen x 70, JP 17 x 13 px; page cursor at x 296 between lines 2 and 3 (docs/re/text.md) |
| battle quote | g13.00 01 08 09 11 12 15 16 | 224 | name + 3 | measured | gameover marker shot: same portrait box as the scenario, pen x 70, translucent box ends x 310 |
| battle comment | g13.13 14 (no name line) | 224 | 3 | measured | gameover shot ([14.000] in the quote box, 3 lines) |
| power help | g13.03 | 232 | 3 | measured | tac_power: border x 35 and 285, pen x 44, margin 9 px each side -> ink to x 276; tag + 2 lines + 3rd line visible |
| battle help | other g13 (02 item help, 04/10 think, 05 06 17 18 info help, 07 ability) | 232 | 3 | guess | JP 02/04 lines are 9-10 chars (a narrower box?): tour item/think/info help with markers |
| charfile profile | cf.* with `&s(165,87)` | 129 | 5 | measured | opt_charfile_page: panel inner x 160-299, pen x 165 (5 px margin -> 294); JP auto-wraps at 10 chars, 16 px lines from y 87, panel bottom y ~180. English needs its own `&n()` |
| dictionary entry | dic.* | 114 | paged | measured | opt_dictionary_page: columns at x 40 (gutter x 160) and x 174 (page border x 288); JP 9 chars x 13 = 117 reaches 291. One entry per column, L/R pages it; total glyph records capped (compact DIC records, docs/re/text.md) |
| other txd | gd rep tu day save op, cf headers | 200 | - | guess | lists are centred (opt_*_all shots): budget = row width minus the number column; measure per screen |
| EXE/overlay strings | exe action battle hen day brain (5-digit ids) | 200 | - | guess (bytes measured) | in place: bytes <= room - 1 (enforced); px per screen still to measure (menus, tac_* windows, ring labels) |
| evd unit names | map*.* | 80 | 1 | guess (bytes measured) | in place in the evd bytecode: bytes <= JP bytes (enforced; 朱雀 = 4 bytes, so most English names need the evd op to grow or a name table) |
