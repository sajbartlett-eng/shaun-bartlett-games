"""Step 18e: the control rule as the app's rule (D-153, D-154) and the open list (search.open_list, D-156).

  python3 tools/step_18e.py replay              Shaun's playtest (game EB3F5B) replayed from its log -> runs/step18e/replay.json
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
import learn_17 as L                                   # noqa: E402

RUN = os.path.join(ROOT, 'docs', 'runs', 'step18e')
WORK = os.environ.get('STEP18E_WORK', os.path.join(RUN, 'work'))
L.WORK = WORK
# the two settings every measure compares: the old default (no control rule, today's list) and the new one
OLD = dict(control='0', open_list=False)
NEW = dict(control=None, open_list='defence')


def run_line(state_json, ctx_json, setting, turns, top=6):
    """tools/line_18d.js on one position under a setting: the search's choice 1 pair ahead, its best few turns, and
    each named turn's value."""
    jf, of = os.path.join(WORK, f'line_{os.getpid()}.job.json'), os.path.join(WORK, f'line_{os.getpid()}.out.json')
    job = dict(state=state_json, ctx=ctx_json, profile=L.profiles()['allstar'], turns=turns, top=top, open_list=setting['open_list'])
    if setting['control'] is not None:
        job['control'] = setting['control']
    json.dump(job, open(jf, 'w'))
    subprocess.run(['node', os.path.join(HERE, 'line_18d.js'), jf, of], check=True)
    return json.load(open(of))


# ---- part 3: Shaun's playtest ----------------------------------------------------------------------------------------

LOG = """[human] O3 Move to M10
[human] O1 Pass to O3
[ai] X2 Move to D9 facing W
[ai] X1 Move to L8 facing NE
[human] O1 Sprint to I7
[human] O3 Pass to O1
[ai] X1 Quick Step to L9
[ai] X4 Sprint to F4
[human] O Hesitate
[ai] X3 Move to J6 facing N
[ai] X5 Move to M2 facing N
[human] O1 Move to G5
[human] O Hesitate
[ai] X1 Sprint to G9
[ai] X3 Move to I7 facing SW
[human] O1 Pass to O4
[ai] X Pause
[human] O4 Shot (three)
[ai] X2 Move to D8 facing S
[ai] X4 Sprint to B4"""
O_PLACED, X_PLACED = ['I11', 'C9', 'O9', 'A3', 'Q3'], ['J10', 'D8', 'L7', 'B4', 'P2']


def _replay(rules, arrows, upto=None):
    """Play the log's lines in order under `rules` from the logged placement with the defence facing `arrows`.
    Returns (states before each line, the line that failed or None). A turn that the log leaves at one action is ended
    by the side's own 'End turn' when the next line belongs to the other side."""
    from playmaker_engine.scenarios import game_state
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    from playmaker_engine.search import actor
    s = game_state('Five Out', 'High-Low', O_PLACED, X_PLACED, arrows, ball=0, rules=rules, quarter_left=18)
    lines = [ln.split('] ', 1)[1] for ln in LOG.splitlines()]
    before = []
    for k, ln in enumerate(lines[:upto]):
        side = ln[0]
        if not isinstance(s, ChanceNode) and s.stage in ('play', 'reaction') and actor(s) != side:
            end = [a for a in legal_actions(s) if a.kind == 'end_turn']      # the log doesn't write a turn's end
            if end:
                s = apply(s, end[0])
        before.append(s)
        a = next((x for x in legal_actions(s) if str(x) == ln), None)
        if a is None:
            return before, dict(line=k + 1, text=ln, state=s.encode(), legal_like=[str(x) for x in legal_actions(s) if str(x).split(' ')[0] == ln.split(' ')[0]][:12])
        s = apply(s, a)
        if isinstance(s, ChanceNode):
            return before, dict(line=k + 1, text=ln, why='the action went to the dice')
    before.append(s)
    return before, None


def _expected(node):
    """The points a resolved shot is worth: the dice at their chances (a possession that plays on isn't expected here)."""
    from playmaker_engine.resolve import ChanceNode
    from playmaker_engine.scoring import score
    if isinstance(node, ChanceNode):
        return sum(float(p) * _expected(sub) for p, _, sub in node.outcomes)
    return float(score(node).total) if node.stage == 'over' else None


def defend(s, ctxj, setting, named=()):
    """The computer's defence from s, one action at a time as it plays (the All-Star, 1 pair ahead, no pick noise): it
    chooses a turn, plays its first action, and chooses again, until the action passes to the offence or the dice.
    Returns (the actions with what it read, the node it ends at)."""
    from playmaker_engine import jsbridge as J
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    from playmaker_engine.search import actor
    steps, n, first = [], s, None
    while not isinstance(n, ChanceNode) and n.stage in ('play', 'reaction', 'contest') and actor(n) == 'X':
        r = run_line(J.state_json(n), ctxj, setting, list(named) if first is None else [], top=6)
        if first is None:
            first = r
        a = J.action_from(r['rows'][0]['turn'][0])
        steps.append(dict(action=str(a), turn_it_chose=r['rows'][0]['words'], read=round(r['rows'][0]['value'], 2), listed=r.get('listed')))
        n = apply(n, a)
        if a.kind in ('end_turn', 'pause'):
            break
    return steps, n, first


def cmd_replay():
    """Shaun's game from its log, up to O4's corner three from A3, and what the defence does from the position just
    before O1's pass to O4: under the old default (no control rule, today's list) and the new one (size 2, the open
    list). The computer's defence is followed one action at a time, as it plays."""
    from playmaker_engine import rules_config as RC
    from playmaker_engine import jsbridge as J
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    from playmaker_engine.search import actor
    rep = dict(log=LOG.splitlines(), placed=dict(offence=O_PLACED, defence=X_PLACED),
               facing_at_placement='the log does not give it; every facing leaves every logged line legal (each defender moves, and so sets his facing, before it matters); N is used')
    lines = [ln.split('] ', 1)[1] for ln in LOG.splitlines()]
    out = {}
    for name, setting in (('old default', OLD), ('new default', NEW)):
        rules = RC.with_rules(digital=True, control='0') if setting['control'] == '0' else RC.with_rules(digital=True)
        before, bad = _replay(rules, ['N'] * 5)
        r = dict(replayed_to_the_end=bad is None, failed=bad)
        if bad is None:
            r['logged_result'] = _expected(before[-1])
        s_before = before[lines.index('O1 Pass to O4')]
        r['position_before_the_pass'] = s_before.encode()
        ctxj = J.ctx_json(s_before.ctx)
        s_pass = apply(s_before, next(a for a in legal_actions(s_before) if str(a) == 'O1 Pass to O4'))
        # the pass is in the air: the defence's turn
        steps, n, first = defend(s_pass, ctxj, setting, [dict(name='the log: the defence Pauses', turn=_named(s_pass, ('X Pause',)))])
        r['defence_after_the_pass'] = dict(played=steps, its_list_top=first['rows'], logged_pause=first['named'][0])
        # the offence shoots the three (as in the log), after the computer's own turn and after the logged Pause
        for tag, after in (('after_its_own_turn', n), ('after_the_logged_pause', before[lines.index('O4 Shot (three)')])):
            if isinstance(after, ChanceNode):
                r['three_' + tag] = dict(note='its turn went to the dice')
                continue
            if after.stage == 'play' and actor(after) == 'X':
                end = [a for a in legal_actions(after) if a.kind == 'end_turn']
                after = apply(after, end[0]) if end else after
            sh = next((a for a in legal_actions(after) if str(a) == 'O4 Shot (three)'), None)
            if sh is None:
                r['three_' + tag] = dict(note='the three is not a legal action here', position=after.encode())
                continue
            s_shot = apply(after, sh)
            turns = []
            for nm, acts in (('the log: X2 Move to D8 facing S, X4 Sprint to B4', ('X2 Move to D8 facing S', 'X4 Sprint to B4')),
                             ('X4 Sprints next to him and Contests', ('X4 Sprint to B4', 'X4 contests')),
                             ('no Contest', ('X End turn',))):
                tj = _named(s_shot, acts, soft=True)
                if tj is not None:
                    turns.append(dict(name=nm, turn=tj))
            rsteps, rn, rfirst = defend(s_shot, ctxj, setting, turns)
            r['three_' + tag] = dict(position=after.encode(), reaction_played=rsteps, worth=_expected(rn),
                                     its_list_top=rfirst['rows'], named=rfirst['named'])
        out[name] = r
    rep['settings'] = out
    json.dump(rep, open(os.path.join(RUN, 'replay.json'), 'w'), indent=1)
    for name, r in out.items():
        print('==', name, 'replayed, logged result', r.get('logged_result') if r['replayed_to_the_end'] else r['failed'])
        d = r['defence_after_the_pass']
        print('  defence after the pass plays:', [(x['action'], x['read']) for x in d['played']], '| logged Pause reads', round(d['logged_pause']['value'], 2))
        for tag in ('three_after_its_own_turn', 'three_after_the_logged_pause'):
            x = r[tag]
            if 'reaction_played' in x:
                print('  ', tag, 'reaction:', [(y['action'], y['read']) for y in x['reaction_played']], 'worth', x['worth'])
                print('     named:', [(y['name'], round(y['value'], 2) if y.get('legal') else None) for y in x['named']])
            else:
                print('  ', tag, x)


def _named(s, names, soft=False):
    """A turn from the actions' own words, played in order (soft: None if one isn't legal)."""
    import exam_evidence as EV
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    out, n = [], s
    for nm in names:
        if isinstance(n, ChanceNode):
            return None if soft else out
        a = next((x for x in legal_actions(n) if str(x) == nm), None)
        if a is None:
            if soft:
                return None
            raise ValueError(f'{nm!r} is not legal here')
        out.append(EV.aj(a))
        n = apply(n, a)
    return out


def _after(s, turn_json):
    """The state after a turn given as action JSON (None if it goes to the dice)."""
    from playmaker_engine import jsbridge as J
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    from playmaker_engine.search import actor
    n = s
    side = actor(s)
    for aj in turn_json:
        a = J.action_from(aj)
        if a not in legal_actions(n):
            return None
        n = apply(n, a)
        if isinstance(n, ChanceNode):
            return None
    if n.stage == 'play' and actor(n) == side:           # a one-action turn: the side ends it
        end = [a for a in legal_actions(n) if a.kind == 'end_turn']
        if end:
            n = apply(n, end[0])
    return n if not isinstance(n, ChanceNode) else None


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
