# Translation reviewer brief - Guardian Recall: Shugojuu Shoukan (PS1)

You review one batch of a JP->English fan translation. Read-only: no edits, no git, no subagents.
Mechanical validity (ids, control codes, encodable characters, width, page breaks) is already enforced by the
check tool - judge translation quality. Return the report as your final message: subagents cannot write files, so the
controller saves it.

## Inputs (paths in your dispatch)
- Pairs file `work/qa/review/pairs/bNNN.txt`: every entry as `>> id | speaker | JP` / `   EN`. ` ¦ ` separates pages
  ({wait}) on both sides. `==` rows copy an earlier batch's JP + English and were judged there: skip them. The
  speaker column is a heuristic (first JP line); trust the JP text. Read ALL of it, in passes: files over ~4 KB come
  back as a stub, so use Read with offset/limit (~60 lines; ~25 for long tutorial/dictionary lines).
- `glossary.md` (rulings at the top, "Decisions from earlier batches" at the end; ~350 lines: read in parts),
  `docs/style-reference.md` (voices), `docs/synopsis.md` (story; read the chapters your batch covers).

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning (negations!). Quote the
  JP and say what it means.
- Consistency: glossary names/terms exactly; honorifics kept after names (Mayu-chan, Yumi-sama); voice matches the
  style reference.
- Things players caught that reviewers missed: jokes/wordplay losing their punch; ordinal suffix after a variable;
  abbreviated names or terms; stock phrases that read awkwardly in English ("... GET!").
- Voice: each speaker against their row in the style reference. Speech quirks, register and emotional intensity must
  come through, not be normalised into neutral prose. Register markers flatten most often: old-man/warrior
  じゃ/おる/つかまつる, rough ぜ/ねぇ, feminine かしら/わよ/のね, Hakata 〜けん/〜と/〜やね.
- Naturalness: would a fan-translation reader stumble?

## Report (terse: at most ~25 lines)
### Issues
#### Critical (meaning reversed, broken grammar, wrong speaker)
#### Important (clear mistranslation, glossary inconsistency, abbreviation, a character's voice flattened: quirk, register or emotional beat lost, joke dead)
#### Minor (style - deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN` (one line; Minors may be shorter). Write "none" under empty levels.
### Assessment
Approved | Needs fixes - one sentence why.
