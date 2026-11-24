# Guardian Recall: Shugojuu Shoukan English translation

Unofficial English fan translation of **Guardian Recall: Shugojuu Shoukan** (PlayStation, XING, 1998, 2 discs): the
source text and tools that build the patch.

**Just want to play?** Download the patch from [Releases](../../releases) and follow its README. This repository holds
no game data you can play; you need your own dump of the Japanese game.

**Found a bug?** [Report it](../../issues/new/choose): untranslated text, typos, overflow, crashes. Attaching a savestate
helps most.

## Translation status

| Part | Status |
|---|---|
| Story dialogue, battle quotes, diary | Translated |
| Menus, units, items, Psi, traits, system and memory-card messages | Translated |
| Dictionaries, character files, guardian pages | Translated |
| Title screen, chapter cards, other graphics with text | Translated |
| Name entry | None in this game (fixed cast) |
| Staff credits movie | Translated (names romanized) |
| Voiced movies (FMV) | Japanese voice, no subtitles |

Tested in PCSX-Redux (SCPH-5500 BIOS), both discs, from a cold boot. Known issues: none known, see
[Issues](../../issues).

Base discs (Redump, BIN/CUE, one track each; the patches fit only these):

| Disc | File | Size | SHA-1 |
|---|---|---|---|
| 1 | Guardian Recall - Shugojuu Shoukan (Japan) (Disc 1).bin | 698261760 | 3ae2071d590825874ae769a9b733e0e00702ad9f |
| 2 | Guardian Recall - Shugojuu Shoukan (Japan) (Disc 2).bin | 729357552 | d45a833f2dc3986227b38aa4de2605ddb5c56785 |

## What's here

| Path | What it is |
|---|---|
| `script/` | Every text block: original Japanese and English. Translation fixes go here. |
| `glossary.md` | Binding names, terms and style rules. |
| `tools/` | Python build chain: extract, insert, lint, release. |
| `tests/` | pytest suite (ROM-dependent tests skip when the ROM is absent). |
| `docs/re/` | Reverse-engineering notes. |
| `docs/decisions.md`, `docs/status.md` | Rulings with their reasons; current progress and open bugs. |
| `docs/fonts.md` | Fonts used and their licences. |
| `AGENTS.md` | Instructions for coding agents (`CLAUDE.md` points to it). |
| `.codex/agents/`, `.opencode/agents/` | Subagent types (translator, reviewer, visual QA, playtester, graphics) for Codex and opencode; Claude Code gets them from the plugin. |

## Build your own patched ROM

Needs Python 3.12+ and your own dump of the Japanese game.

```sh
git clone https://github.com/minhnhattonthat/guardian-recall-shugojuu-shoukan-en
cd guardian-recall-shugojuu-shoukan-en
# copy both discs (.bin + .cue, Redump names above) to rom/; the build refuses any other dump, see rom.sha1
# tools: mkpsxiso 2.30 into tools/mkpsxiso/, xdelta3 3.1.0 into tools/xdelta/ (AGENTS.md "Paths")
python -X utf8 build.py                                # -> build/disc{1,2}/*.bin + .cue
python -X utf8 tools/check.py                          # tests + text lint
```

## Support

If you enjoy this translation, you can support my work on Ko-fi:

[![Support me on Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/minhnhattonthat)

## Licence

Tools and English translation: MIT. Fonts: see `docs/fonts.md`. The original Japanese text in `script/` is XING's
and is included only so the translation can be checked against it. Guardian Recall: Shugojuu Shoukan is (c) XING /
Agumix; this project is not affiliated with them.
Do not share patched ROMs.

The translation was made with extensive AI assistance (Claude by Anthropic). Corrections are very welcome.
