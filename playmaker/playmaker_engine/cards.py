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
    __slots__ = ('key', 'num', 'role', 'tier', 'tagline', 'qs', 'r', 'bands')

    def __init__(self, key, num, role, tier, tagline, qs, off, dfn):
        self.key, self.num, self.role, self.tier, self.tagline, self.qs = key, num, role, tier, tagline, qs
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
