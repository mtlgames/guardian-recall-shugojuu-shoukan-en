"""Writes tools/debug/scenes.tsv (the warp scene list). Edit the rows here, then run from the repo root:

    python -X utf8 tools/debug/mk_scenes.py

Columns: name, disc, target, writes, route, frames (after the warp), note. Targets and route syntax: warp.lua header.
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
                         ("opt_charfile", "8 down;40 -;8 down;40 -;8 circle", "OPTION > キャラファイル (cf.txd)")]:
    rows.append((name, "1", "ovl:16", "", OPT + (";" + keys + ";400 -" if keys else ""), "1800", note))
rows += [
    ("disc_swap", "1", "7>2", "0x8013DE46=0x1", "", "1500", "DAY disc check: DISC 1を入れてください (disc id faked as 2)"),
    ("disc_swap2", "1", "7>call:0x8004C900", "0x8013CEE4=0x2", "", "1500", "DAY disc check: DISC 2を入れてください")]
LABEL = {1: "天の章 opening (city at night)", 2: "熊本支部 KUMAMOTO", 4: "フェリー OITA-EHIME", 5: "桜井海岸 EHIME",
         6: "白虎の間 Unknown Place", 7: "天の章第六話 大鳴門橋の罠", 8: "名古屋地下街 AICHI", 9: "京の宿 KYOTO",
         10: "地の章 opening (city at night)", 11: "地の章 card", 12: "青森支部 AOMORI", 13: "七ヶ宿ダム MIYAGI",
         14: "秋田支部 AKITA", 16: "青龍の間", 17: "栃木支部 TOCHIGI", 20: "七龍の章 日光山中",
         21: "栃木支部 TOCHIGI (disc 2)", 22: "国会前庭洋式庭園", 23: "石神井公園", 24: "日比谷公園", 25: "国会議事堂",
         26: "新宿支部", 27: "トンダーエッグ", 50: "disc 1 (the starter special-cases it)",
         70: "tactics map, Turn 01 (units, HP/AP bars) after its intro"}
for n in range(1, 71):
    disc = "1" if n <= 20 or n == 50 else "2"
    rows.append((f"ev{n:02d}", disc, str(n), "", "", "1800", LABEL.get(n, "")))
with open("tools/debug/scenes.tsv", "w", encoding="utf-8", newline="\n") as f:
    for r in rows:
        assert len(r) == 7, r
        f.write("\t".join(r) + "\n")
