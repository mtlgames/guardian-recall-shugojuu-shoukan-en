# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 6. Translate in progress (batches b001-b004 merged; next b005).
  Last build: 2026-11-23 `build.py` (English, b001-b004): ev02 shows "Yumi / "It failed?"" in the scenario box.
- **Done:**
  - Step 0: PCSX-Redux + SCPH-5500 BIOS in tools/ (original disc 1 boots, circle input + Lua probe verified),
    mkpsxiso/dumpsxiso 2.30, armips 0.11.0, xdelta3 3.1.0 in tools/; rom.sha1 pinned; pre-commit runs
    tools/check.py (failing test rejected: verified); guard hook active (blocked a heredoc); rulings D1-D7.
  - No earlier fan patch found (web search 2026-11-21).
  - Phase 1 recon (docs/re/): encoding + `tbl/jp.tbl`, renderer/glyph map, UNN.PAK index, TX03, scenario (g23) +
    battle quotes (g13); GRETC.RLZ decoded (txd markup text); EXE/overlay string ranges + pointers; free space;
    graphics survey G1-G16.
  - Phase 2 so far (docs/re/debug.md): `tools/debug/warp.lua` cold-boots and starts any event 1-70 through the
    game's own event starter, plus title menus, OPTION (= BRAIN menu) submenus, both disc-swap screens.
    `tools/debug/regen.py` runs the scene list in parallel (sheets in work/qa/warp/, states in work/states/);
    `tools/debug/mk_scenes.py` writes `tools/debug/scenes.tsv`; `overview.py` makes labelled sheets.
    Memory-card checksum known (byte sum at 0x1FFE); fixture `tools/debug/cards/sys.mcd` (system file only).
  - 2026-11-23: tactics map controls mapped (ev70): unit menu, 行動/超力/思考 submenus, △ ring menu (UNIT MAP
    MISSION DIAGRAM SEARCH CONFIG BREAK), BREAK = map save + quit prompt (= field pause/save screen). Scenes
    `tac_*` in scenes.tsv (unit menu, 行動, 超力, 思考, 情報, 待機, ring, CONFIG, MISSION = 勝利/敗北条件, BREAK
    prompt, セーブしました+quit prompt): all 11 regen ok and every final shot checked. Map save lands in the GRS system file (layout in debug.md); fixture
    `tools/debug/cards/ev70_map.mcd` (title gains CONTINUE). New probes tools/lua/{exec_log,watch_u32,pc_log}.lua.
  - 2026-11-23 (2): save editor `tools/debug/save.py` (lists fields; --unlock-all/--poke/--fill/--event; fixes the
    checksum; tests/test_save.py) + fixture `tools/debug/cards/unlock.mcd` (boots clean; every OPTION
    encyclopedia/replay entry incl. epilogues unlocked). scenes.tsv optional 8th column = card. New scenes:
    opt_*_all (5), tac_unit/map/diagram/search, replay_d2, ending (disc 2 イベント再現 > エンディング = ending +
    full STAFF.STR credits), epilogue_miyuki/yuko, opt_music(_track) (OPTION △ = MUSIC MODE, R2 = next track),
    **battle** (cold boot -> 天 new game -> ev01 tactics map, turn-cycle route, stops 500 frames into BATTLE 0x15
    at ~39500 frames: `regen.py --only battle --timeout 2400`). warp.lua: `0xADDR=0xV*N` fill writes, writes on
    ovl: scenes, route step `stop:X+N`. Turn flow: the turn passes only after **every master** acted (L2 = next
    unit); the ev70 "guardian stall" was that. ev48 = swap screen on both discs (labelled). Probes
    tools/lua/{story_blocks,poke}.lua.
  - 2026-11-23 (4): full `regen.py --orig --timeout 2400`: 110/110 ok. **Game over reached** (ev01 defeat =
    美由紀の戦闘不能; GameOver graphic + dialog + map restart, work/qa/gover01c) and scene `gameover` added (new game,
    writes `0x800C3060<0x1` = per-frame HP clamp, route step `stopeq:ADDR=VAL+N`; both new in warp.lua). All 70
    events labelled in mk_scenes.py (51-65 = tactics tutorials). Epilogue scenes lengthened to 12000 (shared FMV
    opening, distinct later). **DIARY reached** naturally (docs/re/debug.md "DIARY reached"; state
    work/states/diary.sstate). Emulator stall after an ally master's retire line found and worked around
    (tools/lua/unstick.lua). New probes units.lua, clamp_hp.lua.
  - 2026-11-23 (5): **phase 2 done.** `gameover` regen from a cold boot: final shot = GameOver graphic + defeat
    dialog. The diary "stall" was not one: Up/Down pick the DAY tabs (DIARY ROUTE SAVE LOAD CONFIG NEXT). Saved a
    DAY save from it: fixture `tools/debug/cards/day01.mcd` (GRDA, block 2); title > LOAD of it = DAY menu from a
    cold boot. Scenes day_diary, day_route, day_route_yes, day_save, day_load, day_config, day_next, day_diary_05/12/33
    (all regen ok, final shots checked). save.py knows the GRDA layout (event +0x238; test); scenes.tsv card
    `day01.mcd@N` = DAY menu / diary of episode N (regen.py makes the card). 122 scene rows.
  - 2026-11-23 (6): **phase 3 done.** `build.py` dumps each disc once (dumpsxiso -> work/iso/d<N>/{tree,layout.xml}),
    copies the tree to work/build/d<N>/, runs `patch(n, tree)` (empty for now), repacks with mkpsxiso into
    build/disc<N>/ (~10 s both discs). Slow test tests/test_identity.py: unpatched rebuild of both discs = rom.sha1
    (passes from a fresh dump). Built disc 1 smoke ok.
  - 2026-11-23 (7): **phase 4 done.** `tools/extract.py` -> script/ (127 files, 7751 strings: scenario 4821, battle
    465, txd 1242, evd unit names 564, exe/overlays 659 of which 57 status data). Library `tools/script_io.py`
    (parse/build of slot blocks, evd names, EXE strings; `unn_repack`, `gretc_repack`). tests/test_script.py: blocks
    and txd rebuild byte-exact, UNN.PAK+EXE and GRETC.RLZ repack byte-identical, EXE/evd strings exact, range
    coverage, script/ == fresh extraction. New finds (docs/re/text.md): evd op 0x34 unit names; g23 entry 43 is
    text (count 0, 254 slots); g13 entry 2 = item help; staging notes between strings; per-record kana table
    variant (`tbl`).
  - 2026-11-23 (8): **phase 5 engine spike.** English VWF font `fonts/vwf12.txt` (drawn, MIT) drawn by `tools/font.py`
    into the game's one font TIM (UNN g9 sub 0 item 7); `asm/hooks.asm` (armips): boot stub -> payload at 0x801F0000,
    ASCII bytes via cell table in the glyph lookup, scenario pen += per-glyph advance, scenario buffer moved to
    0x801E8000 (0x8000), g13 malloc 0x4000, malloc arena cut to end 0x801E7F00 (docs/re/text.md "English font").
    `tools/insert.py` + `build.py [--marker]` rebuild g23/g13 blocks (UNN repack moves groups: works in game).
    **Fixed build bug:** layout.xml pointed at the pristine tree (no patch ever reached the disc). Scenario box
    measured: 224 px/line, 3 lines/page + name. tests/test_font.py. `tools/re.py` (fn/dis/jal xref helper).
  - 2026-11-23 (9): VWF in generic UI 0x80043A64, 0x80044624, txd renderer (0x80017DC8), list-row converter
    0x80012EE0 (keeps ASCII), DIC.BIN grid (compact 10-byte glyph records); blank space cell. Markers for txd, evd
    names, EXE/overlay strings (`work/marker_tags.tsv` maps short tags to ids). Full marker tour 124/125 ok.
    tac_search "stall" = **original disc does it too** (docs/re/debug.md). Width gate: `tools/windows.py` (budgets +
    fit lint + byte budget for in-place records, `--cover`), evidence in `docs/windows.md`; measured: scenario,
    battle quote/comment, power help, charfile profile, dictionary. `build.py --qa ID=TEXT` override; glyph torture
    line OK in the scenario box. Helpers: tools/find_ref.py, tools/boxedge.py, tools/debug/{one,keep_re}.py,
    tools/lua/regs_at.lua.
  - 2026-11-23 (10): **evd unit names hooked** (evd_name_hook at 0x8001E278: evd keeps key `7F hi lo`, unit points at
    a payload name table; 20-char names drawn whole in 情報). **EXE/overlay string relocation**: too-long strings go
    to STR_POOL 0x801F4000 with every ref repointed (insert.repoint; tests/test_insert.py); marker build pads EXE
    labels to 2.5 x JP chars (pool 6960 B). Payload source limit relaxed to the EXE zero area. Measured: think help
    (g13.04, 117 px x 4), field help (g13.17 via ring + SELECT, 220 px x 3), replay list (centred by byte count, <= 34
    bytes), evd name in 情報 panel (108 px). `regen.py --outdir work/qa/warp_orig --orig` keeps original reference
    shots (51 menu scenes there now); `tools/inkrows.py` = ink segments per text row (measure from numbers, not by
    eye). Scenes tac_ring_help, tac_info_help(2) (the latter show no help: trigger unknown).
    Marker tour of this build: smoke ok, 53/54 menu/tac/opt/day scenes ok (tac_search = the original's own stall);
    tac_unit_menu shows relocated labels (E4t 15 chars) and keyed evd names.
  - 2026-11-23 (11): **2D primitive pool crash fixed** (asm/hooks.asm pool_grow; docs/re/text.md "2D primitive
    pool"): the game never checked the pool's malloc; with our heap cut, long text made it fail and glyph packets
    overwrote the kernel. Both ring > UNIT with 20-char names and the original's own tac_search stall now pass.
    Budgets: evd names 75 px (UNIT list, measured; 10-byte cap gone), diary page per `&s()` segment (windows.segments,
    right 273), guardian list 180, tutorial title 280, unit command menu 30; the rest (EXE/overlay, other txd, battle
    help 02/07/10) get the Japanese line's own width as a floor (`px="jp"`, status "jp width"). Fit lint 0, no record
    without a budget. Glyph torture (tools/torture.py) correct in generic, txd and DIC renderers. Probe
    tools/lua/pool2d.lua.
  - 2026-11-23 (12): **phase 5 closed.** Full marker tour: ev43 (HEN formation roster) crashed: our g13 malloc
    (grown to 0x4000) returned 0 on HEN's tight heap, the CD DMA wrote the kernel (docs/re/text.md "ev43 crash").
    Fix: scenario buffer -> zero BSS gap 0x800CAC00 (0x6A78, xref-checked over EXE + all overlays), g13 buffer
    static at 0x801EC000 (free nopped), arena end 0x801E7F00 -> 0x801EBF00 (HEN top free 0x3F88 -> 0x7F88). Re-tour
    128/128 ok (gameover needs `--timeout 3600` under parallel load). Finals of every menu/tac/opt/day/title scene
    and every event read: no font-drawn Japanese; graphics survey gained G17 (tactics element orbs) and G18 (title
    copyright line). New tools: tools/lua/heap.lua (arena walk), tools/lua/malloc_log.lua, tools/xref_range.py.
  - 2026-11-23 (13): **phase 6 started.** `tools/batches.py` (split/check/merge/fit; adapter: speaker name line added
    from glossary.md, scenario bodies word-wrapped to the box and run onto extra {wait} pages, honorifics after
    person names, width lint via tools/windows.py; tests/test_batches.py runs the lint over all shipped English).
    glossary.md seeded (speakers, full names, places, terms, guardian species; readings from dic/gd), D8-D10,
    docs/style-reference.md, docs/translator-brief.md, docs/synopsis.md (00-01). Batches: b001-b002 = all evd unit
    names (wave 0), b003-b057 = g23 scenario in entry order (3000 JP chars each; b003-b004 done = scenario 00-01
    part). Orca workers translate themselves (no subagents): one worker ~8-10 batches before its context limit.
- **Next:** (a) Phase 6: translate b005..b057 in order (`docs/translator-brief.md`; after each block add its summary
  to docs/synopsis.md, merge NEW TERMs into glossary.md), then split and translate g13 (battle), txd, exe/overlays
  (`batches.py split --only 'g13'` etc.; txd needs its own &n() via windows.wrap, EXE strings byte/room budgets).
  Then the review pass (fresh read-only pass per batch file or codex exec after 2026-11-26).
  (a0) Old note: Phase 6 translation batches (docs/decisions.md rulings; budgets from tools/windows.py). Where a "jp
  width" floor is too tight for good English, measure that screen and add a row (docs/windows.md) instead of
  abbreviating. Limits: scenario block 0x6A78 bytes, g13 block 0x4000 (insert.py LIMITS asserts).
  (b) Optional: g13 help 02 (needs a map with items) and 05/06/07/10/18 trigger in 情報 to replace their floors.
  (c) Heap margin: HEN leaves 0x7F88 free at the arena top; if English grows the 2D pool more, consider a smaller
  pool_grow rounding (asm/hooks.asm) before cutting more RAM.
- **Later (debug tool, low priority):** CONTINUE of a warp-made map save hangs on NOW LOADING (zero story blocks).
  Diary text for every episode (phase 8): day.txd slots 512-708 not yet tied to events; `day01.mcd@N` covers
  slots 4*(N-1). GOD mode not needed so far (clamp_hp.lua covers forced wins/losses).
- **Open bugs:** none.
- **Waiting on the user:** (non-blocking) FMVs are voiced Japanese with no subtitles; default = no FMV subtitles,
  only the STAFF.STR credits get English (D3). Ask if subtitles are wanted.
- **Gotchas:** this PCSX-Redux nightly's `L.dump_ppu` writes 2 MB (first 1 MB = VRAM). Context-mode trims tool
  output > ~4 KB: read files with limit, keep command output short. Exec/read hooks need `emu.py --debugger`.
  `codex exec` hit its usage limit (until 2026-11-26): no codex reviews before then. Other repos' emulators share
  this machine: emu.py runs can be 10x slower under load; kill only PIDs whose command line has this repo.
  When a scene stalls on a patched build, run `one.py NAME --orig` before bisecting (tac_search stalls on the
  original too). A game exception pauses PCSX (run ends 124): `tools/lua/pc_log.lua` logs the PC. Yes/no prompts in this game
  often default to いいえ. play.py `--every` sheets are 12 full frames: expensive to read, prefer single shots.
