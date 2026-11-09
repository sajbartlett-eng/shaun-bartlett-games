"""Step 8: the exam book for Shaun's review in step 12 (docs/reports/EXAM_BOOK.html and EXAM_BOOK_index.md).

One page per board: the 17 exam boards, the two playtest candidates (D-108, D-109) and the two trainer tests that
Contest as an action changed (D-112, D-113; D-111 is exam board 6). The pictures use the app's own drawing library
(playmaker_web/static/notation.js) through the pre-installed browser; the words are written here by hand and checked
against the banned-terms list. Results are read from files on file; nothing here runs the exam.

  python3 tools/exam_book.py
"""
import html
import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from playmaker_engine import board as B                                   # noqa: E402
from playmaker_engine import exam as E                                    # noqa: E402
from playmaker_engine import plain                                        # noqa: E402
from playmaker_engine.actions import legal_actions                         # noqa: E402
from playmaker_engine.resolve import apply                                 # noqa: E402
from playmaker_engine.scenarios import game_state, scenario_state          # noqa: E402

OUT_HTML = os.path.join(ROOT, 'docs', 'reports', 'EXAM_BOOK.html')
OUT_MD = os.path.join(ROOT, 'docs', 'reports', 'EXAM_BOOK_index.md')
DRAW = os.path.join(ROOT, 'tools', 'exam_book_draw.js')
NOTATION = os.path.join(ROOT, 'playmaker_web', 'static', 'notation.js')
RUNS = os.path.join(ROOT, 'docs', 'runs')


# ---- the boards, as plain data for the drawing ------------------------------------------------------------------------

def _bits(m):
    return [bool(m >> i & 1) for i in range(5)]


def _data(s, label=''):
    return dict(label=label, o=[B.sq(p) for p in s.o], x=[B.sq(p) for p in s.x],
                arrows=[a if isinstance(a, int) else list(a) for a in s.arrows], ball=s.ball, side=s.side,
                clock=s.clock, phase=s.phase, tok_o=s.tok_o, tok_x=s.tok_x,
                moved_o=_bits(s.moved_o), moved_x=_bits(s.moved_x), qs_o=_bits(s.qs_o), qs_x=_bits(s.qs_x),
                lock_o=_bits(s.lock_o), lock_x=_bits(s.lock_x), beaten=[list(b) for b in s.beaten],
                off=s.ctx.off_team, dfn=s.ctx.def_team)


def boards():
    out = {}
    for n, f in enumerate(E.POSITIONS, 1):
        _, b, _ = f()
        if b is None:
            out[f'b{n}'] = dict(boards=[])
        elif isinstance(b, dict):
            out[f'b{n}'] = dict(boards=[_data(v, str(k)) for k, v in b.items()])
        else:
            out[f'b{n}'] = dict(boards=[_data(b)])

    # D-108: archive/tests/test_deny_catch.py: Five Out v High-Low on the table setup, after O1's one-square lift
    s = game_state('Five Out', 'High-Low', ['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'G4', 'N4'],
                   ['N', 'NE', 'NW', 'N', 'N'])
    a = next(a for a in legal_actions(s) if a.kind == 'move' and a.piece == 0 and a.dest == B.parse_sq('I12'))
    t = apply(s, a)
    t = apply(t, next(x for x in legal_actions(t) if x.kind == 'end_turn'))
    out['d108'] = dict(boards=[_data(t)], marks=[dict(kind='move', side='O', frm='I11', to='I12', turn=1)])

    # D-109: archive/tests/test_passing.py, the position 'prefer_clean' (tests/data/pass_positions.json)
    d = json.load(open(os.path.join(ROOT, 'tests', 'data', 'pass_positions.json')))['prefer_clean']
    fl = dict(d['fields'])
    fl.update(o=tuple(map(tuple, fl['o'])), x=tuple(map(tuple, fl['x'])), arrows=tuple(fl['arrows']),
              cnt=tuple(fl['cnt']), screens=tuple(fl['screens']), beaten=tuple(fl['beaten']))
    s = scenario_state(d['spec'][1]).with_(**fl)
    out['d109'] = dict(boards=[_data(s)], marks=[
        dict(kind='pass', side='O', frm=B.sq(s.o[0]), target=B.sq(s.o[d['clean']]), turn='a'),
        dict(kind='pass', side='O', frm=B.sq(s.o[0]), target=B.sq(s.o[d['contested']]), turn='b')])

    # D-112: tests/test_step3m.py, the early cut: O5 cuts a turn before O1's drive
    s = E.board(['H9', 'C8', 'O8', 'B3', 'P3'], ['H8', 'D8', 'N8', 'C3', 'O3'], ['N', 'W', 'E', 'W', 'E'])
    out['d112'] = dict(boards=[_data(s)], marks=[dict(kind='move', side='O', frm='P3', to='N5', turn=1),
                                                 dict(kind='move', side='O', frm='H9', to='J7', turn=2)])

    # D-113: tests/test_step3n.py, the decoy: O2 lifts and X3 leaves the far side
    s = E.board(['I11', 'C9', 'O9', 'A3', 'Q3'], ['I10', 'D8', 'N8', 'D4', 'N4'], ['N', 'W', 'E', 'E', 'W'])
    out['d113'] = dict(boards=[_data(s)], marks=[dict(kind='move', side='O', frm='C9', to='D9', turn=1)])
    return out


def draw(data):
    zones = [[B.zone((x, y)) for x in range(17)] for y in range(1, 15)]
    with tempfile.TemporaryDirectory() as tmp:
        bp, zp, op = (os.path.join(tmp, f) for f in ('boards.json', 'zones.json', 'svgs.json'))
        json.dump(data, open(bp, 'w'))
        json.dump(zones, open(zp, 'w'))
        subprocess.run(['node', DRAW, NOTATION, bp, zp, op], check=True)
        return json.load(open(op))


# ---- results on file --------------------------------------------------------------------------------------------------

def results():
    fixed = {r['n']: r for r in json.load(open(os.path.join(RUNS, '3n', '3n_exam_fixed4.json')))['rows']}
    timed = {r['n']: r for r in json.load(open(os.path.join(RUNS, '3n', '3n_exam_timed.json')))['rows']}
    board1 = json.load(open(os.path.join(RUNS, '3n', '3n_board1.json')))
    today = json.load(open(os.path.join(RUNS, 'step6', 'exam_results.json')))['boards']
    return fixed, timed, board1, today


# ---- the words --------------------------------------------------------------------------------------------------------
# Every page: title, situation, expect, why, judged, instead (what the computer chose, in plain words), rulings.
# Results not written here come from the files above.

PAGES = [
    dict(key='b1', n='1', title='Straight lane',
         situation='Five-out. O1 has the ball at the top of the key, just inside the arc. X1 has slipped two squares '
                   'to the right of him, so the straight line from O1 to the rim is open. The defence is about to act.',
         expect='The defence takes away the straight drive: X1 recovers in front of O1, or a helper steps into the '
                'lane, or the drive is left open only if it is worse than what the offence already has.',
         why='A ball handler with a straight line to the rim is the first thing a defence has to take away.',
         judged='After the defence\'s turn, look at every move O1 could make straight toward the rim. The board is met '
                'if there is none, or if the best of them is worth less than the offence\'s best other option.',
         instead='',
         rulings='Restated before the 9 November rules: it used to ask for a defender on the line itself, and is now '
                 'judged by what the drive is worth (D-96). The earlier line check failed; the results below use the '
                 'new reading.',
         note='On this board the drive is weak before the defence does anything (worth 10 against 26 for the best '
              'other option), so the board passes easily and tests little. A board where the drive starts strong '
              'would test the rule better.'),
    dict(key='b2', n='2', title='Sag by shooting',
         labels={'4': 'Board A: O2\'s three rated 4', '12': 'Board B: O2\'s three rated 12'},
         teams={'4': 'Five Out (offence; O2\'s three rated 4) v Iron Wall (defence)',
                '12': 'Five Out (offence; O2\'s three rated 12) v Iron Wall (defence)'},
         situation='Two copies of one board. O1 has the ball at the top, X2 guards O2 on the left wing. The only '
                   'difference: on board A, O2 is a poor three-point shooter (rated 4); on board B, a good one '
                   '(rated 12). The defence is about to act.',
         expect='X2 sags further off the poor shooter to help inside, and stays close enough to contest the good '
                'shooter.',
         why='You give a poor shooter room and use the spare defender to protect the paint; you never leave a good '
             'shooter open.',
         judged='After the defence\'s turn, X2 must be closer to the rim on board A than on board B, and on board B '
                'he must still be able to reach O2 to contest his shot.',
         instead='X2 went to D6 against the poor shooter and to D7 against the good one: 5 squares from the rim both '
                 'times, so he did not sag further off the poor shooter. He could still contest the good shooter.',
         rulings='Contest is now an action (D-18): a contest uses one of the defence\'s actions and must come from a '
                 'defender next to the shooter, which changes how far X2 can sag and still contest.',
         note='Searching four moves ahead it passed before the 9 November rules; under time it failed. The step 3n '
              'report put this down to speed: the right answer appears once the computer looks far enough ahead.'),
    dict(key='b3', n='3', title='Help the helper',
         situation='O1 has driven past X1 and has the ball in the lane, 3 squares from the rim. X1 is behind him, '
                   'beaten, and has used his Move. O4 waits on the left baseline, guarded by X4 under the basket. '
                   'The defence is about to act.',
         expect='A low defender steps up to stop O1, and another defender rotates to cover the man he left.',
         why='When the ball handler beats his man, the nearest help has to stop the ball, and the next defender '
             'covers the open man so the kick-out isn\'t free.',
         judged='After the defence\'s turn, at least one defender who was not next to O1 must end next to him, and '
                'at least one other defender must move.',
         instead='X2 stepped in from the left wing to C6 and X5 came in from the right corner to N3. Nobody stepped '
                 'up to stop O1.',
         rulings='None beyond the three that apply to every board (see the top of the book).'),
    dict(key='b4', n='4', title='Two jobs, one defender',
         situation='O1 has the ball at the top of the key, inside the arc, with X1 behind him. O5 stands on the right '
                   'block. X5 sits between them: he is the only defender who can answer both O1\'s pull-up and O5 at '
                   'the rim. The offence is about to act.',
         expect='The offence attacks X5: O1 shoots or drives, or passes to O5, and makes X5 choose.',
         why='When one defender has two jobs, you attack him: whichever he picks, the other is open.',
         judged='The computer\'s own reading of the board must see that X5 is the only answer to both, and the '
                'offence\'s turn must include a shot, a pass to O5, or O1 moving or dribbling.',
         instead='O2 lifted from the left wing to D9 and O1 passed him the ball. The offence swung the ball away '
                 'from X5, and the computer did not see X5 as stretched between O1 and O5.',
         rulings='None beyond the three that apply to every board.'),
    dict(key='b5', n='5', title='Closeout',
         labels={'close': 'Board A: X2 arrives (C7)', 'short': 'Board B: X2 stops 2 short (D7)'},
         situation='O2 has just caught the ball on the left wing. X2 has closed out from 3 squares away, using his '
                   'Move and his Quick Step. On board A he arrives next to O2; on board B he stops two squares short. '
                   'The offence is about to act.',
         expect='Board A: O2 attacks the closeout with a drive. Board B: O2 shoots at once.',
         why='Drive past a defender who arrives on a closeout; shoot over one who stops short.',
         judged='Board A: O2 moves or dribbles, and his first action is not a shot. Board B: O2\'s first action is a '
                'shot.',
         instead='On both boards O2 sprinted up the wing to B8, away from the closeout, instead of driving or '
                 'shooting.',
         rulings='Contest is now an action (D-18): a closeout is now a movement plus a Contest, which changes what '
                 'X2 can still do on both boards.',
         note='Board A counts any movement by O2 as the drive, including the sprint up the wing away from the rim. '
              'So today board A is met and the board fails on board B alone.'),
    dict(key='b6', n='6', title='Catch window', also='D-111',
         situation='O4 has just caught the ball in the left corner. Every defender is far from him: the nearest, X4, '
                   'is in the lane and X2 is up at the top of the left side. The offence is about to act.',
         expect='O4 acts at once: he shoots the open corner three or attacks before the defence recovers.',
         why='The moment after the catch, before the closeout arrives, is the best look the possession will get.',
         judged='The offence\'s first action is O4\'s own: a shot, a movement or a dribble.',
         instead='O2 moved down the left side to A5, next to O4, and set a screen. O4 did nothing himself.',
         rulings='Contest is now an action (D-18). Marked as an expected failure in step 7 for that reason, to be '
                 're-based here (D-111).'),
    dict(key='b7', n='7', title='Clock',
         labels={'phase 2': 'Board A: clock 10, phase 2', 'phase 6': 'Board B: clock 2, phase 6 (the last)'},
         situation='O3 has the ball in the middle of the lane, 4 squares from the rim, with X3 right in front of him '
                   'and two more defenders close. The same board twice: early in the possession (phase 2), then in '
                   'the last phase. The offence is about to act.',
         expect='Early: don\'t take the contested mid-range; move the ball. In the last phase: take it.',
         why='A contested two is a poor shot with time left and the best one available when time is running out.',
         judged='Board A: the first action is not a shot. Board B: the first action is a shot.',
         instead='Early, O3 sprinted out to E9 with the ball and O4 moved to A1 (no shot, as asked). In the last '
                 'phase, O1 moved to J10 and O2 sprinted to B8: O3 did not shoot.',
         rulings='Written before the phase rules settled (D-96): the last phase still holds several offence turns, so '
                 'the computer sees time to set up a better shot. The computer\'s sense of the clock is settled in '
                 'step 13 (D-92).'),
    dict(key='b8', n='8', title='Backdoor',
         situation='O1 has the ball at the top of the arc. O2 is on the left wing, high, and X2 is between him and '
                   'the ball, denying the pass. The lane behind X2, to the rim, is open. The offence is about to act.',
         expect='O2 cuts backdoor toward the rim.',
         why='When a defender overplays the pass, the cut behind him is open.',
         judged='During the turn, O2 moves at least 2 squares closer to the rim.',
         instead='O4 quick-stepped up from the left corner to A4. O2 did not cut.',
         rulings='None beyond the three that apply to every board.',
         note='The step 3n report found the reason: the pass to the cutter has a low chance of arriving, since X1 '
              'can step into its path, so the computer waits.'),
    dict(key='b9', n='9', title='Corner',
         situation='O1 has driven from the right wing to the right side of the paint, 3 squares from the rim. X5 has '
                   'left O5 in the right corner to stop him and has used his Move. O5 is open. The offence is about to '
                   'act.',
         expect='The kick-out: O1 passes to O5 in the corner, or O5 relocates for the pass.',
         why='When the corner defender helps on a drive, the corner three is the open shot.',
         judged='The turn includes a pass to O5 or a movement by O5.',
         instead='',
         rulings='None beyond the three that apply to every board.'),
    dict(key='b10', n='10', title='Steal',
         labels={'good odds': 'Board A: good odds', 'bad odds': 'Board B: bad odds'},
         teams={'good odds': 'Twin Towers (offence) v Run and Gun (defence)',
                'bad odds': 'Ball Movement (offence) v Twin Towers (defence)'},
         situation='Board A: O4, a post scorer with a weak handle, has the ball at the top of the key; X4 is in front '
                   'of him and X1 right behind him. Board B: O1, a point guard with an elite handle, has the ball in '
                   'the same spot with X1 in front, early in the possession. The defence is about to act.',
         expect='Board A: try the steal. Board B: don\'t reach.',
         why='Gamble on a poor ball handler with help close by; don\'t reach on a great one with the whole '
             'possession ahead.',
         judged='Board A: the defence\'s turn includes a Steal. Board B: it doesn\'t.',
         instead='',
         rulings='Written before the steal lock and the two foul rolls (D-96). Every steal foul now gives the offence '
                 '+5 (D-89), which raises the price of a reach.'),
    dict(key='b11', n='11', title='Contested pass',
         labels={'early': 'Board A: clock 12, early', 'final phase': 'Board B: clock 2, the last phase'},
         situation='O1 has the ball at the top, too deep to shoot. X5 has left the right corner and sits in the '
                   'passing lane from O1 to O2 on the left wing. The same board early in the possession, then in the '
                   'last phase. The offence is about to act.',
         expect='Early: don\'t throw the pass to O2 through X5. In the last phase: take the risk and pass.',
         why='A risky pass isn\'t worth it with time left; at the end it may be the only way to get a shot.',
         judged='Board A: no pass to O2. Board B: any pass.',
         instead='Early, O3 sprinted from the right wing to N5 (no pass to O2, as asked). In the last phase, O1 '
                 'quick-stepped to H10 and threw no pass.',
         rulings='Written before the app\'s rule that an interception ends the possession (D-96). A turnover now '
                 'never scores more than the total banked before it (D-82).'),
    dict(key='b12', n='12', title='Strong-side corner',
         situation='O1 has the ball on the left side, 5 squares from the rim, and X1 is in front of him, containing '
                   'the drive. O2, the best shooter on the floor, waits in the left corner with X2 on him. The defence '
                   'is about to act.',
         expect='X2 stays with O2.',
         why='The drive is already contained; helping off an elite corner shooter gives up the best shot on the '
             'floor.',
         judged='After the defence\'s turn, X2 is within 1 square of O2.',
         instead='',
         rulings='None beyond the three that apply to every board.'),
    dict(key='b13', n='13', title='Spacing',
         situation='O1 has the ball at the top of the key. O5 stands in the middle of the lane, right in O1\'s '
                   'driving line, with X5 beside him. The offence is about to act.',
         expect='O5 clears out of the lane, or the offence shoots or passes.',
         why='A teammate standing in the driving lane brings his defender into the drive.',
         judged='After the turn, O5 is out of O1\'s driving lane, unless the turn included a shot or a pass.',
         instead='O3 moved from the right wing to N5. O5 stayed in the lane, and nobody shot or passed.',
         rulings='None beyond the three that apply to every board.'),
    dict(key='b14', n='14', title='Variety',
         teams={'': 'Two mirror-image teams'},
         situation='Two mirror-image teams on a balanced board: O1 at the top, shooters on both wings, two stretch '
                   'fours on the short corners, each guarded straight up. The offence is about to act.',
         expect='The All-Star isn\'t predictable here: it spreads its first move across several good options.',
         why='A computer that always opens the same way is easy to read and dull to play.',
         judged='Over 20 games with different random seeds, no single first move is chosen more than 70% of the '
                'time.',
         instead='4 different first moves over 20 games; the most common came 80% of the time.',
         rulings='None beyond the three that apply to every board. Open question D-97 (widen the variety, restate '
                 'the board, or accept it) belongs to this board.'),
    dict(key='b15', n='15', title='Goal consistency',
         situation='The standard five-out start: O1 at the top, two wings, two corners, each guarded straight up. The '
                   'offence plays six turns in a row from here.',
         expect='The offence sticks to one plan unless something on the board gives it a reason to change.',
         why='A team that changes its mind every turn runs nothing.',
         judged='Over the six turns, the plan never flips back and forth (A, then B, then A again).',
         instead='',
         rulings='None beyond the three that apply to every board.'),
    dict(key='b16', n='16', title='Wearing out one defender',
         situation='O2, an elite shooter, is on the left wing. X2 has sagged off him toward the left elbow and is the '
                   'only defender who can answer cuts on that side, so every cut he answers uses his Move or Quick '
                   'Step. The offence is about to act.',
         expect='Over the phase, the offence makes X2 answer cut after cut until he has no moves left, then gets O2 '
                'his shot.',
         why='Make one defender do two jobs over and over, and eventually he can\'t get back.',
         judged='The first turn includes a move away from the ball; along the computer\'s planned line X2 runs out of '
                'moves; the possession gains at least 3 points along the line; and the trainer finds that first move '
                'helped over the phase by wearing X2 out.',
         instead='Planned line: O1 moved to J10 and O3 sprinted to I9; then O2 sprinted to A7; then O4 moved to A3. '
                 'X2 did run out of moves, but the computer\'s estimate of the possession didn\'t rise (24.9 points '
                 'before and after), and the first move gained nothing over the phase.',
         rulings='None beyond the three that apply to every board.'),
    dict(key='b17', n='17', title='Turn economy',
         situation='No board of its own: a check across the positions of boards 1 to 15 (20 positions in all).',
         expect='The computer\'s reading never assumes more than the turn allows: the defence never answers with '
                'more than 2 actions in a turn, and the offence never gets a shot that would take more actions than '
                'it has.',
         why='A computer that reads impossible plays chooses badly.',
         judged='No position breaks either limit.',
         instead='',
         rulings='None beyond the three that apply to every board.'),
    dict(key='d108', n='C1', title='Deny the shooter\'s catch', also='D-108', candidate=True,
         situation='Five Out against High-Low, from the tabletop starting setup. O1 has lifted one square to the deep '
                   'top (I12) and ended the offence\'s turn. O2, a sharpshooter (three rated 13), is on the left wing; '
                   'X2, whose contest on a three is only 3, guards him. The defence is about to act.',
         expect='The defence takes the catch away from O2: a defender gets onto the passing lane to him, X2 '
                'face-guards him, or a helper shades toward him.',
         why='From Shaun\'s playtests: every possession ended with a pass to O2 for a three that X2 could barely '
             'contest, because the defence never took the catch away.',
         judged='As the old test judged it: after the All-Star defence\'s turn, the pass from the ball to O2 is '
                'blocked or can be intercepted, and at least two of the passes to O2 (from the ball and from one '
                'other passer) are covered.',
         instead='',
         rulings='Contest is now an action (D-18), which changes how well X2 can contest O2\'s three.',
         today='not measured',
         today_note='The old test checked the computer retired in step 5; it '
                    'passed in the last full run with that computer.'),
    dict(key='d109', n='C2', title='Prefer the clean pass', also='D-109', candidate=True,
         teams={'': 'Bucket Brigade (offence) v Iron Wall (defence), scenario card 1 (Baseline Box)'},
         situation='Scenario card 1, with the players placed by hand. O1 has the ball on the left wing, beyond the arc. '
                   'Two teammates are worth about the same if they catch it: O2 at the right elbow, with nobody in the '
                   'path of the pass (a), and O4 on the right block, where the pass goes past defenders (b). O5 is the '
                   'inbounder, still out of bounds under the basket. The offence is about to act.',
         expect='O1 throws the clean pass to O2, never the contested one to O4.',
         why='From Shaun\'s playtests: with two equal targets, take the one the defence can\'t get a hand on.',
         judged='As the old test judged it: the computer rates the pass to O2 above the pass to O4, and the All-Star '
                'does not throw the pass to O4.',
         instead='',
         rulings='None directly. The computer the old test checked was retired in step 5.',
         today='not measured',
         today_note='The old test checked the computer retired in step 5; it '
                    'passed in the last full run with that computer. When the position was built (step 3f), that '
                    'computer moved O1 one square to C9 rather than pass.'),
    dict(key='d112', n='T1', title='An early cut', also='D-112', trainer=True,
         situation='Five-out, O1 with the ball at the top. O5 cuts from the right corner to N5 (1) a turn before O1 '
                   'drives to J7 (2), so the defence can answer the cut before the drive arrives.',
         expect='The trainer flags that the cut came a turn too early, and shows the same two actions in another '
                'order that is legal turn by turn.',
         why='A cut works when it arrives with the drive; too early, and the defence covers it first.',
         judged='The trainer finds the timing cost at least 3 points (its bar for a flag); the defence covered the '
                'cut first; and the order it offers uses the same two actions and is legal.',
         instead='The trainer found the order made less than a point of difference (0.75), below its bar of 3, so '
                 'it raised no flag.',
         rulings='Contest is now an action (D-18). Marked as an expected failure in step 7 for that reason, to be '
                 're-based here (D-112). The test keeps the computer\'s older sense of the clock on purpose (D-92).',
         today='fail', step7=True),
    dict(key='d113', n='T2', title='Naming the helper who answered the decoy', also='D-113', trainer=True,
         situation='Five-out, O1 with the ball at the top. O2 lifts one square on the left wing (1). X3 leaves the far '
                   'side to answer him, which opens the far side for O2\'s teammates.',
         expect='The review names X3 as the defender who answered O2\'s lift.',
         why='A decoy works by moving a defender; the review should say which one, so the player learns why his '
             'move helped.',
         judged='The review finds the lift helped his teammates by enough to report, and names X3; and X3 does '
                'something different with and without the lift.',
         instead='The review still found that the lift helped his teammates, but named X1, not X3.',
         rulings='Contest is now an action (D-18). Marked as an expected failure in step 7 for that reason, to be '
                 're-based here (D-113).',
         today='fail', step7=True),
]

SIDE = {'O': 'Offence to act', 'X': 'Defence to act'}
VERDICT = {True: 'Pass', False: 'Fail'}


def esc(t):
    return html.escape(t, quote=False)


def caption(b, page, label):
    teams = (page.get('teams') or {}).get(label)
    if not teams:
        teams = f"{b['off']} (offence) v {b['dfn']} (defence)"
    used = []
    for side, mv, qs in (('O', b['moved_o'], b['qs_o']), ('X', b['moved_x'], b['qs_x'])):
        for i in range(5):
            k = [w for w, f in (('Move', mv[i]), ('Quick Step', qs[i])) if f]
            if k:
                used.append(f"{side}{i + 1} has used his {' and '.join(k)}")
    locks = [f'O{i + 1}' for i in range(5) if b['lock_o'][i]] + [f'X{i + 1}' for i in range(5) if b['lock_x'][i]]
    bits = [teams, SIDE[b['side']], f"Clock {b['clock']} (phase {b['phase']})",
            f"Tokens left: offence {b['tok_o']}, defence {b['tok_x']}",
            'Locked: ' + ', '.join(locks) if locks else 'No locks']
    if used:
        bits.append('; '.join(used))
    return ' · '.join(bits)


def today_cell(page, today):
    n = page['n']
    if page.get('today') == 'not measured':
        return 'Not measured under the current rules', page['today_note']
    if page.get('trainer'):
        return 'Fail', ('Step 6 run and step 7 run (today\'s rules, including a steal foul on a shooter giving free '
                        'throws only): fails, marked as an expected failure.')
    r = today[n]['result']
    ok = r == 'pass'
    txt = 'Step 6 run: All-Star, full time budget.'
    if n == '6':
        txt += ' The step 7 run (with the shooter foul change) still fails; marked as an expected failure.'
    return ('Pass' if ok else 'Fail'), txt


def earlier(page, fixed, timed, board1):
    """The results before 9 November (step 3n)."""
    if page.get('trainer'):
        return [('Before 9 November (step 3n)', 'Pass', 'The test passed in the step 3n run.')]
    if page.get('candidate'):
        return []
    n = int(page['n'])
    f, t = fixed[n], timed[n]
    rows = []
    if n == 1:
        ok = sum(r['ok'] for r in board1['rows'])
        rows.append(('Four moves ahead, no time limit (All-Star)', 'Not measured now',
                     f"Before 9 November: passed in {ok} of {len(board1['rows'])} games, judged as today."))
    else:
        rows.append(('Four moves ahead, no time limit (All-Star)', 'Not measured now',
                     f"Before 9 November: {VERDICT[f['allstar']['ok']].lower()}."))
    lv = ', '.join(f"{name} {VERDICT[t[k]['ok']].lower()}" for k, name in
                   (('allstar', 'All-Star'), ('starter', 'Starter'), ('rookie', 'Rookie')))
    if n == 1:
        lv = 'All-Star pass, Starter fail, Rookie fail, all judged by the earlier line check'
    rows.append(('On the clock at phone speed, before 9 November', '', lv + '.'))
    return rows


CSS = """
:root { --ink:#1d1b18; --muted:#5a554c; --line:#d9d4c7; --paper:#fdfcf8; --red:#c0392b; --navy:#1f2a44;
  --pass:#1b6e3a; --fail:#a8321f; --na:#6b6457; }
* { box-sizing: border-box; }
body { margin:0; background:#f3f1ea; color:var(--ink); font:16px/1.5 Georgia, 'Times New Roman', serif; }
main { max-width: 900px; margin: 0 auto; padding: 24px 16px 60px; }
h1 { font-size: 30px; margin: 8px 0 4px; } h2 { font-size: 24px; margin: 0 0 4px; }
.lede { color: var(--muted); margin: 0 0 18px; }
.card { background: var(--paper); border: 1px solid var(--line); border-radius: 8px; padding: 22px 22px 18px;
  margin: 26px 0; }
.kicker { font: 600 12px/1.2 system-ui, sans-serif; letter-spacing: .06em; text-transform: uppercase;
  color: var(--muted); margin-bottom: 6px; }
.badge { display:inline-block; font: 700 13px/1 system-ui, sans-serif; padding: 5px 9px; border-radius: 4px;
  color:#fff; vertical-align: middle; margin-left: 8px; }
.pass { background: var(--pass); } .fail { background: var(--fail); } .na { background: var(--na); }
figure { margin: 14px 0 6px; } figure svg { width: 100%; height: auto; display: block; }
figcaption { font: 13px/1.45 system-ui, sans-serif; color: var(--muted); margin-top: 6px; }
.pair { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.pair figure { margin: 10px 0 0; } .pair .lbl { font: 700 14px system-ui, sans-serif; }
@media (max-width: 640px) { .pair { grid-template-columns: 1fr; } }
dl { margin: 14px 0 0; } dt { font: 700 14px/1.3 system-ui, sans-serif; margin-top: 14px; color: var(--navy); }
dd { margin: 4px 0 0; }
table { width: 100%; border-collapse: collapse; font: 14px/1.4 system-ui, sans-serif; margin-top: 6px; }
th, td { text-align: left; border-top: 1px solid var(--line); padding: 7px 6px; vertical-align: top; }
th { width: 38%; font-weight: 600; }
.mark { margin-top: 18px; padding: 12px; border: 2px dashed var(--line); border-radius: 6px;
  font: 15px/1.6 system-ui, sans-serif; }
.mark .boxes span { margin-right: 26px; white-space: nowrap; }
.mark .line { border-bottom: 1px solid #9c968a; height: 28px; margin-top: 4px; }
.note { font-size: 14px; color: var(--muted); }
.key { font: 14px/1.5 system-ui, sans-serif; }
.key li { margin: 3px 0; }
.toc { columns: 2; font: 14px/1.7 system-ui, sans-serif; padding-left: 18px; }
@media (max-width: 640px) { .toc { columns: 1; } }
a { color: var(--navy); }
text { font-family: 'Kalam', 'Patrick Hand', 'Comic Sans MS', 'Segoe Print', cursive; }
.zonelbl { font-size: 8.5px; fill: #5a554c; } .axis { font-size: 11px; fill: #5a554c; font-weight: 700; }
.courtlines path, .courtlines line { fill: none; stroke: #1f2a44; stroke-width: 2.6; stroke-linecap: round; }
.num { font-size: 16px; font-weight: 700; fill: #1d1b18; } .xnum { font-size: 11px; fill: #c0392b; }
.halo { fill: none; stroke: none; }
.evidence { margin-top: 18px; border-top: 2px solid var(--line); padding-top: 12px; }
.evres { font-size: 16px; } table.ev th { width: auto; } table.ev td { font-size: 13.5px; }
.facts { font: 14.5px/1.5 system-ui, sans-serif; padding-left: 20px; } .facts li { margin: 5px 0; }
@media print { body { background: #fff; } .card { page-break-before: always; border: none; margin: 0; }
  .card.first { page-break-before: auto; } }
"""

INTRO = """
<p class="lede">The exam boards for step 12, one page each: the 17 exam boards, two candidate boards from the playtests,
and two trainer tests that Contest as an action changed. Mark each page keep, fix (with a note) or drop.</p>
<div class="card first">
<div class="kicker">How to read the pages</div>
<ul class="key">
<li><b>The court</b> is the printed board: the rim is at the bottom, columns A to Q run left to right, rows 1 to 14
run up from the baseline. Left and right mean left and right as you look at the picture. The faint squares around
the rim are the distance rings.</li>
<li><b>O1 to O5</b> are the offence (black circles). The player with the ball has a double circle and the ball.</li>
<li><b>X1 to X5</b> are the defence (red crosses). The small arrowhead on each X shows which way he faces.</li>
<li>A small <b>M</b> or <b>Q</b> tag under a player means he has used his Move or Quick Step this phase. <b>LOCK</b>
marks a locked player.</li>
<li>Arrows drawn on the court show the move or pass the page is about, numbered in order.</li>
<li><b>Today's result</b> is the All-Star in the step 6 run, on the clock with its full time, under the 9 November
rules: Contest is an action (D-18), a turnover never scores more than the total banked before it (D-82), and every
steal foul is +5 (D-89). These three apply to every board. The step 7 change (a steal foul on a shooter gives free
throws only) came after that run; step 7 re-ran only the three marked tests (board 6 and the two trainer tests).</li>
<li><b>Four moves ahead</b> means the All-Star searching a fixed four moves ahead with no time limit. That run was
before 9 November, so today it is "not measured under the current rules". Its result before is given.</li>
<li><b>Phone speed</b> is the run before 9 November at a quarter of the time budget, for all three levels.</li>
</ul>
</div>
"""


EVIDENCE_PATH = os.path.join(RUNS, 'step9', 'exam_evidence.json')
EV_KEY = {'b2': '2', 'b3': '3', 'b4': '4', 'b5': '5', 'b6': '6', 'b7': '7', 'b8': '8', 'b11': '11', 'b13': '13',
          'b14': '14', 'b16': '16', 'd112': 'T1', 'd113': 'T2', 'd108': 'C1', 'd109': 'C2'}
RESULT_WORDS = {'met': 'Met', 'speed': 'Speed', 'valuation or board': 'Valuation or board',
                'no accepted move': 'No move can meet the judge', 'not measured': 'Not measured'}


def pts(v):
    return '' if v is None else f'{v:.1f}'


def say(turn):
    """A turn stored as action strings, in plain words."""
    if not turn:
        return ''
    return plain.cap(plain.turn_str(turn.split('; ')))


def look_label(r, clock_depth):
    d = r['depth']
    lab = f'{d} move{"s" if d > 1 else ""} ahead'
    return lab + (' (as on the clock)' if d == clock_depth else '')


def values_table(sub, side):
    """The values table for one copy of a board: the computer's choice against the best accepted move, per look."""
    cd = sub['clock']['depth']
    rows = ['<table class="ev"><tr><th>Looking</th><th>The computer\'s choice</th><th>Best move the board accepts</th>'
            '<th>Gap</th></tr>']
    for r in sub['rows']:
        gap = r['gap']
        gtxt = '' if gap is None else ('level' if abs(gap) < 0.05 else
                                       (f'choice ahead by {gap:.1f}' if gap > 0 else f'accepted move ahead by {-gap:.1f}'))
        ch = say(r['choice']) + (' (the board accepts it)' if r['choice_accepted'] else '')
        rows.append(f"<tr><td>{esc(look_label(r, cd))}</td><td>{esc(ch)}: <b>{pts(r['choice_value'])}</b></td>"
                    f"<td>{esc(say(r['best_accepted']))}: <b>{pts(r['best_accepted_value'])}</b></td><td>{esc(gtxt)}</td></tr>")
    if sub.get('capped'):
        rows.append(f"<tr><td>{sub['capped']} moves ahead</td><td colspan=\"3\">Not finished within the board\'s 10 minutes "
                    f"(the deepest complete look: {max([r['depth'] for r in sub['rows']] or [sub.get('reached_in_cap') or 1])} "
                    f"moves ahead).</td></tr>")
    rows.append('</table>')
    who = 'the offence' if side == 'O' else 'the defence'
    ck = sub['clock']
    played = (f"On the clock (the All-Star's 2.5 seconds, as in the step 6 run) it looked {ck['depth']} move ahead"
              + (' and part of the next' if ck.get('partial') else '') + f" and played: {say(ck['choice'])}"
              + (' (the board accepts it). ' if ck['accepted'] else ' (the board doesn\'t accept it). '))
    note = (played + f"Values are the game's own points for the possession, from the offence's side (higher is better "
            f"for the offence; {who} is choosing). {sub['n_accepted']:,} of the {sub['n_turns']:,} legal turns meet the "
            f"judge.")
    return '\n'.join(rows) + f'<p class="note">{esc(note)}</p>'


def evidence_html(p, ev, words):
    k = EV_KEY.get(p['key'])
    if not k or k not in ev:
        return ''
    e, w = ev[k], words.get(k, {})
    out = ['<div class="evidence"><div class="kicker">Evidence (step 9)</div>']
    res = w.get('result') or ''
    out.append(f'<p class="evres"><b>{esc(w.get("verdict", ""))}</b> {esc(res)}</p>')
    subs = e.get('subs') or ({'': e['evidence']} if 'evidence' in e else {})
    labels = p.get('labels') or {}
    for name, sub in subs.items():
        if not sub.get('rows'):
            continue
        if len(subs) > 1:
            out.append(f'<div class="lbl">{esc(labels.get(name, name))}</div>')
        out.append(values_table(sub, sub['side']))
    for extra in w.get('tables', []):
        out.append(extra)
    if k == '14':
        rows = ['<table class="ev"><tr><th>Looking</th><th>First moves, best first</th><th>Gap, first to second</th></tr>']
        for r in e['rows']:
            fm = '; '.join(f'{say(t)}: {v:.1f}' for t, v in r['first_moves'][:4])
            rows.append(f"<tr><td>{r['depth']} move{'s' if r['depth'] > 1 else ''} ahead</td><td>{esc(fm)}</td>"
                        f"<td>{r['gap']:.1f}</td></tr>")
        if e.get('capped'):
            rows.append(f"<tr><td>{e['capped']} moves ahead</td><td colspan=\"2\">Not finished within the 10 minutes.</td></tr>")
        out.append('\n'.join(rows) + '</table>')
    if k == '16':
        rows = ['<table class="ev"><tr><th>Along the computer\'s line</th><th>Possession</th><th>X2 has his Move</th>'
                '<th>X2 has his Quick Step</th></tr>']
        for r in e['line']:
            yes = lambda b: '' if b is None else ('yes' if b else 'no')
            rows.append(f"<tr><td>{esc(say(r['turn']) if r['turn'] else 'At the start')}</td><td>{pts(r['value'])}</td>"
                        f"<td>{yes(r['x2_move_left'])}</td><td>{yes(r['x2_qs_left'])}</td></tr>")
        out.append('\n'.join(rows) + '</table>')
    if k == 'T1':
        rows = ['<table class="ev"><tr><th>Order</th><th>With the test\'s table (step 3m)</th><th>With today\'s table</th></tr>']
        t3, td = e['tables']['step 3m table (as the test runs)']['orders'], e['tables']['today']['orders']
        for name in t3:
            rows.append(f'<tr><td>{esc(name)}</td><td>{pts(t3[name])}</td><td>{pts(td[name])}</td></tr>')
        out.append('\n'.join(rows) + '</table>')
    if w.get('facts'):
        out.append('<ul class="facts">' + ''.join(f'<li>{esc(f)}</li>' for f in w['facts']) + '</ul>')
    out.append('</div>')
    return '\n'.join(out)


def page_html(p, svgs, data, fixed, timed, board1, today, ev=None, ewords=None):
    v, verdict_note = today_cell(p, today)
    cls = {'Pass': 'pass', 'Fail': 'fail'}.get(v, 'na')
    short = 'Not measured' if v.startswith('Not measured') else v
    kind = ('Candidate board' if p.get('candidate') else 'Trainer test' if p.get('trainer') else 'Exam board')
    head = f"{kind} {p['n']}" if not p.get('candidate') and not p.get('trainer') else kind
    also = f" · {p['also']}" if p.get('also') else ''
    out = [f'<section class="card" id="{p["key"]}">',
           f'<div class="kicker">{esc(head)}{esc(also)}</div>',
           f'<h2>{esc(p["title"])}<span class="badge {cls}">{esc(short)}</span></h2>']
    bs = data[p['key']]['boards']
    pics = svgs[p['key']]
    if not bs:
        out.append('<p class="note">No picture: this check has no board of its own.</p>')
    else:
        many = len(bs) > 1
        if many:
            out.append('<div class="pair">')
        for b, svg in zip(bs, pics):
            lbl = (p.get('labels') or {}).get(b['label'], '')
            out.append('<figure>' + (f'<div class="lbl">{esc(lbl)}</div>' if lbl else '') + svg
                       + f'<figcaption>{esc(caption(b, p, b["label"]))}</figcaption></figure>')
        if many:
            out.append('</div>')
    out.append('<dl>')
    out.append(f'<dt>The situation</dt><dd>{esc(p["situation"])}</dd>')
    out.append(f'<dt>What the computer should do</dt><dd>{esc(p["expect"])}</dd>')
    out.append(f'<dt>The basketball reason</dt><dd>{esc(p["why"])}</dd>')
    out.append(f'<dt>How it is judged</dt><dd>{esc(p["judged"])}</dd>')
    out.append('<dt>Today\'s result</dt><dd><table>')
    first = 'Today\'s rules' if p.get('trainer') else 'On the clock, today\'s rules (All-Star)'
    out.append(f'<tr><th>{first}</th><td><b>{esc(v)}.</b> {esc(verdict_note)}</td></tr>')
    for label, val, txt in earlier(p, fixed, timed, board1):
        out.append(f'<tr><th>{esc(label)}</th><td>{("<b>" + esc(val) + ".</b> ") if val else ""}{esc(txt)}</td></tr>')
    instead = p['instead'] or ('Nothing: it did what the board asks.' if v == 'Pass' else 'Not measured.')
    out.append(f'<tr><th>What the computer chose instead</th><td>{esc(instead)}</td></tr>')
    out.append(f'<tr><th>Rulings that changed the board</th><td>{esc(p["rulings"])}</td></tr>')
    out.append('</table></dd>')
    if p.get('note'):
        out.append(f'<dt>Worth knowing</dt><dd class="note">{esc(p["note"])}</dd>')
    out.append('</dl>')
    if ev:
        out.append(evidence_html(p, ev, ewords or {}))
    out.append('<div class="mark"><b>Shaun\'s mark:</b> <span class="boxes"><span>&#9744; Keep</span>'
               '<span>&#9744; Fix</span><span>&#9744; Drop</span></span><div>Note:</div><div class="line"></div>'
               '<div class="line"></div></div>')
    out.append('</section>')
    return '\n'.join(out), v


def main():
    data = boards()
    svgs = draw(data)
    fixed, timed, board1, today = results()
    ev = json.load(open(EVIDENCE_PATH)) if os.path.exists(EVIDENCE_PATH) else None
    from exam_book_words import EVIDENCE_WORDS
    body, index = [], []
    for p in PAGES:
        h, v = page_html(p, svgs, data, fixed, timed, board1, today, ev, EVIDENCE_WORDS)
        body.append(h)
        index.append((p, 'not measured under the current rules' if v.startswith('Not measured') else v))
    toc = '<ol class="toc" style="list-style:none">' + ''.join(
        f'<li><a href="#{p["key"]}">{esc(p["n"])}. {esc(p["title"])}</a>{(" (" + esc(p["also"]) + ")") if p.get("also") else ""}: {esc(v.lower())}</li>'
        for p, v in index) + '</ol>'
    doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
           '<meta name="viewport" content="width=device-width, initial-scale=1">'
           f'<title>Playmaker Exam Book</title><style>{CSS}</style></head><body><main>'
           '<h1>Playmaker exam book</h1>' + INTRO
           + '<div class="card"><div class="kicker">The boards</div>' + toc + '</div>'
           + '\n'.join(body) + '</main></body></html>')
    # the banned-terms check, on the words only (the pictures carry square and zone labels)
    words = '\n'.join([INTRO] + [' '.join(str(p.get(k, '')) for k in
                                          ('title', 'situation', 'expect', 'why', 'judged', 'instead', 'rulings',
                                           'note', 'today_note')) for p in PAGES]
                      + [' '.join([w.get('verdict', ''), w.get('result', ''), w.get('index', '')] + list(w.get('facts', [])))
                         for w in EVIDENCE_WORDS.values()])
    # and the plain words the values tables print
    if ev:
        words += '\n' + '\n'.join(say(r[k]) for e in ev.values() for sub in (e.get('subs') or
                                    ({'': e['evidence']} if 'evidence' in e else {})).values()
                                    for r in sub.get('rows', []) for k in ('choice', 'best_accepted') if r.get(k))
    hits = plain.check(words)
    if hits:
        raise SystemExit(f'banned terms in the exam book: {hits}')
    for ext in ('src=', 'href="http', "url('http", '@import', '<link'):
        assert ext not in doc, ext
    open(OUT_HTML, 'w').write(doc)

    lines = ['# Exam book: the boards', '',
             'Tick each board first; the pages are in `EXAM_BOOK.html`. "Today" is the All-Star on the clock under the 9 '
             'November rules (the step 6 run; step 7 for board 6 and the two trainer tests).', '']
    for p, v in index:
        tag = f" ({p['also']})" if p.get('also') else ''
        status = v if v.startswith('not measured') else f'{v.lower()} today'
        if v.startswith('not measured') and ev and EV_KEY.get(p['key']) in ev:
            status = 'first measured in step 9'
        k = EV_KEY.get(p['key'])
        if ev and k in (ev or {}):
            status += f"; evidence: {EVIDENCE_WORDS.get(k, {}).get('index', '')}"
        lines.append(f"- [ ] {p['n']}. {p['title']}{tag}: {status}. Keep / fix / drop:")
    open(OUT_MD, 'w').write('\n'.join(lines) + '\n')
    print(f'wrote {OUT_HTML} ({len(doc) // 1024} KB) and {OUT_MD}')


if __name__ == '__main__':
    main()
