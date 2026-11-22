"""Writes tools/debug/scenes.tsv (the warp scene list). Edit the rows here, then run from the repo root:

    python -X utf8 tools/debug/mk_scenes.py

Columns: name, disc, target, writes, route, frames (after the warp), note[, card in tools/debug/cards/].
Targets and route syntax: warp.lua header.
Event labels come from the regen sweep's location cards (tools/debug/overview.py); blank = not yet looked at.
"""
rows = [("# name", "disc", "target", "writes", "route", "frames", "note")]
rows += [("title", "1", "ovl:16", "", "520 -", "0", "title screen, PUSH START (overlay TITLE2 0x16 + intro)"),
         ("title_menu", "1", "ovl:16", "", "520 -;8 start;150 -", "0", "title menu: LOAD / NEW GAME / OPTION"),
         ("title_load", "1", "ovl:16", "", "520 -;8 start;150 -;8 up;60 -;8 start;600 -", "1500",
          "title > LOAD (memory card; DAY overlay)"),
         ("route_choice", "1", "idle", "", "60 -", "600", "天/地 route choice (RSEL), where new games start")]
OPT = "520 -;8 start;150 -;8 down;60 -;8 start;1000 -"   # title > OPTION = the BRAIN menu (BRAIN.BIN)
for name, keys, note in [("option", "", "OPTION menu: 守護獣戦術指南 守護獣図鑑 イベント再現 用語辞典 キャラファイル EXIT"),
                         ("opt_tactics", "8 circle", "OPTION > 守護獣戦術指南 (tutorial list, tu.txd)"),
                         ("opt_guardians", "8 right;40 -;8 circle", "OPTION > 守護獣図鑑 (gd.txd)"),
                         ("opt_replay", "8 down;40 -;8 circle", "OPTION > イベント再現 (rep.txd)"),
                         ("opt_dictionary", "8 down;40 -;8 right;40 -;8 circle", "OPTION > 用語辞典 (dic.txd)"),
                         ("opt_charfile", "8 down;40 -;8 down;40 -;8 circle", "OPTION > キャラファイル (cf.txd)"),
                         ("opt_music", "8 triangle;300 -", "OPTION > △ MUSIC MODE (track 1:MAIN THEME, scrolling)"),
                         ("opt_music_track", "8 triangle;300 -;8 r2;300 -", "MUSIC MODE > R2: next track")]:
    rows.append((name, "1", "ovl:16", "", OPT + (";" + keys + ";400 -" if keys else ""), "1800", note))
    if keys and "triangle" not in keys:  # same screen with every entry unlocked: card made by tools/debug/save.py --unlock-all
        rows.append((name + "_all", "1", "ovl:16", "", rows[-1][4], "1800", note + ", all entries (unlock.mcd)",
                     "unlock.mcd"))
# disc 2 OPTION > イベント再現 lists rep entries 44-84 (disc 1 shows 1-43); entry 39 = エンディング (staff credits,
# STAFF.STR ~19000 frames), 40/41 = epilogues. Unlocked card; the list ignores presses closer than ~30 frames.
REP2 = OPT + ";8 down;40 -;8 circle;400 -"
for name, n, frames, note in [("replay_d2", 0, "2000", "disc 2 イベント再現 list (entries 44-84)"),
                              ("ending", 38, "23000", "イベント再現 > エンディング: ending + staff credits to the end"),
                              ("epilogue_miyuki", 39, "5500", "イベント再現 > エピローグ（美由紀バージョン）"),
                              ("epilogue_yuko", 40, "5500", "イベント再現 > エピローグ（裕子バージョン）")]:
    rows.append((name, "2", "ovl:16", "", REP2 + ";6 down;30 -" * n + (";60 -;8 circle;400 -" if n else ""), frames,
                 note, "unlock.mcd"))
rows += [
    ("disc_swap", "1", "7>2", "0x8013DE46=0x1", "", "1500", "DAY disc check: DISC 1を入れてください (disc id faked as 2)"),
    ("disc_swap2", "1", "7>call:0x8004C900", "0x8013CEE4=0x2", "", "1500", "DAY disc check: DISC 2を入れてください")]
LABEL = {1: "天の章 opening (city at night)", 2: "熊本支部 KUMAMOTO", 4: "フェリー OITA-EHIME", 5: "桜井海岸 EHIME",
         6: "白虎の間 Unknown Place", 7: "天の章第六話 大鳴門橋の罠", 8: "名古屋地下街 AICHI", 9: "京の宿 KYOTO",
         10: "地の章 opening (city at night)", 11: "地の章 card", 12: "青森支部 AOMORI", 13: "七ヶ宿ダム MIYAGI",
         14: "秋田支部 AKITA", 16: "青龍の間", 17: "栃木支部 TOCHIGI", 20: "七龍の章 日光山中",
         21: "栃木支部 TOCHIGI (disc 2)", 22: "国会前庭洋式庭園", 23: "石神井公園", 24: "日比谷公園", 25: "国会議事堂",
         26: "新宿支部", 27: "トンダーエッグ",
         48: "DISC 1を入れてください (same screen when warped on disc 1: a swap point, not a disc-1 event)", 50: "disc 1 (the starter special-cases it)",
         70: "tactics map, Turn 01 (units, HP/AP bars) after its intro"}
for n in range(1, 71):
    disc = "1" if n <= 20 or n == 50 else "2"
    rows.append((f"ev{n:02d}", disc, str(n), "", "", "1800", LABEL.get(n, "")))
# tactics-map menus, from ev70's Turn 01 (map ready ~1700 frames after the warp; cursor on the master 天城美由紀)
MAP = "1750 -"
RING = MAP + ";6 triangle;60 -" + ";6 down;40 -" * 6   # ring: UNIT MAP MISSION DIAGRAM SEARCH CONFIG BREAK
for name, keys, frames, note in [
        ("tac_unit_menu", ";6 circle;60 -", "1900", "unit command menu: 移動 情報 行動 思考 待機"),
        ("tac_action", ";6 circle;40 -;6 down;15 -;6 down;15 -;6 circle;60 -", "1950", "行動 submenu: 超力 アイテム 話す 送還"),
        ("tac_power", ";6 circle;40 -;6 down;15 -;6 down;15 -;6 circle;40 -;6 circle;60 -", "2000",
         "超力 list + help box"),
        ("tac_think", ";6 circle;40 -;6 down;15 -;6 down;15 -;6 down;15 -;6 circle;40 -;6 circle;60 -", "2050",
         "思考 list (guardian orders) + help box"),
        ("tac_info", ";6 circle;40 -;6 down;15 -;6 circle;90 -", "1950", "情報 (unit info screen)"),
        ("tac_wait", ";6 circle;40 -;6 down;15 -;6 down;15 -;6 down;15 -;6 down;15 -;6 circle;60 -", "2000",
         "待機: 決定 / キャンセル")]:
    rows.append((name, "2", "70", "", MAP + keys, frames, note))
rows += [("tac_ring", "2", "70", "", MAP + ";6 triangle;80 -", "1900", "field ring menu (triangle), on UNIT"),
         ("tac_config", "2", "70", "", RING.rsplit(";6 down;40 -", 1)[0] + ";6 circle;90 -", "2300", "ring > CONFIG"),
         ("tac_mission", "2", "70", "", MAP + ";6 triangle;60 -;6 down;40 -;6 down;40 -;6 circle;90 -", "2100",
          "ring > MISSION"),
         *[(f"tac_{k}", "2", "70", "", MAP + ";6 triangle;60 -" + ";6 down;40 -" * d + ";6 circle;120 -", "2200",
            f"ring > {k.upper()}") for k, d in [("unit", 0), ("map", 1), ("diagram", 3), ("search", 4)]],
         ("tac_break", "2", "70", "", RING + ";6 circle;60 -", "2300", "ring > BREAK: マップセーブを行いますか？"),
         ("tac_saved", "2", "70", "", RING + ";6 circle;60 -;6 up;20 -;6 circle;1100 -", "3400",
          "BREAK > はい: セーブ中です, then セーブしました + ゲームを終了しますか？ (writes the run's card)")]
# first battle, played from a new game (天 route, event 1): one cycle = a master's 待機 決定 (or dialog ○), cancel,
# L2 to the next unit; the turn passes once every master has acted. The run stops 500 frames into BATTLE (0x15).
# Slow (~60000 frames): regen.py --only battle --timeout 2400.
TURN = "8 circle;30 -" + ";8 down;20 -" * 4 + ";8 circle;30 -;8 circle;60 -;8 cross;20 -;8 cross;20 -;8 l2;40 -"
rows.append(("battle", "1", "idle", "", "60 -;6 circle;90 -;6 circle;90 -;6 circle;" + ";".join([TURN] * 220)
             + ";stop:15+500", "90000", "first battle (BATTLE overlay 0x15), event 1 Turn 3-4, from a new game"))
# the run ends WARP_BOOT (2800) + frames after power-on but the warp lands ~150 frames later: give routes headroom
rows = [r[:5] + (str(int(r[5]) + 400),) + r[6:] if r[0].startswith("tac_") else r for r in rows]
with open("tools/debug/scenes.tsv", "w", encoding="utf-8", newline="\n") as f:
    for r in rows:
        assert len(r) in (7, 8), r
        f.write("\t".join(r) + "\n")
