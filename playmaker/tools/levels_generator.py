"""Playmaker level profiles. Builds Amateur, Elite Youth (U18-20) and Junior (U14-16) card sets from the pro cards.

Rules (from the 8 Nov 2026 research; only changes the evidence warrants):
- Pro cards are FIBA senior / NBL level (card FT average 73% = FIBA qualifiers 72.2%, NBL 73-75%).
- Semi-pro: no card changes. Every measured difference is under half a rating point, below what a d20 can show.
- Contest ratings, foul ratings, Screen v Challenge: unchanged at every level.
- Bands shift with each level's uniform shift, so a mark means above or below average FOR THAT LEVEL.
"""
import sys, os, json, pprint
sys.path.insert(0, os.path.dirname(__file__))
from data import CARDS, OFF, DEF, parse, RANGES, FOUL_RANGES

SHOTS = ['shot_layup', 'shot_dunk', 'shot_post', 'shot_floater', 'shot_mid', 'shot_long', 'shot_three']
JUMP = ['shot_floater', 'shot_mid', 'shot_long', 'shot_three']
# Junior: offensive skills compress toward the all-card average (U15: no positional difference in passing, dribbling or shooting quality).
JUNIOR_SKILL = ['dribble', 'pass', 'shot_layup', 'shot_floater', 'shot_mid', 'shot_long', 'shot_three', 'free_throw']
TYPE_KEEP = 0.5   # share of each type's gap from the all-card average a junior card keeps (judgement: the study could not detect small gaps)

LEVELS = {
 'youth': {
   'label': 'U20', 'name': 'Elite youth (U18-20)',
   'shift': dict({k: -1 for k in SHOTS + ['free_throw']}, steal=+1, intercept=+1), 'c_tail': {},
   'why': 'U19 World Cup v senior FIBA: FT -3.8, 2P -3.7, 3P -4.0 points; steals +32%, other turnovers and fouls flat; same spread.'},
 'junior': {
   'label': 'U16', 'name': 'Junior (U14-16)',
   'shift': dict({k: -2 for k in JUMP}, free_throw=-3, shot_layup=-1, shot_post=-1, shot_dunk=-2, steal=+2, intercept=+2),
   'c_tail': {k: -1 for k in SHOTS + ['free_throw']}, 'compress': True,
   'why': 'U16 FT about 15 points below senior; type gaps halve (no positional skill difference at U15); C tier -1 (less-selected players spread wider); growth tags.'},
}
# Growth tags (junior only), applied at the table to an on-time card. Size and strength effects of maturity are very large
# (height eta2 .67, strength 60%+ of variance); speed, agility and jump effects moderate to large.
GROWTH = {
 'early': {'qs': +1, 'agility': +1, 'challenge': +1, 'screen': +2, 'shot_dunk': +2, 'shot_post': +2, 'con_layup': +2, 'con_dunk': +2, 'con_post': +2},
 'late':  {'qs': -1, 'agility': -1, 'challenge': -1, 'screen': -2, 'shot_dunk': -2, 'shot_post': -2, 'con_layup': -2, 'con_dunk': -2, 'con_post': -2},
}

def rnd(x): return int(x + 0.5) if x >= 0 else -int(-x + 0.5)
def cap(name, v): return max(0, min(20 if name == 'pass' else 19, v))
def type_key(key): return key[:-1]

def level_ranges(lv):
    sh = LEVELS[lv]['shift']
    return {k: (a + sh.get(k, 0), h + sh.get(k, 0)) for k, (a, h) in RANGES.items()}

def band(name, v, rng):
    if name in FOUL_RANGES:
        h, a = FOUL_RANGES[name]; return 'H' if v <= h else ('A' if v <= a else 'L')
    a, h = rng[name]
    return 'H' if v >= h else ('A' if v >= a else 'L')

def raw():
    out = {}
    for c in CARDS:
        out[c[0]] = (dict(zip(OFF, [v for v, _ in parse(c[6])])), dict(zip(DEF, [v for v, _ in parse(c[7])])))
    return out

def build(lv):
    L = LEVELS[lv]; R = raw(); rng = level_ranges(lv)
    allmean = {k: sum(o[k] for o, d in R.values()) / len(R) for k in OFF}
    tmean = {}
    for key, (o, d) in R.items():
        tmean.setdefault(type_key(key), []).append(o)
    tmean = {t: {k: sum(o[k] for o in os_) / len(os_) for k in OFF} for t, os_ in tmean.items()}
    cards = []
    for key, n, role, tier, tag, qs, o_s, d_s in CARDS:
        o, d = dict(R[key][0]), dict(R[key][1])
        for k in OFF:
            v = o[k]
            if L.get('compress') and k in JUNIOR_SKILL:
                tm = tmean[type_key(key)][k]
                v = allmean[k] + TYPE_KEEP * (tm - allmean[k]) + (v - tm)
            v += L['shift'].get(k, 0)
            if tier == 'C': v += L['c_tail'].get(k, 0)
            o[k] = cap(k, rnd(v))
        for k in DEF:
            d[k] = cap(k, d[k] + L['shift'].get(k, 0))
        os_ = '%s %s %s | %s' % tuple(['%d%s' % (o[k], band(k, o[k], rng)) for k in OFF[:3]] + [' '.join('%d%s' % (o[k], band(k, o[k], rng)) for k in OFF[3:])])
        ds_ = '%s %s %s %s %s | %s' % tuple(['%d%s' % (d[k], band(k, d[k], rng)) for k in DEF[:5]] + [' '.join('%d%s' % (d[k], band(k, d[k], rng)) for k in DEF[5:])])
        cards.append((key, n, role, tier, tag, qs, os_, ds_))
    return cards, rng

def growth(card_o, card_d, qs, tag):
    """Apply a growth tag to parsed dicts. Returns new (o, d, qs). Bands are not recoloured: the printed card is on time."""
    g = GROWTH.get(tag, {}); o, d = dict(card_o), dict(card_d)
    for k, dv in g.items():
        if k == 'qs': qs = max(0, min(2, qs + dv))
        elif k in o: o[k] = cap(k, o[k] + dv)
        elif k in d: d[k] = cap(k, d[k] + dv)
    return o, d, qs

# Two dials. AGE picks the cards and modifiers. STANDARD picks the tier shape both teams build to (same strength both sides).
TIER_VALUE = {'A': 1, 'B': 0, 'C': -1}
STANDARDS = {
 'pro':      {'name': 'Pro', 'strength': 0, 'shapes': ['BBBBB', 'ABBBC', 'AABCC']},
 'semi_pro': {'name': 'Semi-pro', 'strength': -1, 'shapes': ['BBBBC', 'ABBCC']},
 'amateur':  {'name': 'Amateur', 'strength': -3, 'shapes': ['BBCCC', 'ACCCC']},
}
AGES = {
 'senior': {'name': 'Senior', 'cards': 'pro', 'modifier': None, 'growth': False},
 'youth':  {'name': 'Elite youth (U18-20)', 'cards': 'pro', 'modifier': 'YOUTH_MODIFIER', 'growth': False},
 'junior': {'name': 'Junior (U14-16)', 'cards': 'junior', 'modifier': None, 'growth': True},
}
GROWTH_DEAL = {'early': 1, 'on_time': 3, 'late': 1}

if __name__ == '__main__':
    res = {lv: build(lv) for lv in LEVELS}
    out = os.path.join(os.path.dirname(__file__), '..', 'engine_handoff', 'data', 'levels_data.py')
    with open(out, 'w') as f:
        f.write('# Generated by cards/levels.py. Same tuple format as data.CARDS. Do not edit by hand.\n')
        f.write('# Semi-pro uses the pro cards unchanged. Junior cards are printed on time; apply GROWTH at the table.\n')
        f.write('LEVEL_INFO = %s\n' % json.dumps({k: {'label': v['label'], 'name': v['name'], 'why': v['why']} for k, v in LEVELS.items()}, indent=1))
        f.write('GROWTH = %s\n' % json.dumps(GROWTH, indent=1))
        f.write('GROWTH_DEAL = %s  # per team, dealt at random\n' % pprint.pformat(GROWTH_DEAL))
        f.write('TIER_VALUE = %s\n' % pprint.pformat(TIER_VALUE))
        f.write('STANDARDS = %s\n' % pprint.pformat(STANDARDS))
        f.write('AGES = %s\n' % pprint.pformat(AGES))
        f.write('# Elite youth is a modifier on the pro cards (colours unchanged): YOUTH_MODIFIER is added to every pro card.\n')
        f.write('YOUTH_MODIFIER = %s\n' % pprint.pformat(LEVELS['youth']['shift']))
        for lv, (cards, rng) in res.items():
            if lv != 'junior': continue
            f.write('\n%s_RANGES = %s\n' % (lv.upper(), json.dumps(rng)))
            f.write('%s_CARDS = [\n' % lv.upper())
            for c in cards: f.write(' %r,\n' % (c,))
            f.write(']\n')
    print('wrote', os.path.normpath(out))
