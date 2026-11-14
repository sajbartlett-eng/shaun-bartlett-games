cd /home/user/step18n/playmaker
W=docs/runs/step18n/work
T1=$(date +%s)
python3 tools/js_equivalence.py --soft --fiba --off-balance on --position-contest on --n 150 --search 8 > $W/eq_on.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --off-balance on --position-contest on --reaction --n 200 > $W/eq_react.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --off-balance on --position-contest on --zone --n 100 --search 4 > $W/eq_zone.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --off-balance on --position-contest on --zone --broken --n 60 --search 2 > $W/eq_broken.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --off-balance on --position-contest on --keep-in-hand --dice-in-hand --ball-loss --n 40 --search 6 > $W/eq_all.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --off-balance on --position-contest off --n 60 --search 3 > $W/eq_off.log 2>&1
echo CHECKS_DONE $(( $(date +%s) - T1 ))
