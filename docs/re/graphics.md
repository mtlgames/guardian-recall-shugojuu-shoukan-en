# Graphics-text survey (phase 1: static sweep complete; marker tour in phase 5 adds rows)

Scope per D5: translate all; keep the Japanese logo only if no official English one exists (the title logo is
already English "Guardian Recall"; the 守護獣召喚 subtitle and ガーディアンリコール ruby are Japanese).

Static sweep (rebuild into work/, not in git):
- TX03 archives: `tools/tx03_sweep.py FILE OUT` (UNN.PAK, SUBTI.PAK, BTL.PAK), `tools/sweep_sheets.py IDX PNGDIR OUT`.
- GRETC.RLZ: `tools/gretc.py extract GRETC.RLZ work/gretc`, then `tools/tim.py work/gretc/*.tim --out DIR`
  (2 TIMs fail: 246 brain/dayf.tim and DATA/NUE01.TIM, multi-image or odd CLUT; check when touched).
- STR movies: `tools/str_frames.py OUT FILE.STR..` (one frame per N s).

| # | Element | Source | Count | Notes |
|---|---|---|---|---|
| G1 | Episode title cards (第N話 + title + small English line) | SUBTI.PAK (TX03 160x240 4bpp) **and** copy in UNN g17 (+64); patch both | 53 | **English** (2026-11-24): `tools/gfx.py` draws every card from gfx/cards.tsv (Episode N, title, chapter; Liberation Serif Bold) and writes TX03 in place into SUBTI.PAK (index ACTION.BIN 0x12664) and g17 (+64 TIM header; g17 = alternate layouts, 37/47 = Hitomi Jin, 49 = Guardian Recall). Shot: `one.py battle --frames 16400` f016050 |
| G2 | Chapter cards (天の章, 地の章, 七龍の章, 覚醒の章, 龍鬼の章; vertical) | same SUBTI/g17 set | 5 | **English** (entries 39-43, "Sky Chapter"...; 26 px so SUBTI's 1-sector entries fit); not shot in game yet |
| G3 | Location/time cards (雪花旅館 + furigana + HOKKAIDO 19:44 ...) | UNN g24 (TX03 160x240) | 66 | **English** (2026-11-24): gfx/locations.tsv -> `tools/gfx.py location()` finds the Japanese block (tallest row band + furigana bands <= 17 px within 8 rows), clears its rows, draws the name aligned like the Japanese; the region/time lines stay. Text shrinks until the stream fits its byte count (65). Shots: `one.py ev02` (51), `one.py ev04` (20) |
| G4 | Battle victory/defeat condition cards (勝利条件 / 敗北条件 / 撤退可能) | UNN g18 (TX03 128x240) | 24 | **English** (2026-11-24): gfx/conditions.tsv -> `tools/gfx.py condition()` (Liberation Serif Bold Italic; bg index 0, ink 15), in place. Shot: `one.py tac_mission` final |
| G5 | Route choice 天 / 地 brush kanji (black and white versions) | GRETC rsel: 220 tiblk, 221 teblk, 223 tiwhi, 226 tewhi (TIM 192x128) | 4 | yin-yang halves 222/224/225/227 have no text |
| G6 | Title screen 守護獣召喚 + ガーディアンリコール ruby | UNN g21 0x1A5EC10 (96x40), 0x1A5F1D8 (64x36); logo with small subtitle UNN g09 0x4698CC (248x144) | 3 | **English** (2026-11-24, D15): `gfx.TITLE` (4bpp, in place in g21: subtitle "Shugojuu Shoukan", ruby blanked); g09 logo (8bpp, disc-swap screens) subtitle via `gfx.logo_sub` (its baked-in ruby stays). Shots: `one.py title_menu`, `one.py disc_swap2` |
| G7 | Boot memory-card messages | GRETC txd/save.txd (font text, not graphics) | - | text work |
| G8 | Disc-swap screen pieces: CHECK DISC を 2 / が違います / 中です 1 / OK! 入れて ください | UNN g09 0x467018 (244x160) **and** an uncompressed TIM copy (g9 entry 8, +0x60) for the DISC 1 screen | 1 | **English** (2026-11-24, D15): `gfx.swap_sheet` draws INSERT / WRONG / ... on the freed sheet areas (TIM copy outlined), `gfx.swap_layout` rewrites DAY.BIN sprites, layout lists 0x8016C3A0[0-7] and the digit x/y immediates (0x8016BC08-1C). All 8 states: `tools/swap_layout.py --render work/build/d1/tree OUT`; shots `one.py disc_swap/disc_swap2/disc_swap3` (state 0) |
| G9 | Battle kanji glyph set (族 霊 鬼 騎 士 ... 直 撃 心 眼 ...) used to compose class/skill labels | GRETC mill 004 split.tim (256x256) | ~53 glyphs | composer: BATTLE.BIN trait records 0x801713E8 + 12n, +4 -> glyph-index list (bytes, FF end) at 0x80171374+ (code 0x8016AE64/0x8016AF20); the string at +8 is never read. Redraw as English label art (phase 8) |
| G10 | Element pentagram (天 風 海 炎 雷 地 聖 飛 kanji round the circle) | GRETC brain 244 penta.tim (320x240) | 1 | |
| G11 | Dictionary cover: 用語辞典 seals + ガーディアンリコール katakana (English "GUARDIAN RECALL DICTIONARY" above) | GRETC dic 204 anim00.tim | 1 | 205 dicic.tim (small vertical label) also kanji |
| G12 | Guardian-dictionary scroll with vertical calligraphy | GRETC gd 210 nun0.tim (170x186) | 1 | decorative poem; translate or leave (low) |
| G13 | Character-file VOICE PLAY legend ○召 △戦 | GRETC cf 217 cfvc.tim (140x55) | 1 | |
| G14 | Character-file emblems (kanji in medallion, e.g. ruen) | GRETC cf 215/216/218 (320x240) | 3 | decorative; check in tour |
| G15 | Staff credits movie (burned-in Japanese roles/names; English "Thanks for Playing" end) | disc 2 STR/STAFF.STR | 1 movie | D3 = English credits: needs STR re-encode (phase 8) |
| G16 | Opening/ending logo with small 守護獣召喚 under "Guardian Recall" | STR movies (OP, MEND) | 2 | leave (movie, logo); see status Waiting |
| G17 | Tactics element orbs: kanji 主 天 地 雷 海 火 飛 冥 聖 in glass spheres (ring > DIAGRAM, unit HUD emblem left of Sp/Mp/Ap) | source not found yet (tactics overlay / UNN, phase 8) | ~9 | found in marker tour 2026-11-23 (tac_diagram, tac_unit_menu); element icons: redraw as letters or keep, decide in phase 8 |
| G18 | Title copyright line ©XING 1998／©1996.1998 アグミックス／藺宮 涼、龍炎 狼牙 (under the logo, 640x480 title); **English** (2026-11-24): g21 +0x64750 "Agumix / Ryo Kamiya, Ruen Rouga" (D15), shot `one.py title_menu` | same title image as G6 (UNN g21/g09, confirm) | 1 | found in marker tour 2026-11-23 (title); romanize: Agumix / Ryo Imiya, Roga Ryuen |

Checked, no Japanese: UNN g01-g08 (battle effect animation frames; first page of each sampled, rest same strip
format), g10 (55 face icons 42x50), g25 (earth), g09 rest (item/element icons, digits, **ASCII font 0x4069EC 128x25**,
"Player Turn / Enemy Turn"), g21 rest (title swirl frames); BTL.PAK 6964 battle sprites (43 wide images checked:
effects); GRETC btbg (battle bgs), gd2 (54 guardian art), cf2 (character art + English name labels, e.g. MIYUKI
AMAGI), opt (English: OPTION, music player), day (fontn.tim = English menu labels LOAD/CONFIG/NEXT/DIARY/ROUTE/SAVE/
OPTION + font), mill digits; DATA/MEM_ERR.TIM (English); STR movies other than STAFF (incidental signage only, e.g.
サウナ室 sign: leave).

Marker tour 2026-11-23 (all 128 scenes, final frames of every menu/tac/opt/day/title scene and every event read):
no font-drawn Japanese left; the Japanese on screen is G1-G5, G8, G10-G13 and the new rows G17 (tactics element
orbs) and G18 (title copyright line).
