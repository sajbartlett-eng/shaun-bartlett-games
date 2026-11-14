#!/bin/bash
cd /home/user/step18k_base/playmaker
export SENSE_RUN=step18k SENSE_18K=1
W=docs/runs/step18k/work
until grep -q "^ALL_DONE" $W/run.log; do sleep 20; done
step() { name=$1; shift; if [ -f $W/done/$name ]; then return; fi; echo "START $name $(date +%H:%M:%S)"; if "$@" > $W/$name.log 2>&1; then touch $W/done/$name; echo "DONE $name $(date +%H:%M:%S)"; else echo "FAILED $name"; fi; }
score() { tag=$1; only=$2; copies=$3; shift 3; SENSE_ONLY="$only" SENSE_COPIES="$copies" python3 tools/sense_18h.py score $tag "$@"; }
final() { tag=$1; shift; SENSE_PLAY=0 SENSE_ONLY="closeout|game EB3F5B|18e's Steal|Contest or not|shoot now|move, then shoot|board 1|board 3|board 8" python3 tools/sense_18h.py score $tag "$@"; }
# a second 16 play-outs where keep_in_hand changed the choice
step b_extra score k18h "shoot now or play on 4|18e's Steal position, clock 2|board 3" 0,1 keep_in_hand=true
step f_a final k18a
step f_h final k18h keep_in_hand=true
step f_d final k18d dice_in_hand=true
step f_hd final k18hd keep_in_hand=true dice_in_hand=true
echo ALL2_DONE
