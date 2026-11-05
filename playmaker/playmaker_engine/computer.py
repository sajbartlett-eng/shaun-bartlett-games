"""The computer opponent, both sides, at three levels (step 3e).

The computer chooses among legal actions only; no rule changes. It sees what a human player sees: the
cards (read exactly, by their marks, or by position, by level), the board and the trackers. It never
reads the Coach's Call target when defending, gets no extra tokens, and uses no stored solver results.

How it values things:
- A contest is valued after the defence's legal reaction (`reachable_contest`): a defender with their
  Move unused, not locked and a token in the pool can still get adjacent and facing once the shot is
  declared; Quick Step keeps the facing, a Sprint faces the way it ran.
- A position is valued by the offence's best next action against it (shoot now, drive, or pass and
  then shoot), the solver's evaluation. A level may instead use the solver's search at a short budget
  (lookahead 'solver'); calibration found the one-turn ranking stronger within the time limit.
- Concepts, habits, tunnel vision, card reading, the comfort line and randomness are the level levers
  (computer_levels.json).
"""
import json
import os
import random
import time

from . import board as B
from . import rules_config as RC
from .actions import Action, legal_actions, MOVEMENT
from .cards import CARDS
from .policies import Policy, expected
from .resolve import apply, ChanceNode
from .state import Context

with open(os.path.join(os.path.dirname(__file__), 'computer_levels.json')) as _f:
    LEVELS = json.load(_f)
LEVEL_NAMES = ('rookie', 'starter', 'allstar')
BUDGET = dict(LEVELS['budget_s'])          # 'server' / 'browser'; the browser build lowers 'active'
BUDGET['active'] = BUDGET['server']


# ---- the reaction (section 1) -------------------------------------------------------------------

def reaction_budget(state):
    """Actions the defence may spend reacting to a declared shot: 0, 1 or 2 (OQ-6), from its tokens."""
    return min(2, state.tok_x) if state.tok_x > 0 else 0


def reachable_contest(state, shooter=None, shot=None, budget=None):
    """Every defender who could contest a shot by `shooter` (default: the ball carrier) from where the
    shooter stands, after the defence's legal reaction. Each entry: defender, clean (arrow on the shooter
    already, or the reaction gets them adjacent and facing), actions (reaction actions needed), contest
    (rating after the -3 when further from the rim than the shooter), value (shot points after this
    contest; a foul roll entry also gives the foul probability). The reaction budget is shared: the
    contest is made by one defender, who may use the whole budget."""
    from .solver import defender_reach
    from .scoring import foul_on_shot_points
    shooter = state.ball if shooter is None else shooter
    spos = state.o[shooter]
    z = B.zone(spos)
    types = RC.ZONE_SHOTS[z]
    if not types:
        return []
    t = shot or max(types, key=lambda k: state.ctx.off[shooter].shot(k))
    pts = RC.ZONE_POINTS[z]
    card = state.ctx.off[shooter]
    budget = reaction_budget(state) if budget is None else budget
    out = []
    for d in range(5):
        free, fixed = defender_reach(state, d, budget)
        best = None
        for q in set(free) | set(fixed):
            if not B.adjacent(q, spos) or q in state.o:
                continue
            on = B.dir_between(q, spos)
            far = B.dist_rim(q) > B.dist_rim(spos)
            c = state.ctx.dfn[d].con(t) - (RC.FAR_CONTEST_PENALTY if far else 0)
            if state.ctx.rules.floor_contest_zero:
                c = max(0, c)
            clean_len = len(free[q]) if q in free else None
            for a, seq in fixed.get(q, {}).items():
                if a == on and (clean_len is None or len(seq) < clean_len):
                    clean_len = len(seq)
            if clean_len is not None:
                cand = dict(defender=d, square=B.sq(q), clean=True, actions=clean_len, contest=c,
                            value=max(0, pts * (card.shot(t) - c)))
            else:
                ln = min(len(seq) for seq in fixed[q].values())
                pf = state.ctx.dfn[d].r['foul_contest'] / 20.0
                fp = float(foul_on_shot_points(card, t, pts, state.ctx.rules)[0])
                v = max(0, pts * (card.shot(t) - c))
                cand = dict(defender=d, square=B.sq(q), clean=False, actions=ln, contest=c, foul_p=pf,
                            value=pf * fp + (1 - pf) * v)
            if best is None or (cand['value'], cand['actions']) < (best['value'], best['actions']):
                best = cand
        if best:
            out.append(best)
    return sorted(out, key=lambda e: e['value'])


# ---- passing judgement (step 3f) ------------------------------------------------------------------

_PASS_CACHE = {}


def pass_risk(state, passer, receiver):
    """A pass judged after the defence's reply. A Pass ends the offence's turn and the defence answers
    before it resolves, so the lane is clean only if no defender can legally get an Intercept on it in
    that turn: directly (on the line) or by an approach (a Move, Quick Step or Sprint onto the line by a
    defender whose arrow already crosses it, then Intercept), with the defence's tokens, unused Moves,
    locks and the intercept limit as the rules have them. Computed from the legal actions, so it is the
    rules' own answer. Returns None if the pass isn't legal, else a dict: clean, risk (the best
    interception chance any defender can reach: 1 - P(d20 <= Pass - Intercept)), by (that defender),
    line (the defence's actions for it), pending (the state with the ball in the air)."""
    from .actions import is_approach
    from .scoring import p_success
    key = (state, id(state.ctx), passer, receiver)         # positions compare equal across contexts
    hit = _PASS_CACHE.get(key)
    if hit is not None and hit['ctx'] is state.ctx:
        return hit
    a = Action('pass', 'O', passer, target=receiver)
    if state.stage != 'play' or state.side != 'O' or state.ball != passer or a not in legal_actions(state):
        return None
    pend = apply(state, a)
    out = dict(clean=True, risk=0.0, by=None, line=(), pending=pend, ctx=state.ctx)
    if not isinstance(pend, ChanceNode) and pend.pending:
        from .actions import inbound_held, intercept_status, movement_actions
        pr = pend.ctx.off[passer].r['pass']
        if pend.inbound:                       # inbound passes (OQ-35): ask the legal actions directly
            cands = []
            for d in legal_actions(pend):
                if d.kind == 'intercept':
                    cands.append((d,))
                elif d.kind in MOVEMENT and is_approach(pend, d):
                    nxt = apply(pend, d)
                    icpt = Action('intercept', 'X', d.piece)
                    if not isinstance(nxt, ChanceNode) and icpt in legal_actions(nxt):
                        cands.append((d, icpt))
        else:                                  # the same answer as the legal actions, computed directly
            cands = []
            can = pend.count('X', 'intercept') < RC.LIMITS['X']['intercept'] and pend.tok_x > 0
            status = [intercept_status(pend, j) for j in range(5)] if can else [None] * 5
            for j in range(5):
                if status[j] == 'direct':
                    cands.append((Action('intercept', 'X', j),))
            if any(st == 'approach' for st in status):
                for d in movement_actions(pend, 'X', pend.ctx.rules):
                    if status[d.piece] == 'approach' and is_approach(pend, d):
                        nxt = apply(pend, d)
                        if not isinstance(nxt, ChanceNode) and nxt.approach == d.piece and nxt.tok_x > 0 and \
                                nxt.count('X', 'intercept') < RC.LIMITS['X']['intercept']:
                            cands.append((d, Action('intercept', 'X', d.piece)))
        for line in cands:
            j = line[-1].piece
            r = 1.0 - float(p_success(pr - pend.ctx.dfn[j].r['intercept'], pend.ctx.rules))
            if out['clean'] or r > out['risk'] or (r == out['risk'] and len(line) < len(out['line'])):
                out.update(clean=False, risk=r, by=j, line=line)
    if len(_PASS_CACHE) > 20000:
        _PASS_CACHE.clear()
    _PASS_CACHE[key] = out
    return out


def pass_outcomes(info):
    """The two positions a pass can lead to, by the rules: caught (the defence's interception attempt
    failed, or there was none) and picked off (a turnover; the ball stays with the passer and play goes
    on, OQ-1). Picked off is None for a clean lane."""
    from .resolve import complete_pass, force
    pend = info['pending']
    if isinstance(pend, ChanceNode) or not pend.pending:
        return pend, None
    if info['clean']:
        return complete_pass(pend), None          # it lands at the start of the defence's turn
    node = pend
    for d in info['line']:
        node = apply(node, d)
    return force(node, 'success'), force(node, 'failure')


# ---- what a side can see; card reading (section 8 lever 4) ----------------------------------------

def _positions():
    from .scouting import position
    return {k: position(c) for k, c in CARDS.items()}


_POS = None
_MIDS = None


def _mids():
    """Middle value of each band of each rating, and each position's typical band and QS, from the 75 cards."""
    global _MIDS, _POS
    if _MIDS is None:
        _POS = _positions()
        vals, by_pos = {}, {}
        for c in CARDS.values():
            for r, v in c.r.items():
                vals.setdefault((r, c.bands[r]), []).append(v)
                by_pos.setdefault((_POS[c.key], r), []).append(c.bands[r])
        mid = {k: round(sum(v) / len(v)) for k, v in vals.items()}
        typical = {k: max(set(v), key=v.count) for k, v in by_pos.items()}
        qs = {}
        for c in CARDS.values():
            qs.setdefault(_POS[c.key], []).append(c.qs)
        qs = {p: sorted(v)[len(v) // 2] for p, v in qs.items()}
        _MIDS = (mid, typical, qs)
    return _MIDS


class SeenCard:
    """A card as the computer reads it at its level: 'exact' (the numbers), 'marks' (only ▲ / plain / ▼:
    every rating is the middle of its band) or 'role' (judged by position: the position's typical band)."""
    __slots__ = ('key', 'num', 'role', 'tier', 'tagline', 'qs', 'r', 'bands')

    def __init__(self, card, reading):
        mid, typical, qs = _mids()
        self.key, self.num, self.role, self.tier, self.tagline = card.key, card.num, card.role, card.tier, card.tagline
        if reading == 'marks':
            self.bands = dict(card.bands)
            self.qs = card.qs
        else:                                   # role
            pos = _POS[card.key]
            self.bands = {r: typical[(pos, r)] for r in card.r}
            self.qs = qs[pos]
        self.r = {r: mid[(r, b)] for r, b in self.bands.items()}

    def shot(self, t):
        return self.r['shot_' + t]

    def con(self, t):
        return self.r['con_' + t]


def seen_context(ctx, reading):
    if reading == 'exact':
        return ctx
    return Context([SeenCard(c, reading) for c in ctx.off], [SeenCard(c, reading) for c in ctx.dfn], ctx.rules,
                   ctx.title, ctx.kind, ctx.scenario, ctx.card_clock, ctx.inbounder, ctx.coach_call,
                   ctx.three_only, ctx.two_or_three, ctx.hold_for_one, ctx.off_team, ctx.def_team)


VISIBLE_FIELDS = ('o', 'x', 'arrows', 'ball', 'clock', 'phase', 'side', 'stage', 'tok_o', 'tok_x', 'pending',
                  'shot', 'screens', 'locks', 'moved', 'counts')


def seen_state(state, side, ctx):
    """The state as `side` may see it: the defence never sees the offence's secret Coach's Call target."""
    s = state.with_(ctx=ctx)
    if side == 'X' and state.ctx.coach_call and state.stage != 'over':
        s = s.with_(target=-1)
    return s


# ---- the level evaluation: the solver's evaluation, with the concepts as switches -----------------

def _evaluator_class():
    from .solver import Evaluator

    class LevelEvaluator(Evaluator):
        """reaction: count reaction-reachable contests (off: only the arrows as they stand);
        reserve: see that a spent token or Move loses the reaction (off: always assume a reaction);
        tunnel: only the N attackers nearest the ball are a threat."""

        def __init__(self, cfg, reaction=True, reserve=True, tunnel=5):
            super().__init__(cfg)
            self.reaction, self.reserve, self.tunnel = reaction, reserve, tunnel

        def reach(self, s, budget):
            if not self.reaction:
                budget = 0
            elif not self.reserve:
                s = s.with_(moved_x=0, tok_x=max(s.tok_x, 2))
                budget = 2
            return super().reach(s, budget)

        def visible(self, s):
            if self.tunnel >= 5:
                return None
            cp = s.o[s.ball]
            order = sorted(range(5), key=lambda i: (i != s.ball, B.cheb(s.o[i], cp), i))
            return set(order[:self.tunnel])

        def carrier_look(self, s, shooter, budget_x, can_move, forced=False):
            vis = self.visible(s)
            if vis is not None and shooter not in vis:
                return (0.0, 0.0, 0.0, None, None)
            return super().carrier_look(s, shooter, budget_x, can_move, forced)

    return LevelEvaluator


# ---- the computer player ---------------------------------------------------------------------------

class Computer(Policy):
    """One side's computer at a level. choose(state) -> a legal action. notes: decisions to log (plans,
    targets, habits that fired)."""
    name = 'computer'

    def __init__(self, side, level='starter', seed=0, overrides=None, habits=None, budget_s='active'):
        if level not in LEVEL_NAMES:
            raise ValueError(f'level must be one of {LEVEL_NAMES}')
        self.side, self.level = side, level
        part = LEVELS['defence' if side == 'X' else 'offence']
        self.cfg = json.loads(json.dumps(part['levels'][level]))
        for k, v in (overrides or {}).items():
            if isinstance(v, dict) and isinstance(self.cfg.get(k), dict):
                self.cfg[k].update(v)
            else:
                self.cfg[k] = v
        self.rng = random.Random(seed * 7919 + (1 if side == 'O' else 2))
        pool = [h for h in part['habits'] if h not in self.cfg.get('habits_not', [])]
        self.habits = list(habits) if habits is not None else self.rng.sample(pool, self.cfg['habits'])
        self.budget_s = BUDGET['active'] if budget_s == 'active' else budget_s
        self.comfort = (LEVELS['defence']['comfort_line'] + self.cfg.get('comfort_offset', 0)) if side == 'X' else None
        self.notes = []
        self.stats = dict(decisions=0, comfort_decided=0, habit_fired={}, seconds=[])
        self._ctx = None
        self.plan = None
        self.queue = None

    # -- setup per possession (the solver's caches key positions without their context) --
    def _context(self, state):
        if state.ctx is self._ctx:
            return
        from .solver import Generator, Searcher
        from .solver_config import with_config
        self._ctx = state.ctx
        self.seen = seen_context(state.ctx, self.cfg['reading'])
        c = self.cfg['concepts']
        reaction = c.get('reaction', c.get('reaction_shot', True))
        reserve = c.get('reserve', True) if self.side == 'X' else c.get('drain', True)
        # no root-wide raw action scan and no exact endgame hand-off: neither watches the clock
        self.ecfg = with_config(eval_turns=1, top_k_raw=0, endgame_tokens=-1, eval_reply_k=2)
        self.ev = _evaluator_class()(self.ecfg, reaction=reaction, reserve=reserve, tunnel=self.cfg['tunnel'])
        self.gen = Generator(self.ecfg, self.ev)
        self.ev._gen = self.gen
        self.Searcher = Searcher
        self.queue = None
        self.plan = None
        self.visited = {}           # offence: (squares, ball) reached at its decisions this possession -> times
        self.picked_off = set()     # offence: passes intercepted this possession, keyed by the full position
        self._last_pass = None

    def describe(self):
        """For the log and the review: level, habits drawn, concepts switched off."""
        off = [k for k, v in self.cfg['concepts'].items() if not v and k != 'reaction_shot']
        return dict(level=self.level, name=LEVELS['names'][self.level][0], habits=self.habits, concepts_off=off)

    def _fire(self, habit):
        self.stats['habit_fired'][habit] = self.stats['habit_fired'].get(habit, 0) + 1

    # -- choose --
    def choose(self, state):
        acts = legal_actions(state)
        if len(acts) == 1:
            return acts[0]
        self._context(state)
        if self.side == 'O' and state.stage == 'play' and state.side == 'O':
            self._remember(state)
        t0 = time.time()
        self._deadline = t0 + self.budget_s if self.budget_s else None
        if self.queue and self.queue[0] == state and self.queue[1] and self.queue[1][0] in acts:
            a = self.queue[1][0]
            self._queue(state, a, self.queue[1][1:])
            self._note_pass(state, a)
            return a
        self.queue = None
        view = seen_state(state, self.side, self.seen)
        if self.side == 'X':
            play = self._defend(view, acts)
        else:
            play = self._attack(view, acts)
        a = play.actions[0] if play is not None else acts[0]
        if a not in acts:
            a = acts[0]
        self._queue(state, a, play.actions[1:] if play is not None else ())
        self._note_pass(state, a)
        self.stats['decisions'] += 1
        self.stats['seconds'].append(time.time() - t0)
        return a

    # -- offence memory over the possession: no loops, no repeating a pass that was just picked off --
    @staticmethod
    def _spot(state):
        return (state.o, state.x, state.arrows, state.ball)

    def _remember(self, state):
        if self._last_pass is not None and state.tos > self._last_pass[2]:
            self.picked_off.add(self._last_pass[:2])
        self._last_pass = None
        k = (state.o, state.ball)
        self.visited[k] = self.visited.get(k, 0) + 1

    def _note_pass(self, state, a):
        if self.side == 'O' and a.kind == 'pass':
            self._last_pass = (self._spot(state), a.target, state.tos)

    def _loop_penalty(self, view, node):
        """No progress: a play that ends where the offence already stood earlier this possession (its five
        squares and the ball) loses this much per earlier visit (at most three)."""
        w = self.cfg.get('loop_penalty', LEVELS['offence'].get('loop_penalty', 0))
        if not w or isinstance(node, ChanceNode):
            return 0.0
        k = (node.o, node.pending[1] if node.pending else node.ball)
        n = self.visited.get(k, 0) - (1 if k == (view.o, view.ball) else 0)
        return w * min(3, max(0, n))

    def _queue(self, state, a, rest):
        nxt = apply(state, a)
        self.queue = (nxt, tuple(rest)) if rest and not isinstance(nxt, ChanceNode) else None

    # -- values --
    def _immediate(self, s):
        """Lookahead 0: the ball carrier's shot as it stands (after the reaction, per the concepts)."""
        if s.stage != 'play' or s.pending:
            return self.ev(s)[0].ev
        base = RC.STEAL_FOUL_BONUS * s.bonus5 + RC.TURNOVER_POINTS * s.tos
        ev = self.ev.carrier_look(s, s.ball, reaction_budget(s), False)[0]
        return base + ev

    def _node_value(self, node, fn):
        if isinstance(node, ChanceNode):
            if self.side == 'O' and not self.cfg['concepts'].get('risk', True):
                return max(self._node_value(sub, fn) for _, _, sub in node.outcomes)
            return sum(float(p) * self._node_value(sub, fn) for p, _, sub in node.outcomes)
        return fn(node)

    def _value_fn(self):
        la = self.cfg['lookahead']
        if la == 0:
            return self._immediate
        if self.side == 'X':
            return self._threat
        return lambda s: (self.ev._reply(s)[0].ev if s.stage == 'play' and s.side == 'X' else self.ev(s)[0].ev)

    def _threat(self, s):
        """The defence's view of the offence's next turn: its best action (a shot, a step and a shot, a pass
        and a shot), or a dribble at the dice, with the defence's reply after it (a won dribble can open a
        step-out shot a turn later)."""
        from .solver import expected
        v = self.ev(s)[0].ev
        if s.stage != 'play' or s.side != 'O' or s.tok_o < 1:
            return v
        for a in legal_actions(s):
            if a.kind == 'dribble':
                v = max(v, expected(apply(s, a), self.ev._reply)[0].ev)
        return v

    def _rank(self, view, plays, fn, maximise, stop):
        from .solver import apply_play
        scored = []
        for p in plays:
            if stop is not None and scored and time.time() > stop:
                break
            node = apply_play(view, p)
            if node is None:
                continue
            v = self._node_value(node, fn)
            scored.append((v, p))
        return scored

    def _pick(self, scored, maximise, key=None):
        """Best, or with the level's randomness the second best (never the main source of mistakes)."""
        if not scored:
            return None
        cost = lambda p: sum(a.kind != 'end_turn' for a in p.actions) * 1e-6
        k = key or (lambda vp: (-vp[0] if maximise else vp[0]) + cost(vp[1]))
        ranked = sorted(scored, key=k)
        if len(ranked) > 1 and self.rng.random() < self.cfg['randomness']:
            return ranked[1][1]
        return ranked[0][1]

    @staticmethod
    def _with_end(view, acts, plays):
        """Mid-turn (one action already taken), stopping is a choice too: the generator builds plays for a
        fresh turn and leaves it out."""
        from .solver import Play
        end = next((a for a in acts if a.kind == 'end_turn'), None)
        if end is not None and view.stage == 'play' and view.turn_n >= 1 and not any(p.actions == (end,) for p in plays):
            plays = list(plays) + [Play('end', (end,))]
        return plays

    def _stop(self):
        return getattr(self, '_deadline', None)

    def _late(self, share=0.85):
        """Most of the thinking time already gone (the search used it): fall back to the quick value."""
        d = self._stop()
        return d is not None and self.budget_s and time.time() > d - self.budget_s * (1 - share)

    # ---- defence ----
    def _defend(self, view, acts):
        from .solver import Play
        h = self.habits
        if 'jumps_first_pass' in h:
            icpt = [a for a in acts if a.kind == 'intercept']
            if icpt:
                self._fire('jumps_first_pass')
                o = view.ctx.off[view.pending[0]]
                return Play('habit', (min(icpt, key=lambda a: o.r['pass'] - view.ctx.dfn[a.piece].r['intercept']),))
        if view.stage == 'contest':
            return self._contest(view, acts)
        if view.stage == 'reaction' and 'nearest_closes_out' in h:
            p = self._nearest_reaction(view, acts)
            if p:
                self._fire('nearest_closes_out')
                return p
        if self.cfg['lookahead'] == 'solver' and view.stage == 'play':
            p = self._search(view)
            if p is not None:
                return self._habit_rewrite(view, p)
        plays = self._with_end(view, acts, self.gen.plays(view, shallow=False))
        if view.stage in ('reaction', 'contest') or view.pending:
            have = {p.actions for p in plays}
            plays += [Play('single', (a,)) for a in acts if (a,) not in have]
        plays = self._concept_filter(view, plays)
        fn = self._value_fn()
        if self._late():
            fn = self._immediate
        scored = self._rank(view, plays, fn, False, self._stop())
        if not scored:
            return None
        comfort = self._comfort_key(view)
        if comfort is not None:
            cost = lambda p: sum(a.kind != 'end_turn' for a in p.actions) * 1e-6
            with_line = min(scored, key=comfort)[1]
            without = min(scored, key=lambda vp: vp[0] + cost(vp[1]))[1]
            if with_line.actions != without.actions:
                self.stats['comfort_decided'] += 1          # the comfort line changed this choice
        best = self._pick(scored, False, key=comfort)
        return self._habit_rewrite(view, best)

    def _comfort_key(self, view):
        if not self.cfg['concepts'].get('help', True) or self.comfort is None:
            return None
        line = self.comfort
        shooters = [i for i, c in enumerate(view.ctx.off) if c.bands['shot_three'] == 'H'] \
            if 'never_leaves_shooter' in self.habits else []
        cost = lambda p: sum(a.kind != 'end_turn' for a in p.actions) * 1e-6

        def key(vp):
            v, p = vp
            k = max(v, line)                     # looks below the comfort line are conceded
            if shooters and v < line:
                k += 1e-3 * v                    # ...except a ▲ shooter's (the habit): still guarded
            return k + cost(p)
        return key

    def _concept_filter(self, view, plays):
        """Concepts off: no help (off-ball defenders stay by their man), no walls (the on-ball arrow stays
        on the ball), no lanes (off-ball arrows face their man)."""
        c = self.cfg['concepts']
        if c.get('help', True) and c.get('walls', True) and c.get('lanes', True):
            return plays
        from .solver import Play
        cp = view.o[view.ball]
        out, seen = [], set()
        for p in plays:
            acts, ok = [], True
            for a in p.actions:
                if a.side == 'X' and a.kind == 'move' and a.dest is not None:
                    on_ball = B.adjacent(a.dest, cp)
                    man = min((o for o in view.o), key=lambda o: B.cheb(o, a.dest))
                    if on_ball and not c.get('walls', True):
                        a = a._replace(arrow=B.nearest_dir(a.dest, cp))
                    elif not on_ball:
                        if not c.get('help', True) and B.cheb(a.dest, man) > 1:
                            ok = False
                        if not c.get('lanes', True):
                            a = a._replace(arrow=B.nearest_dir(a.dest, man))
                acts.append(a)
            if ok and tuple(acts) not in seen:
                seen.add(tuple(acts))
                out.append(Play(p.concept, tuple(acts)))
        return out or plays

    def _habit_rewrite(self, view, play):
        """ball_watcher: help defenders' arrows to the ball; always_force_middle: the on-ball arrow points
        to the baseline."""
        h = self.habits
        if not ('ball_watcher' in h or 'always_force_middle' in h):
            return play
        from .solver import Play
        cp = view.o[view.ball]
        acts = []
        for a in play.actions:
            if a.side == 'X' and a.kind == 'move' and a.dest is not None and B.on_board(cp):
                if B.adjacent(a.dest, cp) and 'always_force_middle' in h:
                    if a.arrow != 4:
                        self._fire('always_force_middle')
                    a = a._replace(arrow=4)                  # S: toward the baseline
                elif not B.adjacent(a.dest, cp) and 'ball_watcher' in h:
                    d = B.nearest_dir(a.dest, cp)
                    if a.arrow != d:
                        self._fire('ball_watcher')
                    a = a._replace(arrow=d)
            acts.append(a)
        return Play(play.concept, tuple(acts))

    def _contest(self, view, acts):
        from .solver import Play
        from .scoring import contest_options
        if 'nearest_closes_out' in self.habits:
            sp = view.o[view.ball]
            real = [a for a in acts if a.piece >= 0]
            if real:
                self._fire('nearest_closes_out')
                return Play('habit', (min(real, key=lambda a: (B.cheb(view.x[a.piece], sp), a.piece)),))
        scored = [(self._node_value(apply(view, a), lambda s: self.ev(s)[0].ev), Play('contest', (a,))) for a in acts]
        return self._pick(scored, False)

    def _nearest_reaction(self, view, acts):
        """nearest_closes_out in the reaction: the nearest defender turns or steps to face the shooter."""
        from .solver import Play
        sp = view.o[view.ball]
        near = min(range(5), key=lambda j: (B.cheb(view.x[j], sp), j))
        for a in acts:
            if a.kind == 'move' and a.piece == near and B.adjacent(a.dest, sp) and a.arrow == B.dir_between(a.dest, sp):
                return Play('habit', (a,))
        return None

    def _search(self, view):
        """The solver's search, deepening until the thinking time is up (a hard stop: when not even depth
        1 finished, the caller falls back to the one-turn ranking with what time is left)."""
        from .solver import Timeout
        se = self.Searcher(self.ecfg)
        se.ev = self.ev
        se.gen = self.gen
        budget = self.budget_s or 0.5
        se.deadline = time.time() + budget * 0.5
        best = None
        try:
            for d in range(1, self.ecfg.max_depth + 1):
                se.root_depth = d
                se.value(view, d)
                e = se.tt.get((view, d))
                if e is not None and e.best is not None:
                    best = e.best
        except Timeout:
            pass
        return best

    # ---- offence ----
    def targets(self, view):
        """Primary and secondary targets: the two largest edges, each a player's ▲ shot type against the
        defender likely to contest it (the nearest), read at the level's card reading."""
        ctx = view.ctx
        three_only = ctx.three_only
        edges = []
        for i, c in enumerate(ctx.off):
            if not B.on_board(view.o[i]) and i != view.ball:
                continue
            near = min(range(5), key=lambda j: B.cheb(view.x[j], view.o[i]))
            for t in ('layup', 'dunk', 'post', 'floater', 'mid', 'long', 'three'):
                if c.bands['shot_' + t] != 'H' or (three_only and t != 'three'):
                    continue
                pts = 3 if t == 'three' else 2
                edges.append((pts * (c.shot(t) - ctx.dfn[near].con(t)), i, t))
        edges.sort(key=lambda e: (-e[0], e[1]))
        if 'star_only' in self.habits:
            star = max(range(5), key=lambda i: (max(ctx.off[i].r[k] for k in ctx.off[i].r if k.startswith('shot_')), -i))
            edges = [e for e in edges if e[1] == star] + [e for e in edges if e[1] != star]
            self._fire('star_only')
        out = []
        for e in edges:
            if e[1] not in [x[1] for x in out]:
                out.append(e)
        if ctx.coach_call and view.target >= 0:
            out = [x for x in out if x[1] == view.target] + [x for x in out if x[1] != view.target]
            if not out or out[0][1] != view.target:
                out.insert(0, (0, view.target, 'three' if three_only else 'any'))
        return [dict(o=i, shot=t, edge=v) for v, i, t in out[:2]]

    def _ensure_plan(self, view):
        c = self.cfg['concepts']
        if not c.get('plan', True) and 'star_only' not in self.habits and not view.ctx.coach_call:
            return
        reset = self.plan is None or (view.phase != self.plan['phase'] and view.inbound == 0 and self.plan.get('inbound'))
        if self.plan is not None and not reset:
            prim = self.plan['targets'][0]['o'] if self.plan['targets'] else None
            if prim is not None and prim != view.ball:
                near = min(range(5), key=lambda j: B.cheb(view.x[j], view.o[prim]))
                t = self.plan['targets'][0]['shot']
                switched = t in ('layup', 'dunk', 'post', 'floater', 'mid', 'long', 'three') and \
                    view.ctx.dfn[near].bands['con_' + t] == 'H' and near != self.plan['near']
                if switched and not view.ctx.coach_call:
                    reset = True
                    self.notes.append(dict(event='replan', why=f'a ▲ {t} contester (X{near + 1}) took O{prim + 1}'))
        if reset:
            tg = self.targets(view)
            near = min(range(5), key=lambda j: B.cheb(view.x[j], view.o[tg[0]['o']])) if tg else None
            before = self.plan['type'] if self.plan else None
            kind = self._plan_kind(view, tg)
            self.plan = dict(targets=tg, phase=view.phase, inbound=bool(view.inbound), near=near, type=kind)
            self.notes.append(dict(event='plan', targets=tg))
            if kind and kind != before:
                self.notes.append(dict(event='plan_type', plan=kind))

    def _plan_bonus(self, view, node_state):
        if not self.plan or not self.plan['targets'] or isinstance(node_state, ChanceNode):
            return 0.0
        w = LEVELS['offence']['plan_weight'] * (3 if 'star_only' in self.habits else 1)
        tg = self.plan['targets'][0]
        s = node_state
        bonus = 0.0
        if s.ball == tg['o']:
            bonus += w
        z = B.zone(s.o[tg['o']]) if B.on_board(s.o[tg['o']]) else '.'
        if tg['shot'] in RC.ZONE_SHOTS.get(z, ()):
            bonus += w
        return bonus

    def _attack(self, view, acts):
        from .solver import Play, apply_play
        if view.stage == 'target':
            tg = self.targets(view)
            want = tg[0]['o'] if tg else 0
            return Play('target', (next((a for a in acts if a.target == want), acts[0]),))
        if view.stage in ('pick', 'forced'):
            scored = [(self._node_value(apply(view, a), lambda s: self.ev(s)[0].ev), Play(view.stage, (a,))) for a in acts]
            return self._pick(scored, True)
        self._ensure_plan(view)
        c = self.cfg['concepts']
        if self.cfg['lookahead'] == 'solver':
            p = self._search(view)
            if p is not None and self._patient(view, p, None):
                return p
        plays = self._with_end(view, acts, self.gen.plays(view, shallow=False))
        if self.picked_off:
            spot = self._spot(view)
            kept = [p for p in plays if not any(a.kind == 'pass' and (spot, a.target) in self.picked_off
                                                for a in p.actions)]
            plays = kept or plays
        if 'never_screens' in self.habits:
            kept = [p for p in plays if not any(a.kind == 'screen' for a in p.actions)]
            if len(kept) < len(plays):
                self._fire('never_screens')
            plays = kept or plays
        if 'ignores_mismatch' in self.habits:
            order = [i for i in list(range(view.ball + 1, 5)) + list(range(view.ball)) if B.on_board(view.o[i])]
            nxt = order[0] if order else None
            kept = [p for p in plays if not any(a.kind == 'pass' and a.target != nxt for a in p.actions)]
            if len(kept) < len(plays):
                self._fire('ignores_mismatch')
            plays = kept or plays
        if 'star_only' in self.habits and self.plan and self.plan['targets']:
            star = self.plan['targets'][0]['o']
            kept = [p for p in plays if not any(a.kind == 'pass' and a.target != star for a in p.actions)]
            plays = kept or plays
        if 'forces_passes' in self.habits and self.plan and self.plan['targets']:
            t = self.plan['targets'][0]['o']
            fp = next((a for a in acts if a.kind == 'pass' and a.target == t), None)
            if fp is not None:                            # to the primary target whenever legal, whatever the risk
                self._fire('forces_passes')
                return Play('habit', (fp,))
        fn = self._value_fn()
        late = self._late()
        if late:
            fn = self._immediate
        stop = self._stop()
        scored, raw = [], {}
        for p in plays:
            if stop is not None and scored and time.time() > stop:
                break
            node = apply_play(view, p)
            if node is None:
                continue
            v = self._node_value(node, fn) if late else self._play_value(view, p, node, fn)
            raw[p] = v                                    # the bar reads the shot's value, not the plan bonus
            if c.get('plan', True) or 'star_only' in self.habits:
                v += self._plan_bonus(view, node)
            if not any(a.kind == 'shot' for a in p.actions):
                v -= self._loop_penalty(view, node)
            scored.append((v, p))
        if not scored:
            return None
        shots = [(v, p) for v, p in scored if any(a.kind == 'shot' for a in p.actions)]
        rest = [(v, p) for v, p in scored if not any(a.kind == 'shot' for a in p.actions)]
        best = self._pick(scored, True)
        if best is None or not shots or not rest:
            return best
        # 7.3 with a bar: a shot goes up only when it clears the level's bar for the time left (higher for
        # a look a defender can still contest than for an open one) and is worth at least what continuing
        # is estimated to be worth (a tie goes to the shot). The bars drop each phase, so a defence that
        # keeps the good looks covered forces a lesser one late. On the last chance there is no bar.
        # The bar reads the look itself, not points already banked this possession (turnovers, the
        # steal-foul bonus). From the level's shoot_by clock on, the best shot goes up whatever it is.
        last = self._last_chance(view)
        banked = RC.STEAL_FOUL_BONUS * view.bonus5 + RC.TURNOVER_POINTS * view.tos
        is_shot = lambda p: any(a.kind == 'shot' for a in p.actions)
        if view.clock <= self.cfg.get('shoot_by', 0) and not last:
            return max(shots, key=lambda vp: vp[0])[1]
        cleared = [(v, p) for v, p in shots if last or raw[p] - banked >= self._bar(view, self._contested(view, p))]
        cv = max(v for v, p in rest)
        if cleared and max(v for v, p in cleared) >= cv - 1e-9:
            sv, sp = max(cleared, key=lambda vp: vp[0])
            if not last and 'settles_early' in self.habits and \
                    raw[sp] - banked < self._bar(view, self._contested(view, sp), early=False):
                self._fire('settles_early')
            best = sp
        elif is_shot(best):
            best = self._pick(rest, True)
        return best

    # -- passing judgement (step 3f) --
    _ALT = {'relocate': 'receiver', 'drive': 'passer', 'dribble': 'passer', 'hesitate': 'passer',
            'screen': 'screen', 'seal': 'screen'}

    def _play_value(self, view, p, node, fn):
        """A play's value. A pass is valued by what the catch gives against the risk after the defence's
        reply (pass_risk); the alternatives this level weighs (moving the receiver, moving the passer or
        dribbling, a screen or seal) are valued with the offence's next turn able to pass, so a cut that
        opens a clean lane is worth that lane. Everything else as before."""
        alts = self.cfg.get('pass_alternatives', [])
        if p.actions and p.actions[-1].kind == 'pass' and not view.inbound:
            v = self._pass_play_value(view, p, follow='two_pass' in alts)
            if v is not None:
                return v
        if self._ALT.get(p.concept) in alts:
            return self._node_value(node, lambda st: self._after_value(st, True))
        return self._node_value(node, fn)

    @staticmethod
    def _banked(s):
        return RC.STEAL_FOUL_BONUS * s.bonus5 + RC.TURNOVER_POINTS * s.tos

    def _pick_off_value(self, pre):
        """Step 3f, section 2: a pass is valued (1 - risk) x the catch - risk x 5. A pick-off counts as the
        -5 alone (scaled by the level's pass_risk_tolerance: 1.0 honest, below 1.0 reckless), on top of
        what is already banked, not as the position it leaves: under OQ-1 the turnover plays on, and that
        position is often worth more to the offence than the catch (the interceptor has left his man and
        spent two tokens), which would make every contested pass nearly free."""
        return self._banked(pre) + RC.TURNOVER_POINTS * self.cfg.get('pass_risk_tolerance', 1.0)

    def _pass_play_value(self, view, p, follow):
        """(1 - risk) x the position after the catch (valued after the defence's reply) + risk x the
        pick-off (see _pick_off_value)."""
        pre = view
        for a in p.actions[:-1]:
            pre = apply(pre, a)
            if isinstance(pre, ChanceNode) or pre.stage != 'play' or pre.side != 'O':
                return None
        a = p.actions[-1]
        info = pass_risk(pre, a.piece, a.target)
        if info is None:
            return None
        caught, lost = pass_outcomes(info)
        cv = self._node_value(caught, lambda st: self._after_value(st, follow))
        if lost is None:
            return cv
        return (1 - info['risk']) * cv + info['risk'] * self._pick_off_value(pre)

    def _after_value(self, st, follow):
        """A position after the offence's play: the defence's best reply (its ball-side plays), then the
        offence's next action; with follow, that next action may be a pass (valued the same way)."""
        from .solver import apply_play
        if isinstance(st, ChanceNode):
            return self._node_value(st, lambda x: self._after_value(x, follow))
        if st.stage != 'play':
            return self.ev(st)[0].ev
        if st.side == 'O':
            return self._o_next(st, follow)
        res = []
        # the defence's full reply set (recovers, switches, contains, combos too): a reply limited to the
        # ball side would never cover the teammate the next pass goes to, and overrate every alternative
        for q in self._with_end(st, legal_actions(st), self.gen.plays(st, False, light=False)):
            n = apply_play(st, q)
            if n is not None:
                res.append(self._node_value(n, lambda x: self._o_next(x, follow) if (
                    not isinstance(x, ChanceNode) and x.stage == 'play' and x.side == 'O') else self.ev(x)[0].ev))
        return min(res) if res else self._o_next(st, follow)

    def _o_next(self, s, follow):
        """The offence to act: its best action now (the evaluation), or with follow a pass to any
        teammate, judged after the defence's reply like the first one (the extra pass costs a turn: the
        defence answers it before the catch is valued)."""
        v = self.ev(s)[0].ev
        if not follow or s.pending or s.inbound or s.tok_o < 1:
            return v
        memo = self.__dict__.setdefault('_next_memo', {})
        if s in memo and memo[s][0] is s.ctx:
            return memo[s][1]
        budget_x = reaction_budget(s)
        reply = lambda t: self.ev._reply(t)[0].ev if (not isinstance(t, ChanceNode) and t.stage == 'play'
                                                      and t.side == 'X') else self.ev(t)[0].ev
        best = v
        for r in range(5):
            if r == s.ball or not B.on_board(s.o[r]):
                continue
            if self.ev.carrier_look(s, r, budget_x, True)[0] + RC.STEAL_FOUL_BONUS * s.bonus5 \
                    + RC.TURNOVER_POINTS * s.tos <= best:
                continue                       # even an open catch there can't beat what it has
            info = pass_risk(s, s.ball, r)
            if info is None:
                continue
            caught, lost = pass_outcomes(info)
            cv = self._node_value(caught, reply)
            if lost is not None:
                cv = (1 - info['risk']) * cv + info['risk'] * self._pick_off_value(s)
            best = max(best, cv)
        if len(memo) > 20000:
            memo.clear()
        memo[s] = (s.ctx, best)
        return best

    def _contested(self, view, play):
        """Could a defender still contest this shot after the reaction (as this level reads the reaction)?"""
        from .solver import apply_play
        node = apply_play(view, play)
        if node is None or isinstance(node, ChanceNode) or node.stage not in ('reaction', 'contest') or not node.shot:
            return False
        budget = reaction_budget(node) if node.stage == 'reaction' and self.cfg['concepts'].get('reaction', True) else 0
        return any(e['contest'] > 0 for e in reachable_contest(node, node.ball, node.shot, budget))

    def _chances(self, view):
        """Clock left in seconds (a phase is two; its tokens reset each phase)."""
        return view.clock

    def _last_chance(self, view):
        return self._chances(view) <= RC.PHASE_SECONDS

    def _bar(self, view, contested, early=True):
        """The shot bar for the time left: 'open' for a look nobody can contest, 'contested' otherwise.
        The habit settles_early reads the bar one phase ahead."""
        t = self._chances(view)
        if early and 'settles_early' in self.habits and t > RC.PHASE_SECONDS:
            t -= RC.PHASE_SECONDS
        curve = {int(k): v for k, v in self.cfg['patience']['contested' if contested else 'open'].items()}
        below = [k for k in sorted(curve) if k <= t]
        return curve[below[-1]] if below else 0

    def _patient(self, view, play, shot_value):
        """For the solver-search path: the shot clears the bar, or it's the last chance."""
        if not any(a.kind == 'shot' for a in play.actions) or shot_value is None or self._last_chance(view):
            return True
        banked = RC.STEAL_FOUL_BONUS * view.bonus5 + RC.TURNOVER_POINTS * view.tos
        return shot_value - banked >= self._bar(view, self._contested(view, play))

    @staticmethod
    def _plan_kind(view, targets):
        """The plan, named once from the primary target (it changes only when the plan does): the carrier
        is the target (isolation), a post-up target (post feed), a rim target off the ball (cut to the
        rim), or a jump-shooter off the ball (swing to the shooter)."""
        if not targets:
            return None
        t = targets[0]
        if t['o'] == view.ball:
            return 'isolation'
        return {'post': 'post feed', 'layup': 'cut to the rim', 'dunk': 'cut to the rim',
                'floater': 'cut to the rim'}.get(t['shot'], 'swing to the shooter')


def make(side, level, seed=0, **kw):
    return Computer(side, level, seed, **kw)


# ---- setup and placement (section 5) -------------------------------------------------------------

def _next_to(o_sq, taken):
    """The empty square next to an attacker that is closest to the rim (ties: compass order)."""
    cands = [B.add(o_sq, d) for d in B.DIRS]
    cands = [q for q in cands if B.on_board(q) and q not in taken]
    return min(cands, key=lambda q: (B.dist_rim(q), cands.index(q))) if cands else None


def place_defence(comp, o_squares, ball, build, budget_s=None):
    """The computer's defensive setup.
    1. Match up by number, unless a switch puts the best on-ball defender (Agility) on the most explosive
       creator (Quick Step, then Dribble), or the best three-point contester on the ▲ shooter, and the
       evaluation says the switch is worth it.
    2. Each defender starts next to their man; the on-ball defender's arrow is on the carrier unless
       walling the carrier's best drive is worth more.
    3. Everyone else: square (next to their man, or sagging up to two squares off) and arrow (their man,
       the ball, or the rim) chosen by the same evaluation as in play: help gain against leave cost,
       with the level's concepts and comfort line.
    build(x_squares, arrows) -> the starting GameState. Returns (x_squares, arrows, matchup)."""
    stop = time.time() + (budget_s if budget_s is not None else max(1.0, 2 * (comp.budget_s or 1.0)))
    o_squares = [tuple(q) for q in o_squares]
    probe = build(*_assign(o_squares, list(range(5))))
    comp._context(probe)
    ctx = comp.seen
    c = comp.cfg['concepts']

    def value(xs, arrows):
        s = build(xs, arrows)
        comp._context(s)
        v = comp._immediate(s) if comp.cfg['lookahead'] == 0 else comp.ev(s.with_(ctx=comp.seen))[0].ev
        return max(v, comp.comfort) + 1e-3 * v if (comp.comfort is not None and c.get('help', True)) else v

    perm = list(range(5))
    creator = max(range(5), key=lambda i: (ctx.off[i].qs, ctx.off[i].r['dribble'], -i))
    stopper = max(range(5), key=lambda j: (ctx.dfn[j].r['agility'], -j))
    shooters = [i for i in range(5) if ctx.off[i].bands['shot_three'] == 'H']
    closer = max(range(5), key=lambda j: (ctx.dfn[j].r['con_three'], -j))
    best_perm, best_v = perm, value(*_assign(o_squares, perm))
    for man, d in [(creator, stopper)] + [(i, closer) for i in shooters[:1]]:
        if perm[d] == man:
            continue
        trial = list(best_perm)
        k = trial.index(man)
        trial[d], trial[k] = trial[k], trial[d]
        v = value(*_assign(o_squares, trial))
        if v < best_v - 0.25:
            best_perm, best_v = trial, v
    xs, arrows = _assign(o_squares, best_perm)
    cp = o_squares[ball]
    # the on-ball defender: on the carrier, or a wall
    jb = best_perm.index(ball)
    if c.get('walls', True):
        for d in range(8):
            if time.time() > stop:
                break
            a2 = arrows[:jb] + [d] + arrows[jb + 1:]
            v = value(xs, a2)
            if v < best_v - 1e-9:
                best_v, arrows = v, a2
    # everyone else
    for j in range(5):
        if j == jb or time.time() > stop:
            continue
        man = o_squares[best_perm[j]]
        squares = [xs[j]]
        if c.get('help', True):
            taken = set(o_squares) | {q for k, q in enumerate(xs) if k != j}
            for dx in range(-2, 3):
                for dy in range(-2, 3):
                    q = (man[0] + dx, man[1] + dy)
                    if B.on_board(q) and q not in taken and q not in squares and B.dist_rim(q) <= B.dist_rim(man) + 1:
                        squares.append(q)
        for q in squares:
            if time.time() > stop:
                break
            faces = {B.nearest_dir(q, man)}
            if c.get('lanes', True):
                faces |= {B.nearest_dir(q, cp), B.nearest_dir(q, RC.RIM)}
            if 'ball_watcher' in comp.habits:
                faces = {B.nearest_dir(q, cp)}
            for d in faces:
                xs2 = xs[:j] + [q] + xs[j + 1:]
                a2 = arrows[:j] + [d] + arrows[j + 1:]
                try:
                    v = value(xs2, a2)
                except Exception:
                    continue
                if v < best_v - 1e-9:
                    best_v, xs, arrows = v, xs2, a2
    return xs, arrows, best_perm


def _assign(o_squares, perm):
    """Defender j next to attacker perm[j] (closest to the rim), arrow on that attacker."""
    taken = set(o_squares)
    xs, arrows = [None] * 5, [None] * 5
    for j in sorted(range(5), key=lambda j: perm[j]):
        o = o_squares[perm[j]]
        q = _next_to(o, taken)
        taken.add(q)
        xs[j] = q
        arrows[j] = B.dir_between(q, o)
    return xs, arrows
