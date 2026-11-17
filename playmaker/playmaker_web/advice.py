"""Step 19, stage 2 (Shaun, 17 Nov 2026): coaching and scouting in advantages, numbers on tap.

"People don't need to think in terms of this number vs this number. They need to think in terms of advantages."

Read-only. Every chance here is the engine's own: the dice of the action as the rules resolve it (the same tree the
referee rolls), the pass chance the rules give (decide._pass_prob, proved equal to the rules' own Intercept in step
18s), and a shot's value against the defence's best contest from where it stands now (scoring.shot_ev). Every word
comes from the scout report's phrases (playmaker_engine/scout_phrases.json, which Shaun rewords freely), chosen by the
band on the card (above average, average, below average). Where the bands are both average, the line says so; it never
invents a reason. Nothing here decides a rule or changes what the computer plays."""
from playmaker_engine import board as B
from playmaker_engine import scouting as SC
from playmaker_engine.resolve import apply, ChanceNode

# a rating on the card -> the scout report's phrase that describes it (offence 'off', defence 'def')
PHRASE_OF = {
    'dribble': 'dribble', 'pass': 'pass', 'screen': 'screen', 'shot_layup': 'rim', 'shot_dunk': 'rim', 'shot_post': 'post',
    'shot_floater': 'floater', 'shot_mid': 'pullup', 'shot_long': 'pullup', 'shot_three': 'three', 'free_throw': 'free_throw',
    'agility': 'agility', 'intercept': 'intercept', 'challenge': 'challenge', 'steal': 'steal', 'con_layup': 'rim_d',
    'con_dunk': 'rim_d', 'con_post': 'post_d', 'con_mid': 'closeout', 'con_long': 'closeout', 'con_three': 'closeout',
    'foul_contest': 'foul', 'foul_steal': 'foul',
}
SHOT_WORD = {'layup': 'layup', 'dunk': 'dunk', 'post': 'post shot', 'floater': 'floater', 'mid': 'mid-range shot',
             'long': 'long two', 'three': 'three'}


def plain(text):
    """The scout report's phrase with any word on the banned list swapped for a plain one. Only 'threat' needs it
    today ('is no threat from three'); the phrase itself is Shaun's to reword in scout_phrases.json."""
    return text.replace('threat', 'danger')


def clause(pid, kind):
    return plain(SC.PHRASES[pid][kind]['clause'])


def phrase(card, rating, who):
    """'O2 is dangerous from three' when the rating is above average and the scout report has a strength for it;
    the weakness when below; None when average (or the report has no phrase for that side of it)."""
    pid = PHRASE_OF.get(rating)
    band = card.bands.get(rating) if rating in card.bands else None
    if pid is None or band not in ('H', 'L'):
        return None
    spec = SC.PHRASES.get(pid, {}).get('strength' if band == 'H' else 'weakness')
    if not spec:
        return None
    return dict(text=f"{who} {plain(spec['clause'])}", band=band, rating=rating, who=who)


def _join(parts, even):
    parts = [p for p in parts if p]
    if not parts:
        return dict(text=even, bands=[])
    if len(parts) == 1:
        return dict(text=parts[0]['text'] + '.', bands=[parts[0]])
    a, b = parts[0], parts[1]
    # an advantage against a weakness reads "and"; a strength against a strength reads "but"
    good_a = a['band'] == 'H'
    good_b = (b['band'] == 'L') if a['who'][0] != b['who'][0] else (b['band'] == 'H')
    joiner = ', and ' if good_a == good_b else ', but '
    return dict(text=f"{a['text']}{joiner}{b['text']}.", bands=[a, b])


def _cards(s, side):
    return s.ctx.off if side == 'O' else s.ctx.dfn


def chance_for(s, a):
    """The engine's chance that the action does what its side wants, from the rules' own dice tree. None: no dice."""
    node = apply(s, a)
    if not isinstance(node, ChanceNode):
        return None
    want = {'dribble': ('success',), 'intercept': ('failure',), 'challenge': ('failure',), 'steal': ('stolen',),
            'contest': ('no foul',)}.get(a.kind)
    if want is None:
        return None
    return float(sum(p for p, lab, _ in node.flatten() if lab.split('/')[-1] in want))


def foul_risk(s, a):
    """The engine's chance that the action is called a foul (a foul roll in its dice tree). None: no dice."""
    node = apply(s, a)
    if not isinstance(node, ChanceNode):
        return None
    return float(sum(p for p, lab, _ in node.flatten() if 'foul' in lab.split('/')))


def action_advice(s, a, threats=None):
    """{chance, value, band, why, why_bands} for one legal action, or None when there is nothing to say."""
    O, X = s.ctx.off, s.ctx.dfn
    k = a.kind
    if k == 'pass':
        from playmaker_engine import decide as D
        try:
            ch = float(D._pass_prob(s, a.target))
        except Exception:
            ch = None
        js = sorted({t['defender'] for t in (threats or [])})
        passer = phrase(O[a.piece], 'pass', f'O{a.piece + 1}')
        if ch is not None and ch >= 0.999 or not js:
            why = dict(text='Nobody can reach the passing lane.', bands=[])
            if passer and passer['band'] == 'L':
                why = _join([passer], '')
        else:
            j = max(js, key=lambda j: X[j].r['intercept'])
            who = ' and '.join(f'X{q + 1}' for q in js[:2])
            lead = dict(text=f'{who} can get to the lane', band='A', who='X', rating=None)
            lane = phrase(X[j], 'intercept', f'X{j + 1}')
            if lane:
                lead = dict(text=f'{who} can get to the lane, and X{j + 1} {clause("intercept", "strength")}', band='H', who='X', rating='intercept')
            why = dict(text=lead['text'] + (f'; {passer["text"]}' if passer else '') + '.', bands=[b for b in (lane, passer) if b])
        return dict(chance=ch, why=why['text'], why_bands=_bands(why))
    if k == 'dribble':
        why = _join([phrase(O[a.piece], 'dribble', f'O{a.piece + 1}'), phrase(X[a.target], 'agility', f'X{a.target + 1}')],
                    f'O{a.piece + 1} and X{a.target + 1} are both average here.')
        return dict(chance=chance_for(s, a), why=why['text'], why_bands=_bands(why))
    if k == 'screen':
        p = phrase(O[a.piece], 'screen', f'O{a.piece + 1}')
        why = _join([p], 'No dice now: a defender can challenge it later.')
        return dict(chance=None, why=why['text'], why_bands=_bands(why))
    if k in ('shot', 'forced_shot'):
        from playmaker_engine.scoring import shot_ev, choose_contest, band
        t = a.shot
        try:
            v = float(shot_ev(s, a.piece, t, k == 'forced_shot'))
            opt = choose_contest(s, a.piece, t, k == 'forced_shot')
        except Exception:
            return None
        sh = phrase(O[a.piece], 'shot_' + t, f'O{a.piece + 1}')
        if opt.defender >= 0:
            dc = phrase(X[opt.defender], 'con_' + t, f'X{opt.defender + 1}')
            why = _join([sh, dc], f'X{opt.defender + 1} is close enough to contest.')
            if not sh and not dc:
                why = dict(text=f'An even matchup: X{opt.defender + 1} is close enough to contest.', bands=[])
        else:
            why = _join([sh], 'Nobody is close enough to contest it now.')
            if sh:
                why['text'] = why['text'][:-1] + ', and nobody is close enough to contest it now.'
        return dict(chance=None, value=round(v), band=band(v), why=why['text'], why_bands=_bands(why))
    if k == 'steal':
        carrier = s.ball
        why = _join([phrase(X[a.piece], 'steal', f'X{a.piece + 1}'), phrase(O[carrier], 'dribble', f'O{carrier + 1}')],
                    f'X{a.piece + 1} and O{carrier + 1} are both average here.')
        return dict(chance=chance_for(s, a), foul=foul_risk(s, a), why=why['text'], why_bands=_bands(why))
    if k == 'intercept':
        passer = s.pending[0] if s.pending else None
        why = _join([phrase(X[a.piece], 'intercept', f'X{a.piece + 1}'), phrase(O[passer], 'pass', f'O{passer + 1}') if passer is not None else None],
                    'Both are average here.')
        return dict(chance=chance_for(s, a), why=why['text'], why_bands=_bands(why))
    if k == 'challenge':
        why = _join([phrase(X[a.piece], 'challenge', f'X{a.piece + 1}'), phrase(O[a.target], 'screen', f'O{a.target + 1}')],
                    'Both are average here.')
        return dict(chance=chance_for(s, a), why=why['text'], why_bands=_bands(why))
    if k == 'contest' and a.piece >= 0 and s.shot:
        t = s.shot
        why = _join([phrase(X[a.piece], 'con_' + t, f'X{a.piece + 1}'), phrase(O[s.ball], 'shot_' + t, f'O{s.ball + 1}')],
                    'Both are average here.')
        fr = foul_risk(s, a)
        return dict(chance=None, foul=fr, why=why['text'], why_bands=_bands(why))
    return None


def _bands(why):
    return [dict(who=b['who'], rating=b['rating'], band=b['band']) for b in why.get('bands', []) if b.get('rating')]


def card_words(card, side):
    """The folded card in words: the player type, and his strengths and weaknesses on this side of the ball, as the
    scout report words them (offence for an attacker, defence for a defender)."""
    k = 'off' if side == 'O' else 'def'
    lists = SC.player_lists(card, 0)
    cap = lambda t: t[:1].upper() + t[1:]
    return dict(type=card.role, tagline=card.tagline,
                plus=[cap(plain(p['text'])) for p in lists[k]['strengths']], minus=[cap(plain(p['text'])) for p in lists[k]['weaknesses']])


def matchup_lines(s, matchups):
    """For each attacker and the defender on him (the board's matchup), the advantage in words, both ways round:
    offence 'hunt' lines (his strength meets the defender's weakness), defence lines (the defender's strength meets
    the attacker's weakness), and 'help off' (no threat from three: his defender can help)."""
    O, X = s.ctx.off, s.ctx.dfn
    out = []
    for i in range(5):
        js = matchups['O'][i] if matchups and matchups.get('O') else []
        if not js:
            out.append(dict(o=i, x=None, hunt=[], guard=[], help=None))
            continue
        j = js[0]
        hunt, guard = [], []
        for pair in SC.CONFIG['mismatches']['offence']:
            if not SC._has(X[j], pair['def'], 'weakness', 'def'):
                continue
            for pid in pair['off']:
                if SC._has(O[i], pid, 'strength', 'off'):
                    hunt.append(f"O{i + 1} {clause(pid, 'strength')}, and X{j + 1} {clause(pair['def'], 'weakness')}.")
        for pair in SC.CONFIG['mismatches']['defence']:
            if not SC._has(O[i], pair['off'], 'weakness', 'off'):
                continue
            for pid in pair['def']:
                if SC._has(X[j], pid, 'strength', 'def'):
                    guard.append(f"X{j + 1} {clause(pid, 'strength')}, and O{i + 1} {clause(pair['off'], 'weakness')}.")
        help_ = f"O{i + 1} {clause('three', 'weakness')}: X{j + 1} can help off him." if SC._has(O[i], 'three', 'weakness', 'off') else None
        out.append(dict(o=i, x=j, hunt=hunt[:2], guard=guard[:2], help=help_))
    return out
