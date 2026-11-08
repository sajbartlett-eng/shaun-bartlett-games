"""Step 3m: the computer player on the new decision engine (replaces steps 3e to 3k for decisions).

One agent for every level; the levels differ only by ai_profiles.json (B8): search depth and beam, the opponent model,
evaluation noise, attention (the threats and defenders read: those nearest the ball), reaction delay (Rookie reads
the board as it was before the opponent's last turn), the goal-switch margin, the variety margin, the time budget and
(All-Star) scouting the human from stored games. Age stays in the ratings.

Each turn: an anytime search (search.Searcher) scores whole turns; noise is added at the root; goals (goals.py) are
read from the scored turns and held with hysteresis; a turn toward the held goal is chosen, then one at random among
the turns within the variety margin. The turn's actions are played one at a time (a roll ends the plan).
"""
import random
import time

from . import board as B
from . import rules_config as RC
from .actions import Action, legal_actions
from .decide import Read, CONFIG
from .goals import Commitment, goals_in, _likeliest
from .resolve import apply, ChanceNode
from .search import Searcher, play_turn, actor, zobrist, terminal_value

LEVELS = ('rookie', 'starter', 'allstar')
SCALE = {'value': 1.0}           # tests shrink the time budgets; the browser build can scale them


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
        srch = Searcher(side, self.p, self._evaluate(s), t0 + budget, self.rng)
        if self.scouting and self.scouting.get('habit'):
            srch.habit = self.scouting['habit']
            srch.habit_weight = self.scouting.get('weight', 0.3)
        results, reached = srch.root(s, hi, lo)
        sign = 1 if side == 'O' else -1
        scored = [(sign * v + self.rng.gauss(0, self.p['noise']), t, sign * v) for v, t in results]
        base_read = Read(s)
        base = sign * base_read.leaf()
        with_goals = []
        for v, t, raw in sorted(scored, key=lambda r: -r[0])[:8]:
            after = _likeliest(play_turn(s, t))
            gs = goals_in(s, after, side, base_read, None if after.stage == 'over' else Read(after), t) \
                if after.stage != 'over' else {}
            with_goals.append((v, t, gs))
        n_log = len(self.commit.log)
        turn, val = self.commit.choose(s, side, with_goals, base, None)
        # variety: one at random among the turns within the variety margin of the chosen one
        near = [t for v, t, _ in with_goals if v >= val - self.p['variety_margin']]
        if self.p['variety_margin'] > 0 and len(near) > 1:
            turn = self.rng.choice(near)
        took = round(time.time() - t0, 3)
        note = dict(event='decision', level=self.level, depth=reached, partial=getattr(srch, 'partial', 0),
                    leaves=srch.leaves, nodes=srch.nodes,
                    seconds=took, value=round(val, 2), turn=[str(a) for a in turn],
                    goal=self.commit.words or None,
                    alternatives=[dict(turn=[str(a) for a in t], value=round(v, 2)) for v, t, _ in with_goals[:3]])
        for g in self.commit.log[n_log:]:
            self.notes.append(dict(event='goal', **g))
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

    def _small(self, s, acts):
        """Contest choice, forced shot type, Coach's Call target, failed-inbound pick: one step, valued exactly."""
        side = actor(s)
        ev = self._evaluate(s)

        def val(a):
            n = apply(s, a)
            return ev(n)
        best = max(acts, key=val) if side == 'O' else min(acts, key=val)
        return best


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


# ---- setup (B6) -------------------------------------------------------------------------------------------------------

def _legal_o(sq, ball):
    return (len(set(sq)) == 5 and all(B.on_board(q) for q in sq) and B.zone(sq[ball]) == '.' and sq[ball][1] > 1)


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
                    xq = xs[:j] + [q] + xs[j + 1:]
                    ar = arrows[:j] + [a] + arrows[j + 1:]
                    val = v(xq, ar)
                    if val < cur - 1e-9:
                        xs, arrows, cur, improved = xq, ar, val, True
        if not improved:
            break
    return xs, arrows


def propose_offence(make_names, seed, levels_key=None, budget=None, level='allstar'):
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
        if time.time() > t_end - 0.6 * (t_end - t0) and len(scored) >= 4:
            break
    scored.sort(key=lambda r: -r[0])
    top = []
    for v0, sq, ball in scored[:3]:
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


def propose_defence(make_names, o_sq, ball, seed, levels_key=None, budget=None, level='allstar'):
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
