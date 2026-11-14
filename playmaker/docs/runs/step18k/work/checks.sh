cd /home/user/step18k/playmaker
W=docs/runs/step18k/work
T1=$(date +%s)
python3 -m pytest tests/test_static.py -q -p no:cacheprovider > $W/tests_static.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --n 200 --search 12 > $W/eq_off.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --zone --n 200 --search 8 > $W/eq_zone.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --zone --broken --n 100 --search 4 > $W/eq_broken.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --keep-in-hand moves --n 100 --search 12 > $W/eq_moves.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --keep-in-hand --dice-in-hand --ball-loss --n 60 --search 12 > $W/eq_all.log 2>&1
python3 tools/js_equivalence.py --soft --fiba --reaction --n 200 > $W/eq_react.log 2>&1
echo CHECKS_DONE $(( $(date +%s) - T1 ))
