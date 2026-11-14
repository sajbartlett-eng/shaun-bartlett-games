#!/bin/bash
# Restart-safe. The sense-check set on today's cards and rules, cut to what the compute allows: a possession under
# D-191 runs about half as long again, so a play-out costs about 30 core-seconds. Only the candidates the set names
# and the computer's own choice are played; the positions in order of what hangs on them. Each step can be the last.
cd /home/user/step18n/playmaker
export SENSE_RUN=step18n SENSE_18N=1 SENSE_NAMED=1 SENSE_LEVEL=none
W=docs/runs/step18n/work
step() { name=$1; shift; if [ -f $W/done/$name ] || [ -f $W/STOP ]; then return; fi; echo "START $name $(date +%H:%M:%S)"; if "$@" > $W/$name.log 2>&1; then touch $W/done/$name; echo "DONE $name $(date +%H:%M:%S)"; else echo "FAILED $name"; fi; }
score() { tag=$1; only=$2; n=$3; shift 3; SENSE_ONLY="$only" SENSE_COPIES=0 SENSE_PLAYOUTS=$n python3 tools/sense_18h.py score $tag "$@"; }
step s1_cheap score n18a "game EB3F5B|Contest or not|move, then shoot" 16
step s2_closeout score n18a "closeout, shooter cannot move" 16
step s3_boards score n18a "board 1|board 8" 16
step s4_board3 score n18a "board 3" 8
step s5_steal score n18a "18e's Steal|closeout, shooter can move|closeout, step 2" 8
step s6_shoot score n18a "shoot now" 8
echo C_DONE
