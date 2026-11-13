"""Step 3m B6: search. Whole turns (one or two actions) are the units; the two sides alternate (alpha-beta, the offence
maximising the possession's expected value, the defence minimising it), rolls are chance nodes (Star2: Star1 bounds
with a probing pass), iterative deepening under a deadline, a Zobrist-keyed transposition table (chance nodes
included), killer and history heuristics, no random rollouts. Leaves are scored by decide.Read.leaf().

Turns are generated from geometry: every legal action is a candidate; the ones worth searching are kept by the change
they make to THREAT and COVERAGE (the leaf value after the action) and the dilemmas they create, a beam of 8 to 24
turns. Labels (B7) never change a candidate's value.
"""
import random
import time

from . import board as B
from . import rules_config as RC
from .actions import Action, legal_actions, MOVEMENT
from .resolve import apply, ChanceNode
from .scoring import score
from .decide import Read, CONFIG, foul_externality

VMIN, VMAX = CONFIG['eval']['value_bounds']
FORCING = ('shot', 'contest', 'steal', 'end_turn', 'intercept', 'pause', 'hesitate')


PARTS = ('quiet_points', 'like_with_like', 'tempo', 'play_on', 'clear_reason')


def stable_cfg():
    """Step 12: the stable-search switches and their measured numbers (ai_profiles.json 'search')."""
    return CONFIG.get('search', {})


def stable_parts():
    """Step 13: the stable search's five parts, each its own switch (off by default); search.stable is the shorthand
    that turns on all five."""
    cfg = stable_cfg()
    every = cfg.get('stable') is True
    return {k: every or cfg.get(k) is True for k in PARTS}


def phase_of(s):
    return str(min(6, max(1, (RC.START_CLOCK - s.clock) // RC.PHASE_SECONDS + 1)))


def mid_turn(s):
    """A side between its two actions: not a completed team turn."""
    return s.stage == 'play' and s.turn_n > 0 and not s.pending


class Timeout(Exception):
    pass


# Step 13: the speed-ups that change no result (a tool may turn one off, to time it and to prove the same choices and
# values with and without it). tt_order: a position's best turn from the look-ahead one shorter is tried first.
SPEED = {'tt_order': True}


# ---- Zobrist keys -----------------------------------------------------------------------------------------------------
_ZR = random.Random(20261108)
_ZPIECE = {(side, i, x, y): _ZR.getrandbits(64) for side in 'OX' for i in range(5)
           for x in range(-1, B.W + 1) for y in range(0, B.H + 2)}
_ZARROW = {(i, a): _ZR.getrandbits(64) for i in range(5) for a in range(8)}
_ZBALL = [_ZR.getrandbits(64) for _ in range(5)]


def zobrist(s):
    """The position's Zobrist key: XOR of a random word per (piece, square), per (defender, arrow) and for the ball,
    combined with the rest of the state (clock, counters, stage) so equal keys mean equal states."""
    h = _ZBALL[s.ball]
    for i, p in enumerate(s.o):
        h ^= _ZPIECE[('O', i, p[0], p[1])]
    for i, p in enumerate(s.x):
        h ^= _ZPIECE[('X', i, p[0], p[1])] ^ _ZARROW[(i, s.arrows[i])]
    rest = (s.stage, s.side, s.clock, s.tok_o, s.tok_x, s.moved_o, s.moved_x, s.cnt, s.turn_n, s.final, s.lock_o,
            s.lock_x, s.screens, s.pending, s.shot, s.prev_wait, s.beaten, s.fouls, s.bonus5, s.tos, s.qs_o, s.qs_x,
            s.phase, s.inbound, s.target, s.approach, s.turn_lead, s.turn_x, s.react_moved, s.forced, s.result,
            s.rush_o, s.rush_x, s.key_o, s.grd)
    return h ^ (hash(rest) & 0xFFFFFFFFFFFFFFFF)


# ---- who acts --------------------------------------------------------------------------------------------------------

def actor(s):
    """'O' or 'X': the side making the next decision."""
    if s.stage in ('target', 'pick', 'forced'):
        return 'O'
    if s.stage in ('reaction', 'contest'):
        return 'X'
    return s.side


def terminal_value(s):
    from .decide import foul_externality
    return float(score(s).total) + foul_externality(s)      # step 3n F4: the quarter's price of the fouls


# ---- turn generation (B6) --------------------------------------------------------------------------------------------

def _wait(acts):
    for k in ('hesitate', 'pause', 'end_turn', 'forfeit'):
        for a in acts:
            if a.kind == k:
                return a
    return None


def candidate_actions(s, read=None, per_player=3):
    """The legal actions worth trying as the next action, from geometry: every shot, pass, dribble, steal, intercept
    and challenge; movement to the squares that matter (each attacker's best looks, the carrier's drives, each
    defender's top responses and the best cover); a few screens; one wait. Every one is legal (taken from
    legal_actions)."""
    acts = legal_actions(s)
    side = actor(s)
    if s.stage in ('contest', 'forced', 'target', 'pick') or len(acts) <= 12:
        return acts
    keep, seen = [], set()

    def add(a):
        if a not in seen:
            seen.add(a)
            keep.append(a)
    for a in acts:
        if a.kind in ('shot', 'pass', 'dribble', 'steal', 'intercept', 'challenge', 'forced_shot', 'contest'):
            add(a)
    w = _wait(acts)
    if w:
        add(w)
    read = read or Read(s)
    moves = [a for a in acts if a.kind in ('move', 'qs', 'sprint')]
    if side == 'O':
        want = {}
        for i, lks in read.looks.items():
            want[i] = [lk.c for lk in lks[:per_player]]
        for a in moves:
            if a.dest in want.get(a.piece, ()):
                add(a)
        # each attacker's move that most raises the best look of a teammate (spacing, dragging a defender) is found
        # by the ordering pass; here a few of his moves that change who blocks whom: away from the carrier's lane
        bp = s.o[s.ball]
        for i in range(5):
            if i == s.ball:
                continue
            mine = [a for a in moves if a.piece == i and a.kind == 'move']
            mine.sort(key=lambda a: (-B.cheb(a.dest, bp), a.dest))
            for a in mine[:1]:
                add(a)
        scr = [a for a in acts if a.kind == 'screen']
        scr.sort(key=lambda a: min(B.cheb(B.add(s.o[a.piece], B.DIRS[a.target]), xp) for xp in s.x))
        for a in scr[:4]:
            add(a)
    else:
        if s.stage == 'reaction' and s.ctx.rules.contest_action:
            # D-18: the closeouts: every movement that ends next to the shooter (a Move facing him), so a Contest can follow
            sp = s.o[s.ball]
            for a in moves:
                if B.adjacent(a.dest, sp) and (a.kind != 'move' or a.arrow == B.dir_between(a.dest, sp)):
                    add(a)
        cv = read.cover()
        targets = {}
        for j, resp in cv['choice'].items():
            targets.setdefault(j, []).append(resp)
        for j, rs in cv['R'].items():
            for resp, _ in rs[1:per_player + 1]:
                targets.setdefault(j, []).append(resp)
        for a in moves:
            for (q, arrow, used) in targets.get(a.piece, []):
                if a.dest == q and (a.kind != 'move' or a.arrow == arrow):
                    add(a)
        # every defender keeps at least one movement: the one nearest the offence's best look (ordering only)
        spots = [lk.c for lks in read.looks.values() for lk in lks[:1]] or [s.o[s.ball]]
        for j in range(5):
            mine = [a for a in moves if a.piece == j]
            if mine and not any(a.piece == j for a in keep if a.kind in ('move', 'qs', 'sprint')):
                mine.sort(key=lambda a: (min(B.cheb(a.dest, c) for c in spots), a.kind != 'move', a.dest, a.arrow))
                add(mine[0])
    if not keep:
        return acts
    return keep


def _step(s, a):
    """Apply one action; returns the state or ChanceNode."""
    return apply(s, a)


# ---- step 18e (search.open_list, D-156) --------------------------------------------------------------------------------
# The list of turns without the hand-written choice of which actions to consider (candidate_actions): every legal
# action is read, and only the reading decides what goes forward. No kind of action is named, kept or preferred.
# The defence in open play: reading every legal action in full costs too much (about 1,000 actions a position), so
#   1. every legal first action gets a cheap read: the looks of the position the turn leaves when it ends, with every
#      piece where it stands (resolve.null_step, twice when the turn has two actions), re-read with that one defender
#      where the action leaves him (Read.reread), and the quick reading taken from them. An action that leaves every
#      piece where it stands, goes to the dice or keeps a pass in the air has no such re-read and is read in full at
#      once;
#   2. every pair of those actions by two defenders is read the same way, each attacker's best look being the lower of
#      the two re-reads (the rule the reading's own cover uses). A second action is only read as part of a turn if the
#      reading says it changes something;
#   3. after each of the best `follow` first actions, every other legal second action is read: the same defender
#      moving again by a re-read where it leaves him; anything that goes to the dice by its chances, a possession that
#      ends at its own value and one that plays on at the first action's reading;
#   4. actions the cheap read can't tell apart are one candidate (the first in the rules' order);
#   5. the best `full` candidates by the cheap read are read in full (the ordering reading every turn gets today), and
#      the best `beam` of those are the list.
# Elsewhere (a declared shot's reaction, and the offence under 'both'): every legal action is read in full.

def open_mode(profile=None):
    """The switch: search.open_list (False, 'defence' or 'both') when it is set; when it is None, the level's own
    setting (profiles.<level>.open_list). The All-Star plays 'defence' by default (step 18e)."""
    g = CONFIG.get('search', {}).get('open_list')
    return ((profile or {}).get('open_list') or False) if g is None else g


def open_width(profile=None):
    """How many turns a level reads in full, and how many first actions it follows (step 18f, D-157: the levels think
    the same way and differ in how well they choose): the level's own open_full and open_follow, or the config's."""
    cfg, p = CONFIG.get('search', {}), profile or {}
    full = p.get('open_full', cfg.get('open_full'))
    follow = p.get('open_follow', cfg.get('open_follow'))
    return (8 if full is None else full, 4 if follow is None else follow)


def open_on(side, mode=None):
    v = open_mode() if mode is None else mode
    return v is True or v == 'both' or (v == 'defence' and side == 'X')


def _r6(x):
    return round(x, 6)


def _banked(s):
    return (RC.STEAL_FOUL_BONUS * s.bonus5 + (0 if s.ctx.rules.digital else RC.TURNOVER_POINTS * s.tos)
            + foul_externality(s))


def _ends_turn(s, nxt, side):
    return isinstance(nxt, ChanceNode) or nxt.stage == 'over' or actor(nxt) != side or nxt.stage != s.stage


# ---- step 18f (search.whole_turns) -------------------------------------------------------------------------------------
# A one-action turn is valued as the turn ended there: the side's own End turn is played, so the other side has the
# reply the rules give it before the position is judged. (The computer plays one action and then decides again, so
# "this action, then stop" is what the turn is worth at least.)

def whole_on():
    return CONFIG.get('search', {}).get('whole_turns') is True


def in_hand_on():
    """search.rank_in_hand (step 18f, off): with whole turns, a turn's first actions are ranked, and the ones to follow
    with a second action chosen, by the reading with the second action still in hand (as before whole turns); the
    search still values a one-action turn as the turn ended."""
    return CONFIG.get('search', {}).get('rank_in_hand') is True


def ended_turn(s, n):
    """n: the node a turn from s leads to; the same with a one-action turn ended."""
    if isinstance(n, ChanceNode) or s.stage != 'play' or n.stage != 'play' or n.pending or n.turn_n == 0:
        return n
    side = actor(s)
    if actor(n) != side:
        return n
    return apply(n, Action('end_turn', side))


def open_turns_x(s, beam, evaluate, deadline, expand, whole=False, width=None):
    from .resolve import null_step
    from .decide import _caps
    acts = legal_actions(s)
    if len(acts) <= 12:
        return None
    ref1 = null_step(s)
    if isinstance(ref1, ChanceNode) or ref1.stage != 'play':
        return None
    two = not _ends_turn(s, ref1, 'X')
    ref2 = null_step(ref1) if two else None
    if two and (isinstance(ref2, ChanceNode) or ref2.stage != 'play'):
        return None
    cfg = CONFIG.get('search', {})
    nexp = expand if expand is not None else max(3, beam // 3)
    full_n, follow_n = width or open_width()
    K = beam + nexp * full_n
    F = nexp * follow_n
    # one read to re-read from: the position the turn leaves when it ends (two actions on, or one if that ends it)
    ref = ref2 if two else ref1
    R = Read(ref)
    att = R.att_o
    b2 = _banked(ref)

    def q_of(vec):
        return R._quick_cont(R._cont_of(vec), vec[5], vec[6], vec)

    def facts(n, j, left):
        cm, ql = _caps(left, 'X', j)
        return R.reread(j, n.x[j], n.arrows[j], cm, ql, (left.rushed('X', j), left.moved('X', j)))

    def raw_of(vec):
        # what the quick reading is taken from, before the phase table's floor and the map flatten it
        return _r6(max(vec[5], vec[6], R._cont_of(vec)))

    def tie_of(vec):
        return _r6(sum(vec[i] for i in att))

    def key_of(c, vec):
        return (c, _r6(vec[5]), _r6(vec[6])) + tuple(_r6(vec[i]) for i in att)

    def check():
        if deadline and time.time() > deadline:
            raise Timeout

    fresh = ref.phase != s.phase
    full, U, seen = [], [], set()
    # 1. every legal first action
    for a in acts:
        check()
        nxt = apply(s, a)
        if isinstance(nxt, ChanceNode) or nxt.stage != 'play' or nxt.pending or a.dest is None:
            full.append((-evaluate(ended_turn(s, nxt) if whole else nxt), (a,)))
            continue
        v2 = facts(nxt, a.piece, ref if fresh else nxt)
        q2 = q_of(v2)
        c = _r6(q2)
        u = dict(turn=(a,), j=a.piece, c=c, raw=raw_of(v2), tie=tie_of(v2), key=key_of(c, v2), v2=v2, q2=q2)
        if u['key'] in seen:
            continue
        seen.add(u['key'])
        U.append(u)
    by_cheap = lambda u: (u['c'], u['raw'], u['tie'], len(u['turn']), u['n'])
    for n, u in enumerate(U):
        u['n'] = n
    U.sort(key=by_cheap)
    C = list(U)
    n = len(U)
    if two:
        # 2. every pair of them by two defenders
        idx = list(att) + [5, 6]
        for x, ua in enumerate(U):
            check()
            for ub in U[x + 1:]:
                if ub['j'] == ua['j']:
                    continue
                lt = gt = False
                m = [0.0] * 7
                va_, vb_ = ua['v2'], ub['v2']
                for i in idx:
                    va, vb = va_[i], vb_[i]
                    if vb < va:
                        lt = True
                        m[i] = vb
                    else:
                        if va < vb:
                            gt = True
                        m[i] = va
                if not (lt and gt):
                    continue
                c = _r6(q_of(m))
                C.append(dict(turn=(ua['turn'][0], ub['turn'][0]), j=-1, c=c, raw=raw_of(m), tie=tie_of(m), key=key_of(c, m) + ('p',),
                              pair=True, n=n))
                n += 1

        # 3. after the best first actions: the same defender again, and whatever goes to the dice
        def cheap_node(nd, u):
            if isinstance(nd, ChanceNode):
                return sum(float(p) * cheap_node(sub, u) for p, _, sub in nd.outcomes)
            if nd.stage == 'over':
                return terminal_value(nd)
            return u['q2'] + _banked(nd) - b2

        followed = 0
        for ua in U:
            if followed >= F:
                break
            check()
            followed += 1
            a = ua['turn'][0]
            nxt = apply(s, a)
            for b in legal_actions(nxt):
                if b.kind in ('end_turn', 'forfeit'):
                    continue
                if b.dest is not None and b.piece != ua['j']:
                    continue                             # two defenders moving: read with the pairs above
                n2 = apply(nxt, b)
                if not isinstance(n2, ChanceNode) and n2.stage == 'play' and not n2.pending and b.dest is not None:
                    v = facts(n2, ua['j'], n2)
                    c = _r6(q_of(v))
                    C.append(dict(turn=(a, b), j=ua['j'], c=c, raw=raw_of(v), tie=tie_of(v), key=key_of(c, v) + ('s', ua['j']), n=n))
                else:
                    c = _r6(cheap_node(n2, ua))
                    C.append(dict(turn=(a, b), j=ua['j'], c=c, raw=raw_of(ua['v2']), tie=tie_of(ua['v2']), key=key_of(c, ua['v2']) + ('d', b), n=n))
                n += 1
    # 4, 5. one candidate for each distinct read; the best by the cheap read are read in full
    C.sort(key=by_cheap)
    legal_after, seen_c = {}, set()

    def ids_after(a):
        r = legal_after.get(a)
        if r is None:
            nx = apply(s, a)
            r = legal_after[a] = set() if isinstance(nx, ChanceNode) else set(legal_actions(nx))
        return r

    done = 0
    for u in C:
        if done >= K:
            break
        check()
        turn = u['turn']
        if len(turn) == 2:
            if u['key'] in seen_c:
                continue
            if u.get('pair') and turn[1] not in ids_after(turn[0]):
                if turn[0] not in ids_after(turn[1]):
                    continue
                turn = (turn[1], turn[0])
            seen_c.add(u['key'])
        nd = play_turn(s, turn)
        full.append((-evaluate(ended_turn(s, nd) if whole else nd), turn))
        done += 1
    full.sort(key=lambda r: -r[0])
    seen_t, final = set(), []
    for v, t in full:
        key = frozenset(t) if len(t) == 2 and all(x.kind in ('move', 'qs', 'sprint') for x in t) else t
        if key in seen_t:
            continue
        seen_t.add(key)
        final.append((v, t))
        if len(final) >= beam:
            break
    return final


def turns(s, beam, read=None, evaluate=None, deadline=None, expand=None, second=2, mode=None, whole=False, width=None):
    """The candidate whole turns from s (lists of 1 or 2 actions), ordered by the value after the turn's
    deterministic part (the side's own point of view), at most `beam`. A turn ends at a turn-ender, a roll, the
    side's second action or a change of side."""
    side = actor(s)
    sign = 1 if side == 'O' else -1
    open_ = open_on(side, mode) and evaluate is not None        # mode: the level's open list (open_mode)
    in_hand = in_hand_on()                                      # step 18f (search.rank_in_hand)
    if open_ and side == 'X' and s.stage == 'play':
        r = open_turns_x(s, beam, evaluate, deadline, expand, whole, width)
        if r is not None:
            return r
    first = legal_actions(s) if open_ else candidate_actions(s, read)
    scored = []
    for a in first:
        if deadline and time.time() > deadline:
            raise Timeout
        nxt = _step(s, a)
        if isinstance(nxt, ChanceNode) or nxt.stage == 'over' or actor(nxt) != side or nxt.stage != s.stage:
            v = evaluate(nxt) if evaluate else 0.0
            scored.append((sign * v, (a,)))
            continue
        v = evaluate(ended_turn(s, nxt) if whole and not in_hand else nxt) if evaluate else 0.0
        scored.append((sign * v, (a,)))
        if len(scored) > 4 * beam:
            continue
    scored.sort(key=lambda r: -r[0])
    out = list(scored[:beam])
    # second actions after the best non-ending first actions
    for _, t in scored[:(expand if expand is not None else max(3, beam // 3))]:
        a = t[0]
        nxt = _step(s, a)
        if isinstance(nxt, ChanceNode) or nxt.stage == 'over' or actor(nxt) != side or nxt.stage != s.stage:
            continue
        for b in (legal_actions(nxt) if open_ else candidate_actions(nxt, None, per_player=second)):
            if deadline and time.time() > deadline:
                raise Timeout
            if b.kind in ('end_turn', 'forfeit'):
                continue
            n2 = _step(nxt, b)
            v = evaluate(n2) if evaluate else 0.0
            out.append((sign * v, (a, b)))
    out.sort(key=lambda r: -r[0])
    seen, final = set(), []
    for v, t in out:
        key = frozenset(t) if len(t) == 2 and all(x.kind in ('move', 'qs', 'sprint') for x in t) else t
        if key in seen:
            continue
        seen.add(key)
        final.append((v, t))
        if len(final) >= beam:
            break
    return final


def play_turn(s, t):
    """Apply a turn's actions; a roll mid-turn stops it (the rest of the turn is decided after the roll)."""
    node = s
    for a in t:
        if isinstance(node, ChanceNode) or node.stage == 'over':
            break
        if a not in legal_actions(node):
            break
        node = _step(node, a)
    return node


# ---- the searcher ------------------------------------------------------------------------------------------------------

class Searcher:
    """Expectimax alpha-beta over whole turns with Star2 at chance nodes. me: the side whose decision this is;
    opp_weight: the opponent model (1.0 = the opponent's best reply; 0 = a passive opponent; between: the mix).
    evaluate(s): the leaf value (offence's view)."""

    def __init__(self, me, profile, evaluate, deadline, rng=None):
        self.me = me
        self.p = profile
        self.evaluate = evaluate
        self.deadline = deadline
        self.tt = {}
        self.tcache = {}
        self.killers = {}
        self.history = {}
        self.nodes = 0
        self.leaves = 0
        self.rng = rng or random.Random(0)
        self.lam = profile['opponent_model']
        self.habit = None                # All-Star scouting: the human's most frequent first action by stage
        self.habit_weight = 0.0
        cfg = stable_cfg()
        on = stable_parts()                                  # step 13: the stable search's five switches (all off)
        self.quiet = on['quiet_points']                      # judge only after a complete team turn
        self.like = on['like_with_like']                     # the answer from the deepest even depth
        self.tempo_on = on['tempo']                          # the measured tempo term
        self.play_on = on['play_on']                         # extend while something is pending
        self.clear = on['clear_reason']                      # keep the earlier choice unless beaten by the margin
        self.stable = any(on.values())
        self.ext_cap = int(cfg.get('extension_cap', 2))
        self.margin = cfg.get('stable_margin', {})
        self.tempo = cfg.get('tempo_gap', {})
        self.extensions = 0
        self.cap_hits = 0
        self.trace = []                  # the root choice at each completed depth: [(depth, turn, value)]
        self.kept = 0                    # times 'change only for a clear reason' kept the earlier choice
        # step 16, stage 4 (search.goals, off; needs eval.advantages): goals order the search, and a position gains its
        # goal potential (decide.Read.phi; 0 when the possession ends)
        self.goals = cfg.get('goals') is True and CONFIG['eval'].get('advantages') is True
        self.phis = {}
        self.touches = {}
        self.depth_seconds = []          # step 13: the time each completed depth was reached at: [(depth, seconds)]
        # step 18b (eval.settle_shots, off): a declared shot at the horizon is valued by playing the reaction out
        self.settle_shots = CONFIG['eval'].get('settle_shots') is True
        self.scache = {}
        # step 18c (eval.help_readings, off): with the offence to act, a position is worth at least the best shot it
        # can release this turn, settled by the rules (the floor)
        self.help = CONFIG['eval'].get('help_readings') is True
        self.open = open_mode(profile)                # step 18e (search.open_list, or the level's own)
        self.whole = whole_on()                       # step 18f (search.whole_turns)
        self.split = CONFIG.get('search', {}).get('split_ties') is True      # step 18f (search.split_ties)
        self.spread = {}                              # a reply node's values, best first
        self.width = open_width(profile)              # step 18f: how many turns this level reads in full
        self.fcache = {}
        self.t0 = time.time()

    def check(self):
        if time.time() > self.deadline:
            raise Timeout

    def leaf(self, s):
        self.leaves += 1
        if self.settle_shots and not isinstance(s, ChanceNode) and s.stage != 'play' and s.stage != 'over':
            return self.settled(s)
        v = self.evaluate(s)
        if self.help and not isinstance(s, ChanceNode) and s.stage == 'play' and not s.pending and actor(s) == 'O':
            v = self.floor(s, v)                         # step 18c: never below the shot the offence can take now
        if self.tempo_on and self.tempo and not isinstance(s, ChanceNode) and s.stage == 'play':
            # the measured tempo term: the same position reads higher with the offence to act; a leaf is read as the
            # mean of the two (the gap measured on the step 3n positions, ai_profiles.json search.tempo_gap)
            t = float(self.tempo.get(phase_of(s), 0.0))
            v += -t / 2 if actor(s) == 'O' else t / 2
        if self.goals:
            v += self.phi(s)                 # progress: the potential here (the root's is taken off at the end)
        return v

    def floor(self, s, v):
        """Step 18c, the first help reading: the drive priced by the rules. With the offence to act in open play, the
        possession is worth at least the best shot the ball handler can release this turn: his shot from where he
        stands, or after one movement, each settled by the rules (the defence's best reaction, self.settled). The
        reading names the candidates (its looks released now, best first) and the rules value them; a candidate whose
        reading is no better than the value so far can't raise it. Returns the larger of v (the reading) and that
        shot's value; self.fcache keeps (value, square, shot type) for the reasons record."""
        key = zobrist(s)
        hit = self.fcache.get(key)
        if hit is not None:
            return hit[0]
        banked = RC.STEAL_FOUL_BONUS * s.bonus5 + (0 if s.ctx.rules.digital else RC.TURNOVER_POINTS * s.tos)
        banked += foul_externality(s)
        best = (v, None, None)
        acts = None
        for lk in Read(s).looks.get(s.ball, []):
            if not lk.now:
                continue
            if banked + lk.base <= best[0]:
                break
            n = s
            if lk.route != 'shoot':
                if acts is None:
                    acts = legal_actions(s)
                a = next((x for x in acts if x.kind in MOVEMENT and x.piece == s.ball and x.dest == lk.c), None)
                if a is None:
                    continue
                n = apply(s, a)
                if isinstance(n, ChanceNode) or n.stage != 'play' or actor(n) != 'O':
                    continue
            for b in legal_actions(n):
                if b.kind == 'shot':
                    w = self.settle_node(apply(n, b))
                    if w > best[0]:
                        best = (w, lk.c, b.shot)
        self.fcache[key] = best
        return best[0]

    def settled(self, s):
        """Step 18b: a position with a shot declared (the reaction, the Contest choice, a forced shot's choice), valued
        by the rules themselves: the side to act takes its best legal action, and so on until the possession ends or
        open play resumes (after a steal at the table), with the dice at their chances. In the reaction a movement
        that doesn't end next to the shooter can't change the Contest or a Steal (the reaction is at most two actions
        and those are its last), so only movements ending next to him are played, and after a movement only a
        Contest, a Steal or ending the reaction. No number is set by hand."""
        key = zobrist(s)
        v = self.scache.get(key)
        if v is not None:
            return v
        side = actor(s)
        acts = legal_actions(s)
        if s.stage == 'reaction':
            if s.turn_n >= 1:        # after a movement: only a Contest, a Steal or ending the reaction counts
                acts = [a for a in acts if a.kind not in MOVEMENT]
            else:
                sp = s.o[s.ball]
                acts = [a for a in acts if a.kind not in MOVEMENT or B.adjacent(a.dest, sp)]
        best = None
        for a in acts:
            w = self.settle_node(apply(s, a))
            if best is None or (w > best if side == 'O' else w < best):
                best = w
        v = self.evaluate(s) if best is None else best
        self.scache[key] = v
        return v

    def settle_node(self, n):
        if isinstance(n, ChanceNode):
            return sum(float(p) * self.settle_node(sub) for p, _, sub in n.outcomes)
        if n.stage == 'over':
            return terminal_value(n)
        if n.stage == 'play':
            return self.leaf(n)
        return self.settled(n)

    def phi(self, s):
        """The goal potential of a position (the offence's view): 0 unless play goes on; a pass in the air carries the
        catch's potential by its chance."""
        if isinstance(s, ChanceNode) or s.stage != 'play':
            return 0.0
        z = zobrist(s)
        v = self.phis.get(z)
        if v is None:
            if s.pending:
                from .decide import _lane_p
                passer, recv = s.pending
                v = _lane_p(s.with_(ball=passer), recv, s.o[recv]) * self.phi(s.with_(ball=recv, pending=None))
            else:
                v = Read(s).phi()
            self.phis[z] = v
        return v

    def touch(self, s, z):
        """The top goals at a position, as (attacker, square): for the ordering only."""
        g = self.touches.get(z)
        if g is None:
            g = []
            if s.stage == 'play' and not s.pending:
                top = {}
                for a in Read(s).advantages():
                    if a['sq'] is not None and a['worth'] > 1e-9 and a['worth'] > top.get(a['i'], (0.0,))[0]:
                        top[a['i']] = (a['worth'], a['sq'])
                g = [(i, top[i][1]) for i in sorted(top)]
            self.touches[z] = g
        return g

    def unsettled(self, s):
        """Why this position isn't a quiet point (None if it is). 'mid' belongs to quiet_points; the rest to play_on."""
        if s.stage != 'play':
            return 'stage' if self.play_on else None  # a declared shot's reaction, a contest choice, a forced shot
        if s.pending:
            return 'pass' if self.play_on else None   # a pass's dice still to come
        if mid_turn(s):
            if self.quiet:
                return 'mid'                          # between a side's two actions
        if self.play_on and actor(s) == 'O':
            r = Read(s, k=0, looks_per=3)
            sn = r.shot_now()
            if sn is not None and sn > r.possession() + 1e-9:
                return 'shot'                         # a shot now worth more than the possession
        return None

    def extend(self, s, why, depth, alpha, beta):
        """Play on with only the forcing replies until quiet (at most ext_cap extra team turns)."""
        side = actor(s)
        acts = legal_actions(s)
        if why == 'mid':
            ts = self.turns_of(s)                     # the side completes its turn
            turns_ = [t for _, t in ts]
        else:
            kinds = ('shot',) if why == 'shot' else FORCING
            turns_ = [(a,) for a in acts if a.kind in kinds or why == 'stage' and s.stage != 'reaction']
        if not turns_:
            return self.leaf(s)
        self.extensions += 1
        best = None
        if why == 'shot':
            best = Read(s).possession()             # the offence may also not shoot: what the possession is worth
        for t in turns_:
            child = play_turn(s, t)
            d = depth if why == 'mid' or (self.quiet and not isinstance(child, ChanceNode) and child.stage != 'over'
                                          and actor(child) == side and mid_turn(child)) else depth - 1
            v = self.value(child, d, VMIN, VMAX)
            if best is None or (v > best if side == 'O' else v < best):
                best = v
        return best

    def value(self, node, depth, alpha, beta):
        """The value of a state or ChanceNode with `depth` turn plies to go (offence's view)."""
        self.check()
        if isinstance(node, ChanceNode):
            return self.chance(node, depth, alpha, beta)
        s = node
        if s.stage == 'over':
            return terminal_value(s)
        if depth <= 0:
            if self.settle_shots and s.stage != 'play':
                return self.leaf(s)                      # step 18b: the declared shot is settled by the rules
            if self.quiet or self.play_on:
                why = self.unsettled(s)
                if why is not None:
                    if depth <= -self.ext_cap and why != 'mid':
                        self.cap_hits += 1
                        return self.leaf(s)
                    return self.extend(s, why, depth, alpha, beta)
            return self.leaf(s)
        key = (zobrist(s), depth)
        hit = self.tt.get(key)
        if hit is not None:
            v, flag = hit[0], hit[1]
            if flag == 0 or (flag == 1 and v >= beta) or (flag == -1 and v <= alpha):
                return v
        side = actor(s)
        ts = self.turns_of(s)
        if not ts:
            return self.leaf(s)
        ts = self.order(ts, depth, key[0], s)
        self.nodes += 1
        a0, b0 = alpha, beta
        best = None
        rec = [] if self.split and depth == 1 and a0 == VMIN and b0 == VMAX else None     # step 18f: its replies' values
        opponent = side != self.me
        mix = opponent and (self.lam < 1.0 or bool(self.habit))
        passive = None
        if mix:
            w = [t for _, t in ts if t[0].kind in ('end_turn', 'pause', 'hesitate', 'forfeit')]
            passive = self.value(self.play_t(s, w[0]), depth - 1, VMIN, VMAX) if w else None
        for _, t in ts:
            child = self.play_t(s, t)
            d = depth - 1
            if self.quiet and not isinstance(child, ChanceNode) and child.stage != 'over' and actor(child) == side \
                    and mid_turn(child):
                d = depth                    # 'quiet points': look-ahead counts completed team turns only
            v = self.value(child, d, VMIN if mix else alpha, VMAX if mix else beta)
            if rec is not None:
                rec.append(v)
            if side == 'O':
                if best is None or v > best[0]:
                    best = (v, t)
                if not mix:
                    alpha = max(alpha, v)
            else:
                if best is None or v < best[0]:
                    best = (v, t)
                if not mix:
                    beta = min(beta, v)
            if not mix and alpha >= beta:
                self.killer(depth, t)
                self.history[t[0]] = self.history.get(t[0], 0) + depth * depth
                break
        if rec is not None and len(rec) == len(ts):
            self.spread[key[0]] = sorted(rec, reverse=side == 'O')
        v = best[0]
        if mix and passive is not None:
            v = self.lam * v + (1 - self.lam) * passive
        if mix and self.habit:
            kind = self.habit.get(s.stage + '/' + side)
            hv = next((self.value(self.play_t(s, t), depth - 1, VMIN, VMAX) for _, t in ts if t[0].kind == kind), None)
            if hv is not None:
                v = (1 - self.habit_weight) * v + self.habit_weight * hv
        flag = 0
        if not mix:
            flag = 1 if v >= b0 else -1 if v <= a0 else 0
        self.tt[key] = (v, flag, best[1])
        return v

    def chance(self, node, depth, alpha, beta):
        """Star2 (Ballard): bounds from the values already searched and [VMIN, VMAX] for the rest; a probing pass
        searches each outcome's first turn only, which bounds it from one side; then the full search, cutting off as
        soon as the bounds fall outside the window."""
        outs = node.outcomes
        key = None
        probs = [float(p) for p, _, _ in outs]
        lo_b = [VMIN] * len(outs)
        hi_b = [VMAX] * len(outs)
        # Star2 probing: one turn of each outcome bounds it from one side (a max node is at least the value of its
        # first-ordered turn, a min node at most); a terminal outcome is exact; a transposition hit may be exact
        for k, (p, _, sub) in enumerate(outs):
            if probs[k] == 0 or isinstance(sub, ChanceNode):
                continue
            if sub.stage == 'over':
                lo_b[k] = hi_b[k] = terminal_value(sub)
                continue
            z = zobrist(sub)
            hit = self.tt.get((z, depth))
            if hit is not None and hit[1] == 0:
                lo_b[k] = hi_b[k] = hit[0]
                continue
            if depth <= 0:
                continue
            ts = self.turns_of(sub)
            if not ts:
                continue
            first = self.order(ts, depth, z, sub)[0][1]
            v = self.value(self.play_t(sub, first), depth - 1, VMIN, VMAX)
            if actor(sub) == 'O':
                lo_b[k] = max(lo_b[k], v)
            else:
                hi_b[k] = min(hi_b[k], v)
        lo = sum(p * l for p, l in zip(probs, lo_b))
        hi = sum(p * h for p, h in zip(probs, hi_b))
        if hi <= alpha:
            return hi
        if lo >= beta:
            return lo
        total = 0.0
        for k, (p, _, sub) in enumerate(outs):
            pf = probs[k]
            if pf == 0:
                continue
            if lo_b[k] == hi_b[k]:
                v = lo_b[k]
            else:
                rest_lo = sum(probs[m] * lo_b[m] for m in range(k + 1, len(outs)))
                rest_hi = sum(probs[m] * hi_b[m] for m in range(k + 1, len(outs)))
                a = (alpha - total - rest_hi) / pf
                b = (beta - total - rest_lo) / pf
                v = self.value(sub, depth, max(VMIN, a), min(VMAX, b))
            total += pf * v
            lo_b[k] = hi_b[k] = v
            done_lo = total + sum(probs[m] * VMIN for m in range(k + 1, len(outs)))
            done_hi = total + sum(probs[m] * VMAX for m in range(k + 1, len(outs)))
            if done_hi <= alpha:
                return done_hi
            if done_lo >= beta:
                return done_lo
        return total

    def play_t(self, s, t):
        """A turn played; a one-action turn ended (search.whole_turns)."""
        n = play_turn(s, t)
        return ended_turn(s, n) if self.whole else n

    def quick(self, node):
        """Move ordering only: THREAT without the coverage search (a cheaper read than the leaf)."""
        if isinstance(node, ChanceNode):
            return sum(float(p) * self.quick(sub) for p, _, sub in node.outcomes)
        if node.stage == 'over':
            return terminal_value(node)
        if self.settle_shots and node.stage != 'play':
            return self.settled(node)                    # step 18b: a declared shot is ordered by its settled value
        return Read(node, k=0, looks_per=3).leaf()

    def turns_of(self, s):
        key = zobrist(s)
        hit = self.tcache.get(key)
        if hit is None:
            hit = turns(s, self.p['beam'], evaluate=self.quick, deadline=self.deadline, expand=3, second=1, mode=self.open, whole=self.whole, width=self.width)
            self.tcache[key] = hit
        return hit

    def killer(self, depth, t):
        ks = self.killers.setdefault(depth, [])
        if t not in ks:
            ks.insert(0, t)
            del ks[2:]

    def order(self, ts, depth, z=None, s=None):
        ks = self.killers.get(depth, [])
        prev = self.tt.get((z, depth - 1)) if z is not None and SPEED['tt_order'] else None
        first = prev[2] if prev is not None else None      # this position's best turn, one shorter: tried first
        goals = self.touch(s, z) if self.goals and s is not None and depth >= 2 else []

        def off_goal(t):                 # step 16: a turn that works on a top goal is searched first (ordering only)
            for a in t:
                for i, sq in goals:
                    if (a.side == 'O' and a.piece == i) or a.dest == sq or \
                            (a.side == 'X' and a.dest is not None and B.adjacent(a.dest, sq)):
                        return 0
            return 1
        return sorted(ts, key=lambda r: (-1 if r[1] == first else 0 if r[1] in ks else 1, off_goal(r[1]) if goals else 0,
                                         -(r[0] + 0.01 * self.history.get(r[1][0], 0))))

    def root(self, s, max_depth, min_depth=1):
        # step 18h: the level's own map is in force for the length of its search and no longer (a reading made outside
        # a search takes the shared map, in both engines)
        from . import decide as _decide
        prev = _decide.LEVEL[0]
        _decide.LEVEL[0] = self.p.get('level')
        try:
            return self._root(s, max_depth, min_depth)
        finally:
            _decide.LEVEL[0] = prev

    def _root(self, s, max_depth, min_depth=1):
        """Iterative deepening. Returns (scored turns [(value, turn)], depth reached, the principal turn)."""
        side = actor(s)
        budget = self.deadline - time.time()
        root_read = Read(s, exact=budget >= 0.8)            # the rules' exact reach when the budget allows
        ts = turns(s, self.p['beam'], read=root_read, evaluate=self.quick, deadline=None,
                   expand=None if budget >= 0.8 else 2, second=2 if budget >= 0.8 else 1, mode=self.open, whole=self.whole, width=self.width)
        deadline, self.deadline = self.deadline, float('inf')
        results = []
        sign = 1 if side == 'O' else -1
        for k, (q, t) in enumerate(ts):
            # the first ply: each turn's leaf; once the deadline passes (and the first three have their leaf), the
            # rest keep their ordering value
            if k >= 3 and time.time() > deadline:
                results.append((sign * q, t))
                continue
            n = self.play_t(s, t)
            if self.quiet or self.play_on:
                results.append((self.value(n, self._child_depth(s, n, 1), VMIN, VMAX), t))
            else:
                results.append((self.leaf(n) if not isinstance(n, ChanceNode) else self.value(n, 0, VMIN, VMAX), t))
        self.deadline = deadline
        reached = 1
        self.partial = 0
        by_depth = {1: list(results)}
        self._note(1, results, side)                    # the root choice at each completed depth (a record only)
        for depth in range(2, max_depth + 1):
            out = []
            try:
                for _, t in sorted(results, key=lambda r: -r[0] if side == 'O' else r[0]):
                    n = self.play_t(s, t)
                    v = self.value(n, self._child_depth(s, n, depth), VMIN, VMAX)
                    out.append((v, t))
                results = out
                reached = depth
                by_depth[depth] = list(out)
                self._note(depth, out, side)
            except Timeout:
                if self.like or self.clear:
                    break                    # 'like with like' and 'clear reason': only completed depths count
                # a partial iteration: the principal turn was re-searched first; a turn searched deeper replaces it
                # only if it is better at that depth
                self.partial = len(out)
                if out:
                    pv_v = out[0][0]
                    best = max(out, key=lambda r: r[0]) if side == 'O' else min(out, key=lambda r: r[0])
                    if (best[0] > pv_v if side == 'O' else best[0] < pv_v) or len(out) == 1:
                        done = {r[1] for r in out}
                        results = out + [r for r in results if r[1] not in done]
                break
        if self.like or self.clear:
            results, reached = self._settle(s, by_depth, side)
        if self.goals:                       # the root's own potential comes off: a turn earns potential after less before
            p0 = self.phi(s)
            results = [(v - p0, t) for v, t in results]
            self.trace = [(d, t, v - p0) for d, t, v in self.trace]
        results.sort(key=lambda r: -r[0] if side == 'O' else r[0])
        if self.split:
            results = self.split_ties(s, results, side)
        return results, reached

    def split_ties(self, s, results, side):
        """Step 18f (search.split_ties): turns that read exactly the same are separated by evidence the search already
        has: after the other side's best reply, how good its next-best replies are. Within each run of turns that read
        the same (results best first), those whose reply node was wholly searched are put in order, the turn that
        leaves the other side the fewest good replies first; the rest keep their places."""
        def key_of(t):
            n = self.play_t(s, t)
            if isinstance(n, ChanceNode) or n.stage == 'over' or actor(n) == side:
                return None
            sp = self.spread.get(zobrist(n))
            return tuple(round(-v if side == 'O' else v, 6) for v in sp[1:]) if sp else None

        out = list(results)
        i = 0
        while i < len(out):
            j = i + 1
            while j < len(out) and abs(out[j][0] - out[i][0]) < 1e-9:
                j += 1
            if j - i > 1:
                slots, items = [], []
                for k in range(i, j):
                    key = key_of(out[k][1])
                    if key is not None:
                        slots.append(k)
                        items.append((key, len(items), out[k]))
                items.sort(key=lambda r: (r[0], r[1]))
                for k, it in zip(slots, items):
                    out[k] = it[2]
            i = j
        return out

    def _child_depth(self, s, child, depth):
        """The depth left after a root turn: a turn that leaves the same side mid-turn isn't a completed team turn."""
        if self.quiet and not isinstance(child, ChanceNode) and child.stage != 'over' and actor(child) == actor(s) \
                and mid_turn(child):
            return depth
        return depth - 1

    def _note(self, depth, res, side):
        best = max(res, key=lambda r: r[0]) if side == 'O' else min(res, key=lambda r: r[0])
        self.trace.append((depth, best[1], best[0]))
        self.depth_seconds.append((depth, round(time.time() - self.t0, 3)))

    def _settle(self, s, by_depth, side):
        """'Like with like': the answer comes from the deepest completed depth that ends on the same side's completed
        turn as the look-ahead's pairs (even depths: an offence turn and the reply), else depth 1. 'Change only for a
        clear reason': its best turn replaces the best of two depths before only if it beats it by more than the
        reading's margin of error at this phase. Without like_with_like the deepest completed depth is used."""
        done = sorted(by_depth)
        even = [d for d in done if d % 2 == 0] if self.like else []
        d = even[-1] if even else done[-1]
        res = list(by_depth[d])
        sign = 1 if side == 'O' else -1
        best = max(res, key=lambda r: sign * r[0])
        prev = by_depth.get(d - 2) if self.clear else None
        if prev:
            p_turn = max(prev, key=lambda r: sign * r[0])[1]
            p_now = next((r for r in res if r[1] == p_turn), None)
            margin = float(self.margin.get(phase_of(s), 0.0)) if isinstance(self.margin, dict) else float(self.margin)
            if p_now is not None and p_turn != best[1] and sign * (best[0] - p_now[0]) <= margin:
                self.kept += 1
                res = [(best[0], p_turn) if r[1] == p_turn else r for r in res]
                res.sort(key=lambda r: (-sign * r[0], 0 if r[1] == p_turn else 1))
                return res, d
        return res, d
