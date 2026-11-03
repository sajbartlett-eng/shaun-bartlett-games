"""A playtest game session. The engine decides every rule; this only keeps the session."""
import datetime
import json
import os
import random
import secrets
import threading
import time
from fractions import Fraction

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions, intercept_status
from playmaker_engine.cards import TEAMS, FIRST_GAME
from playmaker_engine.policies import GreedyPolicy
from playmaker_engine.resolve import apply, ChanceNode
from playmaker_engine.scenarios import SCENARIOS, scenario_state, game_state
from playmaker_engine.scoring import score, band, choose_contest, shot_points, match_result

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT, 'playtest_logs')

# The preview pack's table setup, used for both possessions of a full game.
TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']
TABLE_ARROWS = ['N', 'NE', 'NW', 'N', 'N']

FEEDBACK_QUESTIONS = [
    'Did the token-and-phase rhythm feel like basketball tempo?',
    'Was scoring shot quality, not makes and misses, a satisfying payoff?',
    'Were defender arrows clear, or one thing too many?',
    'Where did the rules lose you first?',
    'What would you change first?',
]


class GameError(Exception):
    pass


def action_to_json(a):
    return dict(kind=a.kind, side=a.side, piece=a.piece, dest=list(a.dest) if a.dest is not None else None,
                arrow=a.arrow, target=a.target, shot=a.shot, text=str(a))


def action_from_json(d):
    dest = d.get('dest')
    return Action(d['kind'], d['side'], int(d.get('piece', -1)), tuple(dest) if dest is not None else None,
                  int(d.get('arrow', -1)), int(d.get('target', -1)), d.get('shot', '') or '')


def resolve_chance(node, rng):
    """Pick outcomes layer by layer exactly as resolve.sample does (same RNG calls), and record each
    roll as a d20 face: face = floor(r * 20) + 1, so 'the first outcome on N or less' is exact."""
    rolls = []
    while isinstance(node, ChanceNode):
        r = Fraction(rng.random())
        acc = Fraction(0)
        pick = node.outcomes[-1]
        for o in node.outcomes:
            acc += o[0]
            if r < acc:
                pick = o
                break
        first_p, first_label = node.outcomes[0][0], node.outcomes[0][1]
        need = int(first_p * 20)
        rolls.append(dict(what=node.what, outcomes=[[l, float(p)] for p, l, _ in node.outcomes], picked=pick[1],
                          face=int(r * 20) + 1, need=need, first=first_label,
                          text=f'{node.what}: {first_label} on {need} or less ({float(first_p):.0%})'))
        node = pick[2]
    return node, rolls


def chance_preview(state, a):
    """Plain-words description of the roll an action would need, without rolling."""
    node = apply(state, a)
    out = []
    while isinstance(node, ChanceNode):
        p, label, sub = node.outcomes[0]
        out.append(f'{node.what}: {label} on {int(p * 20)} or less ({float(p):.0%})')
        node = max(node.outcomes, key=lambda o: o[0])[2]
    return out


class Game:
    def __init__(self, mode='hotseat', scenario=None, teams=None, seed=None, ai=None, full=False, rules=None):
        self.code = secrets.token_hex(3).upper()
        self.mode = mode
        self.scenario = scenario
        self.full = full and scenario is None
        self.teams = list(teams or FIRST_GAME)
        self.seed = int(seed if seed is not None else random.randrange(10 ** 6))
        self.rng = random.Random(self.seed)
        self.rules = rules
        self.ai = {k: v for k, v in (ai or {}).items() if v}
        self.policies = {side: GreedyPolicy() for side in self.ai}
        self.tokens = {'both': secrets.token_hex(8)} if mode == 'hotseat' else {}
        self.seats = {}
        self.version = 0
        self.possession = 1
        self.scores = []                 # finished possessions: dict
        self.undo = []                   # [(state, rng_state, phase_slots)] since the last roll
        self.undo_votes = set()
        self.rolls = []
        self.slots = {'O': {i: [] for i in range(5)}, 'X': {i: [] for i in range(5)}}
        self.last_decision = time.time()
        self.lock = threading.RLock()
        self.feedback = None
        self.match = None
        os.makedirs(LOG_DIR, exist_ok=True)
        self.log_path = os.path.join(LOG_DIR, f'{datetime.date.today().isoformat()}_{self.code}.jsonl')
        self.state = self._possession_state()
        self._log('setup', mode=mode, scenario=scenario, teams=self.teams, seed=self.seed, full=self.full,
                  ai=self.ai, possession=self.possession, start=self.state.encode())
        self._run_ai()

    # ---- setup ----
    def _possession_state(self):
        if self.scenario:
            return scenario_state(self.scenario, rules=self.rules)
        off, dfn = (self.teams if self.possession == 1 else self.teams[::-1])
        return game_state(off, dfn, TABLE_O, TABLE_X, TABLE_ARROWS, ball=0, rules=self.rules)

    def offence_player(self):
        """Which player (A or B) is attacking this possession."""
        return 'A' if self.possession == 1 else 'B'

    # ---- seats ----
    def join(self, seat):
        if self.mode != 'remote':
            raise GameError('only remote games have seats')
        if seat not in ('O', 'X'):
            raise GameError('seat must be O or X')
        if seat in self.seats.values():
            raise GameError(f'seat {seat} is taken')
        tok = secrets.token_hex(8)
        self.seats[tok] = seat
        self.version += 1
        return tok

    def seat_of(self, token):
        if self.mode == 'hotseat':
            return 'both' if token == self.tokens['both'] else None
        return self.seats.get(token)

    def side_to_act(self):
        s = self.state
        if s.stage == 'over':
            return None
        if s.stage in ('target', 'pick'):
            return 'O'
        return s.side

    def can_act(self, token):
        seat = self.seat_of(token)
        side = self.side_to_act()
        if seat is None or side is None or side in self.ai:
            return False
        return seat == 'both' or seat == side

    # ---- acting ----
    def legal(self):
        return legal_actions(self.state)

    def act(self, token, data):
        with self.lock:
            if self.state.stage == 'over':
                raise GameError('the possession is over')
            if not self.can_act(token):
                raise GameError('not your turn' if self.seat_of(token) else 'unknown player token')
            try:
                a = action_from_json(data)
            except (KeyError, TypeError, ValueError) as e:
                raise GameError(f'malformed action: {e}')
            legal = self.legal()
            if a not in legal:
                raise GameError(f'illegal action: {a} is not among the {len(legal)} legal actions now')
            return self._apply(a, legal, actor='human')

    def _apply(self, a, legal, actor):
        before = self.state
        now = time.time()
        node = apply(before, a)
        rolls = []
        if isinstance(node, ChanceNode):
            node, rolls = resolve_chance(node, self.rng)
            self.undo = []
        else:
            self.undo.append((before, self.rng.getstate(), json.dumps(self.slots)))
        if a.kind not in ('end_turn', 'forfeit', 'target', 'pick'):
            self.slots[a.side][a.piece if a.piece >= 0 else 0].append(a.kind)
        if node.phase != before.phase:
            self.slots = {'O': {i: [] for i in range(5)}, 'X': {i: [] for i in range(5)}}
        self.state = node
        self.rolls = rolls
        self.undo_votes = set()
        self.version += 1
        rec = dict(actor=actor, action=action_to_json(a),
                   legal=[str(x) for x in legal] if a.kind != 'target' else [f'O{i + 1}' for i in range(5)],
                   seconds=round(now - self.last_decision, 2), clock=before.clock, phase=before.phase,
                   possession=self.possession, after=node.encode())
        if a.kind == 'target':
            rec['action'] = dict(kind='target', side='O', text="Coach's Call target chosen (secret)", target=a.target)
        self._log('action', **rec)
        for r in rolls:
            self._log('roll', possession=self.possession, **r)
        self.last_decision = time.time()
        if node.stage == 'over':
            self._end_possession()
        return dict(rolls=rolls)

    def _run_ai(self):
        while True:
            side = self.side_to_act()
            if side is None or side not in self.ai:
                return
            pol = self.policies[side]
            pol.reset(self.seed * 7 + self.version)
            a = pol.choose(self.state)
            self._apply(a, self.legal(), actor='ai')

    def after_human(self):
        with self.lock:
            self._run_ai()

    def do_undo(self, token):
        with self.lock:
            if not self.undo:
                raise GameError('nothing to undo (undo stops at the last roll)')
            if self.mode == 'remote':
                seat = self.seat_of(token)
                if seat is None:
                    raise GameError('unknown player token')
                self.undo_votes.add(seat)
                if self.undo_votes != {'O', 'X'}:
                    self.version += 1
                    return dict(waiting='undo needs both players: waiting for the other side')
            elif self.seat_of(token) is None:
                raise GameError('unknown player token')
            st, rs, slots = self.undo.pop()
            self.state = st
            self.rng.setstate(rs)
            self.slots = {k: {int(i): v for i, v in d.items()} for k, d in json.loads(slots).items()}
            self.undo_votes = set()
            self.rolls = []
            self.version += 1
            self._log('undo', possession=self.possession, state=st.encode())
            return dict(ok=True)

    # ---- possessions and the match ----
    def _end_possession(self):
        sc = score(self.state)
        r = self.state.result
        final = None
        if r and r.kind in ('shot', 'forced', 'free_throws') and r.points:
            final = (r.rating, max(0, r.contest))
        self.scores.append(dict(possession=self.possession, attacker=self.offence_player(), total=sc.total,
                                band=sc.band, detail=sc.detail, breakdown=_score_json(sc),
                                target=self.state.target, final_shot=final))
        self._log('end', possession=self.possession, score=_score_json(sc), target=self.state.target)
        if self.full and self.possession == 2:
            self._finish_match()

    def next_possession(self, token):
        with self.lock:
            if self.seat_of(token) is None:
                raise GameError('unknown player token')
            if not (self.full and self.possession == 1 and self.state.stage == 'over'):
                raise GameError('no next possession')
            self.possession = 2
            self.state = self._possession_state()
            self.undo, self.rolls = [], []
            self.slots = {'O': {i: [] for i in range(5)}, 'X': {i: [] for i in range(5)}}
            self.version += 1
            self._log('possession', possession=2, teams=self.teams[::-1], start=self.state.encode())
            self._run_ai()

    def _finish_match(self):
        a, b = self.scores[0], self.scores[1]
        m = dict(A=a['total'], B=b['total'])
        if a['total'] == b['total']:
            fa, fb = a['final_shot'] or (0, 0), b['final_shot'] or (0, 0)
            probs = match_result(a['total'], b['total'], fa, fb)
            ra, rb = self.rng.randint(1, 20), self.rng.randint(1, 20)
            make_a, make_b = ra <= fa[0] - fa[1], rb <= fb[0] - fb[1]
            m['tiebreak'] = dict(A=dict(roll=ra, need=fa[0] - fa[1], make=make_a),
                                 B=dict(roll=rb, need=fb[0] - fb[1], make=make_b),
                                 p={k: float(v) for k, v in probs.items()})
            m['winner'] = 'A' if make_a and not make_b else 'B' if make_b and not make_a else 'tie'
        else:
            m['winner'] = 'A' if a['total'] > b['total'] else 'B'
        self.match = m
        self._log('match', **m)

    def save_feedback(self, token, answers):
        if self.seat_of(token) is None:
            raise GameError('unknown player token')
        self.feedback = answers
        self._log('feedback', seat=self.seat_of(token),
                  answers=[dict(question=q, answer=answers.get(str(i), '')) for i, q in enumerate(FEEDBACK_QUESTIONS)])

    # ---- log ----
    def _log(self, kind, **data):
        data = dict(type=kind, time=round(time.time(), 3), code=self.code, **data)
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(data, default=str) + '\n')

    def read_log(self):
        with open(self.log_path) as f:
            return [json.loads(line) for line in f]


def _score_json(sc):
    return dict(total=sc.total, band=sc.band, shot_value=sc.shot_value, free_throws=sc.free_throws,
                bonus=sc.bonus, turnovers=sc.turnovers, turnover_points=sc.turnover_points,
                coach_bonus=sc.coach_bonus, look=sc.look, goal_met=sc.goal_met, late_clock=sc.late_clock,
                detail=sc.detail)
