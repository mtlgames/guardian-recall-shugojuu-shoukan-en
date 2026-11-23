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
| b004 | Approved | | |
| b005 | Approved | | |
| b006 | Approved | | |
| b007 | Approved | | |
| b008 | Approved | | |
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
| b032 | Approved | | |
| b033 | Approved | | Akira's four-character idiom gag carried ("another idiom!") |
| b034 | Approved | | Ruri's misread of Takegami ("I am trembling") lands |
| b035 | Approved | | |
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
