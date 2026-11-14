#!/bin/bash
cd /home/user/step18k_base/playmaker
export SENSE_RUN=step18k SENSE_18K=1
W=docs/runs/step18k/work
until grep -q "^ALL2_DONE" $W/run2.log; do sleep 20; done
git checkout -q --detach step-18k-shortlist
step() { name=$1; shift; if [ -f $W/done/$name ]; then return; fi; echo "START $name $(date +%H:%M:%S)"; if "$@" > $W/$name.log 2>&1; then touch $W/done/$name; echo "DONE $name $(date +%H:%M:%S)"; else echo "FAILED $name"; fi; }
score() { tag=$1; only=$2; copies=$3; shift 3; SENSE_ONLY="$only" SENSE_COPIES="$copies" python3 tools/sense_18h.py score $tag "$@"; }
final() { tag=$1; shift; SENSE_PLAY=0 SENSE_ONLY="closeout|game EB3F5B|18e's Steal|Contest or not|shoot now|move, then shoot|board 1|board 3|board 8" python3 tools/sense_18h.py score $tag "$@"; }
step m_changed score k18m "game EB3F5B|18e's Steal position, clock 2|board 3" 0,1 keep_in_hand=moves
step f_m final k18m keep_in_hand=moves
step trace_moves python3 tools/step_18k.py trace moves 160 1 keep_in_hand=moves
step h2h_moves_1 python3 tools/step_18k.py h2h moves_vs_default 40 "keep_in_hand=moves" ""
echo ALL3_DONE
