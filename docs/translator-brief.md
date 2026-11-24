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
- txd markup stays as in JP (same `&c`, `&s`... counts); `&n()` and `&g(pitch,h)` are free (charfile header names
  use `&g(13,0)`; the lint measures at the pitch). Card titles (day.00250, exe.01580, exe.021d0, action.006b4) stay
  full-width SJIS.
- Plain printable ASCII only: no curly quotes, no …, no ～ (write "~" or letters), no full-width characters.
- Dry run: `python -X utf8 tools/batches.py fit '<english>' --id <id>` prints the stored, wrapped form and its lint.

## Check (run until OK, then merge)
    python -X utf8 tools/batches.py check bNNN
    python -X utf8 tools/batches.py merge bNNN

## FMV batches (fmvNN, D18: movie subtitles)
- Ids `fmv.<MOVIE>.<n>`; the group column is the movie and its start second. M<NN> movies belong to synopsis
  episode NN (PRO = prologue narration, MEND = ending, EP_A = Miyuki epilogue, EP_B = Yuko epilogue, SYO = guardian
  summon incantations). The JP is a **Whisper transcript of the voice track**: expect misheard names and homophones
  (巣王ちかな = 周防ちかな, 無気づき = 美由紀, 郊外 = 校外, エグバド = 荏狗覇菟 Egubado), merged speakers and the odd
  garbled line. Translate what was most likely said, from context, synopsis and glossary; report `UNSURE: id - note`
  for real guesses. Mantras (オン…ソワカ) are romanised as heard ("On aun raken sowaka!").
- Subtitles: say it in short, natural spoken English; about 15 characters per second of the line's time reads
  comfortably. ` / ` starts a new subtitle page at a sentence end (long narration); a page wraps itself and goes on
  in a further page past 2 lines. No `{wait}`, no speaker names, plain ASCII.
- Check and merge: `python -X utf8 tools/fmv_subs.py --merge fmvNN` then `--check fmvNN` until `ok` (glossary lint
  is the reviewer's job here, not batches.py).

## Quality bar (past mistakes)
- Keep each voice: Miyuki's bubbly childishness, Mayu's Hakata folksiness, Chikana's cool tomboy clip. A flattened
  voice is an Important review finding.
- Honorifics stay after names (Mayu-chan, Suzune-san, Yumi-sama). さん after a non-person (守護獣さん) is not one.
- Names exactly as glossary.md (Western order). Furigana in the text (由美（ゆみ）) is dropped.
- Jokes and songs keep their punch (the hot-spring egg song rhymes and lilts).
- Notes from review (phase 6):
  - Negations that can flip: 美里のためにもね = "for Misato's sake too" (08.213), あんたなんて！ = "Someone like
    you!" (29.016), not "Not you!".
  - Check whose companions/friends a line means (18.017: 私の仲間 = her Dragon Wielder companions).
  - Recurring set pieces (Akira's roll call) are copied word for word from the first instance (`tools/find_en.py`).
  - Name tables follow the glossary even in odd company (battle.00808 真竜樹 = True Ryuki).
  - Register words count: いいわ = "Very well", not "Never mind"; a villain's フフフッ is "Heh heh heh", not "Hahaha".
- Report at the end: `NEW TERM: jp -> en`, `UNSURE: id - note`, `CUT: id - what was dropped`. The worker merges new
  terms into glossary.md itself.
