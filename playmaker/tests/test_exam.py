"""Step 31: the fundamentals exam (docs/reference/GRAVITY_AND_SPACING_DESIGN.md, "Board checks"). Every check is one
reading of one board (tests/exam_boards.py), by its number. Each fails if its principle is missing from the build;
how that was confirmed is in docs/reports/STEP31_REPORT.md. CLAUDE.md: every later step runs this file and reports it.

The JavaScript engine reads every board once (one Node process for the whole file); the Python engine reads the same
boards where it fits the test limit (check B2)."""
import json
import os
import shutil
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
needs_node = pytest.mark.skipif(shutil.which('node') is None, reason='needs Node for the JavaScript engine')

import exam_boards as X          # noqa: E402


@pytest.fixture(scope='module')
def T():
    import step_31 as T
    return T


@pytest.fixture(scope='module')
def values(T):
    """Every board's value by the JavaScript engine: {name: the 'value' reading}."""
    names = list(X.BOARDS)
    return {r['name']: r['res'] for r in T.js([T.req(n, dict(only='value')) for n in names])}


# ---- the one number (stage 1) ----------------------------------------------------------------------------------------

@needs_node
def test_O1_a_cutter_who_catches_under_the_rim_with_one_late_defender_shoots(values, T):
    """E13. Take the good shot: he takes it unless playing on reads higher, and then the report says what beats it.

    RE-RECORDED in step 31, Part C, with this note. The first line was `shot_now > play_on + 1.0` (36 against 23.53).
    The ruling of 25 November ("later answers cost actions too", D-302) changed what playing on reads: a step and a
    shot in the same turn now face no defensive movement in between, so playing on read 36 as well.

    REWRITTEN in fix 4 (Shaun, 27 Nov 2026: "the shooter takes the shot unless playing on reads higher, and the report
    says what beats it"). Since fix 3c, O5's cut from the corner to G3 reads 38 against O4's shot at 36, so the turn
    passes to O5. The guard now holds both sides of that: if the shot is the most, the number is the shot's and the
    turn ends in it; if playing on reads more, the number is playing on's, the report names the look that beats the
    shot at exactly that worth, and the turn doesn't end in his shot from where he stands."""
    v = values['E13']
    assert v['shot_now'] is not None, v
    prof = json.load(open(os.path.join(ROOT, 'playmaker_engine', 'data', 'ai_profiles.json')))['profiles']['allstar']
    out = T.js([T.req('E13', None, fn='searchJSON', profile=prof, max_depth=1)], timeout=300)[0]['res']
    turn = out['results'][0][1]
    if v['shot_now'] >= v['play_on'] - 1e-9:
        assert v['value'] == pytest.approx(v['shot_now']) and v['beats_shot'] is None, v
        # (he may step to a square the late defender can't reach first: the turn still ends in his shot, this turn)
        assert turn[-1][0] == 'shot' and turn[-1][2] == 3 and all(a[2] == 3 for a in turn), out['results'][:3]
    else:
        bs = v['beats_shot']
        assert bs is not None and v['value'] == pytest.approx(v['play_on']), v
        assert bs['p'] * bs['worth'] == pytest.approx(v['play_on'], abs=1e-2) and bs['worth'] > v['shot_now'], bs
        assert not (len(turn) == 1 and turn[0][0] == 'shot'), out['results'][:3]


@needs_node
def test_O1_fails_without_the_defences_answer_inside_the_number(values):
    """The principle missing: read with the defence standing still, playing on looks worth more than the shot (the 20
    November fault: the cutter didn't shoot). `before_answer` is that reading.

    RE-RECORDED in step 31, Part C: the last comparison was `shot_now > play_on`; under D-302 the two are level (see the
    note on the test above). REWRITTEN in fix 4, as the test above: the answer inside the number never raises playing
    on; if the shot is the most, the answer is what makes it so (before it, playing on read more); if playing on reads
    more even with the answer, the report says what beats the shot."""
    v = values['E13']
    assert v['before_answer'] >= v['play_on'] - 1e-9, v
    if v['shot_now'] >= v['play_on'] - 1e-9:
        assert v['before_answer'] > v['shot_now'], v
    else:
        assert v['beats_shot'] is not None and v['beats_shot']['worth'] > v['shot_now'], v


@needs_node
def test_G5_covering_one_of_two_equal_looks_leaves_the_number_unchanged_covering_both_lowers_it(values):
    """REWRITTEN in fix 4b (Shaun, 27 Nov 2026): on E23d to E23f, boards where the backdoor cuts are covered (O4 and O5
    stand deep with no shot, so their defenders help on the low blocks), so it tests covering one of two equal threes.
    On E23a to E23c, covering a shooter tight opened his cut behind the defender (the fix 4 report, section 2)."""
    a, b, c = values['E23d']['value'], values['E23e']['value'], values['E23f']['value']
    assert a == pytest.approx(b), (a, b)                  # both sagging; one covered
    assert c < b - 1.0, (b, c)                            # both covered


@needs_node
def test_the_shot_clock_running_out_is_minus_5_on_the_scale(values, T):
    """Scale audit, row 4: a last-phase board with no shot read 0; the rules score -5 (D-198)."""
    s = X.get('E22').with_(clock=2, tok_o=0, side='X')     # O1 on plain wood, nothing left to act with
    r = T.js([T.req('x', dict(only='value'), state=s)])[0]['res']
    assert r['shot_now'] is None and r['value'] == -5


def test_A12_the_mix_holds_when_holding_is_level_and_gambles_when_the_gamble_wins():
    """D-298 (carry-over 2). Step 30's board 3, the three replies to a pass that may be a fake, worth to the offence
    (real, fake): go for the Intercept (19.3, 27), hold the lane (21, 21), step off (22, 18). Holding can't be made
    worse by the offence's choice, so it is the reply. Before the fix the mix took the first on its list (the gamble)."""
    from playmaker_engine.search import mix_game
    v, p, q = mix_game([(19.3, 27.0), (21.0, 21.0), (22.0, 18.0)])
    assert v == pytest.approx(21.0) and q == {1: 1.0}
    # A13: against a ball handler who can't fake, the fake column is the real one: the Intercept now wins outright
    v, p, q = mix_game([(19.3, 19.3), (21.0, 21.0), (22.0, 22.0)])
    assert v == pytest.approx(19.3) and q == {0: 1.0}


@needs_node
def test_the_mix_is_the_same_in_both_engines(tmp_path):
    from playmaker_engine.search import mix_game
    import subprocess
    cases = [[(19.3, 27.0), (21.0, 21.0), (22.0, 18.0)], [(19.3, 19.3), (21.0, 21.0)], [(10.0, 30.0), (25.0, 12.0)], [(5.0, 5.0)], [(8.0, 20.0), (20.0, 8.0), (15.0, 15.0)]]
    js = "const E=require(process.argv[1]);console.log(JSON.stringify(JSON.parse(process.argv[2]).map(c=>E.mixGame(c))))"
    out = json.loads(subprocess.run(['node', '-e', js, os.path.join(ROOT, 'playmaker_web', 'static', 'engine.js'), json.dumps(cases)], capture_output=True, text=True, check=True).stdout)
    for c, (v, p, q) in zip(cases, out):
        pv, pp, pq = mix_game(c)
        assert pv == pytest.approx(v) and pp == pytest.approx(p) and pq == {k: pytest.approx(w) for k, w in q}


# ---- both engines (B2), the value ------------------------------------------------------------------------------------

B2_FAST = ('E13', 'E16', 'E23c', 'E28', 'BLK1')         # the boards the Python engine reads inside the test limit


@needs_node
@pytest.mark.parametrize('name', B2_FAST)
def test_B2_both_engines_read_the_same_value_the_same_bar_and_the_same_answer(name, values):
    from playmaker_engine import board as B, decide as D, value as V
    s = X.get(name)
    j = values[name]
    pp = V.poss_parts(s)
    assert D.Read(s).leaf() == pytest.approx(j['value'], abs=1e-4)          # (the JavaScript reading is printed to four places)
    assert pp['V'] == pytest.approx(j['play_on'], abs=1e-4)
    assert [round(b, 2) for b in pp['bars']] == j['bars']
    assert [[d, B.sq(q), a] for d, q, a in pp['moves']] == j['answer']


# ---- the cuts that can't change the answer (D-299) ---------------------------------------------------------------------

BRUTE_JS = r"""
const fs = require('fs'), path = require('path');
const root = process.argv[1];
const E = require(path.join(root, 'playmaker_web', 'static', 'engine.js'));
const load = n => JSON.parse(fs.readFileSync(path.join(root, 'playmaker_engine', 'data', n)));
E.init({ zones: load('court_zones.json'), config: load('ai_profiles.json'), vcoarse: load('vcoarse.json'), segments: load('segments.json'), learned: null });
const out = [];
for (const b of JSON.parse(fs.readFileSync(0, 'utf8'))) {
  const s = E.stateFrom(b.state, E.makeCtx(b.ctx));
  E._pvBrute(false); const a = E.possParts(s);
  E._pvBrute(true); const c = E.possParts(s);
  E._pvBrute(false);
  out.push({ name: b.name, cut: [a.V, a.moves], full: [c.V, c.moves] });
}
process.stdout.write(JSON.stringify(out));
"""


@needs_node
def test_the_defences_answer_is_the_same_with_every_movement_read_in_full(T):
    """The value skips movements that can't lower it, and reads the rest best bound first. With both cuts off (every
    movement read in full) the value and the answer are the same. (765 boards were read this way in step 31; these
    four keep the guard inside the limit.)"""
    import subprocess
    reqs = [T.req(n) for n in ('E13', 'E21', 'E30', 'BLK2')]
    p = subprocess.run(['node', '-e', BRUTE_JS, ROOT], input=json.dumps(reqs), capture_output=True, text=True, timeout=300)
    assert p.returncode == 0, p.stderr[-2000:]
    for r in json.loads(p.stdout):
        assert r['cut'][0] == pytest.approx(r['full'][0], abs=1e-9) and r['cut'][1] == r['full'][1], r


# ---- reading by difference: the memory (D-299) ---------------------------------------------------------------------------

DIFF_JS = r"""
const fs = require('fs'), path = require('path');
const root = process.argv[1];
const E = require(path.join(root, 'playmaker_web', 'static', 'engine.js'));
const load = n => JSON.parse(fs.readFileSync(path.join(root, 'playmaker_engine', 'data', n)));
E.init({ zones: load('court_zones.json'), config: load('ai_profiles.json'), vcoarse: load('vcoarse.json'), segments: load('segments.json'), learned: null });
const out = [];
for (const b of JSON.parse(fs.readFileSync(0, 'utf8'))) {
  const ctx = E.makeCtx(b.ctx), s = E.stateFrom(b.state, ctx);
  const acts = E.legalActions(s).filter((a, i) => i % b.every === 0);
  let n = 0, bad = 0;
  // after the board itself has been read, every board one legal action on is read inside the same memory ...
  const warm = E._withMemo(() => { E.possParts(s); return acts.map(a => { const nx = E.apply(s, a); return (E.isChance(nx) || nx.stage !== 'play') ? null : E.possParts(nx).V; }); });
  // ... and again from nothing (a state rebuilt from its own description, no memory open)
  acts.forEach((a, i) => { const nx = E.apply(E.stateFrom(b.state, E.makeCtx(b.ctx)), a); if (E.isChance(nx) || nx.stage !== 'play') return; n++; if (Math.abs(E.possParts(nx).V - warm[i]) > 1e-9) bad++; });
  out.push({ name: b.name, boards: n, different: bad });
}
process.stdout.write(JSON.stringify(out));
"""


@needs_node
def test_after_each_legal_action_the_reading_from_the_memory_equals_a_fresh_reading(T):
    """The prompt's guard for reading by difference: on the exam's boards in play, after each legal action from the
    position, the reading taken with the think's memory warm (everything the action didn't touch is not read again)
    equals a full fresh reading. (Every third action here, to stay inside the limit; tools/step_31.py checks all.)"""
    import subprocess
    reqs = [dict(T.req(n), every=3) for n in ('E13', 'E16', 'E24', 'E29', 'E30')]
    p = subprocess.run(['node', '-e', DIFF_JS, ROOT], input=json.dumps(reqs), capture_output=True, text=True, timeout=600)
    assert p.returncode == 0, p.stderr[-2000:]
    for r in json.loads(p.stdout):
        assert r['boards'] > 0 and r['different'] == 0, r


# ---- B3: each side thinks alone, on a small board, through the app's own path ------------------------------------------------

@needs_node
def test_B3_changing_one_sides_private_plan_never_changes_the_other_sides_choice():
    """The separate-thinking test (tests/test_step24.py) took 14 minutes as written. Rebuilt on small boards (few
    actions left to each side) through the agents the app plays with (playmaker_web/game.py builds one Agent a side and
    hands each its own setup's plan and scout, nothing of the other side's). The defence's choice is the same whatever
    the offence privately plans; the offence's is the same whatever matchups the defence privately holds; and the new
    setups take the board, the cards and the rules only."""
    import inspect
    import step_31_exam as XM
    from playmaker_engine import setup31
    r = XM.separate_thinking()
    assert len(set(r['defence'])) == 1 and len(set(r['offence'])) == 1 and r['same'], r
    # the setups: what each is handed. The defence's takes the offence's squares and who has the ball (what the board
    # shows), never a plan; the offence's takes nothing of the defence's at all.
    assert list(inspect.signature(setup31.place_defence).parameters)[:3] == ['make', 'o_sq', 'ball']
    assert not {'plan', 'perm', 'assign', 'matchups'} & set(inspect.signature(setup31.place_defence).parameters)
    assert not {'x_sq', 'arrows', 'perm', 'assign', 'matchups'} & set(inspect.signature(setup31.place_offence).parameters)


# ---- every check, by its number, from the exam's readings ------------------------------------------------------------------
# The setups take minutes each, so the readings are taken once by `python3 tools/step_31_exam.py read` (three processes
# side by side) and kept in docs/runs/step31/exam_readings.json; each check is judged here from them, live. A check
# passes on 'pass', or on 'for Shaun' (it fails as written for a reason that is Shaun's to judge, named in the row). 'fail' and
# 'not built' fail the test, with the check's own words.

CHECKS = ['D%d' % i for i in range(1, 13)] + ['O%d' % i for i in range(1, 13)] + ['B%d' % i for i in range(1, 5)] + ['G%d' % i for i in range(1, 6)] + ['A%d' % i for i in range(1, 18)]


@pytest.fixture(scope='module')
def verdicts():
    import step_31_exam as XM
    path = os.path.join(ROOT, 'docs', 'runs', 'step31', 'exam_readings.json')
    if not os.path.exists(path):
        pytest.skip('the exam readings have not been taken: python3 tools/step_31_exam.py read')
    rows = XM.judge(json.load(open(path)))
    by = {}
    for r in rows:
        by.setdefault(r['check'], []).append(r)
    return by


@pytest.mark.parametrize('check', CHECKS)
def test_check(check, verdicts):
    rows = verdicts.get(check)
    assert rows, f'{check}: no reading (the board could not be read)'
    for r in rows:
        assert r['verdict'] in ('pass', 'for Shaun'), f"{check} on {r['board']}: {r['verdict']}. {r['did']}"
