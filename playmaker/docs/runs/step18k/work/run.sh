#!/bin/bash
# Restart-safe: each step leaves a marker when it finishes; a rerun skips the finished ones. Play-outs are saved
# after every step, so a restart loses one step at most.
cd /home/user/step18k_base/playmaker
export SENSE_RUN=step18k SENSE_18K=1
W=docs/runs/step18k/work
step() { name=$1; shift; if [ -f $W/done/$name ]; then return; fi; echo "START $name $(date +%H:%M:%S)"; if "$@" > $W/$name.log 2>&1; then touch $W/done/$name; echo "DONE $name $(date +%H:%M:%S)"; else echo "FAILED $name"; fi; }
score() { tag=$1; only=$2; copies=$3; shift 3; SENSE_ONLY="$only" SENSE_COPIES="$copies" python3 tools/sense_18h.py score $tag "$@"; }
ALL="closeout|game EB3F5B|18e's Steal|Contest or not|shoot now|move, then shoot|board 1|board 3|board 8"
HINGE="closeout|game EB3F5B|18e's Steal position, clock 10|board 1|board 3|board 8"
# A: every candidate once (16 play-outs), group by group
step a_closeout score k18a "closeout" 0
step a_eb_steal score k18a "game EB3F5B|18e's Steal" 0
step a_contest score k18a "Contest or not" 0
step a_shoot score k18a "shoot now" 0
step a_boards score k18a "move, then shoot|board 1|board 8" 0
step a_board3 score k18a "board 3" 0
# the choices under each setting, new ones played once
step h_all score k18h "$ALL" 0 keep_in_hand=true
step d_all score k18d "$ALL" 0 dice_in_hand=true
step hd_all score k18hd "$ALL" 0 keep_in_hand=true dice_in_hand=true
# self-play: the check against basketball, and the recheck
step trace_base python3 tools/step_18k.py trace base 160
step trace_dice python3 tools/step_18k.py trace dice 160 1 dice_in_hand=true
step trace_hand python3 tools/step_18k.py trace hand 160 1 keep_in_hand=true
# B: a second 16 play-outs on the positions the gate turns on
step b_closeout score k18a "closeout" 0,1
step b_eb_steal score k18a "game EB3F5B|18e's Steal position, clock 10" 0,1
step b_boards score k18a "board 1|board 8" 0,1
step b_board3 score k18a "board 3" 0,1
echo ALL_DONE
