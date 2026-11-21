# Graphics-text survey (phase 1, in progress)

Scope per D5: translate all; keep the Japanese logo only if no official English one exists (the title logo is
already English "Guardian Recall"; the 守護獣召喚 subtitle and ガーディアンリコール ruby are Japanese).

Static sweep: `tools/tx03_sweep.py FILE OUT` decodes every TX03 stream (4bpp grey PNGs, index file with every
failure), `tools/sweep_sheets.py IDX PNGDIR OUTDIR --cols 8 --max 48 --div 2` makes per-group sheets
(work/gfx/sweep/sheets/gNN_sheet*.png). Rebuild them; work/ is not in git.

| # | Element | Where seen | Source | Count | Reviewed |
|---|---|---|---|---|---|
| G1 | Episode title cards (第N話 + title + small English line, e.g. 襲撃！旅立ちの序曲 JOURNEY) | after route choice | SUBTI.PAK (TX03 160x240 4bpp) **and** its copy in UNN.PAK group 17 (+64); patch both | 53 (incl. duplicates) | yes, all 3 sheets |
| G2 | Chapter cards (天の章, 地の章, 七龍の章, 覚醒の章, 龍鬼の章; vertical) | before episode cards | same SUBTI/g17 set | 5 | yes |
| G3 | Location/time cards (雪花旅館 + furigana + HOKKAIDO 19:44; 荏狗覇莵基地 ... Unknown Place) | after episode card | UNN.PAK group 24 (TX03 160x240) | 66 | sheet 1 of 2 |
| G4 | Battle victory/defeat condition cards (勝利条件 / 敗北条件 / 撤退可能) | battle start (guess) | UNN.PAK group 18 (TX03 128x240) | 24 | yes |
| G5 | Route choice 天 / 地 (brush kanji over yin-yang) | new game | not found yet (GRETC.RLZ?) | 1 screen | tour only |
| G6 | Title screen: 守護獣召喚, ガーディアンリコール ruby, copyright line with Japanese names | title | not found yet (GRETC.RLZ / TITLE*.BIN?) | 1 screen | tour only |
| G7 | Boot memory-card messages (システムファイルが有りません etc.) | boot without card | probably font text (check) | - | tour only |

Still to review (sheets exist): UNN groups 1, 2 (text-like strips 504x12, 588x12, 240x24: likely pre-rendered
text lines), 3 (1459x16 strips), 4-9, 10 (55x 42x50), 21, 24 sheet 2, 25. Not yet swept: BTL.PAK (6965 TX03,
battle sprites), GRETC.RLZ (format unknown), `DATA/*.TIM` (MEM_ERR.TIM, NUE01.TIM, HAM2.TIM), STR movies (check
for burned-in text: opening showed none), the 天/地 screen, menus, battle UI, save/load screens, ending/credits
(STAFF.STR on disc 2).
