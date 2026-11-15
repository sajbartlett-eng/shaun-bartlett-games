cd /home/user/step18o/playmaker
W=docs/runs/step18o/work
mkdir -p $W/done
until grep -q "zone on his game" $W/prepare.log; do sleep 10; done
for g in setup beaten drive zone_setup zone_beaten zone_drive; do
  [ -f $W/STOP ] && exit 0
  [ -f $W/done/sense_$g ] && continue
  python3 tools/step_18o.py sense $g 16 > $W/sense_$g.log 2>&1 && touch $W/done/sense_$g
done
echo SENSE_DONE
