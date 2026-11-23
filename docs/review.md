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
