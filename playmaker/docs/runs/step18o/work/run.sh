#!/bin/bash
# Restart-safe: each step leaves a marker when it finishes; a rerun skips the finished ones.
cd /home/user/step18o/playmaker
export SENSE_RUN=step18o SENSE_18N=1
W=docs/runs/step18o/work
mkdir -p $W/done
step() { name=$1; shift; [ -f $W/STOP ] && exit 0; if [ -f $W/done/$name ]; then return; fi; echo "START $name $(date +%H:%M:%S)"; if "$@" > $W/$name.log 2>&1; then touch $W/done/$name; echo "DONE $name $(date +%H:%M:%S)"; else echo "FAILED $name"; fi; }
until grep -q SENSE2_DONE $W/sense2.log; do sleep 15; done
# the refit: self-play at each level on today's cards and rules
step fit_allstar python3 tools/step_18o.py trace fit_allstar 200 allstar 1
step fit_starter python3 tools/step_18o.py trace fit_starter 90 starter 1
step fit_rookie python3 tools/step_18o.py trace fit_rookie 120 rookie 1
step maps python3 tools/step_18o.py maps write rookie=fit_rookie starter=fit_starter allstar=fit_allstar
step fouls python3 tools/step_18o.py fouls fit_allstar write
step site python3 -m playmaker_web.build_site
# the test, in two arms, on the final default
step armA python3 tools/step_18o.py trace armA 200 allstar 1 off
step armB python3 tools/step_18o.py trace armB 200 allstar 1 zone
step measures python3 tools/step_18o.py measures armA armB fit_starter fit_rookie
step arm_A python3 tools/step_18o.py arm armA
step arm_B python3 tools/step_18o.py arm armB
# the set: the positions a jump shot's contest decides, and Shaun's game in each arm
step set env SENSE_18O=1 SENSE_NAMED=1 SENSE_LEVEL=none SENSE_COPIES=0 SENSE_PLAYOUTS=16 SENSE_ONLY="closeout|game EB3F5B" python3 tools/sense_18h.py score o18a
step setzone env SENSE_18O=1 SENSE_ZONE=1 SENSE_NAMED=1 SENSE_LEVEL=none SENSE_COPIES=0 SENSE_PLAYOUTS=16 SENSE_ONLY="game EB3F5B" python3 tools/sense_18h.py score o18z
echo RUN_DONE
