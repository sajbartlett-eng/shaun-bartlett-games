#!/bin/bash
# Restart-safe: each step leaves a marker when it finishes; a rerun skips the finished ones.
cd /home/user/step18l/playmaker
export SENSE_RUN=step18l SENSE_18L=1
W=docs/runs/step18l/work
step() { name=$1; shift; if [ -f $W/done/$name ]; then return; fi; echo "START $name $(date +%H:%M:%S)"; if "$@" > $W/$name.log 2>&1; then touch $W/done/$name; echo "DONE $name $(date +%H:%M:%S)"; else echo "FAILED $name"; fi; }
# A: self-play at each level on the new cards with the rule on, for the refit
step fit_rookie python3 tools/step_18l.py trace fit_rookie 160 rookie 1
step fit_starter python3 tools/step_18l.py trace fit_starter 120 starter 1
step fit_allstar python3 tools/step_18l.py trace fit_allstar 200 allstar 1
echo A_DONE
