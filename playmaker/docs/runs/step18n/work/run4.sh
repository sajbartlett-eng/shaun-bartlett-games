#!/bin/bash
# Restart-safe. After the speed fix (the second closeout movement kept to the All-Star): Starter and Rookie play
# differently now, so their self-play and maps are done again; the All-Star's play is unchanged.
cd /home/user/step18n/playmaker
export SENSE_RUN=step18n SENSE_18N=1
W=docs/runs/step18n/work
step() { name=$1; shift; if [ -f $W/done/$name ]; then return; fi; echo "START $name $(date +%H:%M:%S)"; if "$@" > $W/$name.log 2>&1; then touch $W/done/$name; echo "DONE $name $(date +%H:%M:%S)"; else echo "FAILED $name"; fi; }
step fit_starter2 python3 tools/step_18n.py trace fit_starter2 90 starter 1
step fit_rookie2 python3 tools/step_18n.py trace fit_rookie2 120 rookie 1
step maps2 python3 tools/step_18n.py maps write rookie=fit_rookie2 starter=fit_starter2 allstar=fit_allstar
echo D_DONE
