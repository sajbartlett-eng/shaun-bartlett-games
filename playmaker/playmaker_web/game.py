"""A playtest game session. The engine decides every rule; this only keeps the session."""
import datetime
import json
import os
import random
import secrets
import threading
import time
from dataclasses import replace
from fractions import Fraction

from playmaker_engine import board as B
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions, intercept_status
from playmaker_engine.cards import TEAMS, FIRST_GAME, TEAM_TAGLINES, CARDS as CARDS_ALL


def TEAM_TAGLINES_OR(name):
    return TEAM_TAGLINES.get(name, 'Custom team')
from playmaker_engine.resolve import apply, ChanceNode
from playmaker_engine.scenarios import SCENARIOS, scenario_state, game_state, setup_errors
from playmaker_engine.scoring import score, band, choose_contest, shot_points, match_result
from playmaker_engine.timer import timer_forfeit, TIMER_CONFIG, TIMED_STAGES, token_free

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(ROOT, 'playtest_logs')

# The preview pack's table setup, used for both possessions of a full game.
TABLE_O = ['I11', 'C9', 'O9', 'A3', 'Q3']
TABLE_X = ['I10', 'D8', 'N8', 'G4', 'N4']
TABLE_ARROWS = ['N', 'NE', 'NW', 'N', 'N']

REFLECT_QUESTION = 'Was your setup and plan the right one for these two teams?'
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
                          face=int(r * 20) + 1, need=need, first=first_label, roller=node.roller,
                          text=roll_text(node.what, node.roller, first_label, need, first_p)))
        node = pick[2]
    return node, rolls


def roll_text(what, roller, label, need, p):
    who = {'O': 'Offence rolls', 'X': 'Defence rolls'}.get(roller, 'Roll')
    return f'{who}: {what}, {label} on {need} or less ({float(p):.0%})'


def chance_preview(state, a):
    """Plain-words description of the roll(s) an action would need, without rolling."""
    node = apply(state, a)
    out = []
    while isinstance(node, ChanceNode):
        p, label, sub = node.outcomes[0]
        out.append(dict(roller=node.roller, text=roll_text(node.what, node.roller, label, int(p * 20), p)))
        node = max(node.outcomes, key=lambda o: o[0])[2]
    return out


def consequences(before, after, a):
    """What an action changed, in plain words (from the state difference, so it is always true)."""
    out = []
    if after.tos > before.tos:
        lost = before.clock - after.clock if after.stage != 'over' and after.clock < before.clock else 0
        tail = f' and {lost} seconds off the clock' if lost else ''
        if after.stage == 'over' and after.zeroed and a.kind in ('intercept', 'steal'):
            tail = ' on the last phase: the possession scores 0'
        if a.kind == 'intercept':
            out.append(('bad_O', f'Pass intercepted: turnover, −5{tail}. The ball goes back to the passer.'))
        elif a.kind == 'steal':
            what = 'Shot stolen: cancelled. ' if before.stage == 'reaction' and after.stage != 'over' else 'Stolen: '
            out.append(('bad_O', f'{what}turnover, −5{tail}. Play on.'))
        else:
            out.append(('bad_O', 'Turnover, −5.'))
    if after.bonus5 > before.bonus5:
        out.append(('good_O', 'Foul on the steal: +5 to the offence. Play on.'))
    if a.kind == 'intercept' and after.tos == before.tos and before.pending:
        out.append(('good_O', f'Pass completes to O{before.pending[1] + 1}.'))
    if a.kind == 'steal' and after.tos == before.tos and after.bonus5 == before.bonus5 and after.stage != 'over':
        out.append(('good_O', f'Ball kept by O{before.ball + 1}.'))
    if before.pending and not after.pending and a.kind != 'intercept' and after.ball == before.pending[1]:
        out.append(('info', f'The pass lands: O{after.ball + 1} has the ball.'))
    for side, mask_b, mask_a in (('O', before.lock_o, after.lock_o), ('X', before.lock_x, after.lock_x)):
        for i in range(5):
            if mask_a >> i & 1 and not mask_b >> i & 1:
                why = {'dribble': 'beaten on the dribble' if side == 'X' else 'lost the dribble',
                       'challenge': 'held by the screen'}.get(a.kind, '')
                out.append(('bad_X' if side == 'X' else 'bad_O', f'{side}{i + 1} is locked' + (f' ({why}).' if why else '.')))
    if a.kind == 'dribble' and after.lock_o == before.lock_o and after.lock_x == before.lock_x:
        out.append(('info', 'Dribble: no change.'))
    if a.kind == 'challenge':
        for (i, d, f, m) in after.screens:
            if m != dict((x[0], x[3]) for x in before.screens).get(i, m):
                out.append(('good_X', f'X{a.piece + 1} beats the screen: may cross the T square.'))
    if a.kind == 'shot':
        out.append(('info', f'Shot declared ({a.shot}). The defence reacts, then chooses the contest.'))
    if after.stage == 'over' and before.stage != 'over':
        sc = score(after)
        out.append(('end', f'Possession over: {sc.total} ({sc.band}). {sc.detail}'))
    if after.phase != before.phase and after.stage != 'over':
        out.append(('info', f'New phase: clock {after.clock}, tokens back to 6 each.'))
    return [dict(tone=t, text=x) for t, x in out]


def notation(before, after, a, turn):
    """The play-diagram mark for one action, in hand-drawn basketball notation terms (the web layer reads it
    off the before and after states; the engine decides nothing here): kind, side, piece, from and to
    squares, a target square where the action points at one (a pass receiver, the T square, the rim, the
    defender dribbled at), the turn number within the phase, and what came of it."""
    k = a.kind
    side = a.side
    if k in ('end_turn', 'forfeit', 'target', 'pick') or a.piece is None or a.piece < 0 and k not in ('pause', 'hesitate'):
        return None
    # a defence action other than an Intercept lands a pending pass first: the carrier it acts on is the receiver
    carrier = before.pending[1] if (before.pending and side == 'X' and k != 'intercept') else before.ball
    pieces_b = before.o if side == 'O' else before.x
    pieces_a = after.o if side == 'O' else after.x
    i = a.piece if a.piece is not None and a.piece >= 0 else (before.ball if side == 'O' else None)
    frm = B.sq(pieces_b[i]) if i is not None and B.on_board(pieces_b[i]) else None
    to = B.sq(pieces_a[i]) if i is not None and B.on_board(pieces_a[i]) else frm
    m = dict(kind=k, side=side, piece=i, frm=frm, to=to, target=None, turn=turn, result=None)
    if k in ('move', 'qs', 'sprint'):
        if side == 'X':
            m['arrow_from'], m['arrow_to'] = before.arrows[i], after.arrows[i]
    elif k == 'pass':
        m['target'] = B.sq(before.o[a.target])
        m['receiver'] = a.target
        m['result'] = 'landed' if after.ball == a.target else ('in the air' if after.pending else 'intercepted')
    elif k == 'dribble':
        m['target'] = B.sq(before.x[a.target])
        m['defender'] = a.target
        m['result'] = 'won' if after.locked('X', a.target) and not before.locked('X', a.target) else 'lost' if after.locked('O', before.ball) and not before.locked('O', before.ball) else 'even'
    elif k == 'screen':
        m['target'] = B.sq(B.add(before.o[i], B.DIRS[a.target]))
        m['dir'] = a.target
    elif k in ('shot', 'forced_shot'):
        m['target'] = B.sq(RC.RIM)
        m['shot'] = a.shot
    elif k == 'intercept':
        passer, recv = before.pending
        m['target'] = B.sq(before.o[recv])
        m['pass_from'] = B.sq(before.o[passer])
        m['result'] = 'picked off' if after.tos > before.tos else 'missed'
    elif k == 'steal':
        m['target'] = B.sq(before.o[carrier])
        m['result'] = 'stolen' if after.tos > before.tos else ('foul' if after.fouls > before.fouls or after.bonus5 > before.bonus5 else 'kept')
    elif k == 'challenge':
        m['target'] = B.sq(before.o[a.target])
        m['result'] = 'beaten' if after.locked('X', i) and not before.locked('X', i) else 'through'
    elif k == 'contest':
        if i is None or a.piece < 0:
            return dict(kind='no_contest', side='X', piece=None, frm=None, to=None, target=None, turn=turn, result=None)
        m['target'] = B.sq(before.o[carrier])
    elif k in ('hesitate', 'pause'):
        m['frm'] = m['to'] = B.sq(before.o[carrier])
        m['piece'] = carrier if side == 'O' else None
    return m


def man_to_man(o_squares, ball):
    """The computer's defensive placement: each X on the empty square next to its man that is closest
    to the rim (ties: compass order N, NE, E...), arrow on its man."""
    taken = set(o_squares)
    xs, arrows = [], []
    for o in o_squares:
        cands = [B.add(o, d) for d in B.DIRS]
        cands = [q for q in cands if B.on_board(q) and q not in taken]
        q = min(cands, key=lambda q: (B.dist_rim(q), cands.index(q)))
        taken.add(q)
        xs.append(q)
        arrows.append(B.dir_between(q, o))
    return xs, arrows


class Game:
    def __init__(self, mode='hotseat', scenario=None, teams=None, seed=None, ai=None, full=False, rules=None,
                 place=False, code=None, level='scout', custom=None, timer=None, clock=None, age='senior',
                 standard='pro', roster='prescribed', lineups=None, deal=None, random_for='both', coherent=False,
                 draft=None, match_format='tabletop', per_side=8, scouting=None, quarter=None):
        self.code = (code or secrets.token_hex(3)).upper()
        self.now = clock or time.time
        self.timer = self._timer_settings(timer)
        if level not in ('learn', 'scout', 'pro'):
            raise GameError('level must be learn, scout or pro')
        self.level = level
        self.mode = mode
        self.scenario = scenario
        # step 3m Part A: 'digital' = N possessions per side, alternating, turnovers end the possession at 0;
        # 'tabletop' = the printed rules (one possession each in a full game)
        if match_format not in ('tabletop', 'digital'):
            raise GameError("match format: 'digital' or 'tabletop'")
        self.match_format = 'tabletop' if scenario else match_format
        if self.match_format == 'digital':
            if int(per_side) not in (4, 8, 12):
                raise GameError('a digital match is 4, 8 or 12 possessions per side')
            full = True
            rules = replace(rules or RC.DEFAULT_RULES, digital=True)
        self.per_side = int(per_side) if self.match_format == 'digital' else (1 if full else 0)
        self.full = full and scenario is None
        self.n_poss = 2 * self.per_side if self.full else 1
        self.last_setup = {}             # (player, side) -> the human's last setup, for "repeat my last setup"
        # step 3n F3 (digital): team fouls across a running quarter of 18 possessions per side, carried across matches
        # between the same pairing (the client stores it with the pairing and passes it in)
        q = quarter if isinstance(quarter, dict) else {}
        self.quarter = dict(fouls=dict(A=int((q.get('fouls') or {}).get('A', 0)), B=int((q.get('fouls') or {}).get('B', 0))),
                            poss=dict(A=int((q.get('poss') or {}).get('A', 0)), B=int((q.get('poss') or {}).get('B', 0))),
                            number=int(q.get('number', 1)))
        self.teams = list(teams or FIRST_GAME)
        self.custom, self.experimental = {}, []
        self.hidden_teams = {}
        if custom and not scenario:
            roster, lineups = self._redirect_custom(custom)
        self.seed = int(seed if seed is not None else random.randrange(10 ** 6))
        self.levels = self._build_levels(age, standard, roster, lineups, deal, random_for, coherent, draft, ai)
        for t in self.teams:
            if t not in TEAMS:
                raise GameError(f'no team {t}')
        self.rng = random.Random(self.seed)
        self.rules = rules
        # the computer: by side (O / X, fixed for the game) or by player (A / B: it follows the player across the
        # swap of sides in a full game, so "play the computer" means one opponent all match)
        raw = {k: {'greedy': 'starter', 'reader': 'starter'}.get(v, v) for k, v in (ai or {}).items() if v}
        self.ai_players = {k: v for k, v in raw.items() if k in ('A', 'B')}
        self.ai_sides = {k: v for k, v in raw.items() if k in ('O', 'X')}
        self.possession = 1
        self.scouting = scouting if isinstance(scouting, dict) else None    # step 3m: the All-Star reads the human
        self._set_ai()
        self.tokens = {'both': secrets.token_hex(8)} if mode == 'hotseat' else {}
        self.seats = {}
        self.version = 0
        self.scores = []                 # finished possessions: dict
        self.undo = []                   # [(state, rng_state, phase_slots)] since the last roll
        self.undo_votes = set()
        self.rolls = []
        self.feed = []                   # every action with its rolls and consequences, for the page
        self.slots = {'O': {i: [] for i in range(5)}, 'X': {i: [] for i in range(5)}}
        self.turn_no = 0                 # the offence turn number within the phase (its defence answer shares it)
        self.last_decision = time.time()
        self.lock = threading.RLock()
        self.feedback = None
        self.match = None
        os.makedirs(LOG_DIR, exist_ok=True)
        self.log_name = f'{datetime.date.today().isoformat()}_{self.code}.jsonl'
        self.log_path = os.path.join(LOG_DIR, self.log_name)
        if os.path.exists(self.log_path):          # a new game always starts its own log
            os.remove(self.log_path)
        self.place_on = bool(place) and scenario is None
        self.placing = None              # 'O' or 'X' while the pieces are being set up
        self.placed = {}
        self.state = self._possession_state()
        self.picks = {}                  # side -> {hunt: {o, x}, protect: {x}} (private until the review)
        self.reflection = None
        self.review_cache = None
        self._log('setup', mode=mode, scenario=scenario, teams=self.teams, seed=self.seed, full=self.full,
                  match_format=self.match_format, per_side=self.per_side, quarter=self.quarter if self.match_format == 'digital' else None,
                  ai=self.ai, ai_players=self.ai_players or None, possession=self.possession, place=self.place_on, level=self.level,
                  custom=self.custom or None, experimental=self.experimental or None, levels=self.levels,
                  timer=self.timer, computer={side: p.describe() for side, p in self.policies.items()
                                              if hasattr(p, 'describe')} or None,
                  rules={k: getattr(self.state.ctx.rules, k) for k in RC.RULED_3I},
                  start=self.state.encode())
        for side in ('O', 'X'):
            if side in self.ai and self.picks_needed(side):
                self._save_picks(side, self._engine_picks(side), actor='ai')
        if not self.picks_pending():
            self._begin_possession()

    def _set_ai(self):
        """self.ai and self.policies for this possession: the fixed sides plus the players' sides now."""
        att = 'A' if self.possession % 2 == 1 else 'B'
        by_player = {('O' if p == att else 'X'): v for p, v in self.ai_players.items()}
        self.ai = dict(self.ai_sides, **by_player)
        self.policies = {side: self._policy(side, kind) for side, kind in self.ai.items()}

    def _policy(self, side, kind):
        """The computer for a side: 'rookie', 'starter' or 'allstar' (step 3e; 'greedy' means starter, from
        older pages)."""
        kind = {'greedy': 'starter', 'reader': 'starter'}.get(kind, kind)
        from playmaker_engine.agent import Agent, LEVELS
        if kind not in LEVELS:
            raise GameError('computer level: rookie, starter or allstar')
        return Agent(side, kind, seed=self.seed, scouting=getattr(self, 'scouting', None))

    # ---- setup ----
    def _redirect_custom(self, custom):
        """The old custom-team route (step 3d: [{slot: 0 or 1, name, cards: [5 keys]}]) is retired (step 3m Part 0):
        it goes through the slot-based builder, card n in slot n. A legal pro roster plays with the rules on; any
        other plays with the rules off and is labelled experimental, as before."""
        from playmaker_engine import rosters as RO
        lineups = [None, None]
        for c in custom:
            slot = int(c.get('slot', 0))
            keys = list(c.get('cards') or [])
            if slot not in (0, 1) or len(keys) != 5 or any(k not in CARDS_ALL for k in keys):
                raise GameError('a custom team is five cards')
            lineups[slot] = dict(name=c.get('name') or 'Custom', cards=[(k, n + 1) for n, k in enumerate(keys)])
        for i in range(2):
            if lineups[i] is None:
                t = self.teams[i]
                if t not in TEAMS:
                    raise GameError(f'no team {t}')
                lineups[i] = dict(name=t, cards=[(c.key, n + 1) for n, c in enumerate(TEAMS[t])])
        legal = [RO.legal(lu['cards'], 'pro') for lu in lineups]
        self.experimental = [lu['name'] for lu, ok in zip(lineups, legal) if not ok]
        return ('build' if all(legal) else 'free'), lineups

    def _build_levels(self, age, standard, roster, lineups, deal, random_for, coherent, draft, ai):
        """Step 3l: the two dials (Age, Standard) and the roster mode. Sets self.teams to the teams as they play
        (effective cards registered in TEAMS) and returns what the log records. The rules of play never change.
          roster  prescribed  the prescribed teams (Age applies, Standard doesn't)
                  build       lineups, rules on: five different cards, a shape of the standard, at most one flex
                  free        lineups, rules off ("Your team"): any five cards, duplicates, hand-set growth tags
                  random      a deal (code or new), for both teams, yours or the opponent's (coherent or pure)
                  draft       a finished Draft (rosters.Draft), its picks and reasons logged"""
        from playmaker_engine import levels as LV, rosters as RO
        from playmaker_engine.cards import register_cards
        age = age or 'senior'
        if age not in LV.AGE_ORDER:
            raise GameError('age: senior, youth or junior')
        if roster not in ('prescribed', 'build', 'free', 'random', 'draft'):
            raise GameError('roster mode: prescribed, build, free, random or draft')
        stds = standard if isinstance(standard, dict) else {'A': standard or 'pro', 'B': standard or 'pro'}
        stds = {p: stds.get(p) or 'pro' for p in ('A', 'B')}
        if any(v not in LV.STANDARD_ORDER for v in stds.values()):
            raise GameError('standard: pro, semi_pro or amateur')
        handicap = stds['A'] != stds['B']
        if handicap and roster not in ('build', 'draft'):
            raise GameError('a different standard for each side is the handicap option, for building with the rules on')
        if self.scenario:
            if age != 'senior' or roster != 'prescribed':
                raise GameError('scenario cards are played with the senior pro cards')
            return None
        if age == 'senior' and roster == 'prescribed':
            return None                                      # the default: exactly the game before step 3l
        tag_rng = random.Random(f'growth-{self.seed}')
        names = ['Home', 'Away']
        entries, tags, given_tags, out = [None, None], [None, None], [None, None], dict(age=age, roster=roster)
        human = next((p for p in ('A', 'B') if p not in (ai or {})), 'A')
        if roster == 'prescribed':
            for i, t in enumerate(self.teams):
                if t not in TEAMS:
                    raise GameError(f'no team {t}')
                names[i] = t
                entries[i] = [(c.key, n + 1) for n, c in enumerate(TEAMS[t])]
        elif roster in ('build', 'free'):
            if not lineups or len(lineups) != 2:
                raise GameError('two lineups: [home, away]')
            for i, lu in enumerate(lineups):
                lu = lu if isinstance(lu, dict) else dict(cards=lu)
                raw = lu.get('cards') or []
                ents = [(e[0], int(e[1])) if isinstance(e, (list, tuple)) else (e, n + 1) for n, e in enumerate(raw)]
                std = stds['AB'[i]]
                bad = RO.problems(ents, std, rules=roster == 'build')
                if bad:
                    raise GameError(f"{lu.get('name') or names[i]}: " + ' '.join(bad))
                entries[i] = ents
                names[i] = ' '.join(str(lu.get('name') or names[i]).split())[:24] or names[i]
                if lu.get('tags') and roster == 'free' and age == 'junior':
                    tg = lu['tags']
                    tg = {int(k): v for k, v in tg.items()} if isinstance(tg, dict) else {n + 1: v for n, v in enumerate(tg)}
                    if any(v not in LV.TAGS for v in tg.values()):
                        raise GameError('growth tags: early, on_time or late')
                    given_tags[i] = [tg.get(s, 'on_time') for s in range(1, 6)]
        elif roster == 'random':
            if random_for not in ('both', 'yours', 'opponent'):
                raise GameError('random: both, yours or opponent')
            try:
                d = RO.deal(age, stds['A'], bool(coherent), seed=None if deal else self.rng_seed_for_deal(), code=deal)
            except ValueError as e:
                raise GameError(str(e))
            age = d['age']
            stds = {'A': d['standard'], 'B': d['standard']}
            out.update(deal=d['code'], standard=d['standard'], coherent=d['coherent'], random=random_for)
            mine = 'AB'.index(human)
            dealt = {0, 1} if random_for == 'both' else ({mine} if random_for == 'yours' else {1 - mine})
            kept = set()
            for i in range(2):
                if i not in dealt and self.teams[i] in TEAMS:
                    kept = {c.key for c in TEAMS[self.teams[i]]}
            for i in range(2):
                if i in dealt:
                    entries[i] = list(d['rosters'][i])
                    if kept & {k for k, _ in entries[i]}:
                        # one card pool: redeal this side from the code without the prescribed team's cards
                        entries[i] = RO.deal_one(d['standard'], random.Random(f"{d['code']}|{sorted(kept)}"),
                                                 d['coherent'], exclude=kept, age=d['age'])
                    names[i] = ('Home', 'Away')[i] + ' (dealt)'
                    if d['tags']:
                        given_tags[i] = list(d['tags'][i])
                else:
                    t = self.teams[i]
                    if t not in TEAMS:
                        raise GameError(f'no team {t}')
                    names[i] = t
                    entries[i] = [(c.key, n + 1) for n, c in enumerate(TEAMS[t])]
        else:                                                # draft
            if draft is None or not draft.done():
                raise GameError('finish the draft first')
            if draft.age != age:
                age = draft.age
            stds = {'A': draft.standards[1], 'B': draft.standards[2]}
            handicap = stds['A'] != stds['B']
            for i in range(2):
                entries[i] = list(draft.roster(i + 1))
            out.update(draft=draft.log)
        if age == 'junior':
            for i in range(2):
                tags[i] = given_tags[i] or LV.deal_growth(tag_rng)
        out['age'] = age
        if roster != 'prescribed':
            out['standard'] = stds['A'] if not handicap else dict(stds)
        label = LV.LABEL[age]
        lineups_out, teams_out, hidden = {}, [], {}
        for i in range(2):
            tg = {s: t for s, t in zip(range(1, 6), tags[i])} if tags[i] else {}
            cards = LV.team(entries[i], age, tg)
            nm = names[i] + (f' {label}' if label else '')
            if roster != 'prescribed' and names[0] == names[1]:
                nm = f"{names[i]} {'AB'[i]}" + (f' {label}' if label else '')
            reg = register_cards(nm, cards, tagline=TEAM_TAGLINES_OR(names[i]))
            teams_out.append(reg)
            lineups_out[reg] = LV.lineup_spec(cards)
            if tags[i]:
                hidden[reg] = register_cards(reg + ' (tags face down)', LV.on_time(cards), tagline=TEAM_TAGLINES_OR(names[i]))
        self.teams = teams_out
        self.hidden_teams = hidden
        out['lineups'] = lineups_out
        out['tags'] = {t: tags[i] for i, t in enumerate(teams_out)} if age == 'junior' else None
        if roster in ('build', 'free', 'random', 'draft'):
            st = [RO.strength([k for k, _ in entries[i]]) for i in range(2)]
            out['strength'] = {teams_out[i]: st[i] for i in range(2)}
            if st[0] != st[1]:
                lead = 0 if st[0] > st[1] else 1
                out['uneven'] = f"Uneven teams: {('Home', 'Away')[lead]} +{abs(st[0] - st[1])}"
        return out

    def rng_seed_for_deal(self):
        """A new deal's seed from the game seed (the deal code carries it, so the code alone reproduces the deal)."""
        return random.Random(f'deal-{self.seed}').randrange(36 ** 6)

    # ---- growth tags: face down until setup begins (step 3l) ----
    def tags_revealed(self):
        return getattr(self, '_revealed', False) or not getattr(self, 'hidden_teams', None)

    def seen_team(self, side, seat=None):
        """The team name a viewer reads for this side (possession 1 seats): with the growth tags face down until setup
        begins, the opponent's team is its on-time cards. seat None: a neutral view (both teams face down)."""
        name = self.team_of(side)
        if self.tags_revealed() or name not in self.hidden_teams:
            return name
        mine = self._viewer_sides(seat)
        return name if side in mine else self.hidden_teams[name]

    def seen_cards(self, team, seat=None):
        """The cards of a team (by name) as this viewer reads them now (face-down growth tags read as on time)."""
        if self.tags_revealed() or team not in self.hidden_teams:
            return TEAMS[team]
        side = 'O' if team == self.team_of('O') else 'X'
        return TEAMS[team] if side in self._viewer_sides(seat) else TEAMS[self.hidden_teams[team]]

    def _viewer_sides(self, seat):
        if seat in ('O', 'X'):
            return {seat}
        if seat == 'both':
            humans = {s for s in ('O', 'X') if s not in self.ai}
            return humans if len(humans) == 1 else set()
        return set()

    def _possession_state(self, o_sq=TABLE_O, x_sq=TABLE_X, arrows=TABLE_ARROWS, ball=0):
        if self.scenario:
            return scenario_state(self.scenario, rules=self.rules)
        off, dfn = (self.teams if self.possession % 2 == 1 else self.teams[::-1])
        tf, left = self.quarter_context()
        s = game_state(off, dfn, list(o_sq), list(x_sq), list(arrows), ball=ball, rules=self.rules,
                       team_fouls=tf, quarter_left=left)
        s.ctx.levels_key = self.levels_key()        # step 3n C: the phase table of this age and standard
        return s

    def quarter_context(self):
        """(the defence's team fouls before this possession, the defence's possessions left in the quarter including
        this one) in the digital format; (0, 0) otherwise."""
        if getattr(self, 'match_format', 'tabletop') != 'digital':
            return 0, 0
        att = 'A' if self.possession % 2 == 1 else 'B'
        dfn = 'B' if att == 'A' else 'A'
        n = (self.rules or RC.DEFAULT_RULES).quarter_possessions
        return self.quarter['fouls'][dfn], max(1, n - self.quarter['poss'][att])

    def quarter_words(self):
        if self.match_format != 'digital':
            return None
        r = self.state.ctx.rules
        att = self.offence_player()
        dfn = 'B' if att == 'A' else 'A'
        left = max(0, r.quarter_possessions - min(self.quarter['poss'].values()))
        return dict(A=self.quarter['fouls']['A'], B=self.quarter['fouls']['B'], bonus_from=r.bonus_from, left=left,
                    number=self.quarter['number'], defending=dfn,
                    text=f"Team fouls {self.quarter['fouls'][dfn]} · bonus from the {r.bonus_from}th · {left} "
                         f"possession{'s' if left != 1 else ''} left this quarter")

    # ---- the pre-game scouting call (hunt one matchup, protect one weakness) ----
    def picks_needed(self, side):
        """What a side picks at Scout level: in a full match both; otherwise the offence hunts and the
        defence protects."""
        if self.level != 'scout':
            return []
        if self.full:
            return ['hunt', 'protect']
        return ['hunt'] if side == 'O' else ['protect']

    def report_visible(self, seat):
        """Read the cards first (Scout level): the report unlocks for a client once its picks are locked.
        A hot-seat client is both players, so it unlocks when both sides have picked."""
        if self.level == 'pro':
            return False
        if self.level == 'learn':
            return True
        if seat == 'both':
            return not self.picks_pending()
        return seat in ('O', 'X') and (seat in self.picks or not self.picks_needed(seat))

    def picks_pending(self):
        return [side for side in ('O', 'X') if self.picks_needed(side) and side not in self.picks]

    def team_of(self, side):
        """Team name for a seat at possession 1 (in a full match, O = player A)."""
        st = scenario_state(self.scenario) if self.scenario else None
        if self.scenario:
            return st.ctx.off_team if side == 'O' else st.ctx.def_team
        return self.teams[0] if side == 'O' else self.teams[1]

    def _engine_picks(self, side):
        from playmaker_engine.scouting import hunt_protect
        other = 'X' if side == 'O' else 'O'
        mine, theirs = TEAMS[self.team_of(side)], TEAMS[self.seen_team(other, side)]   # their tags still face down
        out = {}
        if 'hunt' in self.picks_needed(side):
            h = hunt_protect(mine, theirs)['hunt']
            out['hunt'] = dict(o=h['o'], x=h['x'])
        if 'protect' in self.picks_needed(side):
            p = hunt_protect(theirs, mine)['protect']
            out['protect'] = dict(x=p['x'])
        return out

    def scout(self, token, body):
        with self.lock:
            seat = self.seat_of(token)
            if seat is None:
                raise GameError('unknown player token')
            side = body.get('side') if seat == 'both' else seat
            if side not in ('O', 'X'):
                raise GameError('say which side is picking')
            need = self.picks_needed(side)
            if not need:
                raise GameError('no scouting picks at this detail level')
            if side in self.picks:
                raise GameError('this side has already picked')
            picks = {}
            for kind in need:
                v = body.get(kind) or {}
                try:
                    if kind == 'hunt':
                        picks['hunt'] = dict(o=int(v['o']), x=int(v['x']))
                        ok = 1 <= picks['hunt']['o'] <= 5 and 1 <= picks['hunt']['x'] <= 5
                    else:
                        picks['protect'] = dict(x=int(v['x']))
                        ok = 1 <= picks['protect']['x'] <= 5
                except (KeyError, TypeError, ValueError):
                    ok = False
                if not ok:
                    raise GameError(f'pick a player for {kind}')
            self._save_picks(side, picks, actor='human')
            if not self.picks_pending():
                self._begin_possession()

    def _save_picks(self, side, picks, actor):
        self.picks[side] = picks
        self.version += 1
        self._log('scout', side=side, actor=actor, picks=picks)

    def review(self, token):
        """The post-game review (labelled estimates where the solver is involved)."""
        from playmaker_engine.review import board_advantages, solver_disagreements
        if self.seat_of(token) is None:
            raise GameError('unknown player token')
        if not self.feedback_due():
            raise GameError('the review comes at the end of the match (or of a scenario or single possession)')
        if self.review_cache is None:
            recs = self.read_log()
            # Only the calls that apply: both in a full match, else the offence hunts and the defence protects.
            shape = {side: (['hunt', 'protect'] if self.full else ['hunt'] if side == 'O' else ['protect'])
                     for side in ('O', 'X')}
            engine = {side: {k: v for k, v in self._engine_picks_any(side).items() if k in shape[side]}
                      for side in ('O', 'X')}
            out = dict(level=self.level, picks=self.picks, engine=engine, advantages=board_advantages(recs))
            from playmaker_engine.review import timer_facts, computer_facts
            out['timer'] = timer_facts(recs) if self.timer else None
            out['computer'] = computer_facts(recs)
            if self.level != 'pro':
                from playmaker_engine.review import report_in_play
                from playmaker_engine.scouting import report
                out['in_play'] = report_in_play(recs, report(self.team_of('O'), self.team_of('X'), 'scout'))
            try:
                if getattr(self, 'static', False):
                    raise ImportError('the in-browser build skips the solver review (too slow there)')
                from playmaker_engine import solver  # noqa: F401
                out['solver'] = solver_disagreements(recs)
                out['solver_note'] = 'Estimates from a short solver search (about a second per decision).'
            except ImportError:
                out['solver'] = None
                out['solver_note'] = ('Solver estimates need the server version (python -m playmaker_web), or run '
                                      '"python -m playmaker_engine review <log>" on the downloaded log.')
            self.review_cache = out
        return self.review_cache

    def _engine_picks_any(self, side):
        from playmaker_engine.scouting import hunt_protect
        mine, theirs = TEAMS[self.team_of(side)], TEAMS[self.team_of('X' if side == 'O' else 'O')]
        h = hunt_protect(mine, theirs)['hunt']
        p = hunt_protect(theirs, mine)['protect']
        return dict(hunt=dict(o=h['o'], x=h['x'], text=h['text']), protect=dict(x=p['x'], text=p['text']))


    # ---- the decision timer (step 3d part C; off by default) ----
    def _timer_settings(self, t):
        """t: None / 0 (off), a number of seconds for both, or {A: s, B: s, handicap: true}. A is the player
        on offence in possession 1. Different settings need handicap ticked by both players."""
        if not t:
            return None
        ok = TIMER_CONFIG['settings']
        if isinstance(t, (int, float)):
            t = dict(A=int(t), B=int(t))
        a, b = t.get('A'), t.get('B')
        a = int(a) if a else None
        b = int(b) if b else None
        if a not in ok or b not in ok:
            raise GameError(f'timer settings are {", ".join(str(x) for x in ok[1:])} seconds or off')
        handicap = bool(t.get('handicap'))
        if a != b and not handicap:
            raise GameError('different timer settings need the handicap ticked by both players')
        if a is None and b is None:
            return None
        return dict(A=a, B=b, handicap=handicap and a != b, grace=TIMER_CONFIG['grace'],
                    regrace_after=TIMER_CONFIG['regrace_after'])

    def _player_of(self, side):
        att = self.offence_player()
        return att if side == 'O' else ('B' if att == 'A' else 'A')

    def _period(self, side):
        return self.timer[self._player_of(side)] if self.timer else None

    def _timed_side(self):
        """The side whose decision is on the clock now, or None (no timer before tip-off, for the computer,
        in the Coach's Call secret entry or once the possession is over)."""
        side = self.side_to_act()
        if not self.timer or side is None or side in self.ai or self.state.stage not in TIMED_STAGES:
            return None
        return side if self._period(side) else None

    def _timer_decision(self, force_ready=False):
        """A new decision began (an action was committed, a forfeit applied, a turn changed...)."""
        if not self.timer:
            return
        now = self.now()
        side = self._timed_side()
        prev = getattr(self, 'tm', None) or {}
        if side is None:
            self.tm = dict(mode='idle', side=None)
            return
        handover = self.mode == 'hotseat' and (force_ready or prev.get('side') != side)
        self.tm = dict(mode='ready' if handover else 'main', side=side, period=self._period(side),
                       left=float(self._period(side)), mark=None if handover else now, paused=False,
                       grace_until=None, grace_left=None, sel_left=None, selected=False, grace_used=0.0,
                       token_free=token_free(self.state))

    def _main_left(self, now):
        tm = self.tm
        if tm['mode'] != 'main' or tm['mark'] is None:
            return tm['left']
        return tm['left'] - (now - tm['mark'])

    def timer_tick(self):
        """Catch the timer up to now: expire graces and apply forfeits at the moments they fell due."""
        if not self.timer:
            return
        with self.lock:
            now = self.now()
            for _ in range(200):
                tm = getattr(self, 'tm', None)
                if not tm or tm['mode'] in ('idle', 'ready') or tm['paused']:
                    return
                if tm['mode'] == 'grace':
                    if now < tm['grace_until']:
                        return
                    t = tm['grace_until']
                    tm['grace_used'] += self.timer['grace']
                    tm.update(mode='main', mark=t, grace_until=None)
                    self._log('timer', event='grace_expired', side=tm['side'], possession=self.possession,
                              clock=self.state.clock, phase=self.state.phase, turn=self.state.turn_n)
                    continue
                due = tm['mark'] + tm['left']
                if now < due:
                    return
                self._forfeit(due)

    def _forfeit(self, t):
        before = self.state
        side = self.tm['side']
        node, effect = timer_forfeit(before)
        rolls = []
        if isinstance(node, ChanceNode):
            node, rolls = resolve_chance(node, self.rng)
        self.state = node
        self.undo, self.undo_votes = [], set()
        if node.phase != before.phase:
            self.slots = {'O': {i: [] for i in range(5)}, 'X': {i: [] for i in range(5)}}
            self.turn_no = 0
        self.rolls = rolls
        self.version += 1
        left = node.tokens(side) if node.stage in ('play', 'reaction') and node.side == side else None
        if effect == 'default':
            what = "Timer: time ran out; the default applies (don't contest)." if before.stage == 'contest' else \
                   'Timer: time ran out; the default applies (the first legal choice).'
        elif effect == 'token':
            what = f'Timer: 1 token lost. {before.tokens(side) - 1} left.'
        elif effect == 'token_end':
            what = 'Timer: 1 token lost, the last one. The turn ends.'
        else:
            what = 'Timer: no tokens left. The turn ends.'
        self._log('timer', event='forfeit', side=side, effect=effect, possession=self.possession,
                  clock=before.clock, phase=before.phase, turn=before.turn_n, stage=before.stage,
                  tokens_before=before.tokens(side), text=what, after=node.encode())
        for r in rolls:
            self._log('roll', possession=self.possession, **r)
        self.feed.append(dict(n=len(self.feed) + 1, actor='timer', side=side, kind='timer', text=what, rolls=rolls,
                              outcomes=consequences(before, node, Action('end_turn', side)) if node.stage == 'over' else [],
                              possession=self.possession, clock=before.clock, phase=before.phase, version=self.version))
        self.timer_note = what
        if node.stage == 'over':
            self._end_possession()
        same = self._timed_side() == side and node.stage in TIMED_STAGES
        if same and self.tm['mode'] == 'main':
            # the turn goes on: the timer restarts at full from the moment of the forfeit
            self.tm.update(left=float(self.tm['period']), mark=t, sel_left=None, selected=False,
                           grace_used=0.0, token_free=token_free(node))
        else:
            self._timer_decision()
            if self.tm['mode'] == 'main':
                self.tm['mark'] = t
        self._run_ai()
        if self.tm.get('mode') != 'idle' and self.tm.get('side') != self._timed_side():
            self._timer_decision()

    def timer_event(self, token, event):
        """From the acting player's page: ready (hot-seat handover), select / cancel (an action), pause /
        resume (a roll preview, roll result or turn card is open)."""
        if not self.timer:
            raise GameError('this game has no timer')
        with self.lock:
            self.timer_tick()
            tm = self.tm
            if tm['mode'] == 'idle' or not self.can_act(token):
                return
            now = self.now()
            if event == 'ready':
                if tm['mode'] == 'ready':
                    tm.update(mode='main', mark=now)
                    self.version += 1
            elif event == 'pause':
                if tm['mode'] in ('main', 'grace') and not tm['paused']:
                    tm['left'] = self._main_left(now)
                    if tm['mode'] == 'grace':
                        tm['grace_left'] = tm['grace_until'] - now
                    tm.update(paused=True, mark=None)
            elif event == 'resume':
                if tm['paused']:
                    tm['paused'] = False
                    if tm['mode'] == 'grace':
                        tm['grace_until'] = now + tm['grace_left']
                    else:
                        tm['mark'] = now
            elif event == 'select':
                if tm['mode'] == 'grace':                       # switching action: like cancel, then select
                    self._end_grace(now, cancelled=True)
                if tm['mode'] == 'main' and not tm['paused']:
                    left = self._main_left(now)
                    fresh = tm['sel_left'] is None or (tm['sel_left'] - left) >= self.timer['regrace_after']
                    tm['selected'] = True
                    if fresh:
                        tm.update(mode='grace', left=left, mark=None, grace_until=now + self.timer['grace'],
                                  sel_left=left, grace_start=now)
            elif event == 'cancel':
                if tm['mode'] == 'grace':
                    self._end_grace(now, cancelled=True)
                elif tm['selected']:
                    tm['selected'] = False
                    self._log('timer', event='cancel', side=tm['side'], possession=self.possession,
                              clock=self.state.clock, phase=self.state.phase, turn=self.state.turn_n, grace=False)
            else:
                raise GameError('timer events: ready, select, cancel, pause, resume')

    def _end_grace(self, now, cancelled):
        tm = self.tm
        tm['grace_used'] += now - tm.get('grace_start', now)
        tm.update(mode='main', mark=now, grace_until=None, selected=False)
        if cancelled:
            self._log('timer', event='cancel', side=tm['side'], possession=self.possession,
                      clock=self.state.clock, phase=self.state.phase, turn=self.state.turn_n, grace=True)

    def timer_json(self):
        if not self.timer:
            return None
        self.timer_tick()
        tm = getattr(self, 'tm', None) or dict(mode='idle', side=None)
        now = self.now()
        out = dict(setting=dict(A=self.timer['A'], B=self.timer['B']), handicap=self.timer['handicap'],
                   by_side=dict(O=self._period('O'), X=self._period('X')), mode=tm['mode'], side=tm.get('side'),
                   period=tm.get('period'), paused=tm.get('paused', False), token_free=tm.get('token_free', False),
                   grace=self.timer['grace'], warn_at=TIMER_CONFIG['warn_at'], note=getattr(self, 'timer_note', None))
        if tm['mode'] in ('main', 'grace', 'ready'):
            out['left'] = round(max(0.0, self._main_left(now)), 2)
        if tm['mode'] == 'grace':
            out['grace_left'] = round(max(0.0, (tm['grace_left'] if tm['paused'] else tm['grace_until'] - now)), 2)
        return out

    # ---- placement (rulebook setup steps 4 and 5) ----
    def _begin_possession(self):
        if self.hidden_teams and not getattr(self, '_revealed', False):
            self._revealed = True                    # setup begins: the growth tags are turned face up
            self.version += 1
            self._log('reveal', tags=self.levels.get('tags'))
        if self.place_on:
            self.placing, self.placed = 'O', {}
            self.version += 1
            self._auto_place()
        else:
            self._run_ai()
        self._timer_decision()

    def _auto_place(self):
        """The computer places its side (step 3m B6): the offence by the placement that maximises the position's value
        against the defence's best reply (it never sees the real defence); the defence by best cover. The baseline
        (an old policy without a setup) uses the preview squares and man-to-man."""
        from playmaker_engine import agent as AG
        while self.placing and self.placing in self.ai:
            comp = self.policies.get(self.placing)
            level = getattr(comp, 'level', None)
            seed = (self.seed or 0) * 31 + self.possession
            budget = self._setup_budget(level)
            if self.placing == 'O':
                if level:
                    r = AG.propose_offence(self._possession_state, seed, self.levels_key(), budget=budget, level=level)
                    self._log('computer', side='O', event='setup', possession=self.possession,
                              squares=[B.sq(q) for q in r['squares']], ball=r['ball'], value=r['value'],
                              candidates=r['candidates'], within=r['within'], text=r['text'])
                    self._place_side('O', r['squares'], r['ball'], None, actor='ai')
                else:
                    self._place_side('O', [B.parse_sq(q) for q in TABLE_O], 0, None, actor='ai')
            else:
                o_sq, ball = self.placed['O']
                if level:
                    r = AG.propose_defence(self._possession_state, o_sq, ball, seed + 7, self.levels_key(), budget=budget,
                                           level=level)
                    comp.setup_perm = tuple(r['perm'])
                    self._log('computer', side='X', event='setup', possession=self.possession,
                              matchup=[f'X{j + 1} on O{r["perm"][j] + 1}' for j in range(5)], value=r['value'], text=r['text'])
                    self._place_side('X', r['squares'], None, r['arrows'], actor='ai')
                else:
                    xs, arrows = man_to_man(o_sq, ball)
                    self._place_side('X', xs, None, arrows, actor='ai')

    def _setup_budget(self, level):
        """Setup thinking time: instant-feeling in the digital format (a fraction of the level's decision budget)."""
        from playmaker_engine import agent as AG
        if not level:
            return 0.0
        b = AG.profile(level)['time_budget_s'] * AG.SCALE['value']
        return b * (0.4 if self.match_format == 'digital' else 1.0)

    def place(self, token, body):
        with self.lock:
            if self.picks_pending():
                raise GameError('waiting for the scouting picks before tip-off')
            if not self.placing:
                raise GameError('nothing to place now')
            seat = self.seat_of(token)
            if seat is None:
                raise GameError('unknown player token')
            if body.get('repeat'):
                # step 3m Part A: repeat this player's last setup on this side (legality unchanged)
                if seat != 'both' and seat != self.placing:
                    raise GameError(f'the {"offence" if self.placing == "O" else "defence"} is placing')
                last = self.last_setup.get((self._player_of(self.placing), self.placing))
                if not last:
                    raise GameError('no earlier setup on this side to repeat')
                sq, ball, arrows = last
                self._place_side(self.placing, sq, ball, arrows, actor='human')
                self._auto_place()
                return
            if body.get('propose'):
                # step 3m Part A: accept the engine's proposed setup for this side
                if seat != 'both' and seat != self.placing:
                    raise GameError(f'the {"offence" if self.placing == "O" else "defence"} is placing')
                if self.placing in self.ai:
                    raise GameError('the computer places this side')
                prop = self.proposal(self.placing)
                self._place_side(self.placing, prop['squares'], prop.get('ball'), prop.get('arrows'), actor='human')
                self._auto_place()
                return
            if body.get('preview'):
                if self.ai:
                    # against the computer: the standard setup for the human's own side only; the computer places its own
                    if self.placing in self.ai:
                        raise GameError('the computer places this side')
                    if self.placing == 'O':
                        self._place_side('O', [B.parse_sq(q) for q in TABLE_O], 0, None, actor='human')
                    else:
                        xs, arrows = man_to_man(self.placed['O'][0], self.placed['O'][1])
                        self._place_side('X', xs, None, arrows, actor='human')
                    self._auto_place()
                    return
                if seat != 'both' and seat != self.placing:
                    raise GameError('the preview shortcut sets both sides: use it in hot-seat or before joining')
                self._place_side('O', [B.parse_sq(q) for q in TABLE_O], 0, None, actor='human')
                self._place_side('X', [B.parse_sq(q) for q in TABLE_X], None, list(TABLE_ARROWS), actor='human')
                return
            if seat != 'both' and seat != self.placing:
                raise GameError(f'the {"offence" if self.placing == "O" else "defence"} is placing')
            if self.placing in self.ai:
                raise GameError('the computer places this side')
            try:
                squares = [B.parse_sq(q) for q in body.get('squares') or []]
            except (ValueError, IndexError):
                raise GameError('squares must be names like I11')
            arrows = body.get('arrows')
            self._place_side(self.placing, squares, body.get('ball'), arrows, actor='human')
            self._auto_place()

    def proposal(self, side):
        """The engine's proposed setup for a side (step 3m B6): {squares, ball} on offence, {squares, arrows} on
        defence. Cached per possession and side."""
        key = (self.possession, side, tuple(map(tuple, self.placed['O'][0])) if side == 'X' else None)
        cache = getattr(self, '_proposals', {})
        if key not in cache:
            from playmaker_engine import agent as AG
            if side == 'O':
                r = AG.propose_offence(self._possession_state, self.seed * 31 + self.possession, self.levels_key())
                cache[key] = dict(squares=r['squares'], ball=r['ball'], text=r.get('text', ''))
            else:
                o_sq, ball = self.placed['O']
                r = AG.propose_defence(self._possession_state, o_sq, ball, self.seed * 37 + self.possession, self.levels_key())
                cache[key] = dict(squares=r['squares'], arrows=r['arrows'], text=r.get('text', ''))
            self._proposals = cache
        return cache[key]

    def levels_key(self):
        lv = self.levels or {}
        std = lv.get('standard', 'pro')
        return (lv.get('age', 'senior'), std if isinstance(std, str) else 'pro')

    def _place_side(self, side, squares, ball, arrows, actor):
        if len(squares) != 5 or len(set(squares)) != 5:
            raise GameError('place all 5 pieces on 5 different squares')
        if not all(B.on_board(q) for q in squares):
            raise GameError('every piece must be on the court')
        if side == 'O':
            if ball is None or not 0 <= int(ball) < 5:
                raise GameError('choose the player with the ball')
            ball = int(ball)
            bq = squares[ball]
            if not (B.zone(bq) == '.' and bq[1] > 1):
                raise GameError('the ball must start on a player standing on plain wood beyond the three-point tiles')
            self.placed['O'] = (squares, ball)
            self.placing = 'X'
        else:
            o_sq, ball = self.placed['O']
            if set(squares) & set(o_sq):
                raise GameError('defenders go on empty squares')
            if arrows is None or len(arrows) != 5:
                raise GameError('set an arrow for each defender')
            arrows = [B.DIR_NAMES.index(a) if isinstance(a, str) else int(a) for a in arrows]
            if not all(0 <= a < 8 for a in arrows):
                raise GameError('arrows are 0-7 or compass names')
            errs = setup_errors(tuple(o_sq), tuple(squares), ball)
            if errs:
                raise GameError('; '.join(errs))
            self.state = self._possession_state([B.sq(q) for q in o_sq], [B.sq(q) for q in squares],
                                                arrows, ball)
            self.placing = None
        if actor == 'human':
            self.last_setup[(self._player_of(side), side)] = (list(squares), ball if side == 'O' else None,
                                                             list(arrows) if side == 'X' else None)
        self._log('placement', possession=self.possession, side=side, actor=actor,
                  squares=[B.sq(q) for q in squares], ball=ball if side == 'O' else None,
                  arrows=[B.DIR_NAMES[a] for a in arrows] if side == 'X' else None,
                  start=self.state.encode() if side == 'X' else None)
        self.version += 1
        if self.placing is None:
            self._run_ai()
            self._timer_decision()

    def offence_player(self):
        """Which player (A or B) is attacking this possession."""
        return 'A' if self.possession % 2 == 1 else 'B'

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

    def feedback_due(self):
        """The feedback form appears once: at the end of the match, a scenario or a single possession."""
        if self.state.stage != 'over' or self.placing:
            return False
        return (not self.full) or self.possession == self.n_poss

    def side_to_act(self):
        if self.placing or self.picks_pending():
            return None
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
            self.timer_tick()
            if self.picks_pending():
                raise GameError('waiting for the scouting picks before tip-off')
            if self.placing:
                raise GameError('the pieces are still being placed')
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
                from playmaker_engine.actions import why_illegal
                why = why_illegal(self.state, a) if self.state.stage != 'over' else None
                raise GameError(f'illegal action: {a}: {why}' if why else f'illegal action: {a} is not among the {len(legal)} legal actions now')
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
            self.undo.append((before, self.rng.getstate(), json.dumps(self.slots), self.turn_no))
        if a.kind not in ('end_turn', 'forfeit', 'target', 'pick'):
            self.slots[a.side][a.piece if a.piece >= 0 else 0].append(a.kind)
        if a.side == 'O' and before.turn_n == 0 and before.stage in ('play', 'target', 'pick', 'forced'):
            self.turn_no += 1            # a new offence turn in this phase
        turn = self.turn_no
        mark = notation(before, node, a, turn)
        if node.phase != before.phase:
            self.slots = {'O': {i: [] for i in range(5)}, 'X': {i: [] for i in range(5)}}
            self.turn_no = 0
        self.state = node
        self.rolls = rolls
        self.undo_votes = set()
        self.version += 1
        rec = dict(actor=actor, action=action_to_json(a),
                   legal=[str(x) for x in legal] if a.kind != 'target' else [f'O{i + 1}' for i in range(5)],
                   seconds=round(now - self.last_decision, 2), clock=before.clock, phase=before.phase,
                   possession=self.possession, after=node.encode())
        if actor == 'ai' and getattr(self, '_think', None) is not None:
            rec['think_s'] = self._think
            self._think = None
        tm = getattr(self, 'tm', None)
        if self.timer and tm and actor == 'human' and tm.get('mode') in ('main', 'grace'):
            g = tm['grace_used'] + ((self.now() - tm.get('grace_start', self.now())) if tm['mode'] == 'grace' else 0)
            rec['grace_s'] = round(g, 2)
            rec['timer_left'] = round(max(0.0, self._main_left(self.now())), 2)
        if a.kind == 'target':
            rec['action'] = dict(kind='target', side='O', text="Coach's Call target chosen (secret)", target=a.target)
        if a.side == 'X' and a.kind in ('move', 'qs', 'sprint') and not isinstance(node, ChanceNode) and node.stage != 'over':
            from playmaker_engine.defence import arrow_job
            rec['arrow_job'] = arrow_job(node, a.piece)
        self._log('action', **rec)
        self.timer_note = None
        for r in rolls:
            self._log('roll', possession=self.possession, **r)
        self.last_decision = time.time()
        text = rec['action']['text']
        from .view import board_json
        from playmaker_engine.review import best_look
        entry = dict(n=len(self.feed) + 1, actor=actor, side=a.side, kind=a.kind, text=text, rolls=rolls,
                     outcomes=consequences(before, node, a), possession=self.possession,
                     clock=before.clock, phase=before.phase, version=self.version,
                     turn=turn, mark=mark, board=board_json(node, self.slots))
        # the read the board offered before this action (the best ▲ look): kept aside, never in a play payload
        # (neutrality: the page judges nothing during play); the story releases it once the possession is over
        if a.kind != 'target':
            self.looks = getattr(self, 'looks', {})
            self.looks[entry['n']] = best_look(before)
        if not self.feed or self.feed[-1]['possession'] != self.possession:
            entry['before'] = board_json(before, self.slots)     # the first of a possession: where it all stood
        self.feed.append(entry)
        if node.stage == 'over':
            self._end_possession()
        self._timer_decision()
        return dict(rolls=rolls)

    def _run_ai(self):
        while True:
            side = self.side_to_act()
            if side is None or side not in self.ai:
                return
            pol = self.policies[side]
            if not hasattr(pol, 'describe'):
                pol.reset(self.seed * 7 + self.version)
            t0 = time.time()
            a = pol.choose(self.state)
            self._think = round(time.time() - t0, 3)
            for note in getattr(pol, 'notes', []):
                self._log('computer', side=side, possession=self.possession, clock=self.state.clock, **note)
            if hasattr(pol, 'notes'):
                pol.notes.clear()
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
            st, rs, slots, turn_no = self.undo.pop()
            if self.feed:
                self.feed.pop()
            self.turn_no = turn_no
            self.state = st
            self.rng.setstate(rs)
            self.slots = {k: {int(i): v for i, v in d.items()} for k, d in json.loads(slots).items()}
            self.undo_votes = set()
            self.rolls = []
            self.version += 1
            self._log('undo', possession=self.possession, state=st.encode())
            self._timer_decision(force_ready=True)
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
                                target=self.state.target, final_shot=final, ended=r.kind if r else None))
        self._log('end', possession=self.possession, score=_score_json(sc), target=self.state.target)
        if self.match_format == 'digital':
            # step 3n F3: the defence's fouls this possession (steal fouls and the shooting foul) join its team total
            att = self.offence_player()
            dfn = 'B' if att == 'A' else 'A'
            self.quarter['fouls'][dfn] += self.state.fouls
            self.quarter['poss'][att] += 1
            n = self.state.ctx.rules.quarter_possessions
            if self.quarter['poss']['A'] >= n and self.quarter['poss']['B'] >= n:
                self.quarter = dict(fouls=dict(A=0, B=0), poss=dict(A=0, B=0), number=self.quarter['number'] + 1)
            self._log('quarter', **self.quarter)
        if self.full and self.possession == self.n_poss:
            self._finish_match()

    def next_possession(self, token):
        with self.lock:
            if self.seat_of(token) is None:
                raise GameError('unknown player token')
            if not (self.full and self.possession < self.n_poss and self.state.stage == 'over'):
                raise GameError('no next possession')
            self.possession += 1
            self._set_ai()
            self.state = self._possession_state()
            self.undo, self.rolls = [], []
            self.feed.append(dict(n=len(self.feed) + 1, actor='system', side='-', kind='possession',
                                  text=f'Possession {self.possession}: sides swap', rolls=[], outcomes=[], possession=self.possession,
                                  clock=self.state.clock, phase=self.state.phase, version=self.version + 1))
            self.slots = {'O': {i: [] for i in range(5)}, 'X': {i: [] for i in range(5)}}
            self.turn_no = 0
            self.version += 1
            self._log('possession', possession=self.possession,
                      teams=self.teams if self.possession % 2 == 1 else self.teams[::-1], start=self.state.encode())
            self._begin_possession()

    def _finish_match(self):
        if self.match_format == 'digital':
            tot = {p: sum(x['total'] for x in self.scores if x['attacker'] == p) for p in ('A', 'B')}
            m = dict(A=tot['A'], B=tot['B'], format='digital', per_side=self.per_side,
                     winner='A' if tot['A'] > tot['B'] else 'B' if tot['B'] > tot['A'] else 'tie')
            self.match = m
            self._log('match', **m)
            return
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

    # ---- step 3m Part D: the trainer ----
    def human_players(self):
        return [p for p in ('A', 'B') if p not in self.ai_players and not (self.ai_sides and len(self.ai_sides) == 2)]

    def trainer_read(self, token, possession=None, budget=None):
        """The trainer's read of one finished possession for each human player in it: every turn group graded
        (snapshots for replays), the 1 to 3 point summary, the possession's accuracy."""
        from playmaker_engine import trainer as TR
        from playmaker_engine.labels import possession_events, recognise
        if self.seat_of(token) is None:
            raise GameError('unknown player token')
        possession = int(possession or self.possession)
        done = [x['possession'] for x in self.scores]
        if possession not in done:
            raise GameError('the trainer reads a possession once it is over')
        cache = getattr(self, '_trainer', {})
        if possession in cache:
            return cache[possession]
        events = dict(possession_events(self.read_log())).get(possession, [])
        att = 'A' if possession % 2 == 1 else 'B'
        sides = {'O': att, 'X': 'B' if att == 'A' else 'A'}
        out = dict(possession=possession, players={}, labels=recognise(events), format=self.match_format)
        for side, player in sides.items():
            if side in self.ai:
                continue
            b = budget if budget is not None else TR.TC.get('budget_s', 0.15)
            r = TR.read_possession(events, side, budget=b)
            out['players'][player] = dict(side=side, **r)
        cache[possession] = out
        self._trainer = cache
        self._log('trainer', possession=possession,
                  accuracy={p: v['accuracy'] for p, v in out['players'].items()},
                  summary={p: [x['text'] for x in v['summary']] for p, v in out['players'].items()})
        return out

    def trainer_why(self, token, possession, group, player=None):
        """'Why?' for one turn group: goals, credits, the defence's reply and the better option, at a deeper read."""
        from playmaker_engine import trainer as TR
        from playmaker_engine.labels import possession_events
        from playmaker_engine.state import GameState
        rd = self.trainer_read(token, possession)
        player = player or next(iter(rd['players']), None)
        if player not in rd['players']:
            raise GameError('no human turn groups in that possession')
        groups = rd['players'][player]['groups']
        if not 0 <= int(group) < len(groups):
            raise GameError('no such turn group')
        g = groups[int(group)]
        events = dict(possession_events(self.read_log())).get(int(possession), [])
        s = events[g['index']][0]
        acts = [e[1] for e in events[g['index']:g['index'] + len(g['actions'])]]
        why = dict(group=g, goal=TR.goal_read(s, acts, budget=0.6))
        if acts and acts[0].side == 'O' and s.stage == 'play':
            c1 = TR.credit(s, acts, depth=1, budget=0.4)
            c2 = TR.credit(s, acts, depth=2, budget=0.6)
            why['credits'] = c1
            why['flags'] = TR.flags(s, acts, c1, c2)
        n = None
        from playmaker_engine.search import play_turn
        after = play_turn(s, acts)
        val, rep, _ = TR._reply(after if not hasattr(after, 'outcomes') else after.outcomes[0][2], 1, 0.4)
        why['reply'] = [str(a) for a in (rep or ())]
        from playmaker_engine import plain as PL
        why['reply_text'] = PL.turn(list(rep)) if rep else None
        why['format'] = self.match_format
        return why

    def save_feedback(self, token, answers):
        if self.seat_of(token) is None:
            raise GameError('unknown player token')
        if not self.feedback_due():
            raise GameError('feedback comes at the end of the match (or of a scenario or single possession)')
        self.feedback = answers
        self._log('feedback', seat=self.seat_of(token),
                  answers=[dict(question=q, answer=answers.get(str(i), '')) for i, q in enumerate(FEEDBACK_QUESTIONS)],
                  reflection=dict(question=REFLECT_QUESTION, answer=answers.get('reflect', '')))

    # ---- the play story: one diagram per phase ----
    def story(self):
        """Every possession's phases: the board at the phase's start (squares, ball, screens, arrows), the
        clock, and the phase's actions with their notation marks and turn numbers."""
        out = []
        cur = None
        prev_board = None
        for e in self.feed:
            if e.get('actor') == 'system':
                prev_board = None
                continue
            key = (e['possession'], e['phase'])
            if cur is None or (cur['possession'], cur['phase']) != key:
                start = e.get('before') or prev_board
                cur = dict(possession=e['possession'], phase=e['phase'], clock=e['clock'], start=_start_json(start), entries=[])
                out.append(cur)
            cur['entries'].append(dict(n=e['n'], side=e['side'], actor=e['actor'], turn=e.get('turn'), text=e['text'],
                                       kind=e['kind'], mark=e.get('mark'),
                                       rolls=[dict(face=r['face'], need=r['need'], picked=r['picked'], roller=r['roller']) for r in e.get('rolls', [])],
                                       outcomes=e.get('outcomes', [])))
            cur['end_clock'] = e['board']['clock'] if e.get('board') else None
            cur['over'] = bool(e.get('board')) and e['board'].get('stage') == 'over'
            prev_board = e.get('board')
            look = getattr(self, 'looks', {}).get(e['n'])
            if look and (cur.get('look') is None or look['value'] > cur['look']['value']):
                cur['look'] = dict(look)
            if e['kind'] in ('shot', 'forced_shot') and cur.get('look') and e.get('mark') and e['mark'].get('piece') == cur['look']['o'] - 1:
                cur['look']['taken'] = True
        # the feedback stays out of a possession still being played: only a finished possession carries its looks
        finished = {p['possession'] for p in out if p.get('over')} | {p['possession'] for p in out if p['possession'] < self.possession}
        for p in out:
            if p['possession'] not in finished:
                p.pop('look', None)                  # absent: not released yet
            else:
                p.setdefault('look', None)           # None: released, and no ▲ look came onto the board
        return dict(possessions=sorted({p['possession'] for p in out}), phases=out,
                    arrow_mode=self.state.ctx.rules.arrow_mode, teams=self.teams, title=self.state.ctx.title,
                    scores=self.scores)

    # ---- log ----
    def _log(self, kind, **data):
        data = dict(type=kind, time=round(time.time(), 3), code=self.code, **data)
        with open(self.log_path, 'a') as f:
            f.write(json.dumps(data, default=str) + '\n')

    def read_log(self):
        with open(self.log_path) as f:
            return [json.loads(line) for line in f]


def _start_json(b):
    if not b:
        return None
    return dict(o=[dict(sq=p['sq'], ball=p['ball'], screen=p.get('screen')) for p in b['o']],
                x=[dict(sq=p['sq'], arrow=p['arrow']) for p in b['x']])


def _score_json(sc):
    return dict(total=sc.total, band=sc.band, shot_value=sc.shot_value, free_throws=sc.free_throws,
                bonus=sc.bonus, turnovers=sc.turnovers, turnover_points=sc.turnover_points,
                coach_bonus=sc.coach_bonus, look=sc.look, goal_met=sc.goal_met, late_clock=sc.late_clock,
                detail=sc.detail)
