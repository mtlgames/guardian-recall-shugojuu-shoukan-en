# Phase 6 review pass

One read-only pass per batch over `work/qa/review/pairs/bNNN.txt` (`python -X utf8 tools/pairs.py bNNN`; rows that
copy an earlier batch's JP + English are listed as `==` and judged there). Brief: the skill's
`assets/reviewer-brief.md` (accuracy, glossary, voice per docs/style-reference.md, naturalness). No reviewer
subagent (Orca worker) and codex is at its usage limit until 2026-11-26: the worker reviews in a fresh read of each
pairs file. Critical/Important get fixed in `work/tl/bNNN.out.tsv` + `batches.py merge bNNN --overwrite` (then
`pairs.py --drift` prints nothing); Minors go to `docs/polish.md`.

| Batch | Verdict | Fixed (Critical/Important) | Notes |
|---|---|---|---|
| b001 | Approved | | evd unit names match the glossary |
| b002 | Approved | | |
| b003 | Approved | | pilot ch. 00; voices match the style reference |
| b004 | Approved after fix | g23.01.016 (re-rated Important by the phase-6 review: Tomomi's silky voice flattened, いいわ misread as "Never mind"; now "...Very well. You'll come over here this instant, won't you, dear?") | |
| b005 | Approved | | |
| b006 | Approved | | |
| b007 | Approved | | |
| b008 | Approved after fix | g23.04.047 (re-rated Important: Yumi's cold フフフッ was "Hahaha"; now "Heh heh heh...") | |
| b009 | Approved after fix | g23.06.000 (Important: まだぁ～ = "are they here yet", Reiko waits in ambush; was "Are we there yet") | |
| b010 | Approved | | |
| b011 | Approved | | |
| b012 | Approved after fix | g23.08.213 (Important: 美里のためにもね = "for Misato's sake too"; was "Not for Misato's sake, either!", reads as the opposite) | |
| b013 | Approved | | Iwao pun -> "Boulder" |
| b014 | Approved | | 10.149 choice pair fine |
| b015 | Approved | | Sayaka's drawl consistent |
| b016 | Approved | | "You dirty rat" / "Don't call me 'rat'" adaptation works |
| b017 | Approved | | |
| b018 | Approved | | |
| b019 | Approved | | |
| b020 | Approved | | |
| b021 | Approved | | |
| b022 | Approved | | |
| b023 | Approved after fix | g23.18.017 (Important: 私の仲間 = her Dragon Wielder companions; was "My friend... meet her") | |
| b024 | Approved | | Rairyu / Thunder Dragon gag inverted for English |
| b025 | Approved after fix | g23.20.203 (Important: Akira's roll call now matches 15.035/17.038; same fix in b030 g23.26.222) | |
| b026 | Approved | | |
| b027 | Approved | | |
| b028 | Approved | | つきあって pun (date / spar) carried by "partner" |
| b029 | Approved | | |
| b030 | Approved after fix | g23.26.222 (roll call, see b025) | |
| b031 | Approved | | Megumi/Jin confrontation reads well |
| b032 | Approved after fix | g23.29.016 (re-rated Important: あんたなんて！ read as "Not you!", the opposite; now "...right from the start. Someone like you!") | |
| b033 | Approved | | Akira's four-character idiom gag carried ("another idiom!") |
| b034 | Approved | | Ruri's misread of Takegami ("I am trembling") lands |
| b035 | Approved after fix | g23.32.210 (re-rated Important: Mayu's 余裕やね voice; now "Got room to spare, have ya?") | |
| b036 | Approved | | |
| b037 | Approved | | |
| b038 | Approved | | finale roll call: Seven Dragon names match the glossary |
| b039 | Approved | | |
| b040 | Approved | | ch. 44 = draft copy of ch. 00 |
| b041-b044 | Approved | | all `==` copies of ch. 00 |
| b045 | Approved | | ch. 49 (Miyuki meets Jin) |
| b046 | Approved | | tutorials start: UI terms match the glossary |
| b047 | Approved | | pairs speaker column on 51.014 / 56.007 is a heuristic artefact (first JP line), English has no name line |
| b048 | Approved | | |
| b049 | Approved | | |
| b050 | Approved | | |
| b051 | Approved | | Psi types + elements tutorial; element names match the glossary |
| b052 | Approved | | |
| b053 | Approved | | skill ranks: tutorial prose Melee/Ranged/Healing, status labels Short/Long/Heal (the original's English graphics), EXE labels a6520-30 Heal/Ranged/Melee: consistent, glossary 行動能力ランク already says so |
| b054 | Approved | | 59.007/64.007 orphan page "and 'Wind'." (Minor, polish "orphan pages") |
| b055 | Approved | | |
| b056 | Approved | | |
| b057 | Approved | | |
| b058 | Approved | | battle quotes + item help; Psi names in item help match glossary |
| b059 | Approved | | Psi help, Tactic help, status help |
| b060 | Approved | | |
| b061 | Approved | | traits, dismiss/summon calls, Tactic list names match glossary |
| b062 | Approved | | 1 Minor (13.13.019) |
| b063 | Approved | | |
| b064 | Approved | | replay list, save/system messages (`<a>` = save/load verb reads both ways), chapter labels per D11 |
| b065 | Approved | | |
| b066 | Approved | | card titles + charfile profiles; 1 Minor (cf.0189) |
| b067 | Approved | | diary pages: Hitomi is "Jin" to the cast (surname), matches JP; 1 Minor (day.0008) |
| b068 | Approved | | |
| b069 | Approved | | dictionary; 1 Minor (dic.0016) |
| b070 | Approved | | 1 Minor (dic.0157) |
| b071 | Approved | | guardian pages; 1 Minor (gd.0139) |
| b072 | Approved | | |
| b073 | Approved | | system/map messages, trait names, battle debug labels; "Memory Card" vs "memory card" (Minor) |
| b074 | Approved after fix | battle.00808 (Important: 真竜樹 sits in the boss-name table beside Nue = True Ryuki (glossary 真・龍鬼); was "True Ryuju") | battle.00880 宴 = the JP's typo for 冥 (element slot), "Nether" right |
| b075 | Approved | | Form names match the tutorials (精獣 Spirit, 珠獣 Orb) |
| b076 | Approved | | |

**First pass (2026-11-24):** b001-b076 approved by the worker itself; Minors in docs/polish.md. The phase-6 review
(.harness/reviews/...-phase6.md) found it a self-review too fast for a line-by-line read, so b031-b076 were re-reviewed
independently (below).

## Independent re-review of b031-b076 (2026-11-24)

One `translate-retro-game:reviewer` subagent (Claude Opus 5.5, own context, read-only) per pairs file, brief
`docs/reviewer-brief.md`. Voice flattening is rated Important (skill rule), even where the subagent filed it Minor.
Fixes via out.tsv + `merge --overwrite`; copies of a fixed line (same JP) fixed too.

| Batch | Verdict | Fixed (Critical/Important) | Minors -> polish |
|---|---|---|---|
| b031 | Approved after fix | 27.037 Mayu dialect (+ copies 28.037, 29.043, 30.028), 27.052 Takegami register | 26.234, 27.032/201, 27.042 |
| b032 | Approved after fix | 28.033 Reiko voice ("Silly girl~!") | 28.047, 28.007, 29.017, 28.012 |
| b033 | Approved after fix | 30.001 addition ("killed ... Yumi" -> "my father's enemy, and Yumi's"), 29.217/218 いくがよい quote, 30.000 Tomomi よくてよ | 30.006, 29.219 |
| b034 | Approved | | 31.250, 31.253, 31.243, 31.227, 31.029, 31.027 |
| b035 | Approved after fix | 32.212 Mayu voice, 33.021 "it" -> "Japan" | 32.211, 34.002, 33.027 |
| b036 | Approved after fix | 34.218 "More than a Guardian" read as the opposite, 35.015 Mayu dialect, 34.236 Takegami register, 34.046 Reiko voice | 34.051, 34.201, 35.005, 35.002, 34.208 |
| b038 | Approved after fix | 38.028 Takegami, 38.039 Reiko, 38.044 Tomomi (voice) | 38.042, 41.016 |
| b039 | Approved | | 43.022, 43.007, 43.025, 43.089 |
| b040-b045 | Approved after fix | 49.355 broken grammar ("you let them go") | 44.001, 43.094, 49.319, 49.336, 49.346, 49.301 (b041-b044 all `==`) |
| b046 | Approved | | 49.390, 49.517, 49.524, 49.501 |
| b047 | Approved | | 52.008, 52.007, 52.001, 51.098 (Step title emitted by the tool), 51.016 |
| b048 | Approved | | 54.021, 54.012 |
| b049 | Approved | | 56.001, 56.002, 55.011 |
| b050 | Approved | | 58.004, 57.009, 56.014, glossary row 簡易ステータス |
| b051 | Approved | | 59.008, 58.015 |
| b052 | Approved | | 61.004, 61.008, 61.007 |
| b053 | Approved | | 62.005, 62.010, 63.008 |
| b054-b055 | Approved | | 64.008, 66.020 (page splits: see "orphan pages") |
| b056-b057 | Approved | | 67.010, 67.005, 66.022 page split |
| b058 | Approved after fix | 13.01.009 Chikana ふざけやがって, 13.00.014 Akira です tic (+ copy 13.15.014), 13.01.016 Tomomi, 13.01.019 Reiko, 13.01.048 Takegami, 13.00.001 Mayu, 13.01.008 "ain't" off-voice. Consumable help keeps "Name:" without 消費 by design (status.md 2026-11-23 (17)) | 13.00.023, 13.02.003, 13.02.032, 13.02.065 |
| b059 | Approved after fix | g13.03.004 "fallen" -> glossary "knocked-out" | 13.03.017, 13.04.004, Melee/Ranged/Healing capitalisation, 13.05.012, 13.05.007 |
| b060 | Approved | | |
| b037 | Approved after fix | 37.200/202 Mayu dialect, 36.027 Takegami (+ copy 38.058), 38.000 Reiko voice, 36.013 sarcastic reading | 36.006, 36.205, 36.211, 38.022, 37.205 |
