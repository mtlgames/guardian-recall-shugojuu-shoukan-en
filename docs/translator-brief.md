# Translator brief

For whoever translates a batch (a subagent, or the phase-6 worker itself: Orca workers have no subagents and
translate in their own context, story order, b003 on). Read with offset/limit: files over ~4 KB come back as a stub.

## Read first
- `glossary.md` (rulings, speakers, terms; lint-enforced), `docs/style-reference.md` (voices, format),
  `docs/synopsis.md` (story so far, who is who), `build/terms_<batch>.txt` (glossary rows in this batch).
- The batch: `work/tl/<batch>.tsv` = `id<TAB>speaker<TAB>group<TAB>limit<TAB>JP`, line breaks shown as ` / `.
  Read it 30-40 lines at a time.

## Write
- `work/tl/<batch>.out.tsv`: `id<TAB>English`, every id once, same order, with the file-write tool (no heredoc).
- Scenario lines (limit `scenario:224pxx3`): the body only. The speaker column is added by the tool; do not write
  the name. Pages: `{wait}` between them (keep the JP page breaks where they carry a beat; the tool adds more pages
  when a page is long). No `\n` except a forced break (choices: `"Option A"\n"Option B"`).
- Plain printable ASCII only: no curly quotes, no …, no ～ (write "~" or letters), no full-width characters.
- Dry run: `python -X utf8 tools/batches.py fit '<english>' --id <id>` prints the stored, wrapped form and its lint.

## Check (run until OK, then merge)
    python -X utf8 tools/batches.py check bNNN
    python -X utf8 tools/batches.py merge bNNN

## Quality bar (past mistakes)
- Keep each voice: Miyuki's bubbly childishness, Mayu's Hakata folksiness, Chikana's cool tomboy clip. A flattened
  voice is an Important review finding.
- Honorifics stay after names (Mayu-chan, Suzune-san, Yumi-sama). さん after a non-person (守護獣さん) is not one.
- Names exactly as glossary.md (Western order). Furigana in the text (由美（ゆみ）) is dropped.
- Jokes and songs keep their punch (the hot-spring egg song rhymes and lilts).
- Report at the end: `NEW TERM: jp -> en`, `UNSURE: id - note`, `CUT: id - what was dropped`. The worker merges new
  terms into glossary.md itself.
