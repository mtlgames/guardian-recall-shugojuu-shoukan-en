# Status

Updated at the end of every session. Keep it to what the next session needs; history is in git.

- **Phase:** 8. QA in the emulator (phase 7 closed 2026-11-24 (14): no "engine pending" or "measured (code)" row
  left from the (0)/(0b) list; see Next).
  Last build: 2026-11-24 (19) `build.py` (write check + jp_refs ok both discs; G1-G6, G8-G11, G13, G17, G18 English),
  check.py green. Phase 8 in progress: graphics rows first (Next (0)); only G15 (credits movie) left.
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
  - 2026-11-23 (14): b016-b023 merged (scenario 11.208-18.234), synopsis 12-18, style rows for Akira, Kagami,
    Sayaka, Ruri; glossary Hime-chan, Operation Dam-Dam, stone circle. Robot announcements in CAPS; Sayaka's mangled
    proverb = "Every clown has a silver..."; ロッカー pun = rocker / rocking chair. g23.18.019 is an empty 「」 in JP
    (kept as "").
  - 2026-11-23 (15): b024-b030 merged (scenario 18.246-26.228), synopsis 19-26. Glossary: Emperor Dragon (皇龍),
    Hibiya Park, Four Gates + the four gate sites. Takegami (old warrior, "have at thee") joins in ch. 23. Voice
    check: Chikana never drops g's (0 of 139 lines); only Mayu (and Kaoru lightly) do.
  - 2026-11-23 (16): b031-b051 merged (scenario 26.229-60.007: story ends at 42; 43 = draft of ch. 05, 44-48 =
    copies of ch. 00, 49 = Miyuki meets Jin (unused/alt scene), 50-65 = tactics tutorials, "Step NN" title cards).
    New `tools/tl_reuse.py bNNN --write` prefills a batch from English already in script/ (same JP body, breaks
    ignored) and `--fill F.tsv` fills the TODO rows: b041-b044 were 100% reuse. Glossary: UI commands (Move, Action,
    Wait, Dismiss, Summon, Execute Order, Change Tactic, Check Target), Tactic orders (Guard me!, Attack!...),
    parameters, Psi (Cure, Rock Shield, Blessing, Focus, Luck, Weaken), elements, Ryuki, Step 01-14 speakers.
    Lint fixes: given name inside a full name (周防ちかな様), name-line heuristic skips lines ending in a particle.
    Synopsis 27-34.
  - 2026-11-23 (17): b052-b063 merged: scenario complete (4821/4821; entries 64-68 are near-copies of 59-63, done
    with new `tools/tl_diff.py bNNN SRC --same F` + tl_reuse --fill), g13 complete (465/465). tl_reuse: speaker test
    = windows.named_jp (narration first lines were dropped before), indexes all script/. `tools/find_en.py PHRASE`
    = shipped English for a JP phrase. windows rows: item help g13.02 = 4 lines (JP floor 130 px), trait/Tactic
    help g13.07/10 = 221 px (group's widest JP line). Glossary: Forms (Battle/Shooter/Orb/Spirit Guardian), skill
    rank/EXP, all Psi names + categories, consumable item names (in g13.02 help line 1), Trait, Levitate (move
    type), Unleash your potential, Expert. Item help line 1 = item name for consumables (JP "(name) 消費：").
  - 2026-11-23 (18): b064-b065 merged. Chapter labels "Sky, Episode 1" (D11; glossary 天の章/第一話), windows row
    "save chapter label" 180 px (day_save measured; Sky+Earth pair test). **Card title**: DAY.BIN 0x8016ABB8 -> new
    asm `title_wide` (ASCII -> full-width SJIS, cap 62 bytes; buffer 0x50); day.002a0 = "GR%d%d %s%s%s %d%d:%d%d";
    verified with new scene `day_save_write` (block 3 title "ＧＲ０２　Ｓｋｙ，　Ｅｐｉｓｏｄｅ　１　００：２６").
    docs/re/text.md "DAY save list + card title". txd auto-wrap: batches.prepare -> windows.wrap_txd (per &s segment
    for diary pages, `wrap` 100 for dic (engine wraps at col 100), new row "guardian page" gd 180 px x 13 (derived from
    &f(14,10) x &g pitch 14, not yet measured)). tools/dis_ovl.py (overlay disassembly).
  - 2026-11-23 (19): b066-b069 merged (charfile names/headers/profiles, day overlay strings, all diary pages, day
    chapter labels, dic 0000-0132). Engine-side widths found and fixed in tools/windows.py (tests/test_windows.py):
    charfile profile holds **6** lines (JP draws 6), new rows charfile header (pitch-aware lint: ASCII advance = width
    + &g pitch - 13; long voice-actor names use `&g(12,0)` letters + `&g(13,0)` space) and charfile list (180),
    dictionary entry **11 lines** (row 12 falls off the page: seen in game), diary body lines 1-2 wrap at 194 px
    (`narrow`: the LOAD button hid words), day.0512-0708 = copy of the save labels (180, reader not found).
    batches.py: `&g(..)` free in the markup check; card titles may use full-width SJIS (CARD_TITLES); font.width
    counts a full-width char as 13. Scratch generator for cf headers not kept (one-off).
  - 2026-11-24: b070-b072 merged (dic 0133-0268, every guardian list name + page). **Guardian page measured**
    (opt_guardians_page now opens it: ○ held 30 frames = art page, △ = text): body x 64, ASCII +1 px/glyph at pitch 14
    (new variant key `adv` in windows.wrap/lint), 192 px x 5 rows (6th row hits the bottom bar). **Bug fixed:**
    dictionary list headings were wrapped like pages ("Inawashiro Lake Hotel" spilled "Hotel" to x 0): new row
    "dictionary list" (223 px, 34 bytes, never wrapped). D12: kana reading lines dropped (gd reading row empty).
    Glossary: 冥 Nether, 皇 Emperor (elements), unit names strike/raider/defense/air force, navy, Royal Guard, True
    Ryuki, Earth Centipede; 思考 also "thought" in prose. Remaining txd records without English are ASCII-only.
    Scratch tools for gd (expander from `id<TAB>Name|Body`) not kept (one-off).
  - 2026-11-24 (2): b073-b076 merged (all EXE/overlay strings: system file + map messages, Psi/trait/item/species/
    Form lists, tactic orders, HEN roster + team prompts, BRAIN menu). **BRAIN base fixed** (0x80162F88, script_io;
    pointer table at file 0x2AF4) so its labels relocate (option shot: "Guardian Tactics" etc. drawn whole).
    extract.is_data: blank-only string = data (exe.a69c4). Measured windows rows (tools/windows.py, docs/windows.md):
    tactic list 115, current tactic 107, 行動 submenu 69, BRAIN menu 90, HEN roster 74, HEN team prompt 273, map
    message box 176. D13 (engine pending list). Glossary: Forms, traits, Takegami equipment set, Retreat, OK.
    Skill rank labels a6520-30 = Heal / Ranged / Melee (glossary lint); glossary 行動能力ランク says the status shows Short / Long / Heal: reconcile in the review.
  - 2026-11-24 (3): **review pass started** (docs/review.md: method + verdict per batch; Minors in docs/polish.md).
    New `tools/pairs.py bNNN` -> work/qa/review/pairs/bNNN.txt (JP + out.tsv English, `==` rows = copies judged
    earlier); `pairs.py --drift` = out.tsv vs script/ (empty = fixes via out.tsv + `merge --overwrite` are safe).
    b001-b010 reviewed: all approved, 1 Important fixed (g23.06.000). One worker covers ~10 scenario batches
    (~15 KB pairs each, read in two 100-line halves) before its context limit.
  - 2026-11-24 (4): b011-b030 reviewed: all approved, 3 Important fixed (g23.08.213, g23.18.017, Akira's roll call
    unified in 20.203 + 26.222); Minors to docs/polish.md. One worker covered 20 batches (~130k context).
  - 2026-11-24 (5): b031-b050 reviewed: all approved, no Critical/Important; 6 Minors to docs/polish.md. Pairs files
    from b046 on are tutorials (long lines: read ~25-30 lines per Read); b051+ are 13-36 KB each.
  - 2026-11-24 (6): **phase 6 closed.** b051-b076 reviewed: all approved, 1 Important fixed (battle.00808 真竜樹 =
    True Ryuki, boss-name table beside Nue). Skill-rank naming reconciled (prose Melee/Ranged/Healing, status
    graphic Short/Long/Heal, EXE labels Heal/Ranged/Melee: consistent). New Minors in docs/polish.md incl. "orphan
    pages" (fitter leaves 1-3 words alone on a {wait} page: 14 ids listed) and Memory Card capitalisation.
  - 2026-11-24 (7): **phase-6 review fixes** (.harness/reviews/...-phase6.md): 4 voice Minors re-rated Important and
    fixed (01.016, 04.047, 29.016, 32.210); synopsis 35-42 written (story ends at 42; ending = FMV); style-reference
    rows Takegami/Kaoru/Reiko/Satomi/Megumi; glossary "Decisions from earlier batches" filled; translator brief "Notes
    from review"; new `docs/reviewer-brief.md`. **Independent re-review** with `translate-retro-game:reviewer`
    subagents (one per pairs file, read-only): b031-b060 done, all approved after ~30 Important fixes (mostly
    flattened voices: Mayu dialect, Takegami register, Reiko/Tomomi; plus 30.001 addition, 34.218 reversed-reading,
    49.355 grammar, g13.03.004 glossary). docs/review.md table + Minors in docs/polish.md.
  - 2026-11-24 (8): **independent re-review finished** (b061-b076, worker's own read-only pass: Orca allows no nested
    workers). 1 Critical fixed: g13.09.017 Kaoru's battle summon lost its 3rd mantra page. Important fixed: battle
    quote voices (Mayu, Tomomi, Akira x3, Takegami x2, Reiko, Yuko), day.0008 garbled line, dic disciples given
    he/him (gender unstated: now neutral), dic.0175 height joke. docs/review.md table sorted; Minors in polish.md.
    Tip: `sed -E 's/&[a-z]\([^)]*\)//g'` on a txd pairs file halves it for reading.
  - 2026-11-24 (9): phase 7 (a) partly: full build of the all-English script ok, `windows.py` fit lint 0, check.py
    green, smoke ok. **asm/hooks.asm load-delay bug fixed** (lbu t1 -> sh t1 in the ASCII advance path; armips had
    warned on every build; now 0 warnings). ev02 + opt_dictionary_page re-shot: VWF spacing correct.
  - 2026-11-24 (10): **write check** (done-when item 3): `tools/writecheck.py`, run by build.patch on both discs
    (build fails on any error). insert.LOG records every in-place string, repointed ref word, UNN index rewrite and
    armips run (`-temp` listing work/asm/hooks.lst = emitted spans; runs > 0x40 bytes must be over dump zeros); romdiff
    `--writes` rules per EXE/overlay; UNN.PAK non-text groups byte-equal (g9 only inside the font TIM pixels);
    GRETC.RLZ non-rebuilt entries byte-equal; no other file changed. tests/test_writecheck.py (mini tree, 2 s, in the
    commit gate) proves stray bytes in EXE/UNN/GRETC/other files and clobbered writes fail. **printf lint**
    (batches.problems): JP format strings keep their conversions in order; g13 help is NOT printf'd ("100% of", "%d"
    drew literally in tac_power: shot). **Psi name slots widened** (asm/hooks.asm "Psi name slots"; windows row
    "Psi name" 64 px measured, 24 ids out of exe_pending.txt).
  - 2026-11-24 (11): **ring > UNIT list widened** (asm/hooks.asm "ACTION.BIN"; insert.py now runs armips on
    DATA/ACTION.BIN too; tests/test_font.py ACTION_ORIG/ACTION_DATA hold the original words). Master tab: element
    (Ali) x 103 -> 121, Lv..Ap +30 (header table 0x80167180 = 7 x {x, y, ptr}); Guardian tab: Type +4, Ali -6, Lv
    +10. Shots (QA build `--qa map70.0245=Suzune Ichinomiya --qa map70.025b=Kotone Ichinomiya`): 90 px names whole.
    windows rows: "UNIT list element" 42 px (action.00148-0016c out of exe_pending.txt, now 211 ids), "evd unit
    name" 94 measured (was 95 pending). New scenes tac_unit_g (R1 = Guardian tab), tac_unit_r (+ right = stat page
    2: As Al Df Hi Es Hl; the name column stays).
  - 2026-11-24 (12): **phase 7 closed: EXE widths.** asm/hooks.asm: ring > SEARCH tabs respaced (Tactic/Trait/Psi
    at 46/86/120, boxes sized), 思考 submenu box + highlight widened, Berserk Alert popup, Retreat Proposal title box,
    TURN END prompt box, Ap-cost popup "Restore Sp", 情報 type row x 88 + Tec. traits one per row, UNIT list Guardian
    Type column draws short Forms (payload `type_short`, D14). Text: True Ryuki parts "R. Arm..." (D14, polish.md),
    HEN roster given names for Kaoru/Sayaka/twins, "Scarlet Wing Necklace". windows.py rows with evidence for every
    group; exe_pending.txt now 34 BATTLE.BIN ids. Card labels (Spare A-D...) = debug printf only. New: scenes
    tac_info_g, tac_search_trait/psi, tac_think_menu, tac_power_cost, hen_unit(2); tools/lua/unit_type.lua (force
    guardian Forms), tools/jal_xref.py (callers of a function), tools/pending.py (pending ids with JP/EN px).
  - 2026-11-24 (13): **phase-7 review fixes** (.harness/reviews/...-phase7.md). Critical 1: 4 referenced JP strings
    sat just past their range end (ACTION 0x10EC ターンを終了 = "End Turn", HEN 0x320 = "Start the battle?", DAY 0x2C0
    = "[Invalid stage]", BATTLE 0x2E28 待機中 = debug printf, data): ranges extended, extracted, translated. New
    `tools/jp_refs.py` (every word/lui-pair ref onto kana/kanji outside the ranges; `--built`: any referenced JP but
    `status: data`) in tests/test_script.py and in build.patch (build fails on leftover JP: Important 5). Important
    3: windows.lint expands each printf `%s` to its longest English (`args`) and knows the byte-count-sized message
    box (`px="bytes"`): "%s evolved into %s" (quotes dropped: 48-byte screen limit). Important 4: TURN END prompt
    (ring item 7 = new scene tac_turnend), its End Turn/Retreat variant and Retreat Proposal (tac_retreat) shot via
    new probe tools/lua/turnend.lua; Berserk Alert, Ap popup, HEN start prompt still code-only (below).
  - 2026-11-24 (14): **phase 7 closed.** (0) The 34 BATTLE.BIN ids are never read: trait records 0x801713E8+12n
    draw a glyph-index list (+4, split.tim = graphics G9), element/boss bg records 0x80171BCC+16n read +0/+4/+0xC
    only; the strings at +8 have no reader (xref EXE + all overlays). windows row "battle unread labels";
    tools/exe_pending.txt empty. **VS banner fix** (asm/hooks.asm vs_left, 0x8004FF6C): the left name was
    right-aligned by byte count (English ended short, 108 px names ran off-screen left); now 91 - pixel width, ends
    x 119 (shot: battle + `--qa exe.a6414=True Ryuki L. Shoulder`). Right "True Ryuki R. Shoulder" 203-309 touches
    the plate end-cap (polish.md). (0b) all shot: Berserk Alert (tools/lua/berserk.lua), Ap "Restore Mp" and
    "Obtained 'Scarlet Wing Necklace'" (new tools/lua/setreg.lua: register writes in exec hooks), HEN "Start the
    battle?" (poke.lua EVERY=1: team-select mode 0x8016B02C=5, sub-state 9). New scene tac_item (行動 > Item);
    inventory = item counts u8[60] at 0x80157F70. Commands per row in docs/windows.md.
  - 2026-11-24 (15): phase-7 review (.harness/reviews/...-phase7.md): no Critical/Important findings. **Phase 8
    graphics pipeline**: `tx03.compress` (greedy; recompresses originals to the same sizes; tests/test_tx03.py),
    `tools/gfx.py` (cards drawn from TSVs with fonts/LiberationSerif-*.ttf, OFL; TX03 written in place before the
    UNN repack, logged; writecheck checks SUBTI.PAK and in-place UNN writes). Done: **G1/G2** title + chapter cards
    (gfx/cards.tsv; SUBTI.PAK index = ACTION.BIN 0x12664, may grow inside its sectors; UNN g17 = alternate layouts,
    37/47/49 differ), shot `one.py battle --frames 16400` f016050; **G4** condition cards (gfx/conditions.tsv,
    g18), shot `one.py tac_mission`. `python tools/gfx.py` writes previews to work/gfx/cards/.
  - 2026-11-24 (16): G3 location cards (gfx/locations.tsv), G6/G18 title subtitle + copyright, G8 disc-swap screens
    (D15).
  - 2026-11-24 (17): **GRETC TIM redraws** (`gfx.gretc_images` -> insert.patch_tree adds them to the GRETC repack;
    same sizes, pixels only; tests/test_gfx.py): G5 SKY / EARTH (new scene route_choice_r), G13 VOICE PLAY legend
    (two lines; the voice actor name is printed right of CV), G11 cover katakana -> "Guardian Recall". D16: G11 seals,
    G12 scroll poem, G14 medallions kept as decoration. All shot in game (graphics.md rows).
  - 2026-11-24 (18): **G17 element orbs** English: source = UNN g09 +0x1323C (TX03 of a TIM; found by VRAM dump
    with the skill's ppudump.lua probe + needle search, CLUTs in the same TIM). `gfx.orb_sheet` re-shades each orb in
    its own CLUT + 7-px caps name (SKY EARTH THUNDER SEA FLAME WIND NETHER HOLY EMPEROR MASTER); shots tac_diagram,
    tac_unit_menu. **G10 pentagram** (OPTION background) English via `gfx.penta`; shot option. tests/test_gfx.py.
  - 2026-11-24 (19): **G9 battle labels English** (docs/re/graphics.md G9 row): `gfx.label_*` + hooks.asm BATTLE
    block (advance 32, centring 32n; BATTLE.BIN now an armips target), all 29 shot (`tools/debug/g9shots.py`,
    probe tools/lua/g9labels.lua). Label watchers scan only twice in the battle state (~220, ~457 frames in).
    **G15 groundwork:** `tools/mdec.py` MDEC v2 decode/encode, all 4797 STAFF.STR frames byte-identical
    (tests/test_mdec.py); pixel decode `to_pixels` matches ffmpeg (mean diff 0.12/255), forward path
    `block_levels`/`gray_mb` written but not yet tried in a frame. Text column x 0-159 (clips at x >= 164, y ~80-160)
    scrolls a constant 2 px/frame until ~frame 4290; `tools/staff_strip.py` stitches it into work/staff/strip.png
    (8326 rows) + offsets.tsv (frame -> strip offset) + strip_NN.png pages. **Every credit transcribed** into
    gfx/staff.tsv (scroll order, draft English; "?" = unconfirmed name reading, `(glossary)` = cast character name
    to take from glossary.md).
- **Next (phase 8):** (0) Graphics row left: **G15 STAFF.STR credits** (D3 = English). Plan: (a) done (gfx/staff.tsv);
  (b) finish en: cast names from glossary.md, check "?" readings against a source (MobyGames, anime staff
  databases; record it in decisions.md; still-unsure ones -> Waiting, non-blocking), G18/D15 spelling for the
  copyright names; (c) done: 2 px/frame, offsets.tsv; (d) render the English strip (same row of each Japanese line:
  find line bands in strip.png; white serif on black, centred at x 80, cast lines "Name …… Actor" across 0-159), then
  per frame: decode, replace the left-column
  macroblocks with the English column rendered on black (forward DCT + PSX quant matrix at the frame's qscale),
  keep the right-side macroblocks' coefficients as they are, re-encode; each frame must fit its own chunks x 2016
  bytes (same sector layout, audio sectors untouched); (e) write the new STR into disc 2's tree in build.patch
  (mkpsxiso keeps form-2 STR as-is; check layout.xml), shoot scene `ending` (disc 2) from a cold boot.
  Still unknown whether other code draws split.tim cells (none seen).
  Chapter cards (SUBTI 39-43) not yet shot in game.
  (1) Full regen tour of every scene on the English build + visual-QA verdicts (qa_gate.py; do
  the read-only verdict pass yourself: no nested workers), graphics-text survey G1-G18 redraws (G9 = battle
  Psi/trait label glyphs in GRETC mill 004 split.tim, composed from glyph-index lists at BATTLE 0x80171374+: redraw
  or re-point to English label art), inkbox on choice/centred boxes, stress saves, textcover. A battle where a
  passive Psi/trait fires is still unshot (needed for G9).
  Review Minors still open: 6 blank-padding rule, 7 keep-list for empty en, 8 orphan-page lint, 10 check.py 176 s,
  11 branch-target check in writecheck. Other rows still "measured (code)" (printf messages, Psi active / target
  prompt): shoot in the phase-8 tour. insert.repoint fails on exe.01324 ("????", pair p8002C9D8 builds 0x80014020)
  if that string ever outgrows its room.
  Earlier phase-7 notes kept for reference:
  (a1) Unit-type name table = flat pointer list at EXE 0x80095D08 (index = unit type; short species names a63xx-a65xx
  and long names 015b4-0270c mixed; master names 01830-0192c too); 3 code refs (EXE file +0x2cbd4/+0x2ce30/+0x2cea8).
  Items 0x8009B51C-5CC, Forms 0x8009BC38-80, traits/types 0x8009BCA8-D14, card labels (Spare A-D, Normal, Never
  Registered) 0x8009CB3C-58. UNIT list Guardian tab: Type column x 107-155 = 48 px; if its values are the type list
  (a68cc-a69bc, up to "Seven Dragons" 73) they won't fit: page 1 has no spare x (Mp ends 303). Idea if several
  screens stay short: a "tight" VWF mode (advance - 1 px per glyph, ~10%) or a condensed font; check legibility.
  (a2) EXE widths: 211 ids in tools/exe_pending.txt carry an "engine pending / unmeasured" budget (D13; docs/windows.md
  "EXE engine pending"). Method that worked for Psi: tools/debug/one.py SCENE -- --debugger --script
  tools/lua/exec_log.lua --var "ADDRS='0x80043A64,0x80044624'" --var FROM=<late frame> --var MAXHITS=5000, group the
  log by ra/a0 (x)/a1 (y): the caller's box/column widths are immediates (`re.py dis`), patch them in hooks.asm, shoot
  with `build.py --qa ID=<longest English>`. Measured narrow: SEARCH tabs (Tactic hides the T of Trait), HEN roster
  for Kaoru/Sayaka/Ichinomiya twins (74 px). Not shot yet: species/guardian/item/trait/Form lists (guardian 情報,
  SEARCH Trait/Psi tabs, HEN equip; equipment names in 情報 Head/Hand/Waist/Foot: check they clear the Aura column now
  at x 208), battle Psi/trait labels (battle.0000c-000d8), 思考 submenu (Change Tactic...), TURN END prompt
  (action.01094 168 px), boot system-file messages, element names in BATTLE (battle.00848..; the action ones = UNIT list Ali, done; 主 orb in 情報 is
  graphics G17). Replace ids in the pending file with measured rows as each screen is fixed.
  Limits: scenario block 0x6A78 bytes, g13 block 0x4000 (insert.py LIMITS asserts).
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
