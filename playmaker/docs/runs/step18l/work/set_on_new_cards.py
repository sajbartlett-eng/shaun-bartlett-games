"""Step 18l: the computer's choice on each scored position of the sense-check set with the position's cards replaced
by the cards as they are now (D-184, D-186). Searches only: no play-outs, so no answers. For each position: its choice
on the cards the set carries (before D-184) and on the new cards, under the six rules of the app.
Run from playmaker/: SENSE_RUN=step18l SENSE_18L=1 python3 docs/runs/step18l/work/set_on_new_cards.py"""
import json, os, sys
sys.path.insert(0, 'tools')
import sense_18h as S
from playmaker_engine.cards import CARDS
from playmaker_engine.jsbridge import card_json
old = json.load(open(sys.argv[1]))                     # the cards before D-184, by key (from step 18k's code)
fp = lambda c: json.dumps([c['qs'], sorted(c['r'].items())])
by = {fp(c): k for k, c in old.items()}
positions, _ = S.load()
ONLY = "closeout|game EB3F5B|18e's Steal|Contest or not|shoot now|move, then shoot|board 1|board 3|board 8".split('|')
scored = [p for p in positions if any(p['id'].startswith(x) for x in ONLY)]
new, miss = [], 0
for p in scored:
    ctx = dict(p['ctx'])
    for side in ('off', 'dfn'):
        cards = []
        for card in ctx[side]:
            k = by.get(fp(card))
            miss += k is None
            cards.append(card_json(CARDS[k]) if k else card)
        ctx[side] = cards
    new.append(dict(p, ctx=ctx))
print('cards not found by their old ratings (exam boards use changed copies of cards):', miss)
a = S.searches(scored, 'set, cards before D-184')
b = S.searches(new, 'set, cards now')
out = []
for p, ra, rb in zip(scored, a, b):
    row = dict(id=p['id'], side=p['side'], before_d184=S.words(ra[0][1]), now=S.words(rb[0][1]), same=S.key(ra[0][1]) == S.key(rb[0][1]),
               reads_before=round(ra[0][0], 2), reads_now=round(rb[0][0], 2))
    out.append(row)
    print(('same ' if row['same'] else 'MOVED'), p['id'], '|', row['before_d184'][:70], '|', row['now'][:70], '|', row['reads_before'], row['reads_now'])
json.dump(out, open('docs/runs/step18l/set_choices_on_new_cards.json', 'w'), indent=1)
print(sum(r['same'] for r in out), 'of', len(out), 'choices the same')
