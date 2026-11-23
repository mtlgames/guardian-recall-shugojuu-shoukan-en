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
| think help | g13.04 | 117 | 4 | measured | tac_think (orig + marker): box borders x 17 / 150, pen x 26, JP 9 chars x 13 px (ink to 143); 4 lines fill the box |
| field help | g13.05 06 17 18 | 220 | 3 | measured (17) | tac_ring_help (ring + SELECT): top band, pen x 50, JP 17 chars to x 271, marker runs to the screen edge (no clip): symmetric 50 px margin. 05/06/18 share the 17-char {wait}-paged format; their trigger (info-screen help) not found yet (○/SELECT/down in 情報 do nothing) |
| battle help | other g13 (02 item help, 07 ability, 10 think + reading) | 220 | 3 | guess | 02 = 10-char lines (narrower box?): 行動 > アイテム is empty in ev70, needs a map with items; 07/10 = 17-char lines like field help |
| replay list | rep.* | 223 | 1 (+ <= 34 bytes) | measured | opt_replay_all (orig + marker): rows centred by **byte count** (marker of the same byte length starts at the same x as the JP: start = 159.5 - 3.25 x bytes); number column ends x 43 -> start >= 48 -> bytes <= 34. VWF-aware centring would fix the off-centre English (phase 7 option) |
| charfile profile | cf.* with `&s(165,87)` | 129 | 5 | measured | opt_charfile_page: panel inner x 160-299, pen x 165 (5 px margin -> 294); JP auto-wraps at 10 chars, 16 px lines from y 87, panel bottom y ~180. English needs its own `&n()` |
| dictionary entry | dic.* | 114 | paged | measured | opt_dictionary_page: columns at x 40 (gutter x 160) and x 174 (page border x 288); JP 9 chars x 13 = 117 reaches 291. One entry per column, L/R pages it; total glyph records capped (compact DIC records, docs/re/text.md) |
| other txd | gd rep tu day save op, cf headers | 200 | - | guess | lists are centred (opt_*_all shots): budget = row width minus the number column; measure per screen |
| EXE/overlay strings | exe action battle hen day brain (5-digit ids) | 200 | - | guess | strings with refs: in place if they fit, else moved to STR_POOL (0x801F4000, 0x3FF8) with every ref repointed (tools/insert.py); no refs (BRAIN menu 6, action 1): bytes <= room - 1 (enforced). Marker build pads labels to 2.5 x JP chars. px per screen still to measure |
| evd unit names | map*.* | 75 | 1 | measured | hook evd_name (asm/hooks.asm): the evd keeps key 7F hi lo, the unit points at a payload name table, so any length fits the evd. 情報 / status panel: pen x 28, emblem from x 142 -> 108 px (20-char marker drawn whole, tac_info). ring > UNIT list (narrowest): name column x 25, orig JP ink to x 88, Ali values from x 103 -> 75 px. 20-char names draw whole there (overlapping Ali) since pool_grow (the old crash was the 2D pool, docs/re/text.md) |
