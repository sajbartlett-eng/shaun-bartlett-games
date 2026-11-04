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
    'X': {'qs': 2, 'intercept': 2, 'challenge': 2, 'steal': 2, 'pause': 1},
}
TURN_ENDERS = {'pass', 'screen', 'dribble', 'hesitate', 'shot',
               'intercept', 'challenge', 'steal', 'pause'}

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
    screen_rule: str = 'from_t_or_corner'
    # OQ-10: arrow line. A ball carrier move is illegal only if its path goes from one
    #   side of the ray to the other (touching or stepping onto the line is fine).
    arrow_line_strict: bool = True
    # OQ-11: a 1 straight + 1 diagonal Move may go in either order.
    move_either_order: bool = True
    # OQ-12 (ruled: the defence chooses any adjacent defender): contest choice.
    #   'min_value' : defence picks the adjacent defender (or none) that minimises the
    #                 expected shot value, counting foul free throws.
    #   'nearest'   : the nearest adjacent defender (rulebook wording), ties by min value.
    #   'player'    : (RULED, step 3b) the defence chooses: contest with any adjacent defender, or not.
    contest_choice: str = 'player'
    # ---- new questions found while building (OPEN_QUESTIONS.md 13+) ----
    # OQ-13: a square is 'on the pass line' if its centre lies within this distance of
    #   the segment (0.5 = the line goes through the middle half of the square;
    #   0 = exact centre, as check_scenarios.py does).
    on_line_tolerance: float = 0.5
    # OQ-14: Quick Step may be shorter than the card value (up to 2, not exactly 2).
    qs_up_to: bool = True
    # OQ-15: a player with Quick Step 0 cannot Sprint.
    sprint_needs_qs: bool = True
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


DEFAULT_RULES = Rules()


def with_rules(**changes):
    """A copy of the default rules with some settings changed."""
    return replace(DEFAULT_RULES, **changes)
