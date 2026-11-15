cd /home/user/step18o/playmaker
export SENSE_RUN=step18o SENSE_18N=1
W=docs/runs/step18o/work
until grep -q SPEED_DONE $W/speed.log 2>/dev/null; do sleep 15; done
env SENSE_18O=1 SENSE_ZONE=1 SENSE_NAMED=1 SENSE_LEVEL=none SENSE_COPIES=0 SENSE_PLAYOUTS=16 SENSE_ONLY="game EB3F5B" python3 tools/sense_18h.py score o18z > $W/setzone2.log 2>&1
echo EBZONE_DONE >> $W/setzone2.log
