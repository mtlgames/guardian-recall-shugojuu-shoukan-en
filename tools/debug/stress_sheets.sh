#!/bin/sh
# Phase-8 stress + card-box runs -> visual-QA sheets and one qa_gate manifest per disc (work/qa/vqa/s<N>/).
# Runs (re-make them after a text/code change, then re-run this):
#   disc 1: sh tools/debug/cardruns.sh                      -> work/qa/card/{zero,fmt}_en (card boot boxes)
#   disc 2: tools/debug/one.py --out stress_<S> <S> -- --script tools/lua/poke.lua --var "POKE='$(cat tools/debug/stress_poke.txt)'"
#             --var EVERY=1                                 (S = tac_info hen_unit: Lv 99, Sp 999, Mp/Ap 255, widest gear)
#           the same + --debugger --script tools/lua/draw_sweep.lua --var "EVD='<hooks.sym evd_names>'"
#             --var "WIDE='Sharihotsu (1-Blue)'" --var FROM=2900 -> stressw_<S> (S = tac_unit tac_unit_g tac_unit_mr
#             tac_unit_r tac_unit_r2 tac_info tac_info_g: the widest evd name in every name column)
#           one.py --out tac_saved tac_saved; one.py --card ev70_map.mcd --out tac_over tac_saved (save/overwrite boxes)
cd "$(dirname "$0")/../.." || exit 1
S=$(python tools/skill.py)
mk() {  # disc, sheet stem, run dir, first frame
  python -X utf8 "$S/scripts/sheet.py" "$3" --from "$4" --changed 0.03 --out "work/qa/vqa/s$1/$2_sheet.png" | tail -n 1
}
rm -rf work/qa/vqa/s1/*.png work/qa/vqa/s2/*.png
mkdir -p work/qa/vqa/s1 work/qa/vqa/s2
mk 1 card_zero work/qa/card/zero_en 2100
mk 1 card_fmt work/qa/card/fmt_en 2100
for r in stress_tac_info stress_hen_unit stressw_tac_unit stressw_tac_unit_g stressw_tac_unit_mr stressw_tac_unit_r \
         stressw_tac_unit_r2 stressw_tac_info stressw_tac_info_g tac_saved tac_over; do
  mk 2 "$r" "work/qa/one/$r" 2800
done
for d in 1 2; do
  python -X utf8 "$S/scripts/qa_gate.py" init "work/qa/vqa/s$d/manifest.tsv" "work/qa/vqa/s$d" \
    --build "$(ls build/disc$d/*.bin)"
done
