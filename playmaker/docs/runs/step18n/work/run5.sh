#!/bin/bash
# Restart-safe. What the compute still allows of the set: the two Steal positions and the other two closeout
# positions (named candidates and the computer's choice, 8 play-outs), and board 1's candidates from earlier steps.
cd /home/user/step18n/playmaker
export SENSE_RUN=step18n SENSE_18N=1 SENSE_LEVEL=none
W=docs/runs/step18n/work
step() { name=$1; shift; if [ -f $W/done/$name ] || [ -f $W/STOP ]; then return; fi; echo "START $name $(date +%H:%M:%S)"; if "$@" > $W/$name.log 2>&1; then touch $W/done/$name; echo "DONE $name $(date +%H:%M:%S)"; else echo "FAILED $name"; fi; }
step s5_steal env SENSE_NAMED=1 SENSE_ONLY="18e's Steal|closeout, shooter can move|closeout, step 2" SENSE_COPIES=0 SENSE_PLAYOUTS=8 python3 tools/sense_18h.py score n18a
step s7_board1 env SENSE_ONLY="board 1" SENSE_COPIES=0 SENSE_PLAYOUTS=16 python3 tools/sense_18h.py score n18a
echo E_DONE
