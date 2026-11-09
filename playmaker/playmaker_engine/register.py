"""Step 3n Part K: the shared rules register. Every rule value and mechanism, marked Shared (both formats), Digital
only or Tabletop only, with the reason; docs/rules_register.md is written from it (python3 -m playmaker_engine.register)
and tests/test_step3n.py asserts that every Shared entry has identical values in both formats.

A setting is read from rules_config.Rules (rules=...), a constant from rules_config (const=...), or it is a mechanism
the engine applies by format (how=...).
"""
from dataclasses import fields

from . import rules_config as RC

SHARED, DIGITAL, TABLETOP, SPLIT = 'Shared', 'Digital only', 'Tabletop only', 'Split by format'

# (name, status, source, what it is, reason for a split / note)
ENTRIES = [
    # ---- the format itself and what differs on purpose
    ('digital', SPLIT, dict(rules='digital'), 'The match format switch.', 'The two formats themselves.'),
    ('Turnover cost', SPLIT, dict(rules='turnover_cost'), 'A successful Intercept or Steal (and a steal of a declared shot).',
     'Tabletop: -5 and the shot clock loses a phase, play on (the setting). Digital, whatever the setting: the possession ends and scores 0, '
     'because a digital match is several possessions a side and the next possession is the cost.'),
    ('Shot-clock expiry', SPLIT, dict(how='expiry'), 'The clock reaches 0.',
     'Tabletop: -5 and a forced shot. Digital: a turnover, the possession scores 0 (as in basketball).'),
    ('Match length', SPLIT, dict(how='match'), 'Possessions a side.',
     'Tabletop: one possession each. Digital: 4, 8 or 12 a side (per_side), sides alternating.'),
    ('Tied match', SPLIT, dict(how='tie'), 'What settles a tied match.',
     'Tabletop: each player rolls for their final shot. Digital: the match stays a tie. Found in the code, not approved.'),
    ('Steal-foul bonus', SPLIT, dict(how='bonus'), 'When a steal foul gives free throws.',
     'Tabletop: the first steal foul of the possession is +5 and play on, the second gives free throws (one '
     'possession is the whole game). Digital (step 3n F3): team fouls run across a quarter; from the 5th a steal foul '
     'gives free throws and ends the possession.'),
    ('quarter_possessions', DIGITAL, dict(rules='quarter_possessions'), 'Possessions a side in a quarter (18).',
     'Team fouls across matches need a running quarter; the table plays one possession.'),
    ('bonus_from', DIGITAL, dict(rules='bonus_from'), 'The team foul that starts the bonus (5th).', 'As above.'),
    ('Team fouls carried across matches', DIGITAL, dict(how='pairing'), 'Stored with the pairing record.',
     'The table has no record between games.'),
    ('Decision timer', DIGITAL, dict(how='timer'), 'Optional per-player thinking clock (step 3c).',
     'An app feature; at the table players agree their own pace.'),
    ('Computer opponents and the trainer', DIGITAL, dict(how='engine'), 'Levels, grading, ratings.', 'App features.'),
    # ---- constants (shared)
    ('Board 17 x 14, rim I2', SHARED, dict(const=('BOARD_COLS', 'BOARD_ROWS', 'RIM')), 'The court.', ''),
    ('Tokens per phase (6 a side)', SHARED, dict(const=('TOKENS_PER_PHASE',)), '', ''),
    ('Phase length (2 seconds), start clock 12', SHARED, dict(const=('PHASE_SECONDS', 'START_CLOCK')), '', ''),
    ('d20 rolls', SHARED, dict(const=('DIE',)), 'Every roll: d20 at or under the target.', ''),
    ('Far-contest -3', SHARED, dict(const=('FAR_CONTEST_PENALTY',)), 'Contester further from the rim than the shooter.', ''),
    ('Turnover points (-5)', SHARED, dict(const=('TURNOVER_POINTS',)), 'The value of a turnover where one is scored.',
     'The number is shared; when it applies is the turnover-cost split above.'),
    ('Steal foul +5', SHARED, dict(const=('STEAL_FOUL_BONUS',)), 'A steal foul before the bonus.', ''),
    ('Free-throw multipliers (x2, x3)', SHARED, dict(const=('FT_MULT_TWO', 'FT_MULT_THREE')), '', ''),
    ('Two actions a turn', SHARED, dict(const=('MAX_ACTIONS_PER_TURN',)), '', ''),
    ('Move shape (3 straight, 2 diagonal)', SHARED, dict(const=('MOVE_STRAIGHT', 'MOVE_DIAGONAL')), '', ''),
    ('Inbound phases (2)', SHARED, dict(const=('INBOUND_PHASES',)), '', ''),
    ('Per-phase limits', SHARED, dict(const=('LIMITS',)), 'Quick Steps, passes, screens, dribbles, waits, shots; '
     'intercepts, challenges, steals.', ''),
    ('Turn-ending actions', SHARED, dict(const=('TURN_ENDERS',)), '', ''),
    ('Zones and shot types', SHARED, dict(const=('ZONE_SHOTS', 'ZONE_POINTS')), '', ''),
    ('Look bands and Coach\'s Call bonus', SHARED, dict(const=('BANDS', 'COACH_BONUS', 'SCENARIO_GOAL')), '', ''),
    ('Playing levels (ages, standards, growth tags)', SHARED, dict(how='levels'),
     'Step 3l: the ratings by age and standard, junior growth tags.', 'Ratings carry age; both formats use the same cards.'),
    ('Lock tokens (8)', SHARED, dict(how='tokens'), 'Grey tokens that mark a locked player.', ''),
    ('Setup placement', SHARED, dict(how='setup'), 'Where the pieces start.', ''),
    ('Phase reset', SHARED, dict(how='reset'), 'What the reset does between phases.', ''),
    ('Dribble', SHARED, dict(how='dribble'), 'Taking on a defender.', ''),
    ('Intercept roll', SHARED, dict(how='intercept'), 'The roll and a missed Intercept.', ''),
    ('Hold for One cards', SHARED, dict(how='scenario'), 'Scenario cards that hold for the last shot.', ''),
    ('Late Clock results', SHARED, dict(how='scenario'), 'How Late Clock cards are compared.', ''),
    ('Tie-break roll', TABLETOP, dict(how='tiebreak'), 'A tied two-possession game.',
     'The app has no tie-break: see Tied match.'),
]
# every Rules setting not named above is shared: the same ruling in both formats
_NAMED = {e[2].get('rules') for e in ENTRIES if e[2].get('rules')}
for f in fields(RC.Rules):
    if f.name not in _NAMED:
        ENTRIES.append((f.name, SHARED, dict(rules=f.name), '', ''))

# tokens and markers the table needs for shared mechanisms with memory (K4)
TOKENS = [
    ('Locks (failed Challenge, lost Dribble, beaten-by-Dribble defender, failed Steal: F1)', 'grey lock tokens',
     'printed: 8 lock tokens (rulebook page 1, token sheet)', 'covered: the worst case in one phase is 6 (2 Dribbles, '
     '2 Challenges and 2 Steals)'),
    ('Screens (hold until the screener moves)', 'the O piece flipped to its T side', 'printed: the pieces have a T side', 'covered'),
    ('A player\'s Move used this phase', 'Move token', 'printed: the action token pool', 'covered'),
    ('A player\'s Quick Step used this phase (one each, OQ-52)', 'the action token in that player\'s Quick Step slot',
     'printed: each player has a Quick Step slot on the tracker', 'covered'),
    ('Dribble wins this phase (the carrier is free of that defender\'s zone)', 'the beaten defender\'s lock token', 'printed',
     'covered by the lock token on the beaten defender'),
    ('Growth tags at junior (Early, On time, Late)', 'one tag per card', 'the levels sheet lists them; no printed tag markers',
     'needs 10 tag markers (5 a team) or written on the team sheet: flag for the designer'),
    ('Steal fouls this possession (tabletop bonus)', 'none needed', 'one possession: players count 0, 1, 2', 'covered'),
]


# ---- the rules in plain words (step 2): one entry per register row, next to it in this file -------------------
# sec: the rulebook section the rule belongs to (None: not in play, kept for old logs).
# text: the rule in the rulebook's voice. tab / dig: the value in each format, in words (the register's columns).
# src: where it is printed ('rulebook', 'trackers', 'court', 'token sheet', 'scenario sheet', 'levels sheet'),
#   'scenario' for scenario-card rules printed only there, or None when no printed page states it.
# oq: the OPEN_QUESTIONS.md row; q: for a rule no page states, the question it answers.
SECTIONS = ['Aim of the game', 'In the box', 'Setup', 'The shot', 'Reading the court', 'Rolling', 'Playing a possession',
            'Screens', 'Defender arrows', 'Passes and intercepts', 'Shooting', 'Scoring', 'Winning']
NOT_IN_PLAY = 'not in play (kept so old logs replay)'

WORDS = {
    # ---- aim, box, setup
    'Match length': dict(
        sec='Aim of the game', src='rulebook',
        text='Two players, two possessions: each attacks once and defends once. The higher score wins. The app plays '
             'longer matches (see Split by format).',
        tab='2 possessions, 1 each', dig='4, 8 or 12 possessions a side, alternating'),
    'Board 17 x 14, rim I2': dict(
        sec='In the box', src='rulebook',
        text='The court board has 17 columns (A to Q) and 14 rows. Squares are named by column and row, like I11. '
             'The rim is on I2.',
        tab='17 columns by 14 rows, rim on I2', dig='17 columns by 14 rows, rim on I2'),
    'Lock tokens (8)': dict(
        sec='In the box', src='rulebook',
        text='8 grey lock tokens mark a player who is locked.', tab='8 lock tokens', dig='shown on screen'),
    'Tokens per phase (6 a side)': dict(
        sec='Setup', src='rulebook',
        text='Each side puts its 6 action tokens in its tracker\'s pool. One token is one action.',
        tab='6 action tokens a side', dig='6 action tokens a side'),
    'Phase length (2 seconds), start clock 12': dict(
        sec='Setup', src='rulebook',
        text='Put the shot clock marker on 12. Each phase is 2 seconds. Scenario cards may start the clock lower.',
        tab='shot clock 12, phases of 2 seconds', dig='shot clock 12, phases of 2 seconds'),
    'Setup placement': dict(
        sec='Setup', src='rulebook',
        text='The offence places its 5 O pieces anywhere. The ball goes on a player on plain wood beyond the '
             'three-point tiles. The defence places its 5 X pieces on empty squares, each arrow pointing any way.',
        tab='offence places first, then defence', dig='offence places first, then defence'),
    'Playing levels (ages, standards, growth tags)': dict(
        sec='Setup', src='levels sheet',
        text='Each player takes 5 cards, one per position: a prescribed team, or a team from the playing levels '
             '(Senior, Youth or Junior; Pro, Semi-pro or Amateur; growth tags at Junior).',
        tab='same cards and levels', dig='same cards and levels'),
    # ---- the shot, the court, rolling
    'Zones and shot types': dict(
        sec='Reading the court', src='rulebook',
        text='Every shot is worth points × (rating − contest). Points come from the tile the shooter stands on: rim '
             'tiles 2 (layup, dunk or post move), mid-range tiles 2 (mid-range or floater), long-two tiles 2 (long two), '
             'three-point tiles 3 (three-pointer). Plain wood: no shot.',
        tab='rim, mid-range and long two score 2, threes 3', dig='rim, mid-range and long two score 2, threes 3'),
    'floor_declared_shot': dict(
        sec='The shot', src=None, oq=5, q='What does a declared shot worth less than 0 score?',
        text='A declared shot worth less than 0 scores 0, as a forced shot does.', tab='below 0 scores 0',
        dig='below 0 scores 0'),
    'd20 rolls': dict(
        sec='Rolling', src='rulebook',
        text='Roll the d20. You succeed on equal to or under your rating minus theirs. Shots are never rolled.',
        tab='d20, succeed at or under the target', dig='d20, succeed at or under the target'),
    'natural_rolls': dict(
        sec='Rolling', src=None, oq=4, q='What do a natural 1 and a natural 20 do, and a target of 20 or more?',
        text='A target of 20 or more always succeeds. A target of 0 or less always fails. A 1 or a 20 has no special '
             'meaning.', tab='no special 1 or 20', dig='no special 1 or 20'),
    # ---- playing a possession
    'Two actions a turn': dict(
        sec='Playing a possession', src='rulebook',
        text='The offence goes first. Then the sides take turns. On your turn, take 1 or 2 actions.',
        tab='1 or 2 actions a turn', dig='1 or 2 actions a turn'),
    'Turn-ending actions': dict(
        sec='Playing a possession', src='trackers',
        text='Pass, Screen, Dribble, Hesitate and Shot end the offence\'s turn. Intercept, Challenge, Steal and Pause '
             'end the defence\'s turn. Play them last.',
        tab='Pass, Screen, Dribble, Hesitate, Shot; Intercept, Challenge, Steal, Pause',
        dig='Pass, Screen, Dribble, Hesitate, Shot; Intercept, Challenge, Steal, Pause'),
    'Per-phase limits': dict(
        sec='Playing a possession', src='trackers',
        text='Each phase, each player has one Move. Each side has 2 Quick Steps (Sprints count). Offence: 2 Passes, '
             '2 Screens, 2 Dribbles, 1 Hesitate, 1 Shot. Defence: 2 Intercepts, 2 Challenges, 2 Steals, 1 Pause.',
        tab='as printed on the trackers', dig='as printed on the trackers'),
    'Move shape (3 straight, 2 diagonal)': dict(
        sec='Playing a possession', src='trackers',
        text='Move: up to 3 squares straight, 2 diagonal, or 1 straight and 1 diagonal. Never through another player.',
        tab='3 straight, 2 diagonal, or 1 + 1', dig='3 straight, 2 diagonal, or 1 + 1'),
    'move_either_order': dict(
        sec='Playing a possession', src=None, oq=11, q='Which comes first in a 1 straight + 1 diagonal Move?',
        text='The straight step and the diagonal step may come in either order.', tab='either order', dig='either order'),
    'diag_move_straight': dict(
        sec='Playing a possession', src=None, oq=25, q='Do the 2 diagonal steps of a Move go the same way?',
        text='Two diagonal steps go the same way, in a straight line.', tab='same way', dig='same way'),
    'qs_up_to': dict(
        sec='Playing a possession', src=None, oq=14, q='Is a Quick Step exactly the card\'s number, or up to it?',
        text='Quick Step: straight, up to the card\'s number of squares (2, 1 or 0).', tab='up to the card value',
        dig='up to the card value'),
    'qs_once_per_player': dict(
        sec='Playing a possession', src=None, oq=52, q='How many Quick Steps may one player take in a phase?',
        text='Each player has one Quick Step a phase. A Sprint uses it.', tab='1 per player a phase',
        dig='1 per player a phase'),
    'sprint_orth_base': dict(
        sec='Playing a possession', src='trackers', oq=3,
        text='Sprint: a Move and a Quick Step in one straight line, as one action, any direction: up to 3 plus the '
             'Quick Step straight, or 2 plus the Quick Step diagonal. It uses that player\'s Move and Quick Step.',
        tab='3 + Quick Step straight', dig='3 + Quick Step straight'),
    'sprint_diag_base': dict(sec=None, src='trackers', oq=3, tab='2 + Quick Step diagonal', dig='2 + Quick Step diagonal'),
    'sprint_needs_qs': dict(
        sec='Playing a possession', src=None, oq=15, q='Can a player with Quick Step 0 Sprint?',
        text='A player with Quick Step 0 can\'t Sprint.', tab='no Sprint at Quick Step 0', dig='no Sprint at Quick Step 0'),
    'wait_chain_block': dict(
        sec='Playing a possession', src='trackers',
        text='Hesitate (offence) and Pause (defence) are each side\'s one wait a phase. Neither may come straight after '
             'the other side\'s wait.', tab='no wait straight after the other side\'s',
        dig='no wait straight after the other side\'s'),
    'defence_empty_ends_phase': dict(
        sec='Playing a possession', src='rulebook',
        text='The phase ends when the offence plays its last token (the defence gets one more turn first), when the '
             'defence plays its last token (at once), or when a shot is taken.',
        tab='defence\'s last token ends the phase at once', dig='defence\'s last token ends the phase at once'),
    'forfeit_when_stuck': dict(
        sec='Playing a possession', src=None, oq=21, q='What happens to a side with tokens but no legal action?',
        text='A side with tokens left but no legal action gives up its remaining tokens.', tab='gives up its tokens',
        dig='gives up its tokens'),
    'locked_can_dribble': dict(
        sec='Playing a possession', src='trackers',
        text='Locked: no Move, Sprint, Dribble or arrow turn for the rest of the phase; Quick Step is still allowed. A '
             'player is locked by losing or being beaten on a Dribble, missing a Steal, or failing a Challenge.',
        tab='a locked carrier can\'t Dribble', dig='a locked carrier can\'t Dribble'),
    'Inbound phases (2)': dict(
        sec='Playing a possession', src='scenario',
        text='Inbounds (scenario cards): the inbounder sits off the court with the ball and can\'t move. The offence '
             'has 2 phases to complete the pass in, and the clock doesn\'t run. Once the ball is in, reset to a new '
             'phase with the card\'s clock. Not in after 2 phases: a turnover, −5, and play on with the ball to the '
             'player furthest from the rim, clock on the card\'s number.',
        tab='2 phases to inbound', dig='2 phases to inbound'),
    'inbounder_pass_only': dict(
        sec='Playing a possession', src=None, oq=19, q='What may the inbounder do before the ball is in?',
        text='Before the ball is in, the inbounder may only pass.', tab='pass only', dig='pass only'),
    'inbound_tie': dict(
        sec='Playing a possession', src='scenario',
        text='On a failed inbound, if players tie for furthest from the rim, the offence picks.', tab='offence picks',
        dig='offence picks'),
    'Phase reset': dict(
        sec='Playing a possession', src='rulebook',
        text='Reset: all action tokens back to the pools, lock tokens off, the shot clock down 2. Players stay where '
             'they are.', tab='tokens back, locks off, clock down 2', dig='tokens back, locks off, clock down 2'),
    'Hold for One cards': dict(
        sec='Playing a possession', src='scenario', q='What may the offence do on a Hold for One card?',
        text='On a Hold for One card the offence can\'t shoot before the last phase, and any turnover scores 0.',
        tab='no shot before the last phase', dig='no shot before the last phase'),
    'Shot-clock expiry': dict(
        sec='Playing a possession', src='rulebook',
        text='If the clock reaches 0 before a shot, at the table: a turnover, −5, and the ball carrier takes '
             'a forced shot from where the pieces stand, contested as normal; plain wood scores 0. The app differs '
             '(see Split by format).',
        tab='turnover, −5, then a forced shot', dig='turnover, the possession scores 0'),
    'forced_shot_choice': dict(
        sec='Playing a possession', src=None, oq=30, q='On a forced shot from a tile with two shot types, who picks?',
        text='On a forced shot the offence picks the shot type its tile allows.', tab='offence picks the type',
        dig='offence picks the type'),
    # ---- screens
    'carrier_can_screen': dict(
        sec='Screens', src='rulebook', oq=63,
        text='Any player except the ball carrier may Screen.', tab='not the ball carrier', dig='not the ball carrier'),
    'screen_rule': dict(
        sec='Screens', src='rulebook', oq=29,
        text='A Screen is the turn\'s first action, or its second straight after that player\'s own Move, and it ends '
             'the turn. It lasts until the screener moves, a Challenge beats it, or the phase ends.',
        tab='holds until the screener moves', dig='holds until the screener moves'),
    'screen_geometry': dict(
        sec='Screens', src='trackers', oq=9,
        text='The screener\'s T marks one square next to him. No defender steps diagonally from the T square or across '
             'its corner.', tab='no diagonal from or across the T', dig='no diagonal from or across the T'),
    'challenge_who': dict(
        sec='Screens', src='trackers', oq=16,
        text='Challenge: only the defender on the T square may Challenge. The offence rolls Screen − Challenge or '
             'under: the screen holds and the challenger is locked. Otherwise the screen is removed for everyone.',
        tab='only from the T square', dig='only from the T square'),
    # ---- defender arrows
    'arrow_mode': dict(
        sec='Defender arrows', src='rulebook',
        text='Each X piece points one arrow, in one of 8 directions. Turning the arrow uses his Move. A Quick Step '
             'can\'t turn it. After a Sprint it faces the way he ran.', tab='one arrow', dig='one arrow'),
    'drive_rule': dict(
        sec='Defender arrows', src='rulebook',
        text='A defender\'s zone is the squares along his arrow that one movement could reach. It stops at the first '
             'player in the way, and shrinks once he has used his Move. The ball carrier may step into the zone of a '
             'defender next to him, but not through it, unless he has beaten him on a Dribble.',
        tab='into the zone, not through', dig='into the zone, not through'),
    'Dribble': dict(
        sec='Defender arrows', src='trackers',
        text='Dribble: take on a defender 1 square away; succeed on Dribble − Agility or under. Win: he is locked, and '
             'you may go through his zone. Lose: you are locked, but may still pass or shoot.',
        tab='Dribble − Agility', dig='Dribble − Agility'),
    'arrow_line_adjacent_at': dict(
        sec='Defender arrows', src=None, oq=24, q='Is "next to him" judged before or after the movement?',
        text='"Next to him" means next to him when the movement starts.', tab='at the start of the movement',
        dig='at the start of the movement'),
    'dribble_win_lasts': dict(
        sec='Defender arrows', src=None, oq=18, q='How long does a Dribble win free the carrier from that defender?',
        text='A Dribble win lets you through his zone for the rest of the phase.', tab='rest of the phase',
        dig='rest of the phase'),
    'steal_lock': dict(
        sec='Defender arrows', src='rulebook',
        text='Steal: from 1 square away, arrow on the ball carrier. No foul, and the carrier keeps the ball on '
             'Dribble − Steal or under: the defender is locked. Otherwise the ball is stolen.',
        tab='a clean miss locks the defender', dig='a clean miss locks the defender'),
    'reach_angle_fouls': dict(
        sec='Defender arrows', src='rulebook',
        text='The foul roll comes first, Foul (Steal) or under: once if the defender is closer to the rim than the '
             'ball carrier, twice if level or further, and either roll fouls. The same count applies to a contest\'s '
             'foul roll.', tab='1 roll from closer, 2 from level or behind', dig='1 roll from closer, 2 from level or behind'),
    # ---- passes
    'pass_resolution': dict(
        sec='Passes and intercepts', src='rulebook', oq=2,
        text='A pass fixes a line from passer to receiver. Passes cross players. The defence answers with its first '
             'action, or the pass lands.', tab='the defence answers first', dig='the defence answers first'),
    'on_line_tolerance': dict(
        sec='Passes and intercepts', src='rulebook', oq=13,
        text='Through you: the line passes through your square\'s centre. Intercept, whatever your facing.',
        tab='through the square\'s centre', dig='through the square\'s centre'),
    'intercept_rule': dict(
        sec='Passes and intercepts', src='rulebook', oq=73,
        text='Jump the lane: one straight Move, Quick Step or Sprint along your arrow whose path touches or crosses the '
             'line, ending where it meets it. Then Intercept. That is the defence\'s whole turn. No intercept on any '
             'square next to the passer: Steal instead.', tab='one straight movement, then Intercept',
        dig='one straight movement, then Intercept'),
    'Intercept roll': dict(
        sec='Passes and intercepts', src='rulebook',
        text='The offence rolls Pass − Intercept or under: the pass gets through. Otherwise it is picked off. A missed '
             'Intercept leaves him on the line, his Move used.', tab='Pass − Intercept', dig='Pass − Intercept'),
    'lane_jump_keeps_facing': dict(
        sec='Passes and intercepts', src='rulebook', oq=76,
        text='The jump keeps your facing.', tab='keeps the facing', dig='keeps the facing'),
    'receiver_denial': dict(
        sec='Passes and intercepts', src='rulebook',
        text='Denied: no pass through the square of a defender next to the receiver.',
        tab='no pass through a defender next to the receiver', dig='no pass through a defender next to the receiver'),
    'receiver_denial_tol': dict(sec=None, src='rulebook', tab='through his square', dig='through his square'),
    'intercept_return': dict(
        sec='Passes and intercepts', src=None, oq=71, q='Where does a successful interceptor end up?',
        text='A successful Intercept puts the interceptor back on the square and arrow he had at the start of the '
             'defence\'s turn; his Move stays used.', tab='back where he started the turn',
        dig='back where he started the turn'),
    'inbound_resolves': dict(
        sec='Passes and intercepts', src=None, oq=35, q='When does an inbound pass land?',
        text='An inbound pass works like any other pass, and lands after the defence\'s whole turn.',
        tab='after the defence\'s turn', dig='after the defence\'s turn'),
    # ---- shooting
    'reaction_kinds': dict(
        sec='Shooting', src='trackers', oq=6,
        text='Declare a Shot (the ball carrier, never from plain wood). The defence takes one last turn to react, '
             'with a Move or a Steal.', tab='Move, Quick Step, Sprint or Steal', dig='Move, Quick Step, Sprint or Steal'),
    'reaction_may_decline': dict(
        sec='Shooting', src=None, oq=6, q='How many actions may the reaction take, and which?',
        text='The reaction may be 0, 1 or 2 actions, and may also use a Quick Step or a Sprint.',
        tab='0, 1 or 2 actions', dig='0, 1 or 2 actions'),
    'contest_choice': dict(
        sec='Shooting', src='rulebook', oq=12,
        text='Then one adjacent defender contests, diagonals included: the defence picks who, or no one. None '
             'adjacent: the contest is 0.', tab='the defence picks', dig='the defence picks'),
    'contest_geometry': dict(
        sec='Shooting', src='rulebook',
        text='Arrow off the shooter: a foul roll first, Foul (Contest) or under.',
        tab='any adjacent defender; arrow off means a foul roll', dig='any adjacent defender; arrow off means a foul roll'),
    'Far-contest -3': dict(
        sec='Shooting', src='rulebook',
        text='Further from the rim than the shooter: contest at −3.', tab='−3', dig='−3'),
    'floor_contest_zero': dict(
        sec='Shooting', src=None, oq=20, q='Can the −3 take a contest below 0?',
        text='The −3 never takes a contest below 0.', tab='never below 0', dig='never below 0'),
    # ---- scoring
    'Turnover cost': dict(
        sec='Scoring', src='rulebook',
        text='A successful Intercept or Steal at the table: −5 and the shot clock loses a phase; play on. A stolen shot '
             'is cancelled. In the last phase the possession scores 0. The app differs (see Split by format).', tab='−5, the shot clock loses a phase, play on', dig='the possession ends and scores 0'),
    'Turnover points (-5)': dict(sec=None, src='rulebook', tab='−5', dig='−5 (where a turnover is scored)'),
    'Steal-foul bonus': dict(
        sec='Scoring', src='rulebook',
        text='A foul on a Steal at the table: the first is +5 and play on; the second gives free throws and the '
             'possession ends. The app counts fouls across a quarter (see Split by format).',
        tab='1st +5 and play on; 2nd free throws, over', dig='+5 and play on until the 5th team foul; then free throws, over'),
    'Steal foul +5': dict(sec=None, src='rulebook', tab='+5', dig='+5'),
    'and_one': dict(
        sec='Scoring', src='rulebook', oq=34,
        text='A foul on a shot (once it is declared, or forced): free throws or the open shot, whichever is higher. '
             'The possession ends.', tab='free throws or the open shot if higher', dig='free throws or the open shot if higher'),
    'Free-throw multipliers (x2, x3)': dict(
        sec='Scoring', src='rulebook',
        text='Free throws score 2 × the shooter\'s free-throw rating, or 3 × on a three.', tab='2 ×, or 3 × on a three',
        dig='2 ×, or 3 × on a three'),
    "Look bands and Coach's Call bonus": dict(
        sec='Scoring', src='scenario',
        text='Scenario cards: a look of 30 or more (Excellent) beats the card. Coach\'s Call: if the secret target '
             'takes the shot, add the bonus for the look: Poor +0, Okay +2, Good +5, Great +8, Excellent +10.',
        tab='Excellent 30+', dig='Excellent 30+'),
    'three_only_ft_on_twos': dict(
        sec='Scoring', src=None, oq=22, q='On Need a Three, do free throws from a fouled two score?',
        text='Need a Three: only a three scores; a fouled two\'s free throws score 0 too.', tab='score 0', dig='score 0'),
    'coach_bonus_on_forced': dict(
        sec='Scoring', src=None, oq=23, q='Does the Coach\'s Call bonus count on a forced shot, and on which look?',
        text='The Coach\'s Call bonus uses the look\'s band (the shot value, or the free throws if fouled), and counts '
             'on a forced shot by the target too.', tab='counts, forced shots too', dig='counts, forced shots too'),
    # ---- winning
    'Tie-break roll': dict(
        sec='Winning', src='rulebook',
        text='After the first possession, swap seats and trackers, flip every card and set up again. After both, the '
             'higher score wins. Tied: each player rolls for their final shot, d20 at or under rating − contest. A make '
             'beats a miss.', tab='roll for the final shot', dig='see Tied match'),
    'Late Clock results': dict(
        sec='Winning', src='scenario', q='How are Late Clock cards compared?',
        text='On Late Clock cards, compare results first (win, then tie, then loss); the shot value breaks ties.',
        tab='result first, then shot value', dig='result first, then shot value'),
    'Tied match': dict(
        sec=None, src='rulebook', tab='roll for the final shot', dig='stays a tie'),
    # ---- the format, digital only
    'digital': dict(sec=None, src=None, tab='tabletop', dig='digital'),
    'quarter_possessions': dict(sec=None, src=None, tab='not used', dig='18 possessions a side'),
    'bonus_from': dict(sec=None, src=None, tab='not used', dig='the 5th team foul'),
    'Team fouls carried across matches': dict(sec=None, src=None, tab='not used',
                                              dig='kept for the same two players, or a player and a computer level'),
    'Decision timer': dict(sec=None, src=None, tab='none', dig='optional thinking clock for each player'),
    'Computer opponents and the trainer': dict(sec=None, src=None, tab='none',
                                               dig='Rookie, Starter and All-Star; the trainer grades decisions'),
    # ---- settings for rules not in play (old logs only)
    'turnover_play_on': dict(sec=None, src=None, tab=NOT_IN_PLAY, dig=NOT_IN_PLAY),
    'arrow_line_strict': dict(sec=None, src=None, tab=NOT_IN_PLAY, dig=NOT_IN_PLAY),
    'late_closeout': dict(sec=None, src=None, tab='off (a rule test, not adopted)', dig='off (a rule test, not adopted)'),
}

DIGITAL_ONLY = [
    ('Quarters and team fouls', 'Each side\'s defensive fouls (steal fouls and shooting fouls) count across a running '
     'quarter of 18 possessions a side. The count carries across matches between the same two players, or a player and '
     'a computer level, and resets when both sides have had 18. The screen shows the count, the bonus line and the '
     'possessions left. (settings: quarter_possessions, bonus_from)'),
    ('Match length', 'A match is 4, 8 or 12 possessions a side, sides alternating. The higher total wins; a tie stays '
     'a tie.'),
    ('The decision timer', 'Each player may set an optional thinking clock.'),
    ('Computer levels', 'The computer plays at three levels: Rookie, Starter and All-Star. The levels differ in how '
     'deep and how long they look ahead, not in the rules.'),
    ('The trainer', 'After a possession the trainer grades a player\'s decisions against the best options it found, '
     'and keeps a rating for each player.'),
]

SPLITS = [
    ('Turnover cost', '−5 and the shot clock loses a phase; play on.', 'The possession ends and scores 0.',
     'A digital match has several possessions a side, so the next possession is the cost.'),
    ('Shot-clock expiry', 'A turnover, −5, then a forced shot from where the pieces stand.', 'A turnover: the '
     'possession scores 0.', 'As in basketball: no shot before the clock runs out is a turnover.'),
    ('Steal-foul bonus', 'First steal foul +5 and play on; second, free throws and the possession ends.',
     '+5 and play on until the 5th team foul of the quarter; from the 5th, free throws and the possession ends.',
     'One possession is the whole tabletop game; the app keeps fouls across a quarter.'),
    ('Match length', '2 possessions, 1 each.', '4, 8 or 12 possessions a side.', 'An app match can be longer.'),
    ('Tied match', 'Each player rolls for their final shot.', 'The match stays a tie.',
     'Found in the code, not yet approved: no reason recorded.'),
]


ENTRIES_BY_NAME = {e[0]: e[2] for e in ENTRIES}


def words_for(name):
    w = WORDS.get(name)
    if w is None:
        raise KeyError(f'register entry {name!r} has no plain words (WORDS)')
    return w


def value(rules, src):
    if 'rules' in src:
        return getattr(rules, src['rules'])
    if 'const' in src:
        norm = lambda v: tuple(sorted(v)) if isinstance(v, (set, frozenset)) else v
        return tuple(norm(getattr(RC, c)) for c in src['const'])
    return None


def markdown():
    out = ['# Playmaker rules register', '',
           'Every rule value and mechanism, marked **Shared** (both formats), **Digital only**, **Tabletop only** or '
           '**Split by format** (deliberately different, with the reason). Written by `python3 -m playmaker_engine.register`; '
           '`tests/test_step3n.py` asserts every Shared entry has identical values in both formats, and any change to a '
           'shared value must be tested under both formats. The value columns give each rule\'s value in words; the '
           'plain rules are in `RULES_CURRENT.md` (`python3 -m playmaker_engine.register --rules`).', '',
           '| Rule | Status | Value (tabletop) | Value (digital) | Notes |', '|---|---|---|---|---|']
    for name, status, src, what, note in ENTRIES:
        w = words_for(name)
        out.append(f'| {name} | {status} | {w["tab"]} | {w["dig"]} | {" ".join(x for x in (what, note) if x)} |')
    out += ['', '## Splits for the designer', '',
            'Where the best value differs between formats (a designer decision, not a bug):', '',
            '- Turnover cost and shot-clock expiry: the engine values a risky pass or a reach differently by format, so a '
            'digital-tuned habit (gambling for a steal late in a possession) is wrong at the table, where play goes on '
            'at -5. The trainer grades each game under its own format.',
            '- The steal-foul bonus: within the possession at the table, across a quarter in digital. A defence two fouls '
            'from the bonus behaves differently in each.',
            '- The coarse phase table (engine data, not a rule) is solved from digital self-play; tabletop possessions '
            'play on after a turnover, so their late-phase values differ.',
            '- A tied match: the table rolls for the final shots, the app leaves a tie. Found in the code, not approved.', '',
            '## Tokens and markers', '', '| Mechanism | Token | Printed | Check |', '|---|---|---|---|']
    for m, t, p, c in TOKENS:
        out.append(f'| {m} | {t} | {p} | {c} |')
    return '\n'.join(out) + '\n'


def _setting_note(name, src):
    if src.get('rules'):
        return f' (setting: {src["rules"]})'
    return ''


def rules_markdown():
    """RULES_CURRENT.md: every rule the game plays by, in plain words, in the rulebook's sections, generated from the
    register so it can't drift from the code."""
    by = {k: [] for k in SECTIONS}
    order = list(WORDS)
    srcs = {e[0]: e[2] for e in ENTRIES}
    for name in sorted(srcs, key=lambda n: order.index(n)):
        w = words_for(name)
        if w.get('sec') and w.get('text'):
            by[w['sec']].append((name, srcs[name], w))
    out = ['# Playmaker: the rules as played', '',
           'Every rule the game plays by, at the table and in the app, in the rulebook\'s order. Generated from the rules '
           'register (`python3 -m playmaker_engine.register --rules`). † marks a rule the rulebook and trackers don\'t '
           'state; the last section lists them.', '']
    for sec in SECTIONS:
        out += [f'## {sec}', '']
        for name, src, w in by[sec]:
            mark = ' †' if w.get('src') in (None, 'scenario') else ''
            out.append(f'- {w["text"]}{mark}{_setting_note(name, src)}')
        out.append('')
    out += ['## Digital only', '']
    for title, text in DIGITAL_ONLY:
        out.append(f'- **{title}.** {text}')
    out += ['', '## Split by format', '']
    for title, tab, dig, why in SPLITS:
        low = lambda t: t[:1].lower() + t[1:] if t[:1].isalpha() else t
        out += [f'**{title}.** At the table: {low(tab)}  ', f'In the app: {low(dig)}  ', f'Why: {low(why)}', '']
    out += ['## Rules the engine plays that the rulebook doesn\'t state', '',
            'Each is something the engine does that no line of the rulebook or the trackers states. Listed, not judged.', '']
    unstated, scenario = [], []
    for name, src in sorted(srcs.items(), key=lambda r: order.index(r[0])):
        w = words_for(name)
        if w.get('sec') and w.get('src') is None:
            unstated.append((w['text'], w.get('q', ''), w.get('oq'), _setting_note(name, src)))
        elif w.get('sec') and w.get('src') == 'scenario':
            scenario.append((w['text'], _setting_note(name, src)))
    for n, (text, q, oq, note) in enumerate(unstated, 1):
        out.append(f'{n}. {text} Question: {q} {"OPEN_QUESTIONS.md row " + str(oq) + "." if oq else "No row."}{note}')
    out += ['', 'Printed on the scenario rules sheet, not in the rulebook or the trackers:', '']
    for n, (text, note) in enumerate(scenario, 1):
        out.append(f'{n}. {text}{note}')
    return '\n'.join(out) + '\n'


def unstated_count():
    """(rules no printed page states, scenario-sheet-only rules): the size of the last section."""
    u = sum(1 for e in ENTRIES if words_for(e[0]).get('sec') and words_for(e[0]).get('src') is None)
    sc = sum(1 for e in ENTRIES if words_for(e[0]).get('sec') and words_for(e[0]).get('src') == 'scenario')
    return u, sc


ROOT = __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))

if __name__ == '__main__':
    import os
    import sys
    if '--rules' in sys.argv:
        path = os.path.join(ROOT, 'RULES_CURRENT.md')
        open(path, 'w').write(rules_markdown())
    else:
        path = os.path.join(ROOT, 'docs', 'rules_register.md')
        open(path, 'w').write(markdown())
    print(path)
