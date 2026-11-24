#!/bin/sh
# Card boot/format flows on the EN build and the original disc 1, for inkbox (tools/inkscan.py):
#   sh tools/debug/cardruns.sh [NAME..]   NAME = zero fmt none corrupt (default all) -> work/qa/card/<NAME>_{en,jp}
# zero = unformatted card, No to formatting (notice); fmt = Yes to formatting + create the system file;
# none = no card; corrupt = sys.mcd with a bad checksum. Routes in tools/routes/card_*.txt.
cd "$(dirname "$0")/../.." || exit 1
S=$(python tools/skill.py)
EN=$(ls build/disc1/*.cue)
JP=$(ls rom/*"Disc 1"*.cue)
mkdir -p work/cards work/qa/card
python -c "open('work/cards/zero.mcd','wb').write(bytes(131072))"
python -c "d=bytearray(open('tools/debug/cards/sys.mcd','rb').read()); d[0x3FFE]^=0x55; open('work/cards/corrupt.mcd','wb').write(d)"
for n in ${*:-zero fmt none corrupt}; do
  case $n in zero|fmt) sav="--sav work/cards/zero.mcd";; corrupt) sav="--sav work/cards/corrupt.mcd";; *) sav="";; esac
  route=tools/routes/card_$n.txt; [ -f "$route" ] || route=tools/routes/card_zero.txt
  for v in en jp; do
    cue=$EN; [ $v = jp ] && cue=$JP
    python -X utf8 "$S/scripts/emu.py" "$cue" --out "work/qa/card/${n}_$v" $sav --route "$route" --shot-every 10 \
      --timeout 400 > "work/qa/card/${n}_$v.out" 2>&1 &
  done
  wait
  tail -n 1 "work/qa/card/${n}_en.out" "work/qa/card/${n}_jp.out"
done
