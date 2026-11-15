cd /home/user/step18o/playmaker
W=docs/runs/step18o/work
until grep -q SENSE_DONE $W/sense.log; do sleep 15; done
for g in arrows zone_arrows; do
  [ -f $W/STOP ] && exit 0
  [ -f $W/done/sense_$g ] && continue
  python3 tools/step_18o.py sense $g 16 > $W/sense_$g.log 2>&1 && touch $W/done/sense_$g
done
echo SENSE2_DONE
