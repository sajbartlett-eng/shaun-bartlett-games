"""Round 2 of the solver programme (step 2b, sections 3-6): read the full-budget results and write the
report. Budgets: 120 s (5 seeds) and 600 s per card; Coach's Call cards: each target its own budget.

The six cards whose teams changed in step 3d (2, 3, 8, 9, 11, 12), and the context runs that swapped in a
rebuilt team, come from runs_3d.json (re-solved with the new teams); runs_r2.json keeps the old values
for comparison.
"""
import json
import os
from collections import Counter, defaultdict

from .scenarios import SCENARIOS
from .solver_report import RESULTS, SOLVE_ORDER, STALE_3D, ROOT, alt_matchups, SCREEN_CARDS, SCREEN_TEAMS

SHORT, LONG = 120, 600
REBUILT = {'Twin Towers', 'Ball Movement'}
UNSTABLE_SPREAD = 2.0


def _load(name):
    path = os.path.join(RESULTS, name)
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        raw = json.load(f)
    return {tuple(json.dumps(x) if isinstance(x, list) else x for x in json.loads(k)): v for k, v in raw.items()}


def _stale(key):
    kind, n = key[0], key[1]
    if n in STALE_3D:
        return True
    return kind == 'context' and len(key) > 4 and bool(REBUILT & set(json.loads(key[4])))


def runs(old=False):
    """The round-2 results in use: runs_r2 with the stale entries replaced from runs_3d (old=True: as solved
    before step 3d)."""
    r2 = _load('runs_r2.json')
    if old:
        return r2
    out = {k: v for k, v in r2.items() if not _stale(k)}
    out.update(_load('runs_3d.json'))
    return out


def coach(n):
    return bool(SCENARIOS[n].get('target'))


def main_run(R, n, budget):
    """The card's run at a budget: seed 0, or for Coach's Call the best of the five known targets."""
    if coach(n):
        ts = {k[4]: v for k, v in R.items() if k[0] == 'target' and k[1] == n and k[2] == budget}
        if not ts:
            return None
        t = max(ts, key=lambda t: ts[t]['value'])
        return dict(ts[t], target=t, per_target={int(x): v['value'] for x, v in ts.items()})
    return R.get(('solve', n, budget, 0))


def summary(R, n):
    m, s = main_run(R, n, LONG), main_run(R, n, SHORT)
    if m is None:
        return None
    vals = [m['value']]
    if coach(n):
        if s:
            vals.append(s['value'])
    else:
        vals += [v['value'] for k, v in R.items() if k[0] == 'solve' and k[1] == n]
    spread = max(vals) - min(vals)
    first = lambda r: r['line'][0]['text'] if r and r['line'] else ''
    changed = s is not None and first(m) != first(s)
    label = 'unstable' if (spread > UNSTABLE_SPREAD or changed) else 'estimated'
    if m.get('exact_full'):
        label = 'exact'
    return dict(main=m, short=s, spread=spread, line_changed=changed, label=label, values=vals)


def six_card_comparison():
    old, new = runs(old=True), runs()
    rows = []
    for n in STALE_3D:
        a, b = summary(old, n), summary(new, n)
        rows.append(dict(n=n, title=SCENARIOS[n]['title'], old=a, new=b))
    return rows


# ---- section 3: the context test -----------------------------------------------------------------

def _within(run, frac=0.9):
    root = run.get('root') or []
    if not root:
        return set()
    best = max(r['value'] for r in root)
    return {r['label'] for r in root if r['value'] >= frac * best}


def context_runs(R, n):
    """The card's own run at the short budget, and its runs with other matchups (same squares and clock)."""
    own = main_run(R, n, SHORT)
    alts = [(json.loads(k[4]), v) for k, v in R.items() if k[0] == 'context' and k[1] == n]
    return own, alts


def context_test(R):
    changes, pairs, per_card = 0, 0, {}
    label_cards = defaultdict(set)
    for n in SOLVE_ORDER:
        own, alts = context_runs(R, n)
        if not own:
            continue
        row = dict(own=own['best_label'], alts=[])
        for teams, r in alts:
            pairs += 1
            changed = r['best_label'] != own['best_label']
            changes += changed
            row['alts'].append(dict(teams=teams, label=r['best_label'], value=r['value'], changed=changed))
        per_card[n] = row
        ctx = [own] + [r for _, r in alts]
        counts = Counter(l for r in ctx for l in _within(r))
        for l, c in counts.items():
            if c > len(ctx) / 2:
                label_cards[l].add(n)
    n_cards = len(per_card)
    flagged = sorted(((l, sorted(c)) for l, c in label_cards.items() if len(c) > n_cards / 2), key=lambda x: -len(x[1]))
    return dict(rate=changes / pairs if pairs else 0.0, changes=changes, pairs=pairs, per_card=per_card,
                flagged=flagged, n_cards=n_cards)


def all_lines(R):
    for k, v in R.items():
        if isinstance(v, dict) and v.get('line'):
            yield k, v


def dead_rules(R):
    """How often Challenge Screen and defensive Sprint closeouts appear anywhere in a best line, and how
    often the offence's best lines use a Screen at all."""
    lines = list(all_lines(R))
    chall = sum(1 for _, v in lines for ln in v['line'] if ln['side'] == 'X' and 'challenge' in ln['kinds'])
    sprint = sum(1 for _, v in lines for ln in v['line'] if ln['side'] == 'X' and 'sprint' in ln['kinds'])
    screens = sum(1 for _, v in lines if any(ln['side'] == 'O' and 'screen' in ln['kinds'] for ln in v['line']))
    chall_root = sum(1 for _, v in lines for r in (v.get('root') or []) if 'challenge' in r['text'].lower())
    screen_cards = {}
    for n in SCREEN_CARDS:
        rs = [(k, v) for k, v in R.items() if k[0] == 'context' and k[1] == n and json.loads(k[4])[0] in SCREEN_TEAMS]
        screen_cards[n] = [dict(teams=json.loads(k[4]), screens=sum('screen' in ln['kinds'] for ln in v['line'] if ln['side'] == 'O'),
                                challenges=sum('challenge' in ln['kinds'] for ln in v['line'] if ln['side'] == 'X'),
                                value=v['value']) for k, v in rs]
    return dict(lines=len(lines), challenge_steps=chall, sprint_steps=sprint, lines_with_screen=screens,
                challenge_root=chall_root, screen_cards=screen_cards)


def pause_count(R):
    x = Counter()
    for n in SOLVE_ORDER:
        m = main_run(R, n, LONG)
        if not m:
            continue
        for ln in m['line']:
            if ln['side'] == 'X':
                for k in ln['kinds'] or ['none']:
                    x[k] += 1
    return x


def oq7(R):
    out = []
    for n in SOLVE_ORDER:
        for b in (SHORT, LONG):
            base = main_run(R, n, b)
            alt = R.get(('rule7b', n, b, 0))
            if base and alt:
                if coach(n):
                    base_v = base['per_target'].get(alt.get('target', base['target']), base['value'])
                else:
                    base_v = base['value']
                out.append(dict(n=n, budget=b, base=base_v, alt=alt['value'], diff=alt['value'] - base_v,
                                changed=(base['line'][:1] and alt['line'][:1] and base['line'][0]['text'] != alt['line'][0]['text'])))
    return out


def coach_secret(R):
    out = []
    for n in SOLVE_ORDER:
        if not coach(n):
            continue
        for b in (SHORT, LONG):
            known = main_run(R, n, b)
            g = R.get(('coachvec', n, b, 0))
            if known and g:
                out.append(dict(n=n, budget=b, known=known['value'], known_target=known['target'],
                                per_target=known['per_target'], guessing=g['guessing'],
                                guessing_target=g['guessing_target'], secret=g['guessing'] - known['value'],
                                depth=g.get('depth')))
    return out


def classify(R):
    return {n: summary(R, n) for n in SOLVE_ORDER}


# ---- the report -------------------------------------------------------------------------------------

def _pct(x):
    return f'{x:.0%}'


def _row(s):
    if not s:
        return 'n/a'
    m = s['main']
    return f'{m["verdict"]} ({s["label"]}): {m["value"]:.1f}, P(30+) {_pct(m["p30"])}, {m["n_plans"]} plans'


def fixes(R=None):
    """Round-2 fix runs, with the card's own value at the same budget beside each."""
    from .solver_fixes import CANDIDATES_R2
    R = R or runs()
    F = _load('runs_fixes2.json')
    out = []
    for k, v in F.items():
        n = k[1]
        i = json.loads(k[4])[0]
        base = summary(R, n)
        out.append(dict(n=n, i=i, text=CANDIDATES_R2[n][i][0], base=base['main'] if base else None, fix=v))
    return sorted(out, key=lambda r: (SOLVE_ORDER.index(r['n']), r['i']))


def write_report(path=None, pause_path=None):
    from .solver_report import format_line
    R = runs()
    path = path or os.path.join(ROOT, 'SOLVER_REPORT.md')
    S = classify(R)
    L = ['# Solver Report (round 2)\n']
    L.append(f'Budgets: **{SHORT // 60} and {LONG // 60} minutes per card**, 5 seeds at the short budget (the full '
             'defaults). Coach\'s Call cards give each of the five targets its own budget. The evaluation looks over '
             'the offence\'s next two turns against the defence\'s best reply. Every value is **estimated** (guided '
             'search, evaluation at the leaves) unless marked exact; a card is **unstable** if its values spread by '
             f'more than {UNSTABLE_SPREAD:g} points across its runs, or its first play changes between budgets.\n')
    L.append('Cards 2, 3, 8, 9, 11 and 12 use Twin Towers or Ball Movement, which were rebuilt in step 3d; they were '
             're-solved with the new teams, as were the context runs that swapped in a rebuilt team.\n')
    L.append('## Summary\n')
    L.append('| # | Card | Value | Look | P(30+) | Plans | Verdict | Label | Depth | Spread |')
    L.append('|---|---|---|---|---|---|---|---|---|---|')
    for n in SOLVE_ORDER:
        s = S.get(n)
        if not s:
            L.append(f'| {n} | {SCENARIOS[n]["title"]} | pending | | | | | | | |')
            continue
        m = s['main']
        L.append(f'| {n} | {SCENARIOS[n]["title"]} | {m["value"]:.1f} | {m["look"]:.1f} | {_pct(m["p30"])} | '
                 f'{m["n_plans"]} | {m["verdict"]} | {s["label"]} | {m["depth"]} | {s["spread"]:.1f} |')
    L.append('')
    counts = Counter(s['main']['verdict'] for s in S.values() if s)
    L.append('Verdicts: ' + ', '.join(f'{k} {v}' for k, v in counts.most_common()) + '. Labels: ' +
             ', '.join(f'{k} {v}' for k, v in Counter(s['label'] for s in S.values() if s).most_common()) + '.\n')
    # six cards
    L.append('## The six re-solved cards (step 3d teams)\n')
    L.append('| # | Card | Before (old teams) | After (new teams) |')
    L.append('|---|---|---|---|')
    for r in six_card_comparison():
        L.append(f'| {r["n"]} | {r["title"]} | {_row(r["old"])} | **{_row(r["new"])}** |')
    L.append('')
    # fixes
    fx = fixes(R)
    L.append('## Proposed card fixes, re-solved\n')
    L.append(f'Setup only (squares, arrows, matchups, teams, clock): never a rule. Each fix was re-solved at the full long '
             f'budget ({LONG // 60} minutes, seed 0) and is compared with the card at the same budget.\n')
    if fx:
        L.append('| # | Card | Fix | Before | After |')
        L.append('|---|---|---|---|---|')
        for r in fx:
            b, f = r['base'], r['fix']
            L.append(f'| {r["n"]} | {SCENARIOS[r["n"]]["title"]} | {r["text"]} | {b["verdict"]}: {b["value"]:.1f}, '
                     f'P(30+) {_pct(b["p30"])}, {b["n_plans"]} plans | **{f["verdict"]}**: {f["value"]:.1f}, '
                     f'P(30+) {_pct(f["p30"])}, {f["n_plans"]} plans |')
    else:
        L.append('*The fix runs are still going.*')
    L.append('')
    L.append('### Notes on the candidate cards\n')
    L.append('- **Need a Three:** the fix that works puts a real three-point defender on the best shooter: swapping X2 '
             'and X3 moves the Defensive SF (contest 6) onto O2 the sharpshooter, and the card becomes a Puzzle (24.0). A '
             'new defence team (Lockdown) also stops the Gift but leaves a Single trick.')
    L.append("- **Coach's Call (Single trick, no Wall at full budget):** a different defence team fixes it: Iron Wall "
             '(Puzzle 21.1, 5 plans) or Bucket Brigade (Puzzle 27.2, 2 plans).')
    L.append('- **In the Bonus:** now a Puzzle at full budget (29.0, P(30+) 0%, 18 plans); no longer borderline.')
    L.append('- **Star Locked:** the one plan is the locked star himself: O1 Quick Steps to H10 for an arc three (a '
             'locked player may still Quick Step, by the ruling that a lock means "can\'t Move or Sprint"). It changes '
             'with the matchup (Lockdown v Bucket Brigade: kick to the post; Twin Towers v Run and Gun: kick to the '
             'shooter). If the intended lesson is "someone else has to score", that is a ruling question (OPEN_QUESTIONS '
             '51). Taking H10 away (X1 starts there) makes it a Puzzle (24.0, 3 plans).')
    L.append('- **No fix found** for Late Clock Reset, Sideline Out or Deny Everything: every setup change tried kept a '
             'Single trick. Deny Everything is a Single trick at 9.2 by design of the card (the defence denies '
             'everything); Sideline Out\'s one plan is the post entry, and denying it only lowered the value (15.2).\n')
    # context test
    ct = context_test(R)
    L.append('## The context test\n')
    L.append(f'**Plan-change rate: {ct["changes"]} of {ct["pairs"]} ({_pct(ct["rate"])}).** That is how often the best '
             'opening plan changes when only the lineup changes (same squares and clock). A high rate is the goal.\n')
    L.append('| # | Card | Best plan with the card\'s teams | Other matchups: best plan |')
    L.append('|---|---|---|---|')
    for n, row in ct['per_card'].items():
        alts = '; '.join(f'{a["teams"][0]} v {a["teams"][1]}: {a["label"]}{"" if a["changed"] else " (same)"}' for a in row['alts'])
        L.append(f'| {n} | {SCENARIOS[n]["title"]} | {row["own"]} | {alts} |')
    L.append('')
    L.append('**Flagged plans** (within 90% of the best in most matchups on most cards): ' +
             ('; '.join(f'{l} ({len(c)} cards)' for l, c in ct['flagged']) if ct['flagged'] else '**none**.') + '\n')
    dr = dead_rules(R)
    L.append('## Dead rules\n')
    L.append(f'Across {dr["lines"]} best lines (every card, budget, seed, target and matchup):\n')
    L.append(f'- **Challenge Screen:** played {dr["challenge_steps"]} times; never among the defence\'s root options '
             f'either ({dr["challenge_root"]}). The offence\'s best lines use a Screen at all in {dr["lines_with_screen"]} '
             f'of {dr["lines"]}.')
    L.append(f'- **Defensive Sprint closeouts:** {dr["sprint_steps"]} times.')
    L.append('- **Screen-heavy teams on the screen cards:** ' + '; '.join(
        f'card {n}: ' + ', '.join(f'{x["teams"][0]} ({x["screens"]} screens, {x["challenges"]} challenges, value {x["value"]:.1f})' for x in xs)
        for n, xs in dr['screen_cards'].items()) + '.\n')
    L.append('Both are dead rules at this depth: no context makes either one best. That is a question for the designer '
             '(see OPEN_QUESTIONS), with the caveat that the search reaches two turns on most cards.\n')
    # pause
    pc = pause_count(R)
    tot = sum(pc.values())
    L.append('## The Pause result\n')
    L.append(f'Defence steps in the principal lines (the 16 cards at {LONG // 60} minutes): ' +
             ', '.join(f'{k} {v}' for k, v in pc.most_common()) + f' ({tot} steps). '
             f'**Pause is still the most-used defensive action in the principal lines ({pc.get("pause", 0)} of {tot}).** '
             'But searched on its own, each of these defence positions has a Move that is clearly better than Pause '
             '(below). The Pause comes from where the defence\'s turn sits in the principal line: below the root, where '
             'the search tries only its concept plays (raw actions are added at the root only) and has little depth '
             'left. **So Pause is a search artefact, not a '
             'rule question**, and the same shallowness means card values (Gift verdicts above all) may favour the '
             'offence.\n')
    pex = []
    pp = pause_path or os.path.join(RESULTS, 'pause_examples.json')
    if os.path.exists(pp):
        with open(pp) as f:
            pex = json.load(f)
    for e in pex:
        opts = e['options']
        pause = [o for o in opts if 'Pause' in o[1]]
        L.append(f'**Card {e["n"]}, {SCENARIOS[e["n"]]["title"]}**, after "{e["offence"]}" (search depth {e["depth"]}): '
                 f'best {e["best"]}. ' + ('Pause: ' + f'{pause[0][0]:.1f}. ' if pause else 'Pause was not among the plays searched. ') +
                 'Best alternatives: ' + '; '.join(f'{t} {v:.1f}' for v, t, _ in opts[:4]) + f'; worst {opts[-1][1]} {opts[-1][0]:.1f}.\n')
    # OQ-7
    L.append('## OQ-7: the defence\'s last token ends the phase\n')
    L.append('| # | Card | Budget | As built | Phase runs on | Difference | Opening changes |')
    L.append('|---|---|---|---|---|---|---|')
    o7 = oq7(R)
    for r in o7:
        L.append(f'| {r["n"]} | {SCENARIOS[r["n"]]["title"]} | {r["budget"] // 60} min | {r["base"]:.1f} | {r["alt"]:.1f} | '
                 f'{r["diff"]:+.1f} | {"yes" if r["changed"] else "no"} |')
    L.append('')
    moved = [r for r in o7 if abs(r['diff']) > 0.05]
    L.append(f'**Result:** {len(moved)} of {len(o7)} comparisons move the value; '
             + (', '.join(f'card {r["n"]} at {r["budget"] // 60} min ({r["diff"]:+.1f})' for r in moved) if moved else 'none do') + '. '
             'The defence does not exploit ending the phase by spending its last token.\n')
    # coach
    L.append("## Coach's Call: the secret's value\n")
    L.append('Known target: the defence plays against the target it knows. Guessing: one defensive strategy for all five '
             'targets. The secret is worth the difference, measured at the same budget as everything else.\n')
    L.append('| # | Card | Budget | Known target (best) | Per target | Guessing defence | Secret worth |')
    L.append('|---|---|---|---|---|---|---|')
    for r in coach_secret(R):
        per = ', '.join(f'O{int(t) + 1} {v:.1f}' for t, v in sorted(r['per_target'].items()))
        L.append(f'| {r["n"]} | {SCENARIOS[r["n"]]["title"]} | {r["budget"] // 60} min | {r["known"]:.1f} (O{r["known_target"] + 1}) | '
                 f'{per} | {r["guessing"]:.1f} (O{r["guessing_target"] + 1}) | {r["secret"]:+.1f} |')
    L.append('')
    L.append('## Limits of this run\n')
    L.append('- **Depth:** at 10 minutes most cards reach 2 turns (Coach\'s Call targets reach 4). The two-turn evaluation '
             'fills in the rest, so values are "what the offence can force over the next few turns".')
    L.append('- **Seeds change only tie-breaking;** the spread reflects budget, not chance.')
    L.append('- **Fixes are one run each** at the long budget; a fix that lands within 2 points of a verdict threshold is '
             'borderline, not a verdict.')
    L.append('')
    # cards
    L.append('## Cards\n')
    for n in SOLVE_ORDER:
        s = S.get(n)
        if not s:
            continue
        m, sc = s['main'], SCENARIOS[n]
        L.append(f'<div class="file"></div>\n\n### {n}. {sc["title"]}\n')
        L.append(f'{sc["kind"]}, clock {sc["clock"]}. O: {sc["off"]}. X: {sc["dfn"]}. *{sc["text"]}*\n')
        L.append(f'**Value {m["value"]:.1f}**, look {m["look"]:.1f}, P(30+) {_pct(m["p30"])}, P(clock 0) {_pct(m["pexp"])}. '
                 f'Plans within 90%: {m["n_plans"]}. **Verdict: {m["verdict"]}** ({s["label"]}; depth {m["depth"]}; '
                 f'spread {s["spread"]:.1f} across ' + ', '.join(f'{v:.1f}' for v in s['values']) + ').\n')
        if m.get('per_target'):
            L.append('Known-target values: ' + ', '.join(f'O{int(t) + 1} {v:.1f}' for t, v in sorted(m['per_target'].items())) + '.\n')
        L.append('**Principal line** (best play, following the most likely roll):\n')
        L.append(format_line(m['line'], m['finish']) + '\n')
        if m['plans']:
            top = sorted(m['plans'], key=lambda p: -p['value'])[:5]
            L.append('**Opening plans within 90% of best** (top 5): ' + '; '.join(f'{p["text"]} ({p["value"]:.1f})' for p in top) + '\n')
    with open(path, 'w') as f:
        f.write('\n'.join(L))
    return path
