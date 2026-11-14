"""Step 6 (plan step 9): Shaun's rulings of 9 Nov 2026. Contest as an action (D-18), overtime in the app (D-19), the
turnover floor (D-82), steal fouls (D-89), growth at Junior (D-88), the distance rings (D-84) and the blocked-step reason
(D-104)."""
import os
import subprocess

import pytest

from conftest import P, mk
from playmaker_engine import rules_config as RC
from playmaker_engine.actions import Action, legal_actions, screen_blocked
from playmaker_engine.resolve import apply, ChanceNode, force, pickoff
from playmaker_engine.scoring import score, contest_options
from playmaker_engine.state import Result

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
needs_node = pytest.mark.skipif(subprocess.run(['node', '-e', "require('playwright')"], capture_output=True).returncode != 0,
                                reason='needs node and playwright')


def _shot(o1='I9', x1='I8', x1_arrow='N', tok_x=6, rules=None):
    """O1 declares a long two from I9; X1 next to him on I8 (arrow N: on the shooter, a clean contest)."""
    s = mk([o1, 'C9', 'O9', 'A3', 'Q3'], [x1, 'D8', 'N8', 'G4', 'N4'], [x1_arrow, 'NE', 'NW', 'N', 'N'], rules=rules)
    s = s.with_(tok_x=tok_x)
    return apply(s, Action('shot', 'O', 0, shot='long'))


# ---- D-18: Contest as an action --------------------------------------------------------------------------------------

def test_contest_costs_a_token_and_is_the_last_action():
    r = _shot()
    assert r.stage == 'reaction'
    c = Action('contest', 'X', 0)
    assert c in legal_actions(r)
    end = apply(r, c)
    assert not isinstance(end, ChanceNode) and end.stage == 'over'           # clean: the shot resolves at once
    assert end.tok_x == r.tok_x - 1 and end.result.contester == 0 and end.result.contest > 0
    # after one movement the Contest is still there, as the second and last action
    mv = next(a for a in legal_actions(r) if a.kind == 'move' and a.piece == 1)
    r2 = apply(r, mv)
    assert r2.stage == 'reaction' and r2.turn_n == 1 and Action('contest', 'X', 0) in legal_actions(r2)
    # after two actions the reaction is over: no third action, no Contest
    mv2 = next(a for a in legal_actions(r2) if a.kind == 'move' and a.piece == 2)
    done = apply(r2, mv2)
    assert done.stage == 'over' and done.result.contester == -1 and done.result.contest == 0
    # a defence with no tokens left can't Contest
    spent = _shot(tok_x=0)
    assert not any(a.kind == 'contest' for a in legal_actions(spent))
    assert 'contest' in RC.TURN_ENDERS and RC.LIMITS['X']['contest'] == 1


def test_no_contest_means_a_contest_of_0():
    r = _shot()
    end = apply(r, Action('end_turn', 'X'))
    assert end.stage == 'over' and end.result.contester == -1 and end.result.contest == 0
    o1 = end.ctx.off[0]
    assert end.result.shot_value == 2 * o1.shot('long')
    assert 'contested by nobody' in score(end).detail


def test_a_steal_reaction_cannot_contest():
    r = _shot()
    st = apply(r, Action('steal', 'X', 0))
    kept = force(st, 'no foul', 'kept')
    assert kept.stage == 'over' and kept.result.contester == -1 and kept.result.contest == 0
    assert not isinstance(kept, ChanceNode)


def test_the_forced_shot_keeps_the_contest_choice():
    s = mk(['I10', 'C9', 'O9', 'A3', 'Q3'], ['I9', 'D8', 'N8', 'G4', 'N4'], ['N', 'NE', 'NW', 'N', 'N'])
    s = s.with_(clock=2, side='X', tok_x=1, tok_o=0, final=True)
    node = apply(s, Action('move', 'X', 3, P('G5'), 0))
    assert node.stage == 'contest' and node.forced
    assert sorted(a.piece for a in legal_actions(node)) == [-1, 0]


def test_the_old_free_contest_replays_under_its_setting():
    old = RC.with_rules(**RC.PRE_9NOV)
    r = _shot(rules=old)
    assert not any(a.kind == 'contest' for a in legal_actions(r))
    assert apply(r, Action('end_turn', 'X')).stage == 'contest'


# ---- D-82: the turnover floor ------------------------------------------------------------------------------------------

def test_a_zeroing_turnover_never_helps_the_offence():
    s = mk(['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'G4', 'N4'], ['N', 'NE', 'NW', 'N', 'N'])
    last = s.with_(clock=2, tos=1)                          # -5 banked before the last phase
    end = pickoff(last)
    assert end.stage == 'over' and end.zeroed and score(end).total == -5
    plus = s.with_(clock=2, bonus5=1)                       # +5 banked: the turnover scores 0
    assert score(pickoff(plus)).total == 0
    clean = s.with_(clock=2)
    assert score(pickoff(clean)).total == 0
    old = mk(['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'G4', 'N4'], ['N', 'NE', 'NW', 'N', 'N'],
             rules=RC.with_rules(turnover_floor=False))
    assert score(pickoff(old.with_(clock=2, tos=1))).total == 0
    dig = mk(['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'G4', 'N4'], ['N', 'NE', 'NW', 'N', 'N'],
             rules=RC.with_rules(digital=True)).with_(bonus5=1)
    assert score(pickoff(dig)).total == 0                    # the app: every turnover scores 0 (nothing negative banked)


# ---- D-89: steal fouls -------------------------------------------------------------------------------------------------

def _steal(rules=None, **kw):
    s = mk(['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'G4', 'N4'], ['N', 'NE', 'NW', 'N', 'N'], rules=rules)
    ctx_kw = {k: kw.pop(k) for k in ('team_fouls',) if k in kw}
    if ctx_kw:
        s.ctx.team_fouls = ctx_kw['team_fouls']
    return s.with_(side='X', **kw)


@pytest.mark.parametrize('fmt', ['tabletop', 'digital'])
def test_a_steal_foul_by_format_and_the_bonus_adds_free_throws(fmt):
    rules = RC.with_rules(digital=fmt == 'digital')
    first = force(apply(_steal(rules), Action('steal', 'X', 0)), 'foul')
    # the table: +5, play on. The app, since D-179 (step 18j): a team foul, no +5, play on
    assert first.stage == 'play' and first.fouls == 1 and first.bonus5 == (1 if fmt == 'tabletop' else 0)
    if fmt == 'tabletop':
        bonus = _steal(rules, fouls=1, bonus5=1)                                     # the second of the possession
    else:
        bonus = _steal(rules, team_fouls=4)                                          # the 5th team foul of the quarter
    end = force(apply(bonus, Action('steal', 'X', 0)), 'foul')
    sc = score(end)
    assert end.stage == 'over' and end.result.kind == 'free_throws'
    # the table: the +5 as well. The app, since D-181 (step 18k): two free throws, nothing more
    assert end.bonus5 == bonus.bonus5 + (1 if fmt == 'tabletop' else 0)
    assert sc.bonus == 5 * end.bonus5 and sc.free_throws == 2 * end.ctx.off[0].r['free_throw']
    assert sc.total == sc.bonus + sc.free_throws + sc.turnover_points


# ---- D-19: overtime ----------------------------------------------------------------------------------------------------

def _finish_possession(g, total):
    """End the possession in play with a chosen score (a test shortcut: the score is set, the bookkeeping is the game's)."""
    g.state = g.state.with_(stage='over', side='-', result=Result('shot', 0, 'long', 2, total // 2, 0, -1, total, 0))
    g._end_possession()


def test_overtime_ends_only_on_a_lead_after_equal_possessions():
    from playmaker_web.game import Game
    g = Game(mode='hotseat', teams=['Five Out', 'High-Low'], seed=4, full=True, match_format='digital', per_side=4)
    g.placing = None
    tot = 0
    for n in range(1, 9):                                    # 4 a side, every possession 10: tied 40-40
        g.possession = n
        _finish_possession(g, 10)
    assert g.n_poss == 10 and getattr(g, 'match', None) is None and g.overtime == 1
    g.possession = 9
    _finish_possession(g, 10)
    g.possession = 10
    _finish_possession(g, 10)                                # still tied after equal possessions: another overtime
    assert g.n_poss == 12 and g.overtime == 2 and getattr(g, 'match', None) is None
    g.possession = 11
    _finish_possession(g, 12)
    g.possession = 12
    _finish_possession(g, 10)                                # a lead after equal possessions: the match is over
    assert g.match and g.match['winner'] in ('A', 'B') and g.match['A'] != g.match['B']
    assert [r['type'] for r in g.read_log()].count('overtime') == 2


def test_a_tied_tabletop_game_keeps_its_final_shot_roll():
    from playmaker_web.game import Game
    g = Game(mode='hotseat', teams=['Five Out', 'High-Low'], seed=4, full=True)
    assert g.n_poss == 2
    for n in (1, 2):
        g.possession = n
        _finish_possession(g, 10)
    assert g.n_poss == 2 and g.match and 'tiebreak' in g.match


# ---- D-88: growth at Junior --------------------------------------------------------------------------------------------

def test_junior_growth_shows_no_tag_names_and_coach_vision_gives_the_two_lines():
    import json
    from playmaker_web.game import Game
    from playmaker_web.view import state_json
    from playmaker_engine.levels import growth_line
    from playmaker_engine.plain import check
    early, late = 'Bigger and stronger than most players his age.', 'Still growing: smaller and slower than most players his age.'
    assert growth_line('early') == early and growth_line('late') == late and growth_line('typical') is None
    g = Game(age='junior', level='learn', seed=11, full=True, match_format='digital', per_side=4)
    g._revealed = True
    st = state_json(g, g.tokens['both'])
    for side in ('o', 'x'):
        lines = [p['card']['coach_growth'] for p in st[side]]
        assert sorted(l for l in lines if l) == sorted([early, late])
        assert all('growth' not in p['card'] for p in st[side])
    text = json.dumps(st)
    for word in ('on_time', 'On time', 'growth tag', 'Early:', 'Late:'):     # tag names never reach the page's words
        assert word not in text, word
    assert not check('Early: Quick Step +1') and check('the tag is on time')       # 'on time' as a growth term is banned
    # the tabletop format: no growth, the junior cards as printed
    t = Game(age='junior', level='learn', seed=11)
    assert t.levels['tags'] is None
    st = state_json(t, t.tokens['both'])
    assert all(p['card']['coach_growth'] is None for side in ('o', 'x') for p in st[side])


def test_banned_terms_include_the_old_words():
    from playmaker_engine.plain import check
    for t in ('a pick-off', 'he was picked off', 'a clean miss'):
        assert check(t), t
    assert not check('the decision timer')                  # 'on time' only as words, not inside 'decision timer'


# ---- D-104: the blocked-step reason, and D-84: the rings toggle ----------------------------------------------------------

def test_a_step_a_screen_blocks_is_reported():
    s = mk(['I11', 'C9', 'H9', 'A3', 'Q3'], ['I12', 'D8', 'G10', 'G4', 'N4'], ['N', 'NE', 'N', 'N', 'N'])
    s = s.with_(screens=((2, 0, True, 0),), side='X')       # O3 on H9, the T to the north (H10); X3 on G10
    blocked = screen_blocked(s, 2)
    assert blocked == {'move': [P('H11'), P('I9')]} and all(q not in [a.dest for a in legal_actions(s) if a.piece == 2 and a.kind == k]
                           for k, qs in blocked.items() for q in qs)
    from playmaker_web.view import screen_blocked_json
    assert screen_blocked_json(s)['2']
    assert screen_blocked(s.with_(screens=()), 2) == {}


NODE_RINGS = r"""
const { chromium } = require('playwright');
const [base] = process.argv.slice(2);
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
  const post = (path, body) => p.evaluate(([u, bd]) => fetch(u, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(bd) }).then(r => r.json()), [base + path, body]);
  await p.goto(base + '/');
  const g = await post('/api/new', { mode: 'hotseat', scenario: 6, seed: 3 });
  await p.goto(`${base}/?code=${g.code}&token=${g.token}`); await p.waitForTimeout(1200);
  for (let i = 0; i < 8 && await p.evaluate(() => !document.getElementById('modal').classList.contains('hidden')); i++) {
    if (await p.$('#modal:not(.hidden) button.primary')) await p.click('#modal:not(.hidden) button.primary').catch(() => {});
    else await p.keyboard.press('Escape');
    await p.waitForTimeout(400);
  }
  const res = { before: await p.$$eval('#court g.rings rect', x => x.length), label1: await p.textContent('#ringsToggle') };
  await p.click('#ringsToggle'); await p.waitForTimeout(300);
  res.after = await p.$$eval('#court g.rings rect', x => x.length);
  res.label2 = await p.textContent('#ringsToggle');
  console.log(JSON.stringify(res));
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
"""


@needs_node
def test_the_distance_rings_show_by_default_and_toggle_off(tmp_path):
    import json
    from playmaker_web.server import start_background
    srv, base = start_background()
    try:
        (tmp_path / 'rings.js').write_text(NODE_RINGS)
        r = subprocess.run(['node', str(tmp_path / 'rings.js'), base], capture_output=True, text=True, timeout=120,
                           cwd=str(tmp_path))
        assert r.returncode == 0, r.stderr[-1500:]
        out = json.loads(r.stdout.strip().splitlines()[-1])
    finally:
        srv.shutdown()
    assert out['before'] > 0 and out['label1'] == 'Distance rings: shown'
    assert out['after'] == 0 and out['label2'] == 'Distance rings: hidden'


@pytest.mark.parametrize('fmt', ['tabletop', 'digital'])
def test_a_steal_foul_on_a_shooter_is_free_throws_only(fmt):
    """Step 7 (D-89): a Steal against a declared shot that fouls is a shooting foul: the free throws only, no +5; it still
    counts as a foul (a team foul in the app)."""
    r = _shot(rules=RC.with_rules(digital=fmt == 'digital'))
    end = force(apply(r, Action('steal', 'X', 0)), 'foul')
    sc = score(end)
    assert end.stage == 'over' and end.result.kind == 'free_throws' and end.fouls == r.fouls + 1
    assert end.bonus5 == r.bonus5 and sc.bonus == 0 and sc.total == sc.free_throws
