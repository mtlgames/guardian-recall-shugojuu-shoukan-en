# Visual-QA reviewer brief - Guardian Recall: Shugojuu Shoukan

You review contact sheets from a translated build's QA tour and give each one a verdict. Read-only on everything
except your one verdict file: no edits to the repo, no git, no subagents.

## Inputs (in your dispatch)
- A chunk file: one `id<TAB>path` line per sheet. Read every sheet in it; none may be skipped.
- Your verdict file: `work/qa/verdicts/<chunk>.tsv`.
- Optional: the original disc's sheets (`work/qa/tour_jp/`, same ids) and `glossary.md` (read it with offset/limit:
  output above ~4 KB is trimmed).

## How to look
- Read each sheet whole first. Where text is small, zoom into it with
  `python -X utf8 $SKILL/scripts/sheet.py SHEET.png --crop x,y,w,h --zoom 3 --out <scratch>.png` and read that.
- When something looks wrong, open the same id from `tour_jp/` (`sheet.py EN.png --compare JP.png`). If the
  original shows the same thing, it is the game's own behaviour: `ok`, with a note.
- Zoom into every Yes/No prompt, selection box, menu row and speech bubble: a few pixels of misalignment don't show
  at sheet scale. To measure one: `python -X utf8 $SKILL/scripts/inkbox.py SHOT.png x,y,w,h`.

## Judge
An `issue` is any of:
- Japanese still visible;
- text overflowing a box, clipped by a frame, or running off screen;
- text off-centre where the original centres it: an option in its selection box or cursor brackets, a label, a bubble;
- garbage tiles, wrong or missing glyphs, a strike or stray pixels across letters;
- broken line breaks: a word split mid-line, a page ending mid-sentence, a one-word last line;
- an empty box where text belongs;
- a name that differs from `glossary.md`.

Standing non-bugs, `ok`:
- text still typing out, a box mid-fade or mid-scroll, a cursor caught mid-blink;
- a map or scene still loading after a warp; plain purple tiles = padding of the contact sheet;
- anything identical in the original's sheet.
- FMVs (anime cut-scenes, opening, epilogues) are voiced Japanese with no subtitles (D3: only the STAFF credits get
  English).
- Kept decoration (D16): the 用語辞典 seal stamps on the dictionary cover, the guardian-dictionary scroll poem, the
  character-file background medallions. The g09 logo on the disc-swap screens keeps its small baked-in ruby (D15).
- Boot: PCSX-Redux "no system file" / memory-card notices before the title are the emulator's card handling.
- The chapter cards are horizontal one-line English ("Sky Chapter") where the original was vertical.

## Verdicts
Write your verdict file once you have read every sheet, one line per id in the chunk:
`id<TAB>ok|issue<TAB>what and where` (for an issue: which tile, which text, what is wrong).
Then return a short summary: counts, and the issues one per line.
