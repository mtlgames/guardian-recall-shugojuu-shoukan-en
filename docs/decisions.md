# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

All D1-D7 came from the owner's standing answers in the Orca one-shot brief (2026-11-21).

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-11-21 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics; Western name order (given name first). Owner's standing choice. |
| D2 | 2026-11-21 | Romanization source for names | official art, earlier patch, Hepburn | Official English names where they exist, else an earlier fan patch, else Hepburn without macrons. |
| D3 | 2026-11-21 | Credits | stay Japanese, translate | English. |
| D4 | 2026-11-21 | Abbreviations | engine work first (default), abbreviate | Engine work first (skill default; owner pre-approved defaults). |
| D5 | 2026-11-21 | Graphics text left in Japanese | none (default), list | Translate all (titles, menus, banners, cards); keep the original Japanese logo only if no official English version exists. |
| D6 | 2026-11-21 | Specs and plans | need approval, pre-approved | Pre-approved: continue through every checkpoint, report at the end. |
| D7 | 2026-11-21 | Existing saves / memory cards | use user's, build debug tool | None provided; build the debug tool as usual. |
| D8 | 2026-11-23 | Register, sound effects (phase 6 defaults; D6 pre-approval) | literal/neutral, natural with voices; romanised SFX, English SFX | Natural contemporary English that keeps each voice (dialect as light folksy English, no phonetic spelling); English onomatopoeia. Worker default under D6. |
| D9 | 2026-11-23 | Guardian species names | romanise (Eiki, Ryusatsuki), English coinages | Short English coinages (Shadow Oni, Dragonbane, Hornram); named guardians romanised (Gao, Koen). Readable on the unit list. Worker default under D6. |
| D11 | 2026-11-23 | Chapter labels 天の章第一話 (save list, card title) | "Sky Chapter, Episode 1", "Sky, Episode 1", "Sky 1" | "Sky, Episode 1": full words, and the Sky + Earth pair the save list draws on one row fits 180 px (the longer form needs ~240). Memory-card titles are full-width Shift-JIS (BIOS manager), via asm title_wide. Worker default under D6. |
| D10 | 2026-11-23 | Unit names wider than the 75 px UNIT list column (Suzune Ichinomiya 90 px) | abbreviate, widen the column (engine) | Engine (D4): full names stay; phase 7 widens or condenses the ring > UNIT name column. Budget 95 px until then. |
| D13 | 2026-11-24 | EXE list labels (Psi, traits, items, species, Forms, element icons) wider than their 2-4 kanji slots (Psi slot 32 px vs "Demon Might" 62) | abbreviate (Dm.Might), engine (widen columns / condensed font) | Engine (D4): full English names stay; ids listed in tools/exe_pending.txt carry an "engine pending" budget until phase 7 widens each screen and a shot replaces it with a measured row. Worker default under D6. |
| D12 | 2026-11-23 | Kana reading lines (dic entry reading, guardian page reading line) | keep romanised, drop, replace with other info | Drop: the English name is already readable; dic pages start the body after the heading, the guardian page reading row stays empty (&e()&d()). Frees room for English. Worker default under D6. |
