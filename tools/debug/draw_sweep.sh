#!/bin/sh
# Text coverage: EXE/overlay pointer-table names through the screens that draw them (tools/lua/draw_sweep.lua)
# -> work/qa/cover/draw/<scene>. Use: sh tools/debug/draw_sweep.sh [SCENE..]
cd "$(dirname "$0")/../.."
SLOTS=$(python -X utf8 tools/cover_tables.py)
EVD=$(awk '$2 == "evd_names" {print $1}' work/asm/hooks.sym)
set -- ${@:-tac_unit tac_unit_g tac_unit_r tac_unit_r2 tac_unit_mr tac_info tac_info_g tac_item tac_power tac_search \
  tac_search_trait tac_search_psi tac_think_menu hen_unit hen_unit2 tac_mission opt_guardians_all opt_tactics_all day_load}
python -X utf8 tools/debug/regen.py --only "$@" --outdir "${OUT:-work/qa/cover/draw}" --cover --jobs 4 --timeout 1800 \
  --lua tools/lua/draw_sweep.lua --var "SLOTS='$SLOTS'" --var "EVD='$EVD'" --var FROM=2900 | tail -3
