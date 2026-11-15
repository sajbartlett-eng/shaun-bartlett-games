cd /home/user/step18o/playmaker
W=docs/runs/step18o/work
until [ -f $W/done/site ]; do sleep 20; done
T1=$(date +%s)
python3 -m pytest tests/test_static.py -q -p no:cacheprovider > $W/tests_static.log 2>&1
python3 -m pytest tests/test_rules_current.py tests/test_position_contest_18n.py tests/test_setup_18o.py tests/test_off_balance_18l.py tests/test_foul_price_18k.py tests/test_contest_18j.py tests/test_see_the_steal_18j.py tests/test_fiba_18i.py tests/test_zone_18g.py tests/test_wedge.py tests/test_movement.py tests/test_defence.py tests/test_intercepts_mti.py tests/test_intercepts_oq72.py tests/test_rolls_scoring.py tests/test_rulebook_nov.py tests/test_rulings_3i.py tests/test_turns_phases.py tests/test_receiver_denial.py tests/test_breaking.py tests/test_scenarios.py tests/test_golden_and_regression.py tests/test_step3m.py tests/test_step3n.py tests/test_step6.py tests/test_web.py tests/test_levels_3l.py tests/test_scouting.py tests/test_teams.py tests/test_computer.py -q -p no:cacheprovider -rxX > $W/tests_final.log 2>&1
echo TESTS_DONE $(( $(date +%s) - T1 )) >> $W/tests_final.log
