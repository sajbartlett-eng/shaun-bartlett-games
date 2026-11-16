"""Step 3m: the computer player on the new decision engine (replaces steps 3e to 3k for decisions).

One agent for every level; the levels differ only by ai_profiles.json (B8): search depth and beam, the opponent model,
evaluation noise, attention (the threats and defenders read: those nearest the ball), reaction delay (Rookie reads
the board as it was before the opponent's last turn), the goal-switch margin, the variety margin, the time budget and
(All-Star) scouting the human from stored games. Age stays in the ratings.

Each turn: an anytime search (search.Searcher) scores whole turns; noise is added at the root; goals (goals.py) are
read from the scored turns and held with hysteresis; a turn toward the held goal is chosen, then one at random among
the turns within the variety margin. The turn's actions are played one at a time (a roll ends the plan).
"""
import json
import random
import time

from . import board as B
from . import jsbridge
from . import rules_config as RC
from .actions import Action, legal_actions
from .decide import Read, CONFIG
from .goals import Commitment, goals_in, _likeliest
from .resolve import apply, ChanceNode
from .search import Searcher, play_turn, actor, zobrist, terminal_value

LEVELS = ('rookie', 'starter', 'allstar')
SCALE = {'value': 1.0}           # tests shrink the time budgets; the browser build can scale them
# step 3n Part A: the search core in JavaScript (playmaker_web/static/engine.js). The browser worker sets JS['search'] to
# PMEngine.searchJSON (JSON text in and out); tests may set it to a Node-backed call. None: the Python search.
JS = {'search': None, 'goals': None, 'reads': None, 'coverage': None}      # step 18o: 'reads', the quick reading of setup placements (readsJSON)
# step 3n Part B: the exam's fixed-depth run (the design verdict): every level searches exactly this depth, no time limit
FIXED = {'depth': None}


def profile(level):
    level = {'greedy': 'starter', 'reader': 'starter'}.get(level, level)
    return dict(CONFIG['profiles'][level], name=level)


def attention_sets(s, n):
    """The n attackers and n defenders nearest the ball (all five when n >= 5)."""
    if n >= 5:
        return None
    bp = s.o[s.ball]
    o = sorted(range(5), key=lambda i: (B.cheb(s.o[i], bp), i))[:n]
    if s.ball not in o:
        o = [s.ball] + o[:n - 1]
    x = sorted(range(5), key=lambda j: (B.cheb(s.x[j], bp), j))[:n]
    return (o, x)


class Agent:
    """The computer for one side (O or X), at one level."""
    name = 'computer'

    def __init__(self, side, level='starter', seed=0, scouting=None):
        self.side = side
        self.level = {'greedy': 'starter', 'reader': 'starter'}.get(level, level)
        if self.level not in LEVELS:
            raise ValueError('computer level: rookie, starter or allstar')
        self.p = profile(self.level)
        self.rng = random.Random(seed * 7919 + (1 if side == 'O' else 2))
        self.commit = Commitment(self.p['goal_margin_m0'])
        self.notes = []
        self.plan = []
        self.expect = None
        self.stale = None              # the opponent's pieces at this side's previous decision (reaction delay)
        self.scouting = scouting if self.p['scout_human'] else None
        self.last = None
        self.setup_perm = None

    def reset(self, seed):
        pass

    def describe(self):
        return dict(level=self.level, engine='step 3m decision engine', profile={k: v for k, v in self.p.items()
                                                                                if k != 'name'},
                    scouting=self.scouting_words())

    def scouting_words(self):
        sc = self.scouting
        if not sc or not sc.get('games'):
            return None
        bits = [f"read {sc['games']} of your completed games"]
        if sc.get('early_shot') is not None:
            bits.append(f"you shot in the first two phases {round(100 * sc['early_shot'])}% of the time")
        if sc.get('pass_risk') is not None:
            bits.append(f"your passes risked an interception {round(100 * sc['pass_risk'])}% of the time")
        if sc.get('drive') is not None:
            bits.append(f"you drove on {round(100 * sc['drive'])}% of your turns with the ball")
        if sc.get('help') is not None:
            bits.append(f"on defence you left your man to help {round(100 * sc['help'])}% of the time")
        return 'All-Star ' + '; '.join(bits) + '.'

    # -- the evaluation this profile sees
    def _evaluate(self, s0):
        att_n = self.p['attention']
        delay = self.p['reaction_delay']
        stale = self.stale

        def ev(node):
            if isinstance(node, ChanceNode):
                return sum(float(p) * ev(sub) for p, _, sub in node.outcomes)
            if node.stage == 'over':
                return terminal_value(node)
            s = node
            if delay == 'previous_board' and stale is not None:
                s = _with_stale(s, self.side, stale)
            att = attention_sets(s, att_n)
            return Read(s, attention=att, k=2 if att_n < 5 else None).leaf()
        return ev

    def choose(self, s):
        side = actor(s)
        # a planned second action, if the position is the one the plan expected
        if self.plan and self.expect == zobrist(s):
            a = self.plan.pop(0)
            if a in legal_actions(s):
                self.expect = None
                if self.plan:
                    nxt = apply(s, a)
                    self.expect = zobrist(nxt) if not isinstance(nxt, ChanceNode) else None
                    if self.expect is None:
                        self.plan = []
                return a
        self.plan, self.expect = [], None
        acts = legal_actions(s)
        if len(acts) == 1:
            return acts[0]
        if s.stage in ('contest', 'forced', 'target', 'pick'):
            return self._small(s, acts)
        t0 = time.time()
        budget = self.p['time_budget_s'] * SCALE['value']
        lo, hi = self.p['depth']
        if FIXED['depth']:
            lo = hi = FIXED['depth']
            budget = None
            if FIXED.get('deadline') is not None:      # step 12: a tool's cap on a fixed look-ahead (the deepest that finishes)
                budget = max(5.0, FIXED['deadline'] - time.time())
        if JS['search'] is not None and jsbridge.ported(s.ctx.rules):
            results, reached, srch = self._js_search(s, budget, hi)
        else:
            srch = Searcher(side, self.p, self._evaluate(s), t0 + budget if budget is not None else float('inf'), self.rng)
            if self.scouting and self.scouting.get('habit'):
                srch.habit = self.scouting['habit']
                srch.habit_weight = self.scouting.get('weight', 0.3)
            results, reached = srch.root(s, hi, lo)
        sign = 1 if side == 'O' else -1
        if CONFIG.get('search', {}).get('split_ties') is True:
            # step 18f (search.split_ties): turns that read exactly the same get one draw of the pick noise, so the
            # evidence that put them in order chooses between them, not chance
            scored, prev, nz = [], None, 0.0
            for v, t in results:
                if prev is None or abs(v - prev) >= 1e-9:
                    nz = self.rng.gauss(0, self.p['noise'])
                prev = v
                scored.append((sign * v + nz, t, sign * v))
        else:
            scored = [(sign * v + self.rng.gauss(0, self.p['noise']), t, sign * v) for v, t in results]
        top8 = sorted(scored, key=lambda r: -r[0])[:8]
        with_goals = []
        if getattr(srch, 'engine', None) == 'js' and JS.get('goals') is not None:
            # the goals of the turns weighed, read by the JavaScript core (the same predicates, goals.goals_in)
            req = dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), side=side,
                       turns=[[[a.kind, a.side, a.piece, B.sq(a.dest) if a.dest else None, a.arrow, a.target, a.shot]
                               for a in t] for _, t, _ in top8])
            g = json.loads(JS['goals'](json.dumps(_lane_req(req))))
            base = sign * g['base']
            for (v, t, raw), gl in zip(top8, g['goals']):
                with_goals.append((v, t, {tuple(k): w for k, w in gl}))
        else:
            base_read = Read(s)
            base = sign * base_read.leaf()
            for v, t, raw in top8:
                after = _likeliest(play_turn(s, t))
                gs = goals_in(s, after, side, base_read, None if after.stage == 'over' else Read(after), t) \
                    if after.stage != 'over' else {}
                with_goals.append((v, t, gs))
        n_log = len(self.commit.log)
        turn, val = self.commit.choose(s, side, with_goals, base, None)
        # variety: one at random among the turns within the variety margin of the chosen one
        near = [t for v, t, _ in with_goals if v >= val - self.p['variety_margin']]
        if CONFIG.get('search', {}).get('split_ties') is True:
            # variety is between turns that read differently: of those that read the same, the first only
            seen, near = set(), []
            for v, t, _ in with_goals:
                if v >= val - self.p['variety_margin'] and round(v, 9) not in seen:
                    seen.add(round(v, 9))
                    near.append(t)
        if self.p['variety_margin'] > 0 and len(near) > 1:
            turn = self.rng.choice(near)
        took = round(time.time() - t0, 3)
        stable = dict(extensions=getattr(srch, 'extensions', 0), cap_hits=getattr(srch, 'cap_hits', 0),
                      kept=getattr(srch, 'kept', 0)) if getattr(srch, 'stable', False) else None
        trace = [[d, [str(a) for a in t], round(v, 2)] for d, t, v in getattr(srch, 'trace', [])]
        note = dict(event='decision', level=self.level, depth=reached, partial=getattr(srch, 'partial', 0), stable=stable,
                    trace=trace, depth_seconds=[list(x) for x in getattr(srch, 'depth_seconds', [])],
                    engine=getattr(srch, 'engine', 'python'), pv=getattr(srch, 'pv', None),
                    leaves=srch.leaves, nodes=srch.nodes,
                    seconds=took, value=round(val, 2), turn=[str(a) for a in turn],
                    goal=self.commit.words or None,
                    alternatives=[dict(turn=[str(a) for a in t], value=round(v, 2)) for v, t, _ in with_goals[:3]])
        if CONFIG['eval'].get('learned') is True:
            note['why'] = self._why(s, turn, with_goals, val)   # step 17: the reasons, in the readings' own words
        if CONFIG['eval'].get('advantages') is True and side in ('O', 'X'):
            note['goals'] = self._goal_note(s, turn)          # step 16: reading and recording only
        for g in self.commit.log[n_log:]:
            self.notes.append(dict(event='goal', **g))
        why = steal_reason(s, turn)
        if why:
            note['reason'] = why
        self.notes.append(note)
        self.last = note
        self.stale = (s.x, s.arrows) if self.side == 'O' else (s.o,)
        a = turn[0]
        if len(turn) > 1:
            nxt = apply(s, a)
            if not isinstance(nxt, ChanceNode) and nxt.stage != 'over':
                self.plan = list(turn[1:])
                self.expect = zobrist(nxt)
        return a

    def _why(self, s, turn, weighed, val):
        """Step 17 (reporting only): why this turn and not the runner-up. The three readings whose weighted parts
        differ most between the positions the two turns lead to (the likeliest outcome of each), in points, in the
        readings' own words. close_call: the gap between the two turns is inside what the weights' spread allows.
        unsure: a reading whose weight changes sign across the 20 resampled fits."""
        from .decide import FEATURES, learned_weights
        from .search import phase_of
        w = learned_weights()
        others = [(v, t) for v, t, _ in weighed if t != turn]
        if w is None or not others:
            return None
        v2, runner = max(others, key=lambda r: r[0])

        def parts(t):
            after = _likeliest(play_turn(s, t))
            if after.stage != 'play' or after.pending:
                return None
            m = w['phases'].get(phase_of(after))
            if m is None:
                return None
            f = Read(after).features()
            z = [(f[i] - m['mean'][i]) / m['sd'][i] for i in range(len(f))]
            return [m['weights'][i] * z[i] for i in range(len(f))], z, m
        a, b = parts(turn), parts(runner)
        out = dict(chosen=[str(x) for x in turn], runner_up=[str(x) for x in runner], gap=round(val - v2, 2))
        if a is None or b is None:
            out['reasons'] = ['one of the two turns ends the possession or leaves a pass in the air: its value is the dice\'s']
            return out
        diff = [a[0][i] - b[0][i] for i in range(len(FEATURES))]
        spread = sum((a[2]['weights_spread'][i] * (a[1][i] - b[1][i])) ** 2 for i in range(len(FEATURES))) ** 0.5
        top = sorted(range(len(FEATURES)), key=lambda i: -abs(diff[i]))[:3]
        sign = 1 if self.side == 'O' else -1
        out['reasons'] = [f"{FEATURES[i][1]}: {'+' if sign * diff[i] >= 0 else '-'}{abs(diff[i]):.1f} for this turn"
                          for i in top if abs(diff[i]) > 0.05]
        out['close_call'] = abs(val - v2) < 1.96 * spread
        out['unsure'] = [FEATURES[i][0] for i in top if abs(a[2]['weights'][i]) < 1.96 * a[2]['weights_spread'][i]]
        return out

    def _goal_note(self, s, turn):
        """Step 16 (for the trainer later): the top goals on the board, their stages, the goal the computer is on (it
        changes only when another beats it by more than the reading's margin of error), the event (ready, lost,
        switched, clock), the defence's mirror answer to each, and which looks the chosen turn raised or lowered."""
        from .search import phase_of
        r0 = Read(s)
        adv = sorted(r0.advantages(), key=lambda a: (-a['worth'], a['i']))
        keys = {(a['kind'], a['i']): a for a in adv}
        margin = float(CONFIG.get('search', {}).get('stable_margin', {}).get(phase_of(s), 0.0))
        best = adv[0] if adv and adv[0]['worth'] > 1e-9 else None
        cur, event = getattr(self, 'goal', None), None
        if cur is not None and (cur not in keys or keys[cur]['worth'] <= 1e-9):
            cur, event = None, 'lost'
        if cur is None:
            cur = (best['kind'], best['i']) if best else None
        elif best and (best['kind'], best['i']) != cur and best['worth'] > keys[cur]['worth'] + margin:
            cur, event = (best['kind'], best['i']), 'switched'
        if cur is not None and keys[cur]['stage'] == 'convert':
            event = event or 'ready'
        if s.clock <= RC.PHASE_SECONDS:
            event = 'clock'
        self.goal = cur
        answer = {'create': 'prevent', 'keep': 'break', 'convert': 'deny'}
        goals = [dict(kind=a['kind'], attacker=f"O{a['i'] + 1}", defender=f"X{a['j'] + 1}" if a['j'] >= 0 else None,
                      square=B.sq(a['sq']) if a['sq'] else None, stage=a['stage'], value=round(a['value'], 1),
                      chance=round(a['chance'], 2), worth=round(a['worth'], 1), gap=a['gap'],
                      defence='run down' if s.clock <= RC.PHASE_SECONDS else answer[a['stage']] if a['worth'] > 1e-9
                      else 'concede') for a in adv[:6]]
        changed = {}
        after = _likeliest(play_turn(s, turn))
        if after.stage == 'play' and not after.pending:
            r1 = Read(after)
            for i in range(5):
                d = r1.threat[i]['value'] - r0.threat[i]['value']
                if abs(d) > 0.05:
                    changed[f'O{i + 1}'] = round(d, 1)
        return dict(goals=goals, current=f'{cur[0]} O{cur[1] + 1}' if cur else None, event=event, potential=round(r0.phi(), 2),
                    target=B.sq(keys[cur]['sq']) if cur and keys[cur]['sq'] else None,
                    looks_changed=changed)

    def _js_search(self, s, budget, max_depth):
        """The same search in JavaScript (engine.js, proved equal to search.Searcher by tools/js_equivalence.py)."""
        sq = B.sq
        stale = None
        if self.stale is not None and self.p['reaction_delay'] == 'previous_board':
            stale = [[sq(q) for q in self.stale[0]], list(self.stale[1])] if self.side == 'O' else [[sq(q) for q in self.stale[0]]]
        req = dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), profile=self.p, budget=budget,
                   max_depth=max_depth, stale=stale)
        if self.scouting and self.scouting.get('habit'):
            req['habit'] = self.scouting['habit']
            req['habit_weight'] = self.scouting.get('weight', 0.3)
        out = json.loads(JS['search'](json.dumps(_lane_req(req))))
        results = [(v, tuple(jsbridge.action_from(a) for a in t)) for v, t in out['results']]

        class _Stats:
            pass
        st = _Stats()
        st.leaves, st.nodes, st.partial, st.pv = out['leaves'], out['nodes'], out['partial'], out.get('pv')
        st.engine = 'js'
        st.stable = out.get('stable', False)
        st.extensions, st.cap_hits, st.kept = out.get('extensions', 0), out.get('cap_hits', 0), out.get('kept', 0)
        st.trace = [(d, tuple(jsbridge.action_from(a) for a in t), v) for d, t, v in out.get('trace', [])]
        st.depth_seconds = [(d, round(x, 3)) for d, x in out.get('depth_seconds', [])]
        return results, out['reached'], st

    def _small(self, s, acts):
        """Contest choice, forced shot type, Coach's Call target, failed-inbound pick: one step, valued exactly."""
        side = actor(s)
        ev = self._evaluate(s)

        def val(a):
            n = apply(s, a)
            return ev(n)
        best = max(acts, key=val) if side == 'O' else min(acts, key=val)
        return best


def steal_reason(s, turn):
    """Step 3n F4: why the defence reached for a steal or didn't, in plain words, when the bonus line matters."""
    if actor(s) != 'X' or not s.ctx.rules.digital or s.stage != 'play':
        return None
    if not any(a.kind == 'steal' for a in legal_actions(s)):
        return None
    f, b = s.ctx.team_fouls + s.fouls, s.ctx.rules.bonus_from
    reached = any(a.kind == 'steal' for a in turn)
    if reached:
        return (f'Reached for the steal: {f} team foul{"s" if f != 1 else ""}, so a foul costs 5 points and play goes on.'
                if f + 1 < b else f'Reached for the steal even though a foul now gives free throws.')
    if f + 1 >= b:
        return (f'Didn\'t reach for the steal: a foul now would be their {f + 1}th team foul, and from the {b}th a steal '
                f'foul gives free throws.')
    return None


def _with_stale(s, side, stale):
    """The board as this side saw it before the opponent's last turn (Rookie's reaction delay): the opponent's pieces
    where they stood then, if those squares are free now."""
    if side == 'O':
        xs, arrows = stale
        if set(xs) & set(s.o):
            return s
        return s.with_(x=xs, arrows=arrows)
    (os_,) = stale
    if set(os_) & set(s.x):
        return s
    return s.with_(o=os_)


# ---- setup (B6; rebuilt in step 18o, D-195) ---------------------------------------------------------------------------
#
# The setup must fit the players (Shaun, 15 Nov 2026). Before step 18o both sides were improved from a fixed start (the
# table's squares; each defender next to his man) by the quick reading, with two arrow directions tried, and were never
# judged by play. Now:
#   - nothing is a starting answer: a search starts from a placement drawn at random;
#   - every placement is treated alike: a change moves one player, drawn at random, to any empty square of the court
#     or to a square next to his own, and gives a defender any of the eight arrows;
#   - the quick reading shortlists (speed needs it): a change is kept when the reading's own parts say it is better
#     for the side placing: the position's value first, then the best look the defence's cover leaves, then the next;
#   - the shortlist is judged by play: each search's placement is read by the search itself, with the level's own
#     settings, the offence's turn played out and its shot settled; the best by that reading is taken.
# Setup has a fraction of a decision's time (game._setup_budget), which holds a few hundred quick readings and a
# handful of played-out ones. So the searches of a game are carried on from possession to possession (memory): each
# setup starts from where that side's own search stood, never from a set placement.
#
# It is behind a switch, off (ai_profiles.json setup.search): played out on Shaun's board, the placements it finds
# give up more than the old setup's (docs/reports/STEP18O_REPORT.md). The readings can't tell a good setup from a
# bad one at the start of a possession; only play can, and play doesn't fit in the setup's time.
SETUP = dict(chains=3, batch=6, quick_share=0.55)   # how many searches side by side, changes read at a time, the quick reading's share of the time


def _legal_o(sq, ball):
    return (len(set(sq)) == 5 and all(B.on_board(q) for q in sq) and B.zone(sq[ball]) == '.' and sq[ball][1] > 1)


def _court():
    return [(x, y) for x in range(B.W) for y in range(1, B.H + 1)]


def _read_key(s):
    """The quick reading's own parts, the offence's view: the position's value, then each attacker's best look after
    the defence's best cover, largest first (decide.Read.leaf and .cover)."""
    r = Read(s)
    res = r.cover()['residual']
    return tuple([r.leaf()] + sorted((float(res.get(i, 0.0)) for i in range(5)), reverse=True))


def _reads(make, items):
    """[(o_sq, ball, xs, arrows)] -> the reading's parts of each (None for a placement that isn't legal). One call to
    the JavaScript engine when it is there (engine.js readsJSON: the same Read)."""
    ok = [(_legal_o(list(o), b) and len(set(xs) | set(o)) == 10 and all(B.on_board(q) for q in xs)) for o, b, xs, ar in items]
    out = [None] * len(items)
    live = [k for k, v in enumerate(ok) if v]
    if not live:
        return out
    if JS.get('reads') is not None:
        o, b, xs, ar = items[live[0]]
        s0 = make(o, b, xs, ar)
        if jsbridge.ported(s0.ctx.rules):
            req = dict(state=jsbridge.state_json(s0), ctx=jsbridge.ctx_json(s0.ctx),
                       items=[dict(o=[B.sq(q) for q in items[k][0]], ball=items[k][1], x=[B.sq(q) for q in items[k][2]],
                                   arrows=list(items[k][3])) for k in live])
            for k, key in zip(live, json.loads(JS['reads'](json.dumps(_lane_req(req))))):
                out[k] = tuple(key)
            return out
    for k in live:
        o, b, xs, ar = items[k]
        out[k] = _read_key(make(o, b, xs, ar))
    return out


def _better(a, b, sign):
    """Is reading a better than b for the side placing (sign +1 the offence, -1 the defence), part by part?"""
    for u, v in zip(a, b):
        if sign * (u - v) > 1e-9:
            return True
        if sign * (u - v) < -1e-9:
            return False
    return False


def coverage(s, answers=None):
    """Step 18s (D-199): the coverage map of a position, from the fast engine (engine.js coverage), or None where that
    engine isn't there or doesn't play these rules. Value, reach, influence and weakness for every attacker and square,
    who covers what, the defence's best answers within its tokens, and one line of words. Read by nothing in the
    computer's play yet: it is shown to the coach and checked (stop one)."""
    if JS.get('coverage') is None or not jsbridge.ported(s.ctx.rules) or s.stage != 'play':
        return None
    req = dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx))
    if answers is not None:
        req['options'] = dict(answers=answers)
    return json.loads(JS['coverage'](json.dumps(req)))


_LANE_FILE = CONFIG.get('eval', {}).get('lane') is True      # eval.lane as ai_profiles.json has it


def set_lane(on):
    """Step 18q: eval.lane for this process: on, or back to the file's own setting. The JavaScript search follows it
    request by request (_lane_req)."""
    CONFIG['eval']['lane'] = bool(on) or _LANE_FILE
    return CONFIG['eval']['lane']


def _lane_req(req):
    req['lane'] = CONFIG['eval'].get('lane') is True
    return req


def _played(make, o_sq, ball, xs, arrows, level, t_end, depth=1):
    """The search's own played-out reading of a placement (the offence to act): the level's search, the offence's
    turn played out and its shot settled, `depth` turns ahead. None if it could not finish."""
    s = make(o_sq, ball, xs, arrows)
    p = dict(profile(level), noise=0.0, depth=[depth, depth])
    budget = max(0.02, t_end - time.time())
    try:
        if JS['search'] is not None and jsbridge.ported(s.ctx.rules):
            req = dict(state=jsbridge.state_json(s), ctx=jsbridge.ctx_json(s.ctx), profile=p, budget=budget, max_depth=depth, stale=None)
            out = json.loads(JS['search'](json.dumps(_lane_req(req))))
            if out['reached'] < depth or not out['results']:
                return None
            return max(v for v, _ in out['results'])
        ag = Agent('O', level)
        srch = Searcher('O', p, ag._evaluate(s), time.time() + budget, random.Random(0))
        results, reached = srch.root(s, depth, depth)
        if reached < depth or not results:
            return None
        return max(v for v, _ in results)
    except Exception:
        return None


def _random_x(o_sq, rng):
    free = [q for q in _court() if q not in set(o_sq)]
    return rng.sample(free, 5), [rng.randrange(8) for _ in range(5)]


def _random_o(rng):
    court = _court()
    ball = rng.choice([q for q in court if B.zone(q) == '.' and q[1] > 1])
    return [ball] + rng.sample([q for q in court if q != ball], 4)


def _change(sq, taken, rng):
    """One player's new square, drawn alike from two kinds of change: any empty square of the court, or a square next
    to his own (or his own). None if the square drawn is taken."""
    i = rng.randrange(5)
    if rng.random() < 0.5:
        q = rng.choice(_court())
    else:
        q = (sq[i][0] + rng.randint(-1, 1), sq[i][1] + rng.randint(-1, 1))
    if not B.on_board(q) or q in taken or (q in sq and q != sq[i]):
        return None
    return i, q


def _legalise(o_sq, xs, rng):
    """A carried defence against a new offence: a defender whose square an attacker now stands on is drawn again."""
    xs, taken = list(xs), set(o_sq)
    for j in range(5):
        if xs[j] in taken or xs[j] in xs[:j]:
            xs[j] = rng.choice([q for q in _court() if q not in taken and q not in xs])
    return xs


def _defence_chains(make, o_sq, ball, rng, t_end, chains):
    """Carry the defence's searches on until t_end. chains: [dict(xs, arrows)], changed in place; each gets 'key'."""
    o_sq = list(o_sq)
    keys = _reads(make, [(o_sq, ball, c['xs'], c['arrows']) for c in chains])
    for c, k in zip(chains, keys):
        c['key'] = k
    reads = len(chains)
    while time.time() < t_end:
        items, who = [], []
        for n, c in enumerate(chains):
            for _ in range(SETUP['batch']):
                ch = _change(c['xs'], set(o_sq), rng)
                if ch is None:
                    continue
                j, q = ch
                a = rng.randrange(8)
                xs, ar = c['xs'][:j] + [q] + c['xs'][j + 1:], c['arrows'][:j] + [a] + c['arrows'][j + 1:]
                items.append((o_sq, ball, xs, ar))
                who.append(n)
        if not items:
            continue
        keys = _reads(make, items)
        reads += len(items)
        for (o, b, xs, ar), n, k in zip(items, who, keys):
            if k is not None and (chains[n]['key'] is None or _better(k, chains[n]['key'], -1)):
                chains[n].update(xs=list(xs), arrows=list(ar), key=k, played=None)
    return reads


def _pick(heads, value_of, sign, rng, margin):
    """Of the placements judged by play, one of those within the level's variety margin of the best (as a turn in
    play is picked); if none could be judged in time, the best by the quick reading."""
    judged = [h for h in heads if h.get('played') is not None]
    if judged:
        best = max(sign * h['played'] for h in judged)
        near = [h for h in judged if sign * h['played'] >= best - margin]
        return (rng.choice(near) if margin > 0 else max(judged, key=lambda h: sign * h['played'])), len(judged)
    live = [h for h in heads if h.get('key') is not None]
    best = live[0]
    for h in live[1:]:
        if _better(h['key'], best['key'], sign):
            best = h
    return best, 0


def _search_defence(make_names, o_sq, ball, seed, levels_key=None, budget=None, level='allstar', memory=None):
    """The defence's setup (D-195): squares and arrows searched from no starting answer, shortlisted by the quick
    reading, the shortlist judged by the search's played-out reading. memory (a dict the caller keeps for the game)
    carries the searches from one possession to the next. Returns dict(squares, arrows, perm, text, value, ...)."""
    p = profile(level)
    rng = random.Random(seed)
    t0 = time.time()
    total = budget if budget is not None else max(0.2, p['time_budget_s']) * SCALE['value']
    make = lambda o, b, x, a: make_names([B.sq(q) for q in o], [B.sq(q) for q in x], list(a), b)
    o_sq = list(o_sq)
    mem = memory if memory is not None else {}
    chains = mem.get('X')
    if not chains:
        chains = []
        for _ in range(SETUP['chains']):
            xs, ar = _random_x(o_sq, rng)
            chains.append(dict(xs=xs, arrows=ar))
        mem['X'] = chains
    for c in chains:
        c['xs'] = _legalise(o_sq, c['xs'], rng)
        if c.get('against') != (tuple(o_sq), ball):
            c.update(against=(tuple(o_sq), ball), played=None)
    reads = _defence_chains(make, o_sq, ball, rng, t0 + total * SETUP['quick_share'], chains)
    order = sorted(range(len(chains)), key=lambda n: chains[n]['key'] or (1e9,))
    for n in order:                                   # judged by play, the best by the quick reading first
        c = chains[n]
        if c.get('played') is None and time.time() < t0 + total:
            c['played'] = _played(make, o_sq, ball, c['xs'], c['arrows'], level, t0 + total)
    best, judged = _pick(chains, None, -1, rng, p['variety_margin'])
    xs, arrows = list(best['xs']), list(best['arrows'])
    perm = [min(range(5), key=lambda i: (B.cheb(xs[j], o_sq[i]), i)) for j in range(5)]
    words = []
    for j in range(5):
        i = perm[j]
        d = B.cheb(xs[j], o_sq[i])
        words.append(f'X{j + 1} {"on" if d <= 1 else f"{d} squares off"} O{i + 1}')
    how = (f'{len(chains)} placements searched from no starting answer ({reads} quick readings this time), '
           + (f'{judged} of them judged by play' if judged else 'none could be judged by play in the time, so the quick reading chose'))
    value = best['played'] if best.get('played') is not None else best['key'][0]
    text = f'Placed by search ({how}): ' + '; '.join(words) + '.'
    return dict(squares=xs, arrows=arrows, perm=perm, value=round(value, 2), text=text, reads=reads, judged=judged,
                seconds=round(time.time() - t0, 3), shortlist=[dict(squares=[B.sq(q) for q in c['xs']], arrows=list(c['arrows']),
                                                                    played=c.get('played'), key=list(c['key'] or [])) for c in chains])


def _search_offence(make_names, seed, levels_key=None, budget=None, level='allstar', memory=None):
    """The offence's setup (D-195). It never sees the real defence: each of its searches carries a placement of its
    own and a defence that answers it, improved in turn (the offence's change kept when the reading is better for
    the offence, the answering defence's when better for the defence). The shortlist is judged by the search's
    played-out reading against its answering defence. Returns dict(squares, ball, text, value, candidates, within)."""
    p = profile(level)
    rng = random.Random(seed)
    t0 = time.time()
    total = budget if budget is not None else max(0.2, p['time_budget_s']) * SCALE['value']
    make = lambda o, b, x, a: make_names([B.sq(q) for q in o], [B.sq(q) for q in x], list(a), b)
    mem = memory if memory is not None else {}
    chains = mem.get('O')
    if not chains:
        chains = []
        for _ in range(SETUP['chains']):
            o = _random_o(rng)
            xs, ar = _random_x(o, rng)
            chains.append(dict(o=o, ball=0, xs=xs, arrows=ar))
        mem['O'] = chains
    t_quick = t0 + total * SETUP['quick_share']
    keys = _reads(make, [(c['o'], c['ball'], c['xs'], c['arrows']) for c in chains])
    for c, k in zip(chains, keys):
        c['key'] = k
    reads, turn = len(chains), 0
    while time.time() < t_quick:
        items, who = [], []
        side = 'X' if turn % 2 else 'O'               # the offence's change, then its answering defence's, in turn
        turn += 1
        for n, c in enumerate(chains):
            for _ in range(SETUP['batch']):
                if side == 'O':
                    ch = _change(c['o'], set(c['xs']), rng)
                    if ch is None:
                        continue
                    i, q = ch
                    o = c['o'][:i] + [q] + c['o'][i + 1:]
                    items.append((o, c['ball'], c['xs'], c['arrows']))
                else:
                    ch = _change(c['xs'], set(c['o']), rng)
                    if ch is None:
                        continue
                    j, q = ch
                    a = rng.randrange(8)
                    items.append((c['o'], c['ball'], c['xs'][:j] + [q] + c['xs'][j + 1:], c['arrows'][:j] + [a] + c['arrows'][j + 1:]))
                who.append(n)
        if not items:
            continue
        keys = _reads(make, items)
        reads += len(items)
        for (o, b, xs, ar), n, k in zip(items, who, keys):
            if k is not None and (chains[n]['key'] is None or _better(k, chains[n]['key'], 1 if side == 'O' else -1)):
                chains[n].update(o=list(o), xs=list(xs), arrows=list(ar), key=k, played=None)
    order = sorted(range(len(chains)), key=lambda n: [-v for v in (chains[n]['key'] or (-1e9,))])
    for n in order:
        c = chains[n]
        if c.get('played') is None and time.time() < t0 + total:
            c['played'] = _played(make, c['o'], c['ball'], c['xs'], c['arrows'], level, t0 + total)
    best, judged = _pick(chains, None, 1, rng, p['variety_margin'])
    value = best['played'] if best.get('played') is not None else best['key'][0]
    how = (f'{len(chains)} placements searched from no starting answer, each against a defence that answers it '
           f'({reads} quick readings this time), '
           + (f'{judged} of them judged by play' if judged else 'none could be judged by play in the time, so the quick reading chose'))
    text = f'Placed by search ({how}); the value by that reading is {value:.1f}.'
    return dict(squares=list(best['o']), ball=best['ball'], value=round(value, 2), text=text, candidates=len(chains),
                within=max(1, judged), reads=reads, judged=judged, seconds=round(time.time() - t0, 3))


# ---- the setup as it was before step 18o (still the default: setup_search() is off) -----------------------------------

def _o_value(make, o_sq, ball, rng, budget_end):
    xs, arrows = _defence_reply(make, o_sq, ball, rng, budget_end, rounds=1)
    s = make(o_sq, ball, xs, arrows)
    return Read(s).leaf(), xs, arrows


def _defence_reply(make, o_sq, ball, rng, budget_end, rounds=3, perm=None):
    """The defence's placement by best cover: start from each defender on the empty square next to an attacker that
    is nearest the rim (step 3k's legal man-to-man start), then improve one defender at a time over the empty squares
    near the attackers and every arrow, minimising the offence's position value. Returns (squares, arrows)."""
    from playmaker_web.game import man_to_man
    xs, arrows = man_to_man(list(o_sq), ball)
    if perm is not None:
        xs2 = [None] * 5
        ar2 = [None] * 5
        for j in range(5):
            xs2[j], ar2[j] = xs[perm[j]], arrows[perm[j]]
        xs, arrows = xs2, ar2
    xs, arrows = list(xs), list(arrows)

    def v(xq, ar):
        try:
            return Read(make(o_sq, ball, xq, ar)).leaf()
        except ValueError:
            return 1e9
    if time.time() > budget_end:                        # step 18p: out of time before the first reading
        return xs, arrows
    cur = v(xs, arrows)
    occ_o = set(o_sq)
    cands = sorted({(x, y) for (ox, oy) in o_sq for x in range(ox - 3, ox + 4) for y in range(oy - 3, oy + 4)
                    if B.on_board((x, y)) and (x, y) not in occ_o})
    for _ in range(rounds):
        improved = False
        for j in rng.sample(range(5), 5):
            if time.time() > budget_end:
                return xs, arrows
            pool = [q for q in cands if q not in xs or q == xs[j]]
            pool = rng.sample(pool, min(len(pool), 14))
            for q in pool:
                for a in {B.nearest_dir(q, o_sq[ball]), B.nearest_dir(q, min(o_sq, key=lambda p: B.cheb(p, q)))}:
                    if q == xs[j] and a == arrows[j]:
                        continue
                    if time.time() > budget_end:        # step 18p: the setup keeps its time (it read the clock only between defenders, and ran 4 to 6 seconds over)
                        return xs, arrows
                    xq = xs[:j] + [q] + xs[j + 1:]
                    ar = arrows[:j] + [a] + arrows[j + 1:]
                    val = v(xq, ar)
                    if val < cur - 1e-9:
                        xs, arrows, cur, improved = xq, ar, val, True
        if not improved:
            break
    return xs, arrows


def _fixed_offence(make_names, seed, levels_key=None, budget=None, level='allstar'):
    """The offence's setup (B6): the placement that maximises V against the defence's best reply placement, searched
    over sampled legal placements and refined locally. It never sees the real defence. make_names(o_names, x_names,
    arrows, ball) builds the state. Returns dict(squares, ball, text, value, candidates)."""
    p = profile(level)
    rng = random.Random(seed)
    t0 = time.time()
    t_end = t0 + (budget if budget is not None else max(0.2, p['time_budget_s']) * SCALE['value'])
    make = lambda o, b, x, a: make_names([B.sq(q) for q in o], [B.sq(q) for q in x], list(a), b)
    from playmaker_web.game import TABLE_O
    base = [B.parse_sq(q) for q in TABLE_O]
    cands = [(base, 0)]
    plain = [(x, y) for x in range(B.W) for y in range(2, B.H + 1) if B.zone((x, y)) == '.']
    near = [(x, y) for x in range(B.W) for y in range(1, 11)]
    for _ in range(24):
        bq = rng.choice(plain)
        rest = rng.sample([q for q in near if q != bq], 4)
        cands.append(([bq] + rest, 0))
    scored = []
    # screen every sampled placement against the defence's man-to-man start (cheap), then give the best few the
    # defence's best-cover reply, then refine the best one player at a time
    from playmaker_web.game import man_to_man
    for sq, ball in cands:
        if not _legal_o(sq, ball):
            continue
        xs, ar = man_to_man(list(sq), ball)
        try:
            v = Read(make(sq, ball, xs, ar)).leaf()
        except ValueError:
            continue
        scored.append((v, sq, ball))
        if time.time() > t_end - 0.6 * (t_end - t0):    # step 18p: the setup keeps its time (it used to finish 4 placements whatever the clock said)
            break
    scored.sort(key=lambda r: -r[0])
    top = []
    for v0, sq, ball in scored[:3]:
        if top and time.time() > t_end:                 # step 18p: out of time: the placements already answered stand
            break
        v, _, _ = _o_value(make, sq, ball, rng, t_end)
        top.append((v, sq, ball))
    top.sort(key=lambda r: -r[0])
    best_v, best_sq, best_ball = top[0]
    while time.time() < t_end:
        i = rng.randrange(5)
        q = (best_sq[i][0] + rng.randint(-2, 2), best_sq[i][1] + rng.randint(-2, 2))
        sq = best_sq[:i] + [q] + best_sq[i + 1:]
        if not _legal_o(sq, best_ball):
            continue
        v, _, _ = _o_value(make, sq, best_ball, rng, t_end)
        if v > best_v + 1e-9:
            best_v, best_sq = v, sq
    near_best = [r for r in scored if r[0] >= best_v - p['variety_margin']]
    text = (f'Placed for the best value against the defence\'s best reply ({best_v:.1f}): {len(scored)} placements '
            f'screened, the best {len(top)} against the defence\'s best cover, then refined one player at a time.')
    return dict(squares=best_sq, ball=best_ball, value=round(best_v, 2), text=text, candidates=len(scored),
                within=len(near_best))


def _fixed_defence(make_names, o_sq, ball, seed, levels_key=None, budget=None, level='allstar'):
    """The defence's setup (B6): placement and matchups by best cover (search over squares and arrows, minimising the
    offence's position value). Returns dict(squares, arrows, perm, text, value)."""
    p = profile(level)
    rng = random.Random(seed)
    t_end = time.time() + (budget if budget is not None else max(0.2, p['time_budget_s']) * SCALE['value'])
    make = lambda o, b, x, a: make_names([B.sq(q) for q in o], [B.sq(q) for q in x], list(a), b)
    xs, arrows = _defence_reply(make, list(o_sq), ball, rng, t_end, rounds=3)
    s = make(list(o_sq), ball, xs, arrows)
    r = Read(s)
    perm = []
    for j in range(5):
        perm.append(min(range(5), key=lambda i: (B.cheb(xs[j], o_sq[i]), i)))
    words = []
    for j in range(5):
        i = perm[j]
        d = B.cheb(xs[j], o_sq[i])
        words.append(f'X{j + 1} {"on" if d <= 1 else f"{d} squares off"} O{i + 1}')
    text = 'Placed by best cover (the offence\'s best open look kept as low as it can be): ' + '; '.join(words) + '.'
    return dict(squares=xs, arrows=arrows, perm=perm, value=round(r.leaf(), 2), text=text)


def setup_search():
    """Step 18o (D-195): is the setup searched from no starting answer and judged by play (setup.search in
    ai_profiles.json)? Off: the setup as it was."""
    return CONFIG.get('setup', {}).get('search') is True


def _as_it_was(fn, *args):
    """Step 18q: the setup as it was reads positions as it did, without the lane (eval.lane): its readings run in the
    slow engine, where the lane takes it past its time (3.7 seconds against 1.2 on Shaun's board). The lane judges a
    setup when the setup is searched (setup.search), the next stage of the plan."""
    keep = CONFIG['eval'].get('lane')
    CONFIG['eval']['lane'] = False
    try:
        return fn(*args)
    finally:
        CONFIG['eval']['lane'] = keep


def propose_offence(make_names, seed, levels_key=None, budget=None, level='allstar', memory=None, search=None):
    """The offence's setup: the search of step 18o when setup.search is on (or the caller asks), else the setup as it was."""
    if setup_search() if search is None else search:
        return _search_offence(make_names, seed, levels_key, budget, level, memory)
    return _as_it_was(_fixed_offence, make_names, seed, levels_key, budget, level)


def propose_defence(make_names, o_sq, ball, seed, levels_key=None, budget=None, level='allstar', memory=None, search=None):
    """The defence's setup: the search of step 18o when setup.search is on (or the caller asks), else the setup as it was."""
    if setup_search() if search is None else search:
        return _search_defence(make_names, o_sq, ball, seed, levels_key, budget, level, memory)
    return _as_it_was(_fixed_defence, make_names, o_sq, ball, seed, levels_key, budget, level)
