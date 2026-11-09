"""Step 9: the evidence in plain words, one entry per board, for tools/exam_book.py. The numbers come from
docs/runs/step9/exam_evidence.json (the searches) and its supplement (cheap board reads). Points are the game's own
scale for a possession: an open three by a shooter rated 13 is worth 39.

verdict: the result word; result: the one-line finding; facts: what a basketball person needs; index: the tick-list line.
"""

EVIDENCE_WORDS = {
    '2': dict(
        verdict='Level, and on the clock it now depends on timing.',
        result='Looking 4 moves ahead, the computer\'s choice and the best move the board accepts are level on both '
               'copies (18.7). In this run\'s clock decisions the pair met the board; in the step 6 run it didn\'t.',
        facts=[
            'O2\'s three is rated 4 on board A (a poor shooter) and 12 on board B (a good one). X2\'s contest on a three '
            'is 3.',
            'On the clock in this run: against the poor shooter X2 went to D6, 5 squares from the rim; against the good '
            'shooter he stayed at C7, 6 from the rim, next to O2. That pair meets the board (closer to the rim against '
            'the poor shooter, and still able to Contest the good one). In the step 6 run he went to D6 and D7, both 5 '
            'from the rim, which fails. The choice on the clock moves with timing.',
            'Under Contest as an action, X2 can sag as far as F3, 3 squares from the rim and 4 from O2, and still close '
            'out with one movement and a Contest. So sagging costs him almost nothing on either board.',
            'On both boards the computer\'s first concern is X1\'s Steal on O1 at the top, not X2.',
            'The two copies are judged against each other. Each copy\'s accepted moves were judged against the '
            'computer\'s own clock choice on the other copy at the start of the run: on board A, X2 had to end closer '
            'than 5 squares from the rim.',
            '5 moves ahead did not finish within each copy\'s half of the 10 minutes.',
        ],
        index='level at 4 moves ahead; met on this run\'s clock, failed in step 6 (timing); X2 can sag to 3 from the rim and still Contest'),
    '3': dict(
        verdict='Valuation or board.',
        result='The search\'s best answer is X1 recovering in front of O1 with his Quick Step (and a Steal). It holds '
               'the possession to 21.5, against 24.9 for the best answer the board accepts one move ahead, 33.2 at 4 '
               'and 39 at 5. The gap grows the further it looks.',
        facts=[
            'Where he stands, O1\'s best look is a drive to the rim, worth 22.',
            'X1, though beaten, can still quick-step back beside O1 (to J6): O1\'s best look stays at 22.',
            'X4, the low man, is the only other defender who can get next to O1 in one move (to I4). If he does, O1\'s '
            'best look rises to 31: leaving the basket area opens more than it stops.',
            'X2, X3 and X5 can\'t reach O1 in one move.',
            'On the clock the computer played X2 to C6 and X5 to N3. Its plan-keeping chose that over the search\'s '
            'best; it reads the same as the best accepted answer at every look (24.9, 33.2, 39).',
            '35,844 of 553,183 legal turns meet the judge (a helper ends next to O1 and another defender moves).',
            '6 moves ahead did not finish within the 10 minutes (5 did).',
        ],
        index='valuation or board: X1 recovering is better for the defence than the low man helping (O1 22 v 31)'),
    '4': dict(
        verdict='No move can meet the judge.',
        result='Half of the judge is the computer\'s own reading of the board: it must see X5 as the only answer to both '
               'O1 and O5. It doesn\'t, on any move, because X5 isn\'t stretched under today\'s rules. The table below '
               'measures the other half (the offence attacks): the swing to O2 is level with the best attack at 1 and 5 '
               'moves ahead, and 4.5 ahead at 4.',
        facts=[
            'The pass to O5 is not legal: X5 stands next to O5 on the passing line and denies it. The pass to O4 is '
            'denied by X4 the same way.',
            'O5\'s best look is a cut to the rim, but the pass arrives only half the time: worth 9.',
            'O1\'s pull-up from where he stands (a mid-range or a floater) reads 24.9 one move ahead, then 8 and 6 at '
            '4 and 5 moves ahead, once the defence\'s Contest is played out.',
            'O1\'s best look is stepping out to F10 for a three, worth 24.',
            'The swing the computer chose (O2 lifts to D9, O1 passes to him) is worth 25.5 at 1, 4 and 5 moves ahead.',
            'So X5 can deny O5 and still help on O1: the computer finds no overloaded defender anywhere on this board.',
            '17,825 of 34,407 legal turns meet the attacking half (a shot, a pass to O5, or O1 moving or dribbling).',
        ],
        index='no move can meet it: the computer doesn\'t see X5 as stretched (the pass to O5 is denied; the pull-up is worth 8)'),
    '5': dict(
        verdict='Board A met; board B: valuation or board.',
        result='Board A passes as judged (the sprint up the wing counts as a drive). On board B the computer still rates '
               'the sprint to B8 at 39 against 30 for the three where he stands, 9 points ahead at 4 and 5 moves ahead.',
        facts=[
            'O2 is a sharpshooter: his three is rated 13. X2\'s contest on a three is 3.',
            'Board B: X2 has used his Move and his Quick Step and cannot Contest O2 where he stands. But X4 can close '
            'out from the corner in the reaction and Contest the three where O2 stands, so it is worth 30, not the 39 '
            'of an open look.',
            'One square up the wing, at B8, nobody can reach O2 in time: that three is fully open, worth 39. That is '
            'the sprint the computer chose on both boards.',
            'Board A: X2 is next to O2 and can Contest him (30 where he stands). The best move toward the rim, one '
            'square in to C8, is worth 39 one move ahead, level with the sprint; a dribble past X2 is worth 25.5. The '
            'judge counts any movement by O2 as the drive, so board A is met.',
            'On board B the only move the judge accepts is the shot itself (1 of 28,927 legal turns).',
            '6 moves ahead did not finish within the board\'s 10 minutes (5 did).',
        ],
        index='A met; B valuation or board: one step up the wing is an open three (39) against 30 where he stands'),
    '6': dict(
        verdict='Speed, narrowly.',
        result='The computer\'s choice and O4\'s own moves are level at 1 and 4 moves ahead (33 and 39). At 5 moves '
               'ahead O4\'s quick step into the corner edges ahead by 0.2.',
        facts=[
            'O4\'s corner three is rated 11. Nobody can Contest it where he stands: the open three is worth 33.',
            'The phase table (what a possession still alive in phase 1 is worth on average) says 24.9. The open '
            'three beats it by 8.',
            'The screen the computer chose (O2 to A5, then the screen) is worth 33 at 4 and 5 moves ahead: it adds '
            'nothing over the open three. One move ahead it reads only 25.5; the computer took it from part of a '
            'deeper look on the clock.',
            'On the clock the choice and the board\'s moves are level, so the board fails on how the computer breaks '
            'a tie, not on a clear preference.',
            'An earlier run of this board, which by mistake ran past the cap, reached 6 moves ahead: there the '
            'computer\'s choice was 5.9 ahead of the best accepted move it searched. So the "speed" reading is '
            'fragile.',
            '6,028 of 31,744 legal turns meet the judge (any first move by O4).',
        ],
        index='speed, narrowly: level at 1 and 4 moves ahead, accepted move 0.2 ahead at 5 (fragile)'),
    '7': dict(
        verdict='Board A met; board B: valuation or board.',
        result='Early (board A) the computer doesn\'t shoot, as asked. In the last phase (board B) it rates keeping the '
               'ball at 29.5 and the contested mid-range at 10, 19.5 points apart at 4 moves ahead.',
        facts=[
            'Board B: the clock shows 2, the last phase, but each side still has 6 tokens: up to three offence turns '
            'of two actions before time runs out.',
            'The phase table says a possession still alive at the start of the last phase is worth 29.3 on average. '
            'The computer sees that much still to play for.',
            'One move ahead, the mid-range shot and keeping the ball are almost level (29.3 against 29.5). At 4 moves '
            'ahead, with the defence\'s Contest played out, the shot is worth 10.',
            'Only 2 of 34,790 legal turns meet the judge on board B: the mid-range and the floater, first.',
            '5 moves ahead did not finish on board B within its half of the 10 minutes.',
        ],
        index='A met; B valuation or board: the last phase still holds three turns; the contested two is worth 10 against 29.5'),
    '8': dict(
        verdict='Valuation or board.',
        result='The computer\'s choice stays ahead: by 5.1 at 4 moves ahead and by 0.3 at 5. One move ahead everything '
               'is level at 24.9.',
        facts=[
            'The backdoor pass arrives half the time: X1 and X2 can each step into its path. In the app a stolen pass '
            'ends the possession at 0.',
            'O2\'s cut alone is worth 24.9 (the same as standing still). The cut with the pass in the same turn is '
            'worth 12.5: half the time the pass is lost.',
            '2,688 of 32,067 legal turns meet the judge (O2 ends at least 2 squares closer to the rim).',
            'Many moves read exactly 24.9 one move ahead: that is the phase table, which sets the floor of the '
            'computer\'s reading (D-92).',
        ],
        index='valuation or board: the backdoor pass arrives only half the time (X1 or X2 can step in)'),
    '11': dict(
        verdict='Board A met; board B: valuation or board.',
        result='The pass to O2 the board is about is not legal: X2 stands next to O2 on the passing line and denies it. '
               'In the last phase the computer keeps the ball (30) over either corner pass (29.5 at 4 moves ahead).',
        facts=[
            'X2 is next to O2 on the line from O1, so the rules deny that pass outright. X3 denies the pass to O3 the '
            'same way. Only the corner passes, to O4 and O5, are legal.',
            'Each corner pass arrives half the time. One move ahead each is worth about 15 against 31 for keeping '
            'the ball; at 4 moves ahead the gap is 0.5.',
            'Board B: the clock shows 2, the last phase, but the offence still has 6 tokens: up to three turns. The '
            'phase table says that is worth 29.5 on average.',
            'Board A is met because no pass to O2 is possible at all.',
            '5 moves ahead did not finish within each board\'s half of the 10 minutes.',
        ],
        index='A met (the pass to O2 is not legal); B valuation or board: keep the ball 30 v a corner pass 29.5'),
    '13': dict(
        verdict='Level.',
        result='Every move the computer weighs, and every move the board accepts, reads 24.9 at 1, 4 and 5 moves '
               'ahead. Neither side of the board is preferred; the choice falls to how the computer breaks a tie.',
        facts=[
            'O1\'s straight drive is worth 8 with O5 in the lane, and still 8 with O5 cleared to any of 20 squares. '
            'His best other option is worth 15.',
            'The move the computer chose (O3 to N5) changes nothing: 24.9 before and after.',
            '24.9 is the phase table for phase 1, the floor of the computer\'s reading (D-92). Nothing on this board '
            'lifts the reading above it.',
            '7,695 of 32,181 legal turns meet the judge.',
        ],
        index='level: every move reads 24.9 (the phase-table floor); clearing O5 doesn\'t improve the drive (8)'),
    '14': dict(
        verdict='Valuation or board.',
        result='On the clock every first move is level (24.9). Looking further, one move, O1 to K10, is clearly best: '
               'by 4.8 at 4 moves ahead and 2.2 at 5, more than the 2-point margin inside which the All-Star varies.',
        facts=[
            'The All-Star chooses at random among turns within 2 points of its best, after a small random spread '
            '(0.5). So a gap above 2 means the same first move nearly every time.',
            'At 4 and 5 moves ahead, O1 to K10 leads; every other first move reads 24.9.',
            'On the clock (one move ahead) all first moves are level, which is where the variety in the step 6 run '
            'came from (4 different first moves, the most common 80%).',
            '6 moves ahead did not finish within the 10 minutes (5 did).',
        ],
        index='valuation or board: deeper looks make O1 to K10 best by 2.2 to 4.8, above the 2-point variety margin'),
    '16': dict(
        verdict='Valuation or board.',
        result='The computer\'s first turn stays ahead of every first turn the board accepts: level one move ahead, '
               'then by 5.1 at 4 moves ahead.',
        facts=[
            'Along the computer\'s own line the possession reads 24.9 after every turn: it never rises.',
            'Turn 1 (O1 to J10, O3 sprints to I9): X2 still has his Move and Quick Step; O2\'s best look is 30.',
            'Turn 2 (O2 sprints to A7): X2 has now used both, but O2 has moved to where he has no look (0).',
            'Turn 3 (O4 moves to A3): still 24.9.',
            'With X2\'s Move and Quick Step spent and O2 back on the wing, O2\'s catch is worth 39 (30 while X2 can '
            'still answer). The line wears X2 out but never gets O2 that shot.',
            'Only 9 of 141 single moves away from the ball show the trainer\'s wearing-out effect over the phase, all '
            'small (under 0.8). The judge\'s first-turn part accepts turns that start with one of them: 1,586 turns.',
            '5 moves ahead did not finish within the 10 minutes (the trainer\'s readings took half of it).',
        ],
        index='valuation or board: the line wears X2 out but moves O2 away; the possession stays at 24.9'),
    'T1': dict(
        verdict='Fails: the order makes almost no difference.',
        result='With the phase table the test uses (step 3m), playing the drive first is worth 0.75 more than the cut '
               'first, against the bar of 3. With today\'s table every order reads 24.9: no difference at all.',
        facts=[
            'Cut first, then the drive (as played): 24.2 with the test\'s table; 24.9 today.',
            'Drive first, then the cut: 24.9 with the test\'s table; 24.9 today.',
            'Both in one turn, either order: 23.1 with the test\'s table; 24.9 today.',
            'The trainer does find that the defence covered the cut before the drive came, as the board intends.',
            'The test keeps the step 3m table on purpose, because today\'s higher table flattens the reading (D-92).',
        ],
        index='fails: the better order is worth 0.75 (bar 3) with the test\'s table, 0 with today\'s'),
    'T2': dict(
        verdict='Fails: the review names X1, and today X1 is the one who answers.',
        result='With the lift, the defence\'s best reply moves X1 off the ball toward O2 (F10) and slides X3 into the '
               'middle (J8). Putting X1 back takes back 6 of the teammates\' 27-point gain; putting X3 back takes '
               'back none. So the review names X1.',
        facts=[
            'Without the lift, the defence stays home: X1 at I10, X3 at N8.',
            'With the lift: X1 goes to F10 facing west (toward O2); X3 comes from N8 to J8 facing west.',
            'X2, X4 and X5 do the same with or without the lift.',
            'The lift is worth 8.3 over the phase (33.2 with it, 24.9 without), well above the bar for a review note.',
            'The test expected X3 because, before the 9 November rules, X3 was the one who left the far side.',
        ],
        index='fails: today X1 answers the lift (X3 rotates behind him); the review names X1'),
    'C1': dict(
        verdict='Met.',
        result='On the clock the All-Star defence sprints X1 to H11 and moves X3 to N8 facing north: the pass from the '
               'ball to O2 is covered, and so is a second pass to him.',
        facts=[
            'O2\'s three is rated 13; X2\'s contest on a three is 3. Where O2 stands, his catch is worth 30.',
            'Most defensive turns meet this judge: 796,931 of 1,201,980 legal turns (every move comes with a choice '
            'of 8 facings).',
            'Judging all 1.2 million turns took 11.8 minutes, because this judge reads every passing lane, so the '
            'board ran to 12.5 minutes, over its 10-minute cap. The deeper looks had the last 30 seconds: 4 moves '
            'ahead did not finish, and 3,406 of the accepted turns were valued one move ahead.',
        ],
        index='met: X1 and X3 cover the passes to O2'),
    'C2': dict(
        verdict='Met, but the board doesn\'t test what it was built for.',
        result='The All-Star moves O1 to C9 and throws neither pass. But today the "clean" pass to O2 is no cleaner '
               'than the pass to O4: each arrives 40% of the time.',
        facts=[
            'Both passes read the same at 4 and 5 moves ahead (28.0 each). One move ahead the pass to O4 is slightly '
            'ahead (26.6 against 26.2).',
            'The board\'s second test (the clean pass rated above the contested one) does not hold under today\'s rules.',
            'O1\'s move to C9 is worth 36 at 1, 4 and 5 moves ahead: more than either pass.',
        ],
        index='met, but the clean pass is no longer clean (both arrive 40%)'),
}
