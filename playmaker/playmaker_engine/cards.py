"""Load the player cards, teams and scenario cards from the provided data files."""
import os
import sys
import types

DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')


def _load(name, extra=None):
    path = os.path.join(DATA_DIR, name + '.py')
    mod = types.ModuleType('playmaker_data_' + name)
    mod.__file__ = path
    saved = {}
    for k, v in (extra or {}).items():       # satisfy plain 'from teams import TEAMS'
        saved[k] = sys.modules.get(k)
        sys.modules[k] = v
    try:
        with open(path) as f:
            exec(compile(f.read(), path, 'exec'), mod.__dict__)
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v
    return mod


DATA = _load('data')
TEAMS_MOD = _load('teams')
SCEN_MOD = _load('scenarios', {'teams': TEAMS_MOD})

OFF, DEF = DATA.OFF, DATA.DEF


class Card:
    # num: the card's printed position (1 PG .. 5 C). slot: the slot it fills on its team (it sets the piece: O4 is
    # slot 4); age and growth: the playing level (levels.py); flex: it plays a position up or down.
    __slots__ = ('key', 'num', 'role', 'tier', 'tagline', 'qs', 'r', 'bands', 'age', 'growth', 'slot', 'flex')

    def __init__(self, key, num, role, tier, tagline, qs, off, dfn):
        self.key, self.num, self.role, self.tier, self.tagline, self.qs = key, num, role, tier, tagline, qs
        self.age, self.growth, self.slot, self.flex = 'senior', None, num, False
        vals = DATA.parse(off) + DATA.parse(dfn)
        names = OFF + DEF
        self.r = {n: v for n, (v, _) in zip(names, vals)}
        self.bands = {n: b for n, (_, b) in zip(names, vals)}

    def shot(self, t):
        return self.r['shot_' + t]

    def con(self, t):
        return self.r['con_' + t]

    def __repr__(self):
        return f'Card({self.key})'


CARDS = {row[0]: Card(*row) for row in DATA.CARDS}
TEAMS = {name: [CARDS[k] for k in keys] for name, _, keys in TEAMS_MOD.TEAMS}
TEAM_TAGLINES = {name: tag for name, tag, _ in TEAMS_MOD.TEAMS}
FIRST_GAME = TEAMS_MOD.FIRST_GAME
SCENARIO_CARDS = SCEN_MOD.SC


# ---- custom lineups (step 3d) ------------------------------------------------------------------------
PRESCRIBED = [name for name, _, _ in TEAMS_MOD.TEAMS]
CUSTOM = {}


def register_team(name, keys):
    """Add a custom lineup to TEAMS and return the name it is registered under. The same name with the
    same cards is reused; a name already taken by other cards gets ' (2)', ' (3)' ..."""
    keys = [str(k) for k in keys]
    if len(keys) != 5 or any(k not in CARDS for k in keys):
        raise ValueError('a custom team is five card keys')
    base = ' '.join(str(name or '').split())[:30] or 'Custom'
    n, i = base, 2
    while n in TEAMS and [c.key for c in TEAMS[n]] != keys:
        n, i = f'{base} ({i})', i + 1
    if n not in TEAMS:
        TEAMS[n] = [CARDS[k] for k in keys]
        TEAM_TAGLINES[n] = 'Custom team'
        CUSTOM[n] = keys
    return n


def register_cards(name, cards, tagline='Custom team'):
    """Add a lineup of Card objects as they play (step 3l: effective cards, slot order) to TEAMS and return the name it
    is registered under. Same rule as register_team: the same name with the same cards is reused, else ' (2)' ..."""
    sig = lambda cs: [(c.key, getattr(c, 'age', 'senior'), getattr(c, 'growth', None), getattr(c, 'slot', c.num))
                      for c in cs]
    cards = list(cards)
    base = ' '.join(str(name or '').split())[:40] or 'Custom'
    n, i = base, 2
    while n in TEAMS and sig(TEAMS[n]) != sig(cards):
        n, i = f'{base} ({i})', i + 1
    if n not in TEAMS:
        TEAMS[n] = cards
        TEAM_TAGLINES[n] = tagline
        CUSTOM[n] = [c.key for c in cards]
    return n
