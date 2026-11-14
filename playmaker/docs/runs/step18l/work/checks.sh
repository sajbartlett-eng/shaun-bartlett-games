cd /home/user/step18l/playmaker
W=docs/runs/step18l/work
T1=$(date +%s)
python3 tools/js_equivalence.py --soft --fiba --off-balance on --n 200 --search 12 > $W/eq_on.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --off-balance on --zone --n 200 --search 8 > $W/eq_zone.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --off-balance on --zone --broken --n 100 --search 4 > $W/eq_broken.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --off-balance on --keep-in-hand --dice-in-hand --ball-loss --n 60 --search 12 > $W/eq_all.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --off-balance on --reaction --n 200 > $W/eq_react.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --off-balance off --n 100 --search 6 > $W/eq_off.log 2>&1
echo CHECKS_DONE $(( $(date +%s) - T1 ))
