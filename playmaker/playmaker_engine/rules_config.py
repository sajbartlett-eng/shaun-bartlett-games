"""Every number and every open ruling in Playmaker lives here.

Numbers come straight from the rulebook, the trackers and the scenario rules.
Settings marked OQ-n match the numbered items in OPEN_QUESTIONS.md: each default
is the one the designer asked for, and a ruling is a one-line change here.
"""
from dataclasses import dataclass, field, replace

# ---- fixed numbers from the rules ------------------------------------------
BOARD_COLS = 17            # A..Q
BOARD_ROWS = 14            # 1..14, row 1 is the baseline
RIM = (8, 2)               # I2
TOKENS_PER_PHASE = 6
PHASE_SECONDS = 2
START_CLOCK = 12
DIE = 20                   # d20
FAR_CONTEST_PENALTY = 3    # defender further from the rim than the shooter
TURNOVER_POINTS = -5
STEAL_FOUL_BONUS = 5       # first foul on a steal
FT_MULT_TWO = 2
FT_MULT_THREE = 3
MAX_ACTIONS_PER_TURN = 2
MOVE_STRAIGHT = 3          # up to 3 straight
MOVE_DIAGONAL = 2          # up to 2 diagonal
INBOUND_PHASES = 2
SCENARIO_GOAL = 30         # an Excellent look

# Per-phase limits. 'move' is once per player; the rest are per side.
LIMITS = {
    'O': {'qs': 2, 'pass': 2, 'screen': 2, 'dribble': 2, 'hesitate': 1, 'shot': 1},
    'X': {'qs': 2, 'intercept': 2, 'challenge': 2, 'steal': 2, 'pause': 1, 'contest': 1},
}
TURN_ENDERS = {'pass', 'screen', 'dribble', 'hesitate', 'shot',
               'intercept', 'challenge', 'steal', 'pause', 'contest'}

# Prestige bands, highest first: (name, lowest score in band)
BANDS = [('Excellent', 30), ('Great', 25), ('Good', 20), ('Okay', 15), ('Poor', None)]
# Coach's Call bonus by band of the look
COACH_BONUS = {'Poor': 0, 'Okay': 2, 'Good': 5, 'Great': 8, 'Excellent': 10}

# Zone -> allowed shot types and points
ZONE_SHOTS = {
    'K': ('layup', 'dunk', 'post'),
    'M': ('mid', 'floater'),
    'L': ('long',),
    '3': ('three',),
    '.': (),
}
ZONE_POINTS = {'K': 2, 'M': 2, 'L': 2, '3': 3}


@dataclass(frozen=True)
class Rules:
    # OQ-1: ball after an intercept or steal that plays on.
    #   'play_on' : ball back to the passer / stays with the carrier, -5, play continues.
    #   'end'     : the possession ends at that point.
    turnover_play_on: str = 'play_on'
    # OQ-2: when a pass resolves.
    #   'defence_turn' : on the defence's next turn (it may Intercept); if it doesn't,
    #                    the pass completes at the start of that turn.
    #   'immediate'    : completes at once unless a defender is already on the line.
    pass_resolution: str = 'defence_turn'
    # OQ-3: Sprint length = Move length + Quick Step, in one straight line.
    sprint_orth_base: int = MOVE_STRAIGHT
    sprint_diag_base: int = MOVE_DIAGONAL
    # OQ-4: roll bounds. A target >= 20 always succeeds, <= 0 always fails.
    natural_rolls: bool = False
    # OQ-5 (ruled): a declared shot worth less than 0 scores 0, matching the forced shot.
    floor_declared_shot: bool = True
    # OQ-6: defence reaction to a declared shot may use 0, 1 or 2 actions (movement, arrow
    #   turns, Steal) from the tokens still in the pool.
    reaction_kinds: tuple = ('move', 'qs', 'sprint', 'steal')
    reaction_may_decline: bool = True
    # OQ-7: defence out of tokens ends the phase at once (as written).
    defence_empty_ends_phase: bool = True
    # OQ-8: a wait (Hesitate / Pause) may not be played on the turn straight after the
    #   other side's wait.
    wait_chain_block: bool = True
    # OQ-9: screen geometry.
    #   'from_t_or_corner' : a defender's diagonal step is banned if it starts on the T
    #                        square or cuts the T square's corner (T is one of the two
    #                        squares the diagonal passes between).
    #   'from_t_only'      : only diagonal steps that start on the T square are banned.
    screen_geometry: str = 'from_t_or_corner'
    # OQ-29 (RULED, step 3i follow-up): how long a screen lasts and when it can be set.
    #   'hold_until_move' : a Screen is the turn's first action, or its second straight after that same
    #                       player's Move; it ends the turn and lasts until the screener moves (he may Move at
    #                       any time), a Challenge beats it (removed for every defender) or the phase ends.
    #   'two_turns'       : the old engine: any time in the turn; the screener can't move; it flips back after
    #                       the offence's next turn and survives the phase reset; a beaten Challenge lets that
    #                       one defender through.
    screen_rule: str = 'hold_until_move'
    # OQ-10: arrow line. A ball carrier move is illegal only if its path goes from one
    #   side of the ray to the other (touching or stepping onto the line is fine).
    arrow_line_strict: bool = True
    # Drives (RULED, step 3i follow-up). 'zone': the ball carrier may enter a square in the zone of a defender
    #   adjacent to him at the start of the movement, but no square of the path before the destination may
    #   lie in it, unless he beat that defender with a Dribble this phase. 'arrow_line': the old rule (the
    #   path may not cross the defender's arrow line).
    drive_rule: str = 'zone'
    # Intercept outcome (RULED, step 3i follow-up). True: an Intercept that wins (-5, the ball stays with the
    #   passer) puts the interceptor back on the square and arrow he had at the start of the defence's turn
    #   (his Move stays used); one that misses leaves him where he moved, on the pass line. False: the old
    #   engine (he stays on the pass line either way).
    intercept_return: bool = True
    # Interception (RULED, the OQ-72 refinement). 'move_then_intercept':
    #   the pass line is fixed from passer to receiver once the pass is declared;
    #   one defender answers in the defence's turn: (a) one Move, Quick Step or Sprint from his starting square,
    #   straight along one of his arrow lines, whose path crosses or ends on the pass line, ending on the
    #   pass-line square it meets (the corner-slip fix: a diagonal pass can't slip between corner-touching
    #   squares), a Sprint keeping his facing; then the Intercept (the defence's whole turn); or (b) through
    #   you: the line passes through his square, and the Intercept is his first action, whatever his facing;
    #   anything else first and the pass completes before that action: no other defender's action creates
    #   or opens an Intercept;
    #   the passer's ring: no Intercept on any square next to the passer (a defender there Steals instead).
    #   A failed Intercept (the pass completes) leaves him on the pass line with his Move used. What a
    #   successful one costs is turnover_cost.
    # 'ring_jump': the first OQ-72 ruling (the Intercept is itself a straight Move or Quick Step, a defender
    #   may follow first, success ends the possession). 'approach': the rule before OQ-72. Both kept so old
    #   logs replay.
    intercept_rule: str = 'move_then_intercept'
    # What a successful Intercept or Steal costs the offence (RULED, play-on; intercepts and steals alike).
    #   'minus5_lose_phase' : -5 and the shot clock loses one phase (2 seconds); the current phase goes on
    #                         with the same tokens and actions left; in the final phase the possession ends
    #                         and scores 0. The ball stays with the passer (an Intercept) or the carrier (a
    #                         Steal); a Steal on a declared shot cancels the shot (it doesn't use the phase's
    #                         shot) and play goes on.
    #   'minus5' | 'minus10' : the points only, play on.   'lose_phase' : the clock only (no points).
    #   'end_possession'     : the possession ends at -5.
    #   'legacy'             : the engine before this ruling (an Intercept as its intercept_rule says; a Steal
    #                          in play -5 and play on, on a declared shot the possession ends at -5).
    #   The old name intercept_cost is an alias (with_rules accepts it; Rules.intercept_cost reads it).
    turnover_cost: str = 'minus5_lose_phase'
    # OQ-11: a 1 straight + 1 diagonal Move may go in either order.
    move_either_order: bool = True
    # OQ-12 (ruled: the defence chooses any adjacent defender): contest choice.
    #   'min_value' : defence picks the adjacent defender (or none) that minimises the
    #                 expected shot value, counting foul free throws.
    #   'nearest'   : the nearest adjacent defender (rulebook wording), ties by min value.
    #   'player'    : (RULED, step 3b) the defence chooses: contest with any adjacent defender, or not.
    contest_choice: str = 'player'
    # ---- new questions found while building (OPEN_QUESTIONS.md 13+) ----
    # OQ-13 (RULED by the rulebook, Nov 2026): "Through you: the line passes through your square's centre."
    #   0 = the pass line passes exactly through the square's centre (as check_scenarios.py does; rows,
    #   columns, diagonals and the rational lines between); 0.5 was the engine's earlier reading (the line
    #   through the middle half of the square). Only 'through you' uses it under move_then_intercept: a lane
    #   jump is geometry (lane_meet).
    on_line_tolerance: float = 0
    # OQ-76 (RULED by the rulebook, Nov 2026): "Jump the lane: one straight Move, Quick Step or Sprint along your
    #   arrow, keeping your facing." True: the Move half of move-then-intercept keeps the defender's arrow (a
    #   Sprint always did, a Quick Step never turns). False: the engine before the ruling (the Move could turn).
    lane_jump_keeps_facing: bool = True
    # Receiver denial (RULED by the designer, Nov 2026): a pass may not travel through the square of a defender next
    #   to the receiver: the lane is blocked, not interceptable, whatever his facing. "Through" is the pass line within
    #   receiver_denial_tol of the defender's centre (half a square), strictly between passer and receiver. Defenders
    #   elsewhere on the line are unchanged (through-you intercept, the roll as normal). False: no denial.
    receiver_denial: bool = True
    receiver_denial_tol: float = 0.5
    # OQ-14: Quick Step may be shorter than the card value (up to 2, not exactly 2).
    qs_up_to: bool = True
    # OQ-15: a player with Quick Step 0 cannot Sprint.
    sprint_needs_qs: bool = True
    # OQ-52 (RULED): each player has one Quick Step a phase, and a Sprint uses it ("uses that player's
    #   Move and Quick Step", trackers). So no Sprint after that player's Quick Step, no Quick Step after
    #   their Sprint, no second Quick Step. The side's limit of 2 Quick Steps (Sprints count) still applies.
    qs_once_per_player: bool = True
    # A defender's arrow (RULED: back to the single arrow after the move-then-intercept run, where the single
    #   arrow with late closeout off was the cell closest to basketball; the wedge is kept available).
    #   'single' : one arrow line.
    #   'wedge'  : two arrow lines 45 degrees apart (directions a and a+1 for arrow index a): passes,
    #              drives, steals and contest facing test either line; a Sprint sets one edge to the run
    #              direction and the defender picks the side of the other.
    arrow_mode: str = 'single'
    # Step 3h (rule test, not adopted): contest quality.
    #   'current'      : any adjacent defender contests; arrow off the shooter = a foul roll; -3 when the
    #                    contester is further from the rim than the shooter.
    #   'wedge_mirror' : facing gates the contest (shooter on an arrow line); Front if the rim square
    #                    lies in the wedge mirrored backwards, Behind if it lies in the forward wedge,
    #                    else Side (needs arrow_mode 'wedge').
    #   'rim_distance' : facing gates the contest; Front if closer to the rim than the shooter, Side if
    #                    level, Behind if further.
    #   Front: full contest. Side: a foul roll (Foul contest rating). Behind: a foul roll and the -3.
    contest_geometry: str = 'current'
    # OQ-63 (RULED, step 3i): the ball carrier can't Screen (a handoff is a short pass, not a screen).
    carrier_can_screen: bool = False
    # Step 3i (rule test, not adopted): a contester who used a reaction movement (Move, Sprint or Quick
    #   Step) to reach the contest is late: at the rim, post or floater a foul roll; on a mid-range, long
    #   two or three the -3 and no foul roll. One who was already adjacent (and only turns) contests as now.
    late_closeout: bool = False
    # OQ-16 (ruled): who may Challenge a screen.
    #   'on_t'     : only the defender standing on the screen's T square (the one it blocks).
    #   'adjacent' : any defender next to the screener.   'any' : any defender.
    challenge_who: str = 'on_t'
    # OQ-17 (ruled): a locked ball carrier may not Dribble: a lost dribble means pass or shoot.
    locked_can_dribble: bool = False
    # OQ-18: a Dribble win frees the carrier from that defender's arrow line for the rest
    #   of the phase.
    dribble_win_lasts: str = 'phase'
    # OQ-19: before the inbound pass lands the inbounder may only Pass.
    inbounder_pass_only: bool = True
    # OQ-20 (ruled): the far-contest -3 never takes a contest below 0.
    floor_contest_zero: bool = True
    # OQ-21: a side with tokens but no legal action forfeits its remaining tokens.
    forfeit_when_stuck: bool = True
    # OQ-22: Need a Three: a two-point shot (and its free throws) scores 0.
    three_only_ft_on_twos: bool = False
    # OQ-23: Coach's Call bonus uses the band of the look (shot value, or free throws if fouled)
    #   and also applies to a forced shot by the target.
    coach_bonus_on_forced: bool = True
    # OQ-24: the arrow-line restriction applies to defenders adjacent at the start of the
    #   movement action.
    arrow_line_adjacent_at: str = 'start'
    # OQ-25: two diagonal steps of a Move go the same way (a straight diagonal line).
    diag_move_straight: bool = True
    # OQ-27 (ruled): on a failed inbound, a tie for "furthest from the rim" is the offence's
    #   choice ('offence'); 'lowest' gives the ball to the lowest piece number.
    inbound_tie: str = 'offence'
    # OQ-30 (RULED, step 3b): the forced shot's type at clock 0. 'player' = the offence picks among the
    #   types its zone allows; 'best' = the engine picks the best expected value.
    forced_shot_choice: str = 'player'
    # OQ-35 (ruled): an inbound pass works like any other pass. The defence gets its normal
    #   turn (1 or 2 actions: e.g. Move then Intercept, Sprint then Intercept, or move two
    #   players); the pass resolves after that turn, then the phase resets to the card's clock.
    #   'after_defence_turn' (ruled) | 'defence_turn_start' (step 1: lands at the start of the turn)
    inbound_resolves: str = 'after_defence_turn'
    # OQ-34 (new rule, the and-one): once a shot is declared (or forced at clock 0), any foul
    #   scores the higher of the free throws and the shot's uncontested value. Fouling a good
    #   look can then never help the defence. False = free throws only.
    and_one: bool = True
    # Step 3m Part A: the digital match format. A turnover (a successful Intercept, a successful Steal, including on
    #   a declared shot, and shot-clock expiry) ends the possession and it scores 0. Steal fouls are unchanged.
    #   False = the printed (tabletop) rules.
    digital: bool = False
    # Step 3n designer rulings (shared by both formats unless marked):
    # F1: a failed Steal (no foul, the ball kept) locks the defender for the rest of the phase, as a failed Challenge
    #   locks the challenger (no Move or Sprint; his Quick Step is left).
    steal_lock: bool = True
    # F2: the angle of a reach decides the foul risk. A Steal, or a contest that needs a foul roll, makes one foul roll
    #   if the defender is closer to the rim than the ball carrier (or shooter), two if level or further (either fouls).
    #   The contest -3 for further from the rim is unchanged.
    reach_angle_fouls: bool = True
    # F3 (digital only): team fouls run across a quarter of this many possessions per side; from the bonus_from-th
    #   team foul a steal foul gives free throws and ends the possession. Tabletop keeps its within-possession rule
    #   (first steal foul +5, second free throws).
    quarter_possessions: int = 18
    bonus_from: int = 5
    # Shaun's rulings of 9 Nov 2026 (DECISIONS.md), shared by both formats:
    # D-18: Contest is an action. After a shot is declared the defence reacts with up to 2 actions from its remaining
    #   tokens (Move, Quick Step, Sprint, Steal or Contest). A Contest is the last action, one a phase, by one defender
    #   next to the shooter at that moment, and uses a token; no Contest means a contest of 0. A forced shot at clock 0
    #   (not declared) keeps the contest choice. False: the free contest after the reaction (before the ruling).
    contest_action: bool = True
    # D-82: a turnover that scores the possession 0 scores 0 or the total banked before it, whichever is lower.
    #   False: it scores 0.
    turnover_floor: bool = True
    # D-151, D-153, D-154 (Shaun, 11 Nov 2026): the control rule, the app's rule at size 2; the table's rules stay
    #   without it (on hold, D-146). Control against reaction. A player whose last movement this phase was a Quick Step
    #   or a Sprint is rushed; a Move, or no movement this phase, is set (a Move after a Quick Step or Sprint restores
    #   control). A rushed shot has a reduced rating. A rushed Contest has a reduced rating, and today's foul rolls for
    #   its position with no extra roll for being rushed (D-154). No exceptions: the forced shot and its free Contest
    #   follow the same test.
    #   'app' (the default: size 2 in the app's format, off at the table) | '0' (off; 'off' is the same) | '1' | '2' |
    #   '3': the reduction in rating steps, the same for every shot type and for the Contest. control_size(rules) is
    #   the size in play.
    control: str = 'app'
    # Step 18g (D-167, Shaun, 12 Nov 2026; the app only, under test): the zone of influence. 'on': each defender
    #   carries two equal arrows 45 degrees apart (directions a and a+1 for arrow index a), each under the normal
    #   arrow rules. A ball handler or shooter on either counts as "the arrow on him" (a Steal, a Contest); an
    #   Intercept goes along either. The wedge between them, out to the squares one movement still left to him
    #   reaches, is his zone: an adjacent ball handler may end in it but not pass through it. A Dribble won against
    #   him breaks it for the rest of the phase: no arrow at all (no Steal, a Contest with the wrong-angle foul roll,
    #   an Intercept only through his own square), and his movement is locked as today. 'off': today's rules.
    zone: str = 'off'
    # D-89: every steal foul is +5 to the offence; in the bonus it also gives free throws and the possession ends.
    #   False: in the bonus the foul gives free throws only (no +5).
    steal_foul_always_plus5: bool = True

    @property
    def intercept_cost(self):
        return self.turnover_cost


# The step 3i follow-up rulings (screens, the wedge, drives through a zone, the interceptor's return): a log
# records these settings in its setup line; a log from before them replays with the old values.
RULED_3I = ('arrow_mode', 'screen_rule', 'drive_rule', 'intercept_return', 'late_closeout', 'intercept_rule',
            'turnover_cost', 'on_line_tolerance', 'lane_jump_keeps_facing', 'receiver_denial', 'receiver_denial_tol',
            'steal_lock', 'reach_angle_fouls', 'quarter_possessions', 'bonus_from', 'contest_action', 'turnover_floor',
            'steal_foul_always_plus5')
# A log from before Shaun's rulings of 9 Nov 2026 (no contest_action in its setup line) replays without them.
PRE_9NOV = dict(contest_action=False, turnover_floor=False, steal_foul_always_plus5=False)
# A log from before the step 3n rulings replays without them (nor the later ones).
PRE_3N = dict(steal_lock=False, reach_angle_fouls=False, **PRE_9NOV)
LEGACY_3I = dict(arrow_mode='single', screen_rule='two_turns', drive_rule='arrow_line', intercept_return=False,
                 intercept_rule='approach', turnover_cost='legacy', on_line_tolerance=0.5, lane_jump_keeps_facing=False,
                 receiver_denial=False)
# A log from before the rulebook revision of Nov 2026 (no on_line_tolerance / lane_jump_keeps_facing in its setup
# line) replays with the readings it was played under.
PRE_RULEBOOK = dict(on_line_tolerance=0.5, lane_jump_keeps_facing=False, receiver_denial=False)
# A log from before the receiver-denial ruling replays without it (a log recording the rulebook readings but not it).
PRE_DENIAL = dict(receiver_denial=False)
TURNOVER_COSTS = ('minus5_lose_phase', 'minus5', 'minus10', 'lose_phase', 'end_possession', 'legacy')
INTERCEPT_RULES = ('move_then_intercept', 'ring_jump', 'approach')

# D-151: the control rule's sizes, in rating steps: one size, for every shot type and for the Contest alike
CONTROL = {'off': 0, '0': 0, '1': 1, '2': 2, '3': 3}
CONTROL_APP = 2                      # D-153: the app's size
RUSH_QS, RUSH_SPRINT = 1, 2          # what left a player rushed (two bits a player in GameState.rush_o / rush_x)


def control_size(rules):
    """The control rule's size in play, in rating steps (0: the rule is off): the app's format plays size 2 by
    default (D-153), the table's rules none (D-146)."""
    if rules.control == 'app':
        return CONTROL_APP if rules.digital else 0
    return CONTROL[rules.control]


def control_cut(rules, shot_type=None):
    """The reduction a rushed shot, or a rushed Contest of it, takes under rules.control (0 when the rule is off)."""
    return control_size(rules)


DEFAULT_RULES = Rules()


def with_rules(**changes):
    """A copy of the default rules with some settings changed (intercept_cost is the old name of
    turnover_cost)."""
    if 'intercept_cost' in changes:
        changes = dict(changes)
        changes['turnover_cost'] = changes.pop('intercept_cost')
    return replace(DEFAULT_RULES, **changes)
