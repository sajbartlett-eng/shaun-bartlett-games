"""Step 16: the goals' own measures, on the JavaScript search (the app's own, proved equal).

  python3 tools/goals_16.py pairs out.json        the three sensitivity pairs: the reading, the goal potential and the
                                                  ball handler's best paint square next phase, budget off and on
  python3 tools/goals_16.py integrity out.json    tactical integrity, goals off against on, 1 pair ahead:
      1. a better shot exists now: where the search without goals shoots, it must still shoot (the exam boards, and a
         board built from each: the ball handler put on a free paint square, the defenders near it sent away);
      2. a goal no longer worth chasing (the same board in the last phase): no set-up goal may remain, and where
         nothing is left the choice must be the one without goals;
      3. the defence breaks the plan (a defender put on the target): the record must say lost, and move on;
      4. a chance no top goal named: every choice with goals on, valued by the search without goals, must be within the
         margin of error of the best turn there.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playmaker_engine import agent as AG, jsbridge, exam as EX, board as B          # noqa: E402
from playmaker_engine import rules_config as RC                                      # noqa: E402
from playmaker_engine.decide import CONFIG, Read                                     # noqa: E402
from playmaker_engine.search import actor, phase_of                                  # noqa: E402
import exam_12 as X12                                                                # noqa: E402
import exam_13 as X13                                                                # noqa: E402


def run_pairs(out):
    res = {}
    for setting in ('adv', 'budget_adv'):
        X13.set_switches(None, setting)
        for name, (a, b) in X12.pairs().items():
            row = []
            for s in (a, b):
                r = Read(s)
                pen = [x for x in r.advantages() if x['kind'] == 'penetration' and x['stage'] == 'create']
                row.append(dict(reading=round(r.leaf(), 2), potential=round(r.phi(), 2),
                                paint_next=dict(square=B.sq(pen[0]['sq']), value=round(pen[0]['value'], 1),
                                                worth=round(pen[0]['worth'], 2)) if pen else None,
                                advantages=[dict(kind=x['kind'], attacker=x['i'] + 1, square=B.sq(x['sq']) if x['sq'] else None,
                                                 stage=x['stage'], value=round(x['value'], 1), worth=round(x['worth'], 2),
                                                 gap=x['gap']) for x in r.advantages()]))
            res.setdefault(name, {})[setting] = dict(first=row[0], second=row[1],
                                                     reading_difference=round(row[1]['reading'] - row[0]['reading'], 2),
                                                     with_potential_difference=round(row[1]['reading'] + row[1]['potential']
                                                                                     - row[0]['reading'] - row[0]['potential'], 2))
    X13.set_switches(None, 'base')
    json.dump(res, open(out, 'w'), indent=1)
    for k, v in res.items():
        for st, x in v.items():
            print(k[:30], st, x['reading_difference'], x['with_potential_difference'], x['first']['paint_next'], x['second']['paint_next'])


class Pick:
    """One decision by the search alone (no noise, no variety pick): its best turn, every root value, the goal record."""
    def __init__(self, eng, setting, s, ag=None):
        X13.set_switches(eng, setting)
        self.ag = ag or AG.Agent(actor(s), 'allstar', seed=1)
        results, _, _ = self.ag._js_search(s, None, 2)
        sign = 1 if actor(s) == 'O' else -1
        self.values = {' ; '.join(str(a) for a in t): sign * v for v, t in results}
        turn = max(results, key=lambda r: sign * r[0])[1]
        self.turn = [str(a) for a in turn]
        self.goals = self.ag._goal_note(s, turn)


def run_integrity(out):
    eng = jsbridge.NodeEngine().install()
    states = X13.boards(range(1, 17)) + [('C2', EX.c2()[1])]
    rep = dict(shot_now=[], dropped=[], broken=[], any_chance=[])
    margin = CONFIG['search']['stable_margin']
    for name, s in states:
        off, on = Pick(eng, 'adv', s), Pick(eng, 'goals', s)
        # 4. the goals-on choice, valued by the search without goals
        best = max(off.values.values())
        loss = best - off.values.get(' ; '.join(on.turn), best)
        rep['any_chance'].append(dict(board=name, same=off.turn == on.turn, off=off.turn, on=on.turn, loss=round(loss, 2),
                                      beyond_margin=loss > margin[phase_of(s)], goals=on.goals['goals'][:3],
                                      looks_changed=on.goals['looks_changed']))
        # 1. a shot now: on this board, and on a board built from it (the ball handler put on a free paint square,
        #    the defenders near it sent to the far end)
        cases = [(name, off, on)]
        if actor(s) == 'O':
            from playmaker_engine.decide import PAINT_SQUARES
            spot = next((q for q in PAINT_SQUARES if q not in s.o and q not in s.x), None)
            if spot is not None:
                near = [j for j in range(5) if B.cheb(s.x[j], spot) <= 3]
                free = sorted((q for q in ((x, y) for x in range(B.W) for y in range(1, B.H + 1))
                               if B.on_board(q) and q not in s.o and q not in s.x and q != spot),
                              key=lambda q: (-B.cheb(q, spot), q))
                x = list(s.x)
                for k, j in enumerate(near):
                    x[j] = free[k]
                built = s.with_(o=s.o[:s.ball] + (spot,) + s.o[s.ball + 1:], x=tuple(x))
                cases.append((name + ' (built: the ball handler free in the paint)', Pick(eng, 'adv', built), Pick(eng, 'goals', built)))
        for nm, a_off, a_on in cases:
            if any('Shot' in a for a in a_off.turn):
                rep['shot_now'].append(dict(board=nm, off=a_off.turn, on=a_on.turn, still_shoots=any('Shot' in a for a in a_on.turn),
                                            potential=a_on.goals['potential']))
        # 2 and 3 need a goal worth something on the board
        if on.goals['potential'] > 0 and actor(s) == 'O':
            last = s.with_(clock=RC.PHASE_SECONDS)                       # 2. the last phase: nothing left to set up
            a_off, a_on = Pick(eng, 'adv', last), Pick(eng, 'goals', last)
            rep['dropped'].append(dict(board=name, potential_before=on.goals['potential'],
                                       potential_last_phase=a_on.goals['potential'],
                                       set_up_goals_left=sum(g['stage'] == 'create' for g in a_on.goals['goals']),
                                       off=a_off.turn, on=a_on.turn, same=a_off.turn == a_on.turn))
            top = max(Read(s).advantages(), key=lambda a: a['worth'])    # 3. a defender put on the target square
            free = [j for j in range(5) if not B.adjacent(s.x[j], s.o[s.ball])]
            if top['sq'] not in s.o and top['sq'] not in s.x and free:
                j = min(free, key=lambda j: B.cheb(s.x[j], top['sq']))
                broken = s.with_(x=s.x[:j] + (top['sq'],) + s.x[j + 1:])
                first = Pick(eng, 'goals', s)
                before = (first.goals['current'], first.goals['target'])
                g = Pick(eng, 'goals', broken, first.ag)
                rep['broken'].append(dict(board=name, goal_before=' to '.join(str(x) for x in before), defender=f'X{j + 1}',
                                          to=B.sq(top['sq']), event=g.goals['event'], goal_after=g.goals['current'],
                                          target_after=g.goals['target'], turn=g.turn,
                                          moved_on=(g.goals['current'], g.goals['target']) != before or g.goals['event'] == 'lost'))
    X13.set_switches(eng, 'base')
    AG.FIXED['depth'] = None
    eng.close()
    rep['summary'] = dict(
        shot_now=f"{sum(r['still_shoots'] for r in rep['shot_now'])} of {len(rep['shot_now'])} still shoot",
        dropped=f"{sum(r['set_up_goals_left'] == 0 for r in rep['dropped'])} of {len(rep['dropped'])} have no set-up goal left; "
                f"{sum(r['same'] for r in rep['dropped'] if r['potential_last_phase'] == 0)} of "
                f"{sum(r['potential_last_phase'] == 0 for r in rep['dropped'])} with nothing left choose as without goals",
        broken=f"{sum(r['moved_on'] for r in rep['broken'])} of {len(rep['broken'])} moved on",
        any_chance=f"{sum(r['same'] for r in rep['any_chance'])} of {len(rep['any_chance'])} choices the same; "
                   f"{sum(r['beyond_margin'] for r in rep['any_chance'])} cost more than the margin; "
                   f"largest cost {max(r['loss'] for r in rep['any_chance'])}")
    json.dump(rep, open(out, 'w'), indent=1)
    print(json.dumps(rep['summary'], indent=1))
    for r in rep['any_chance']:
        if not r['same']:
            print(r['board'], r['off'], '->', r['on'], 'cost', r['loss'])


if __name__ == '__main__':
    {'pairs': run_pairs, 'integrity': run_integrity}[sys.argv[1]](sys.argv[2])
