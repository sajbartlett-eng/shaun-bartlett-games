"""Step 12: the two measured numbers the stable search needs, from the step 3n seed positions (the positions the phase
table and the averages were built from), read the way the leaf reads them today.

1. The tempo effect: the same position read with the offence to act and with the defence to act (each at the start of
   its turn); the mean gap and its spread.
2. The reading's margin of error at each phase: the standard error of the reading's two measured parts, the phase
   table's value (its own standard error, vcoarse.json _se) and the average continuation it is compared with (the
   spread of the seed positions' continuation over the square root of their number). The margin is the combined
   standard error, sqrt(se_table^2 + se_average^2); one standard error is the provisional margin (Shaun, step 12).

  python3 tools/stable_measures.py [--write]       the measures (and, with --write, the margins into ai_profiles.json)
"""
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playmaker_engine import rules_config as RC                   # noqa: E402
from playmaker_engine.decide import Read, coarse_key, CONFIG       # noqa: E402
import relative_average as RA                                     # noqa: E402

OUT = os.path.join(ROOT, 'docs', 'runs', 'step12', 'stable_measures.json')
PROFILES = os.path.join(ROOT, 'playmaker_engine', 'data', 'ai_profiles.json')


def main():
    gaps, conts = {}, {}
    for age, std, r in RA.rows():
        if (age, std) != ('senior', 'pro'):
            continue
        rules = RC.with_rules(digital=(r.get('format', 'digital') == 'digital'))
        off, dfn = RA.team_of(r['off'], age, std), RA.team_of(r['dfn'], age, std)
        seen = set()
        for enc in r['snapshots']:
            if not enc.startswith('play:O'):
                continue
            s = RA.decode(enc, off, dfn, rules)
            s.ctx.levels_key = (age, std)
            ph = coarse_key(s).split('|')[2]
            o_turn = s.with_(side='O', stage='play', turn_n=0)
            x_turn = s.with_(side='X', stage='play', turn_n=0)
            gaps.setdefault(ph, []).append(Read(o_turn).leaf() - Read(x_turn).leaf())
            if ph not in seen:
                seen.add(ph)
                conts.setdefault(ph, []).append(Read(s).continuation())
    tables = json.load(open(os.path.join(ROOT, 'playmaker_engine', 'data', 'vcoarse.json')))['senior/pro']
    se_table = tables.get('_se', {})

    def mean_sd(v):
        m = sum(v) / len(v)
        sd = math.sqrt(sum((x - m) ** 2 for x in v) / (len(v) - 1)) if len(v) > 1 else 0.0
        return m, sd
    tempo, margin = {}, {}
    allg = [g for v in gaps.values() for g in v]
    for ph in sorted(gaps):
        m, sd = mean_sd(gaps[ph])
        tempo[ph] = dict(mean=round(m, 2), sd=round(sd, 2), n=len(gaps[ph]), se=round(sd / math.sqrt(len(gaps[ph])), 2))
    m, sd = mean_sd(allg)
    tempo['all'] = dict(mean=round(m, 2), sd=round(sd, 2), n=len(allg), se=round(sd / math.sqrt(len(allg)), 2))
    for ph in sorted(conts):
        _, sd = mean_sd(conts[ph])
        se_avg = sd / math.sqrt(len(conts[ph]))
        st = float(se_table.get(ph, 0.0))
        margin[ph] = dict(se_average=round(se_avg, 2), se_table=round(st, 2), se=round(math.sqrt(se_avg ** 2 + st ** 2), 2),
                          n=len(conts[ph]))
    rep = dict(tempo=tempo, margin=margin, leaf_mode=CONFIG['eval'].get('leaf_mode'),
               how='Senior Pro seed positions (step 3n), today\'s rules and reading')
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(rep, open(OUT, 'w'), indent=1)
    print(json.dumps(rep, indent=1))
    if '--write' in sys.argv:
        prof = json.load(open(PROFILES))
        srch = prof.setdefault('search', {})
        srch['stable_margin'] = {ph: v['se'] for ph, v in margin.items()}
        open(PROFILES, 'w').write(json.dumps(prof, indent=2))


if __name__ == '__main__':
    main()
