#!/bin/bash
# Restart-safe, after run.sh: the refit, then the set replay and the self-play on the final default.
cd /home/user/step18l/playmaker
export SENSE_RUN=step18l SENSE_18L=1
W=docs/runs/step18l/work
until grep -q "^A_DONE" $W/run.log; do sleep 20; done
step() { name=$1; shift; if [ -f $W/done/$name ]; then return; fi; echo "START $name $(date +%H:%M:%S)"; if "$@" > $W/$name.log 2>&1; then touch $W/done/$name; echo "DONE $name $(date +%H:%M:%S)"; else echo "FAILED $name"; fi; }
score() { tag=$1; only=$2; copies=$3; shift 3; SENSE_ONLY="$only" SENSE_COPIES="$copies" python3 tools/sense_18h.py score $tag "$@"; }
final() { tag=$1; shift; SENSE_PLAY=0 SENSE_ONLY="closeout|game EB3F5B|18e's Steal|Contest or not|shoot now|move, then shoot|board 1|board 3|board 8" python3 tools/sense_18h.py score $tag "$@"; }
# B: the refit: the maps per level, and the two numbers that price a foul
step maps python3 tools/step_18l.py maps write rookie=fit_rookie starter=fit_starter allstar=fit_allstar
step fouls python3 tools/step_18l.py fouls fit_allstar write
# B2: the All-Star's first map had 105 and 70 positions for its phase 3 lines, and both sloped down (a better reading
# worth less): too few to trust. A second 200 possessions, played on the first map, and the map fitted on all 400.
step fit_allstar2 python3 tools/step_18l.py trace fit_allstar2 200 allstar 3
step maps2 python3 tools/step_18l.py maps write rookie=fit_rookie starter=fit_starter allstar=fit_allstar,fit_allstar2
step fouls2 python3 tools/step_18l.py fouls fit_allstar,fit_allstar2 write
[ -f $W/done/maps2 ] && [ -f $W/done/fouls2 ] || { echo "REFIT_FAILED"; exit 1; }
# C: All-Star self-play on the final default (other starts' dice than the fit), and the same with the rule off
step trace_final python3 tools/step_18l.py trace final 200 allstar 2
step trace_off python3 tools/step_18l.py trace off 160 allstar 2 off_balance=off
# D: the sense-check set replayed: every candidate once (16 play-outs), group by group
step a_closeout score l18a "closeout" 0
step a_eb_steal score l18a "game EB3F5B|18e's Steal" 0
step a_contest score l18a "Contest or not" 0
step a_shoot score l18a "shoot now" 0
step a_boards score l18a "move, then shoot|board 1|board 8" 0
step a_board3 score l18a "board 3" 0
# a second 16 play-outs on the positions the score turns on
step b_closeout score l18a "closeout" 0,1
step b_eb_steal score l18a "game EB3F5B|18e's Steal position, clock 10" 0,1
step b_boards score l18a "board 1|board 8" 0,1
step b_board3 score l18a "board 3" 0,1
step f_a final l18a
echo B_DONE
