# Guardian Recall: Shugojuu Shoukan (PS1, 2 discs) English translation

Skill: translate-retro-game (Claude Code: plugin, enabled in .claude/settings.json; other agents: `<SKILL_DIR>/SKILL.md`; `$SKILL` = `python tools/skill.py`). Read it before ROM, text or QA work.

## Commands (run from repo root)
- Build:    `python -X utf8 build.py` -> build/disc{1,2}/*.bin+.cue (checks the dump against `rom.sha1` first)
- Check:    `python -X utf8 tools/check.py` (fast tests; the pre-commit hook runs it; `git config core.hooksPath tools/hooks` once per clone). Slow tests: `python -X utf8 -m pytest -m slow tests`
- Smoke:    `python -X utf8 $SKILL/scripts/emu.py build/disc1/<cue> --out work/qa/smoke --route tools/routes/boot.txt --smoke`
- Warp:     `python -X utf8 $SKILL/scripts/emu.py build/disc<N>/<cue> --out work/qa/warp --sav tools/debug/cards/sys.mcd --script tools/debug/warp.lua --var "SCENE='<name>'" --frames 4600 --sheet` (scenes + their disc: `tools/debug/scenes.tsv`, written by `tools/debug/mk_scenes.py`; never ask the user to play to a scene)
- Regen:    `python -X utf8 tools/debug/regen.py [--only NAME..] [--orig]` (every scene from a cold boot: sheets in work/qa/warp/, states in work/states/)
- Release:  `python -X utf8 tools/release.py` (xdelta per .bin + verify; never publish without the user)
- Clean:    `python -X utf8 tools/clean.py`

## Paths
- Original discs: `rom/Guardian Recall - Shugojuu Shoukan (Japan) (Disc N).bin/.cue` (gitignored; SHA-1 in `rom.sha1`, checked by `tools/check_rom.py`).
- Emulator: `tools/pcsx/` (PCSX-Redux nightly 32338.20261121.15 x64, distrib.app manifest dev-win-x64, via `fetch_emu.py pcsx`); BIOS `tools/bios/scph5500.bin` (`fetch_emu.py psx-bios`). Savestates: `work/states/`. Memory cards: `work/cards/`.
- Disc tools (gitignored, re-download): `tools/mkpsxiso/` (mkpsxiso/dumpsxiso v2.30 win64, github.com/Lameguy64/mkpsxiso), `tools/armips/` (v0.11.0, github.com/Kingcom/armips), `tools/xdelta/` (xdelta3 3.1.0 x86_64, github.com/jmacd/xdelta-gpl).
- Text: `script/`. Tables: `tbl/`. Glossary: `glossary.md`. RE notes index: `docs/re/README.md`. Fonts and their licences: `docs/fonts.md`.

## Rulings
- Edit source files (.py .lua .asm .tbl .json) only with the file-edit tool; scripts here read and analyse, never `.replace()` and write back.
- Subagents: dispatch the agent types (translator, reviewer, visual-qa, playtester, graphics) shipped by the plugin as `translate-retro-game:<type>` (Claude Code), `.codex/agents/` (Codex) or `.opencode/agents/` (opencode), never general-purpose.
- The user's decisions, with the options and reasons: `docs/decisions.md`. Read it before asking the user anything; add each new ruling there the same session.
- Player bug reports: GitHub issues (`gh issue list --label bug`). Copy the attached save into `work/states/`, reproduce in the emulator, fix, commit with `Fixes #N`, and update `docs/status.md`.
- Gotchas: PCSX-Redux boot shows "no system file" without a memory card (normal). Context-mode trims tool output above ~4 KB: read files with offset/limit.

## Status
`docs/status.md`: done, next, open bugs. Update it at the end of every session.
