"""Step 10: the average position for leaf_mode 'relative'. The positions the phase table was built from (the step 3n
self-play: docs/runs/3n/3n_seed/*.json and, for Senior Pro, the aggregate run; the F5 run kept no positions), read the
way the leaf reads them today: the continuation (the best look the defence's best cover leaves, times the continuation)
at the first offence turn of each phase, as the phase table counts them. The mean per age, standard and phase goes to
ai_profiles.json (eval.relative_average), so a typical position adds about 0.

  python3 tools/relative_average.py [--write]          the averages (and, with --write, into ai_profiles.json)
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from playmaker_engine import board as B, rules_config as RC                     # noqa: E402
from playmaker_engine.cards import TEAMS, register_cards                        # noqa: E402
from playmaker_engine.decide import Read, coarse_key                            # noqa: E402
from playmaker_engine.scenarios import game_state                               # noqa: E402

PROFILES = os.path.join(ROOT, 'playmaker_engine', 'data', 'ai_profiles.json')
OUT = os.path.join(ROOT, 'docs', 'runs', 'step11', 'relative_average.json')


def decode(enc, off, dfn, rules):
    """A stored position (selfplay's snapshot) as a state (the decoder of tools/d81_paired_read.py)."""
    p = enc.split('|')
    stage, side = p[0].split(':')
    kw = {}
    o = x = arrows = None
    ball = 0
    for f in p[1:]:
        k, v = f[0], f[1:]
        if k == 'c':
            kw['clock'] = int(v)
        elif k == 't':
            a, b = v.split('/')
            kw['tok_o'], kw['tok_x'] = int(a), int(b)
        elif k == 'O':
            o = [B.parse_sq(q) for q in v.split(',')]
        elif k == 'X':
            x, arrows = [], []
            for q in v.split(','):
                m = re.match(r'([A-Q@R]\d+)([NESW]+)$', q)
                x.append(B.parse_sq(m.group(1)))
                arrows.append(B.DIR_NAMES.index(m.group(2)))
        elif k == 'b':
            ball = int(v) - 1
        elif k == 'm':
            kw['moved_o'], kw['moved_x'] = int(v[:2], 16), int(v[2:], 16)
        elif k == 'n':
            kw['cnt'] = tuple(int(c) for c in v)
        elif k == 'u':
            kw['turn_n'] = int(v[0])
            kw['final'] = v.endswith('F')
        elif k == 'L':
            kw['lock_o'], kw['lock_x'] = int(v[:2], 16), int(v[2:], 16)
        elif k == 'S':
            scr = []
            for t in v.split(','):
                m = re.match(r'(\d)([NESW]+)(\*?)([0-9a-f]+)$', t)
                scr.append((int(m.group(1)) - 1, B.DIR_NAMES.index(m.group(2)), bool(m.group(3)), int(m.group(4), 16)))
            kw['screens'] = tuple(scr)
        elif k == 'P':
            m = re.match(r'(\d)>(\d)(?:a(\d))?', v)
            kw['pending'] = (int(m.group(1)) - 1, int(m.group(2)) - 1)
            if m.group(3):
                kw['approach'] = int(m.group(3)) - 1
        elif k == 'f':
            m = re.match(r'(\d+)\+(\d+)-(\d+)', v)
            kw['fouls'], kw['bonus5'], kw['tos'] = map(int, m.groups())
        elif k == 'q':
            kw['qs_o'], kw['qs_x'] = int(v[:2], 16), int(v[2:], 16)
    s = game_state(off, dfn, [B.sq(q) for q in o], [B.sq(q) for q in x], [B.DIR_NAMES[a] for a in arrows], ball=ball,
                   rules=rules, check=False)
    return s.with_(stage=stage, side=side, **kw)


_DEALT = {}


def team_of(name, age, std):
    """A row's team: a named team, or a dealt roster rebuilt as tools/seed_3n.py dealt it."""
    if name in TEAMS:
        return name
    m = re.match(r'seed (\w+) ([\w-]+) (\d+) ([AB])$', name)
    if not m:
        raise KeyError(name)
    if name not in _DEALT:
        from playmaker_engine import levels as L, rosters as R
        a, sd, seed, side = m.group(1), m.group(2), int(m.group(3)), m.group(4)
        d = R.deal(a, sd, seed=seed)
        tags = d['tags'] or [None, None]
        k = 0 if side == 'A' else 1
        _DEALT[name] = register_cards(name, L.team(d['rosters'][k], a, tags[k]))
    return _DEALT[name]


def rows():
    out = []
    for p in sorted(glob.glob(os.path.join(ROOT, 'docs', 'runs', '3n', '3n_seed', '*.json'))):
        age, std = os.path.basename(p)[:-5].split('_', 1)
        for r in json.load(open(p)):
            if r.get('snapshots'):
                out.append((age, std, r))
    agg = json.load(open(os.path.join(ROOT, 'docs', 'runs', '3n', '3n_aggregate_rows.json')))
    for r in (agg['rows'] if isinstance(agg, dict) else agg):
        if r.get('snapshots') and r.get('format', 'digital') == 'digital':
            out.append((r.get('age', 'senior'), r.get('standard', 'pro'), r))
    return out


def main():
    by = {}
    skipped = 0
    for age, std, r in rows():
        rules = RC.with_rules(digital=(r.get('format', 'digital') == 'digital'))
        try:
            off, dfn = team_of(r['off'], age, std), team_of(r['dfn'], age, std)
        except KeyError:
            skipped += 1
            continue
        seen = set()
        for enc in r['snapshots']:
            if not enc.startswith('play:O'):
                continue
            s = decode(enc, off, dfn, rules)
            s.ctx.levels_key = (age, std)
            ph = coarse_key(s).split('|')[2]
            if ph in seen:                      # one position per possession per phase: the phase's first turn
                continue
            seen.add(ph)
            by.setdefault(f'{age}/{std}', {}).setdefault(ph, []).append(Read(s).continuation())
    own = {k: {ph: round(sum(v) / len(v), 2) for ph, v in sorted(rows_.items())} for k, rows_ in sorted(by.items())}
    count = {k: {ph: len(v) for ph, v in sorted(rows_.items())} for k, rows_ in sorted(by.items())}
    avg, source = scaled(own, count)
    rep = dict(average=avg, source=source, own_average=own, positions=count, skipped_rows=skipped, min_positions=MIN_OWN,
               how='the leaf\'s continuation read (today\'s rules) at the first offence turn of each phase, per '
                   'possession; D-114: Senior Pro is the base, scaled by the phase table for the other levels, a '
                   'level\'s own average once it has MIN_OWN positions at that phase')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(rep, open(OUT, 'w'), indent=1)
    print(json.dumps(dict(average=avg, source=source, positions=count), indent=1))
    if '--write' in sys.argv:
        prof = json.load(open(PROFILES))
        prof['eval']['leaf_mode'] = 'relative'
        prof['eval']['relative_average'] = avg
        prof['eval']['relative_average_source'] = source
        prof['eval']['_relative'] = ('D-92 (Shaun, 10 Nov 2026): leaf_mode relative (the default: the phase table plus '
                                     'how much this position\'s continuation read beats the average at its phase) or '
                                     'floor. relative_average per age/standard and phase from tools/relative_average.py '
                                     '(D-114): Senior Pro is the base; other levels scale it by their phase table over '
                                     'Senior Pro\'s, and use their own average once they have 100 positions at the phase '
                                     '(provisional); relative_average_source says which')
        open(PROFILES, 'w').write(json.dumps(prof, indent=2))


MIN_OWN = 100          # D-114 (provisional): a level's own average once it has this many positions at the phase
BASE = 'senior/pro'


def scaled(own, count):
    """D-114: Senior Pro's averages are the base. Any other level: its own average at a phase once it has MIN_OWN
    positions there; otherwise Senior Pro's average scaled by that level's phase table value over Senior Pro's at the
    same phase (vcoarse.json, _phaseK). Returns (averages, source per level and phase: base / own / scaled)."""
    tables = json.load(open(os.path.join(ROOT, 'playmaker_engine', 'data', 'vcoarse.json')))
    levels = sorted({k for k in tables if '/' in k and not k.startswith('_')} | set(own))
    avg, source = {}, {}
    for lv in levels:
        avg[lv], source[lv] = {}, {}
        for ph in map(str, range(1, 7)):
            base = own.get(BASE, {}).get(ph)
            if base is None:
                continue
            if lv == BASE:
                avg[lv][ph], source[lv][ph] = base, 'base'
            elif count.get(lv, {}).get(ph, 0) >= MIN_OWN:
                avg[lv][ph], source[lv][ph] = own[lv][ph], 'own'
            else:
                vb = tables[BASE].get(f'_phase{ph}')
                vl = tables.get(lv, {}).get(f'_phase{ph}', vb)
                avg[lv][ph], source[lv][ph] = round(base * vl / vb, 2), 'scaled'
    return avg, source


if __name__ == '__main__':
    main()
