#!/bin/bash
# Restart-safe. The runs on the cards as they are now: the first runs of this step (run.sh, run2.sh) played on a copy
# of step 18's pool made before D-184, which keeps its own copy of the cards. (These three ran on the same boards with
# each card replaced by today's card of the same key; "python3 tools/step_18.py pools" now rebuilds that pool.)
cd /home/user/step18l/playmaker
export SENSE_RUN=step18l SENSE_18L=1
W=docs/runs/step18l/work
step() { name=$1; shift; if [ -f $W/done/$name ]; then return; fi; echo "START $name $(date +%H:%M:%S)"; if "$@" > $W/$name.log 2>&1; then touch $W/done/$name; echo "DONE $name $(date +%H:%M:%S)"; else echo "FAILED $name"; fi; }
step new_allstar python3 tools/step_18l.py trace new_allstar 200 allstar 2
step new_starter python3 tools/step_18l.py trace new_starter 90 starter 1
step new_rookie python3 tools/step_18l.py trace new_rookie 120 rookie 1
echo C_DONE
