"""GameState: an immutable, hashable snapshot of a possession, plus printers."""
from dataclasses import dataclass, field, replace

from . import board as B
from . import rules_config as RC

# Per-phase counters, in a fixed order inside GameState.cnt
COUNT_KEYS = ('o_qs', 'pass', 'screen', 'dribble', 'hesitate', 'shot',
              'x_qs', 'intercept', 'challenge', 'steal', 'pause')
CI = {k: i for i, k in enumerate(COUNT_KEYS)}
ZERO_COUNTS = (0,) * len(COUNT_KEYS)


def count_key(side, kind):
    if kind == 'qs':
        return 'o_qs' if side == 'O' else 'x_qs'
    return kind


class Context:
    """Static facts about one possession (teams, rules, scenario). Compared by identity."""

    def __init__(self, off_cards, def_cards, rules=None, title='Game', kind='GAME', scenario=None,
                 card_clock=RC.START_CLOCK, inbounder=-1, coach_call=False, three_only=False,
                 two_or_three=False, hold_for_one=False, off_team='', def_team='', team_fouls=0, quarter_left=0):
        self.off = tuple(off_cards)
        self.dfn = tuple(def_cards)
        self.rules = rules or RC.DEFAULT_RULES
        self.title, self.kind, self.scenario = title, kind, scenario
        self.card_clock = card_clock
        self.inbounder = inbounder
        self.coach_call = coach_call
        self.three_only, self.two_or_three, self.hold_for_one = three_only, two_or_three, hold_for_one
        self.off_team, self.def_team = off_team, def_team
        # step 3n F3 (digital): the defence's team fouls before this possession, and the defence's possessions left in
        # the quarter including this one
        self.team_fouls, self.quarter_left = team_fouls, quarter_left


@dataclass(frozen=True)
class Result:
    """How the possession ended."""
    kind: str                 # 'shot', 'free_throws', 'steal', 'turnover_end', 'forced'
    shooter: int = -1
    shot_type: str = ''
    points: int = 0           # 2 or 3 for the declared/forced shot, 0 if none
    rating: int = 0
    contest: int = 0
    contester: int = -1
    shot_value: int = 0       # points x (rating - contest), as scored
    free_throws: int = 0
    and_one: bool = False     # the foul scored the uncontested shot value (higher than the free throws)


@dataclass(frozen=True)
class GameState:
    ctx: Context = field(compare=False, hash=False, repr=False)
    o: tuple                  # 5 O squares
    x: tuple                  # 5 X squares
    arrows: tuple             # 5 direction indices
    ball: int                 # O index of the ball carrier
    stage: str = 'play'       # 'target', 'play', 'reaction', 'over'
    side: str = 'O'
    clock: int = RC.START_CLOCK
    tok_o: int = RC.TOKENS_PER_PHASE
    tok_x: int = RC.TOKENS_PER_PHASE
    moved_o: int = 0          # bitmask: players who used their Move
    moved_x: int = 0
    cnt: tuple = ZERO_COUNTS
    turn_n: int = 0           # actions already taken this turn
    final: bool = False       # defence's final turn after the offence ran out
    lock_o: int = 0
    lock_x: int = 0
    screens: tuple = ()       # (o index, T direction, fresh, beaten-by bitmask)
    pending: tuple = None     # (passer, receiver) awaiting the defence's answer
    approach: int = -1        # defender that moved onto the pass line this turn
    shot: str = None          # declared shot type while the defence reacts
    prev_wait: str = ''       # 'H' or 'P' if the other side's last turn ended in a wait
    beaten: tuple = ()        # (o, x) pairs: dribble wins this phase
    fouls: int = 0            # steal fouls so far
    bonus5: int = 0           # +5 bonuses earned
    tos: int = 0              # turnovers
    inbound: int = 0          # inbound phase number (1 or 2), 0 when the ball is in
    target: int = -1          # Coach's Call target (O index)
    result: Result = None
    zeroed: bool = False      # Hold for One turnover: possession scores 0
    phase: int = 1
    turn_moved: int = 0
    qs_o: int = 0             # bitmask: players who used their Quick Step this phase (a Sprint uses it too)
    qs_x: int = 0
    forced: bool = False      # the pending contest is for a forced shot at clock 0
    react_moved: int = 0      # step 3i (late_closeout test): defenders who moved square in the reaction to a shot
    turn_lead: int = -1       # OQ-29 ruling: the offence player whose Move opened this turn (he may Screen next)
    turn_x: tuple = ()        # intercept ruling: the defence's squares and arrows at the start of its turn

    # ---- helpers ----
    def count(self, side, kind):
        return self.cnt[CI[count_key(side, kind)]]

    def tokens(self, side):
        return self.tok_o if side == 'O' else self.tok_x

    def occupied(self):
        return set(self.o) | set(self.x)

    def screen_of(self, i):
        for s in self.screens:
            if s[0] == i:
                return s
        return None

    def is_screening(self, i):
        return self.screen_of(i) is not None

    def locked(self, side, i):
        return bool((self.lock_o if side == 'O' else self.lock_x) >> i & 1)

    def moved(self, side, i):
        return bool((self.moved_o if side == 'O' else self.moved_x) >> i & 1)

    def quick_stepped(self, side, i):
        return bool((self.qs_o if side == 'O' else self.qs_x) >> i & 1)

    @property
    def carrier_pos(self):
        return self.o[self.ball]

    def with_(self, **kw):
        return replace(self, **kw)

    # ---- text forms ----
    def encode(self):
        """Compact one-line encoding (stable, human-diffable)."""
        a = B.DIR_NAMES
        parts = [
            f'{self.stage}:{self.side}', f'c{self.clock}', f't{self.tok_o}/{self.tok_x}',
            'O' + ','.join(B.sq(p) for p in self.o), 'X' + ','.join(f'{B.sq(p)}{a[d]}' for p, d in zip(self.x, self.arrows)),
            f'b{self.ball + 1}', f'm{self.moved_o:02x}{self.moved_x:02x}', 'n' + ''.join(str(c) for c in self.cnt),
            f'u{self.turn_n}{"F" if self.final else ""}', f'L{self.lock_o:02x}{self.lock_x:02x}',
        ]
        if self.screens:
            parts.append('S' + ','.join(f'{i + 1}{a[d]}{"*" if f else ""}{m:x}' for i, d, f, m in self.screens))
        if self.pending:
            parts.append(f'P{self.pending[0] + 1}>{self.pending[1] + 1}' + (f'a{self.approach + 1}' if self.approach >= 0 else ''))
        if self.shot:
            parts.append('Y' + self.shot)
        if self.prev_wait:
            parts.append('W' + self.prev_wait)
        if self.beaten:
            parts.append('D' + ','.join(f'{o + 1}{x + 1}' for o, x in self.beaten))
        parts.append(f'f{self.fouls}+{self.bonus5}-{self.tos}')
        if self.inbound:
            parts.append(f'i{self.inbound}')
        if self.target >= 0:
            parts.append(f'g{self.target + 1}')
        if self.result:
            r = self.result
            parts.append(f'R{r.kind}:{r.shot_value}:{r.free_throws}')
        if self.zeroed:
            parts.append('Z')
        if self.qs_o or self.qs_x:
            parts.append(f'q{self.qs_o:02x}{self.qs_x:02x}')
        if self.react_moved:
            parts.append(f'v{self.react_moved:02x}')
        if self.turn_lead >= 0:
            parts.append(f'g{self.turn_lead + 1}')
        return '|'.join(parts)

    def board(self):
        """ASCII board: O1* = ball, O5T^ = screen with T to the north, X2NE = arrow, L = locked."""
        cells = {}
        for i, p in enumerate(self.o):
            s = f'O{i + 1}'
            if i == self.ball:
                s += '*'
            sc = self.screen_of(i)
            if sc:
                s += 'T' + B.DIR_NAMES[sc[1]].lower()
            if self.locked('O', i):
                s += 'L'
            cells[p] = s
        for i, p in enumerate(self.x):
            s = f'X{i + 1}{B.DIR_NAMES[self.arrows[i]]}'
            if self.locked('X', i):
                s += 'L'
            cells[p] = s
        cw = 7
        lines = []
        hdr = ('   ' + ' ' * cw + ''.join(f'{c:<{cw}}' for c in B.COLS)).rstrip()
        lines.append(hdr)
        for y in range(B.H, -1, -1):
            row = ''
            for x in range(-1, B.W + 1):
                p = (x, y)
                if p in cells:
                    row += f'{cells[p]:<{cw}}'
                elif B.on_board(p):
                    z = B.zone(p)
                    row += f'{"·" if z == "." else z:<{cw}}'
                else:
                    row += ' ' * cw
            label = f'{y:>2}' if y >= 1 else '  '
            lines.append(f'{label} {row}'.rstrip())
        lines.append(hdr)
        info = f'{self.ctx.title} | clock {self.clock} | phase {self.phase} | tokens O {self.tok_o} X {self.tok_x} | to act: {self.side} ({self.stage})'
        if self.inbound:
            info += f' | inbound phase {self.inbound}'
        lines.append(info)
        lines.append('Zones: K rim  M mid/floater  L long two  3 three  · plain wood.  O1* ball, Tx screen T side, L locked, X arrows by compass.')
        return '\n'.join(lines)

    def __str__(self):
        return self.board()
