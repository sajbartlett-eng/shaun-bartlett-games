#!/bin/bash
# Restart-safe, after run.sh: the refit, the test run on the final default, then the sense-check set on today's cards.
cd /home/user/step18n/playmaker
export SENSE_RUN=step18n SENSE_18N=1
W=docs/runs/step18n/work
until grep -q "^A_DONE" $W/run.log; do sleep 20; done
step() { name=$1; shift; if [ -f $W/done/$name ]; then return; fi; echo "START $name $(date +%H:%M:%S)"; if "$@" > $W/$name.log 2>&1; then touch $W/done/$name; echo "DONE $name $(date +%H:%M:%S)"; else echo "FAILED $name"; fi; }
score() { tag=$1; only=$2; copies=$3; shift 3; SENSE_ONLY="$only" SENSE_COPIES="$copies" python3 tools/sense_18h.py score $tag "$@"; }
final() { tag=$1; shift; SENSE_PLAY=0 SENSE_ONLY="closeout|game EB3F5B|18e's Steal|Contest or not|shoot now|move, then shoot|board 1|board 3|board 8" python3 tools/sense_18h.py score $tag "$@"; }
# B: the refit
step maps python3 tools/step_18n.py maps write rookie=fit_rookie starter=fit_starter allstar=fit_allstar
step fouls python3 tools/step_18n.py fouls fit_allstar write
[ -f $W/done/maps ] && [ -f $W/done/fouls ] || { echo "REFIT_FAILED"; exit 1; }
# C: the test: All-Star self-play on the final default (other dice than the fit)
step trace_final python3 tools/step_18n.py trace final 200 allstar 2
# D: the sense-check set on today's cards and rules: every candidate once (16 play-outs), group by group
step a_closeout score n18a "closeout" 0
step a_eb_steal score n18a "game EB3F5B|18e's Steal" 0
step a_contest score n18a "Contest or not" 0
step a_shoot score n18a "shoot now" 0
step a_boards score n18a "move, then shoot|board 1|board 8" 0
step a_board3 score n18a "board 3" 0
step f_a final n18a
echo B_DONE
