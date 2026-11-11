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


# ---- part 2: the head to head ----------------------------------------------------------------------------------------

def pool():
    return json.load(open(os.path.join(ROOT, 'docs', 'runs', 'step18', 'pools.json')))['senior/pro/digital']


def cmd_h2h(pairs='400', which='defence', tag=None):
    """The All-Star with the open list (a) against the All-Star on the new default (b): paired possessions (the same
    start and dice, sides swapped), in batches of 80, each with its own pick noise, 1 pair ahead. Sequential: it stops
    when the test for a gain of 1 point a pair against none gives its verdict, or at `pairs`."""
    import time
    a = L.policy('allstar', 2, 0.5, open_list=which)
    b = L.policy('allstar', 2, 0.5, open_list=False)
    pl, rows, secs, k, t0 = pool(), [], 0.0, 0, time.time()
    starts = pl['starts']
    tag = tag or f'open_{which}'
    while len(rows) < int(pairs):
        k += 1
        n = min(80, int(pairs) - len(rows))
        part = [starts[(i + 37 * k) % len(starts)] for i in range(n)]
        part = [dict(p, seed=104729 * (i + 1) + 15485863 * k) for i, p in enumerate(part)]
        r, s = L.run_jobs('h2h', part, pl['contexts'], n=1, seed=300 + k, a=a, b=b)
        rows += r
        secs += s
        st = L.h2h_stats(rows, delta=1.0)
        print(tag, len(rows), st['mean_difference'], st['interval'], st['wins'], st['losses'], st['ties'], st['sequential_stop'], round(secs / 3600, 2), flush=True)
        json.dump(dict(tag=tag, stats=st, core_hours=round(secs / 3600, 2), rows=rows), open(os.path.join(WORK, f'h2h_{tag}_partial.json'), 'w'))
        if st['sequential_stop'] and len(rows) >= 160:
            break
    st = L.h2h_stats(rows, delta=1.0)
    rep = dict(tag=tag, a=f'All-Star, search.open_list {which}', b='All-Star, the new default', stats=st, core_hours=round(secs / 3600, 2),
               wall_minutes=round((time.time() - t0) / 60, 1), a_on_offence=L.endings([r['a_end'] for r in rows]),
               b_on_offence=L.endings([r['b_end'] for r in rows]),
               a_shots=shot_timing([r['a_end'] for r in rows]), b_shots=shot_timing([r['b_end'] for r in rows]), rows=rows)
    json.dump(rep, open(os.path.join(RUN, f'h2h_{tag}.json'), 'w'))
    print(json.dumps({k_: v for k_, v in rep.items() if k_ != 'rows'}, indent=1), flush=True)


def shot_timing(e):
    """Shots by phase, the clock-out rate and the ball lost per 100 phases kept, from possession endings
    [kind, clock, offence tokens, decisions] (step 18c's measure). Under the app's rules a possession passes through
    the phases in order, so its ending says which phases it entered."""
    ph = lambda x: min(6, max(1, (12 - x[1]) // 2 + 1))
    shot = lambda x: x[0] in ('shot', 'free_throws', 'forced')
    ran = lambda x: x[0] == 'turnover_end' and x[1] <= 2 and x[2] <= 0
    kept = sum(sum(1 for x in e if ph(x) >= k) - sum(1 for x in e if ph(x) == k and shot(x)) for k in range(1, 7))
    lost = sum(1 for x in e if not shot(x) and not ran(x))
    p, lo, hi = L.wilson(lost, kept)
    shots = [ph(x) for x in e if shot(x)]
    out_ = sum(1 for x in e if ran(x))
    cp, clo, chi = L.wilson(out_, len(e))
    return dict(possessions=len(e),
                shots_by_phase_pct=[round(100 * sum(1 for x in shots if x == k) / max(1, len(shots))) for k in range(1, 7)],
                shots_in_phases_1_and_2_pct=round(100 * sum(1 for x in shots if x <= 2) / max(1, len(shots))),
                decisions=round(sum(x[3] for x in e) / len(e), 1),
                clock_ran_out=out_, clock_interval_in_100=[round(100 * max(0.0, clo), 1), round(100 * chi, 1)],
                lost_in_100_phases_kept=round(100 * p, 1), lost_interval=[round(100 * max(0.0, lo), 1), round(100 * hi, 1)])


# ---- part 2: do the answers fall out? -----------------------------------------------------------------------------

def closeout_board():
    """Step 18d's board: the corner shooter (O4, three 11) has the ball and has used his Move and Quick Step, so he can
    only shoot from where he stands, or pass. His defender (X3, Quick Step 1) is at F4, one square too far to step
    next to him with a Move."""
    from playmaker_engine import exam as EX
    return EX.board(['I11', 'B7', 'P7', 'A3', 'Q3'], ['I10', 'C8', 'F4', 'O7', 'P3'], ['N', 'W', 'W', 'E', 'E'], ball=3, side='X',
                    moved_o=1 << 3, qs_o=1 << 3, cnt=(1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))


def _apply_names(s, names):
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    for nm in names:
        s = apply(s, next(a for a in legal_actions(s) if str(a) == nm))
    return s


def _brief(r):
    return dict(chose=r['rows'][0]['words'], reads=round(r['rows'][0]['value'], 2), listed=r.get('listed'),
                named=[dict(name=x['name'], legal=x['legal'], reads=round(x['value'], 2) if x['legal'] else None,
                            behind_the_choice=round(x['behind_the_choice'], 2) if x['legal'] else None,
                            on_the_list=x.get('list_rank')) for x in r['named']])


def cmd_closeout():
    """Shaun's closeout line (Quick Step closer, Pause, Move into the Contest) on step 18d's board, under the old and
    the new default: at each step what the computer chooses, whether the line's move is on its list and what it
    reads; and what happens when the computer plays the whole thing its own way against the same offence."""
    from playmaker_engine import jsbridge as J
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    rep = {}
    for name, setting in (('old default', OLD), ('new default', NEW)):
        s0 = closeout_board()
        if setting['control'] == '0':
            from dataclasses import replace
            s0 = s0.with_(ctx=_ctx_with(s0.ctx, control='0'))
        ctxj = J.ctx_json(s0.ctx)
        out = {}
        # the line, step by step
        r1 = run_line(J.state_json(s0), ctxj, setting, [
            dict(name='the line: X3 Quick Steps closer, not next to him', turn=_named(s0, ('X3 Quick Step to E4',))),
            dict(name='X3 Sprints next to him now', turn=_named(s0, ('X3 Sprint to B4',))),
            dict(name='X3 Moves closer now', turn=_named(s0, ('X3 Move to C4 facing W',))),
            dict(name='does nothing', turn=_named(s0, ('X Pause',)))], top=6)
        out['1. the ball is in the corner; the defence acts'] = _brief(r1)
        s1 = _apply_names(s0, ('X3 Quick Step to E4', 'X End turn', 'O2 Move to B8', 'O End turn'))
        r2 = run_line(J.state_json(s1), ctxj, setting, [
            dict(name='the line: the defence Pauses', turn=_named(s1, ('X Pause',))),
            dict(name='X3 Moves next to him now', turn=_named(s1, ('X3 Move to B4 facing SW',)))], top=6)
        out['2. X3 a Quick Step closer, the offence has moved an off-ball player; the defence acts'] = _brief(r2)
        s2 = _apply_names(s1, ('X Pause', 'O4 Shot (three)'))
        turns = []
        for nm, acts in (('the line: X3 Moves next to him and Contests', ('X3 Move to B4 facing SW', 'X3 contests')),
                         ('no Contest', ('X End turn',))):
            tj = _named(s2, acts, soft=True)
            if tj is not None:
                turns.append(dict(name=nm, turn=tj))
        rsteps, rn, rfirst = defend(s2, ctxj, setting, turns)
        out['3. the three goes up after the Pause; the reaction'] = dict(played=[x['action'] for x in rsteps], worth=_expected(rn), **_brief(rfirst))
        # its own way, against the same offence (an off-ball Move, then the three)
        own = []
        st, n, _ = defend(s0, ctxj, setting)
        own.append(dict(defence=[x['action'] for x in st]))
        for step in (1, 2):
            if isinstance(n, ChanceNode):
                own.append(dict(note='its action went to the dice (a Steal or an Intercept); the line stops here'))
                break
            n = _own_end(n)
            if step == 1:
                mv = next((a for a in legal_actions(n) if str(a) == 'O2 Move to B8'), None)
                if mv is None:
                    own.append(dict(note='the offence cannot make the same off-ball Move here'))
                    break
                n = _apply_names(n, ('O2 Move to B8', 'O End turn'))
                st, n, _ = defend(n, ctxj, setting)
                own.append(dict(defence=[x['action'] for x in st]))
            else:
                sh = next((a for a in legal_actions(n) if str(a) == 'O4 Shot (three)'), None)
                if sh is not None:
                    st, n, _ = defend(apply(n, sh), ctxj, setting)
                    own.append(dict(reaction=[x['action'] for x in st], the_three_is_worth=_expected(n)))
        out['its own way, against the same offence'] = own
        rep[name] = out
    json.dump(rep, open(os.path.join(RUN, 'closeout_line.json'), 'w'), indent=1)
    print(json.dumps(rep, indent=1))


def _own_end(n):
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply, ChanceNode
    from playmaker_engine.search import actor
    if not isinstance(n, ChanceNode) and n.stage == 'play' and actor(n) == 'X':
        end = [a for a in legal_actions(n) if a.kind == 'end_turn']
        if end:
            n = apply(n, end[0])
    return n


def _ctx_with(ctx, **rule_changes):
    """A copy of a context with some rule settings changed."""
    import copy
    from dataclasses import replace
    c = copy.copy(ctx)
    c.rules = replace(ctx.rules, **rule_changes)
    return c


# ---- the sense check: two moves played out by the rules ----------------------------------------------------------

def sense(tag, state_json, ctx_json, turns, n=160, setting=NEW):
    """From a position, each named turn played out n times by the rules with common dice (both sides the All-Star on
    the setting, each with its pick noise): what the offence went on to score after each, with a 95% interval, and
    each turn against the first, paired. Evidence from play, separate from the reading that made the choice."""
    pol = L.policy('allstar', 2, 0.5, open_list=setting['open_list'])
    per = max(1, int(n) // L.CORES)
    pos = [dict(id=f'{tag}/{k}', state=state_json, ctx=0, seed=7919 * (k + 1), turns=[t for _, t in turns]) for k in range(L.CORES)]
    job = dict(n=per, seed=7, keep=True, policies=dict(O=pol, X=pol))
    if setting['control'] is not None:
        job['control'] = setting['control']
    rows, secs = L.run_jobs('rollout', pos, [ctx_json], **job)
    out, base = [], None
    for m, (name, _) in enumerate(turns):
        v = [x for r in rows for x in r['turns'][m]['values']]
        if base is None:
            base = v
        mean, sd, ci = L.mean_ci(v)
        d = [a - b for a, b in zip(v, base)]
        dm, dsd, dci = L.mean_ci(d) if m else (0.0, 0.0, 0.0)
        out.append(dict(move=name, playouts=len(v), offence_scores=round(mean, 2), interval=[round(mean - ci, 2), round(mean + ci, 2)],
                        against_the_first=round(dm, 2), difference_interval=[round(dm - dci, 2), round(dm + dci, 2)]))
    return dict(moves=out, core_hours=round(secs / 3600, 3))


def cmd_sense(which='closeout1,closeout2,replay,defence242,defence377', n='160'):
    """The sense checks: where the computer on the new default prefers something other than the expected move, both
    played out by the rules from the position, with common dice."""
    from playmaker_engine import jsbridge as J
    from playmaker_engine import rules_config as RC
    from playmaker_engine.actions import legal_actions
    from playmaker_engine.resolve import apply
    path = os.path.join(RUN, 'sense_checks.json')
    rep = json.load(open(path)) if os.path.exists(path) else {}
    for name in which.split(','):
        if name == 'closeout1':
            s = closeout_board()
            turns = [("the computer's: X3 Moves closer (C4), facing the shooter", _named(s, ('X3 Move to C4 facing SW',))),
                     ("Shaun's line: X3 Quick Steps closer (E4)", _named(s, ('X3 Quick Step to E4',))),
                     ('X3 Sprints next to him at once', _named(s, ('X3 Sprint to B4',))),
                     ('the defence does nothing', _named(s, ('X Pause',)))]
            sj, cj, enc = J.state_json(s), J.ctx_json(s.ctx), s.encode()
        elif name == 'closeout2':
            s = _apply_names(closeout_board(), ('X3 Quick Step to E4', 'X End turn', 'O2 Move to B8', 'O End turn'))
            turns = [("the computer's: X3 Moves next to him, then Steals", _named(s, ('X3 Move to B4 facing SW', 'X3 Steal'))),
                     ('X3 Moves next to him and stops', _named(s, ('X3 Move to B4 facing SW', 'X End turn'))),
                     ("Shaun's line: the defence Pauses", _named(s, ('X Pause',)))]
            sj, cj, enc = J.state_json(s), J.ctx_json(s.ctx), s.encode()
        elif name == 'replay':
            before, _ = _replay(RC.with_rules(digital=True), ['N'] * 5)
            lines = [ln.split('] ', 1)[1] for ln in LOG.splitlines()]
            sb = before[lines.index('O1 Pass to O4')]
            s = apply(sb, next(a for a in legal_actions(sb) if str(a) == 'O1 Pass to O4'))
            own = json.load(open(os.path.join(RUN, 'replay.json')))['settings']['new default']['defence_after_the_pass']['played'][0]['action']
            turns = [(f"the computer's: {own}", _named(s, (own,))),
                     ('X4 Quick Steps closer to the corner (E4)', _named(s, ('X4 Quick Step to E4',))),
                     ('the log: the defence Pauses', _named(s, ('X Pause',)))]
            sj, cj, enc = J.state_json(s), J.ctx_json(s.ctx), s.encode()
        else:
            job = json.load(open(os.path.join(WORK, f'regret_open_defence_{name}.job.json')))
            o = json.load(open(os.path.join(WORK, f'regret_open_defence_{name}.out.json')))
            on = [r for r in o['rows'] if r['stage'] == 4]
            choice = min(on, key=lambda r: r['pair'])
            steals = [r for r in o['rows'] if 'Steal' in r['words']]
            best_steal = min(steals, key=lambda r: r['pair'])
            pause = next((r for r in o['rows'] if r['words'] == 'X Pause'), None)
            turns = [(f"the computer's: {choice['words']}", choice['turn']), (f"the expected: {best_steal['words']}", best_steal['turn'])]
            if pause and pause['words'] != choice['words']:
                turns.append(('the defence Pauses', pause['turn']))
            sj, cj, enc = job['state'], job['ctx'], None
        r = sense(name, sj, cj, turns, n=int(n))
        r['position'] = enc or dict(o=sj['o'], x=sj['x'], arrows=sj.get('arrows'), ball=sj['ball'], clock=sj['clock'])
        rep[name] = r
        print(name, json.dumps(r, indent=1), flush=True)
        json.dump(rep, open(path, 'w'), indent=1)


# ---- speed, and part 5 ------------------------------------------------------------------------------------------------

def _p90(v):
    v = sorted(v)
    return round(v[int(0.9 * (len(v) - 1) + 0.5)], 3) if v else None


def cmd_speed(which='defence', runs='2'):
    """The time to finish 1 pair at each level on the hand boards' 22 decisions (one warm engine each), the new default
    beside the open list, against docs/SPEED_BUDGET.md. The two are timed in the same run, in turn."""
    positions, contexts = L.hand_boards()
    target = dict(rookie=(0.3, 1.0), starter=(1.0, 2.0), allstar=(2.5, 3.0))
    rep = []
    for run in range(int(runs)):
        one = {}
        for name, ol in (('new default', False), ('open list', which)):
            pols = {lv: L.policy(lv, 2, 0.0, open_list=ol) for lv in target}
            L.run_jobs('search', positions[:6], contexts, chunks=1, policies=pols)
            rows, _ = L.run_jobs('search', positions + positions, contexts, chunks=1, policies=pols)
            rows = rows[len(positions):]
            one[name] = {}
            for lv in target:
                v = sorted(r['by'][lv]['seconds'] for r in rows)
                p90 = v[int(0.9 * (len(v) - 1) + 0.5)]
                one[name][lv] = dict(median=round(v[len(v) // 2], 3), nine_in_ten=round(p90, 3), slowest=round(v[-1], 3),
                                     desktop_target=target[lv][0], fits_desktop=p90 <= target[lv][0],
                                     phone=round(4 * p90, 2), phone_target=target[lv][1],
                                     nine_in_ten_by_side={side: _p90([r['by'][lv]['seconds'] for r in rows if r.get('side') == side]) for side in ('O', 'X')})
            print(run + 1, name, {lv: (x['median'], x['nine_in_ten']) for lv, x in one[name].items()}, flush=True)
        rep.append(one)
    json.dump(dict(note="seconds to finish 1 pair on the hand boards' 22 decisions; median and 9 decisions in 10", runs=rep),
              open(os.path.join(RUN, f'speed_{which}.json'), 'w'), indent=1)


BOARD_TURNS = {
    # board: [(name, the turn in the actions' own words)] (step 18d's)
    '1': [('does nothing', ['X Pause']), ("step 18a's choice", ['X2 Move to D6 facing E'])],
    '3': [('does nothing', ['X Pause']),
          ("the board's help: the low man steps up, another covers", ['X4 Move to I4 facing N', 'X2 Quick Step to D6']),
          ("the board's help, both with a Move", ['X2 Move to E5 facing SE', 'X4 Move to I4 facing N'])],
    '6': [("the board's move: O4 shoots the open three", ['O4 Shot (three)'])],
    '8': [("the board's move: the backdoor cut and the pass", ['O2 Move to D7', 'O1 Pass to O2']),
          ('the cut alone', ['O2 Move to F7'])],
    '9': [("the board's move: the kick-out to the corner", ['O1 Pass to O5']),
          ('the corner man relocates', ['O5 Move to Q4'])],
}


def cmd_boards(names='1,3,6,8,9'):
    """Boards 1, 3, 6, 8 and 9 move by move, under the old and the new default: what the search chooses 1 pair ahead
    (no pick noise), and what each board move reads when it is searched."""
    from playmaker_engine import exam as EX, jsbridge as J
    rep = {}
    for n in names.split(','):
        rep[n] = {}
        for name, setting in (('old default', OLD), ('new default', NEW)):
            _, s, _ = EX.POSITIONS[int(n) - 1]()
            if setting['control'] == '0':
                s = s.with_(ctx=_ctx_with(s.ctx, control='0'))
            turns = [dict(name=nm, turn=tj) for nm, tj in ((nm, _named(s, acts, soft=True)) for nm, acts in BOARD_TURNS[n]) if tj is not None]
            r = run_line(J.state_json(s), J.ctx_json(s.ctx), setting, turns, top=4)
            for x in r['named']:
                x.pop('after', None)
            for x in r['rows']:
                x.pop('turn', None)
            rep[n][name] = dict(side=r['side'], choice=r['rows'][0], top=r['rows'], named=r['named'], listed=r.get('listed'))
            print('board', n, name, '| choice:', r['rows'][0]['words'], round(r['rows'][0]['value'], 2))
            for x in r['named']:
                if x['legal']:
                    print('      ', x['name'], '|', round(x['value'], 2), 'behind the choice', round(x['behind_the_choice'], 2), 'list', x['list_rank'])
    json.dump(rep, open(os.path.join(RUN, 'boards.json'), 'w'), indent=1)


if __name__ == '__main__':
    globals()['cmd_' + sys.argv[1]](*sys.argv[2:])
