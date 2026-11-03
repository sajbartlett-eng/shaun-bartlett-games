# Open questions

Every ruling the rules leave open is a named setting in `playmaker_engine/rules_config.py` (class `Rules`).
Changing a ruling is one line: `with_rules(setting=value)` or edit the default.
Items 1 to 12 come from the build prompt. Items 13 onward were found while building or reading the PDFs.
Section C lists where the reference PDFs and the prompt disagree.

**Designer rulings (3 Nov 2026).** Ruled and built: 5, 12, 16, 17, 20, 27, 32, C1, C4, plus a new rule,
the and-one (34). Confirmed as built: 1 to 4, 6, 8 to 11, 13 to 15, 18, 19, 21 to 26 and 28 to 31.
Item 33 follows from the and-one. Still open: 7 (see 38), re-tested by the solver at full budgets. Ruled in step 2b: 35. Closed in step 2b: 39. Rows marked **RULED**
show the ruling.

## A. Questions from the prompt

| # | Question | Default (setting) | Alternative | What it changes |
|---|---|---|---|---|
| 1 | Ball after an intercept or steal that "plays on" | Ball back to the passer (intercept) or stays with the carrier (steal), −5, play continues. `turnover_play_on='play_on'` | `'end'`: the possession ends | Whether a turnover is a setback or a full stop. The Offence tracker ("Fail: no pass, −5") and the rulebook score table ("−5, play on") both support the default. |
| 2 | When a pass resolves | On the defence's next turn. It may Intercept; if it does anything else, the pass lands at the start of that turn. `pass_resolution='defence_turn'` | `'immediate'`: lands at once unless an on-line defender is already there | Whether arrow-across defenders get a chance to close the lane. Under the default an inbound pass that lands mid-turn starts the new phase at once, so the defence's turn ends there. |
| 3 | Sprint length | Up to 3 + QS straight, 2 + QS diagonal. `sprint_orth_base=3`, `sprint_diag_base=2` | Any other base | Reach of fast players. |
| 4 | Roll bounds | Target ≥ 20 always succeeds, ≤ 0 always fails, no naturals. `natural_rolls=False` | `True`: natural 1 always succeeds, natural 20 always fails | Sure things (Pass 20 v Intercept 0) and hopeless rolls. |
| 5 | Negative value on a declared shot | **RULED: floor at 0**, matching the forced shot. `floor_declared_shot=True` | `False`: scores as negative | Otherwise declaring a bad shot could be worse than letting the clock run out. |
| 6 | Defence reaction to a declared shot | 0, 1 or 2 actions from tokens still in the pool: Move (incl. arrow turn), Quick Step, Sprint, Steal. Steal limits apply. Empty pool: only the contest. `reaction_kinds`, `reaction_may_decline=True` | Force at least one action; widen the kinds | How much a declared shot can be closed out. Declining is allowed because the contest is automatic and forcing a pointless move adds nothing. |
| 7 | Defence out of tokens while the offence has some | Phase ends at once, as written. `defence_empty_ends_phase=True` | `False`: the offence plays out its tokens | Whether the defence can "run out the phase" by spending fast. **Open: the solver will show whether the defence exploits it.** |
| 8 | Hesitate / Pause chaining | Each passes the turn and uses a token. Pause is illegal for the whole defence turn right after an offence turn that ended with Hesitate, and vice versa. `wait_chain_block=True` | `False`: no chaining limit | Stops wait-for-wait stalling. **Needs confirmation** of "straight after" = the whole following turn. |
| 9 | Screen geometry | A defender's diagonal step is banned if it starts on the T square, or cuts the T square's corner (T is one of the two squares the diagonal passes between). `screen_rule='from_t_or_corner'` | `'from_t_only'` | Exact squares are in `tests/test_movement.py::test_screen_t_square_exact_squares`: screener I6, T on I5. From I5 a Quick Step reaches only J5, I4, H5 (H4, J4, H6, J6 banned). From H5, I4 is banned (cuts T's corner); H6, I5, H4, G4, G5, G6 are open. |
| 10 | Arrow line crossing | Illegal only if the carrier's path goes from one side of the ray to the other (touching it, or stepping onto it and back, is fine). Checked over the whole path of one movement action. `arrow_line_strict=True` | `False`: stepping onto the ray at all counts | How hard an adjacent defender walls off a side. A carrier who ends one action on the line and leaves to the far side with the next is not caught (each action is checked on its own). |
| 11 | Move path order for 1 straight + 1 diagonal | Either order, if the middle square is empty. `move_either_order=True` | `False`: straight first (the old script) | Explains several regression differences (REGRESSION.md). |
| 12 | Contest choice | **RULED: the defence chooses any adjacent defender** (fix the rulebook's "nearest" wording, C1). The defence picks the adjacent defender, or nobody, with the lowest expected value, counting foul free throws. `contest_choice='min_value'` | `'nearest'`: the nearest adjacent defender (rulebook wording, see C1) | Note: under the default the defence sometimes prefers an arrow-off contest because free throws (2 × FT) are worth less than a great look. That is a real "foul the shooter" decision the rules allow. |

## B. New questions found while building

| # | Question | Default (setting) | Alternative | What it changes / source |
|---|---|---|---|---|
| 13 | When is a defender "on" the pass line? | Its square's centre lies within 0.5 of the segment, strictly between passer and receiver. `on_line_tolerance=0.5` | `0`: exact centre on the line (as `check_scenarios.py` uses for deny arrows); or any overlap with the square | How many squares can intercept directly. Prompt "Intercept"; Defence tracker "On the line: any arrow". |
| 14 | Quick Step length | Up to the card value (a QS-2 player may step 1). `qs_up_to=True` | Exactly the card value | Defence tracker "A burst set by the card: 2, 1 or 0 squares". |
| 15 | Sprint with Quick Step 0 | Not allowed. `sprint_needs_qs=True` | Allowed (it is then a straight Move that spends a Quick Step) | Only removes a dominated option. |
| 16 | Who may Challenge a screen | **RULED: only the defender standing on the screen's T square** (the one it blocks; covers the post seal). `challenge_who='on_t'` | `'adjacent'`: any defender next to the screener; `'any'` | Defence tracker "Name the screen you're fighting through". |
| 17 | Can a locked ball carrier Dribble? | **RULED: no.** A lost dribble means pass or shoot. `locked_can_dribble=False` | Yes | Offence tracker "Lose: you're locked, but can still pass or shoot" could be read as listing the only allowed ball actions. |
| 18 | How long a Dribble win frees the carrier from that arrow line | Rest of the phase (the defender's lock clears then too). Tied to that carrier: after a pass the new carrier is bound again. `dribble_win_lasts='phase'` | Until the carrier's next movement action | Offence tracker "Win: they're locked; you may cross their arrow line". |
| 19 | What the inbounder may do before the ball is in | Pass only (no Dribble, Screen or movement). `inbounder_pass_only=True` | Normal offence actions except movement | Scenario rules "It cannot move". Defenders may still Steal from an inbounder whose arrow is on it (normal Steal rule). |
| 20 | Can the far-contest −3 take a contest below 0? | **RULED: no, floor at 0.** A contest never makes a shot better. `floor_contest_zero=True` | Allow below 0 | Prompt "the contest is −3". |
| 21 | A side with tokens but no legal action | It forfeits its remaining tokens (defence: phase ends; offence: defence gets its final turn). `forfeit_when_stuck=True` | Pass the turn without a token | Rules are silent; needed so every game terminates. |
| 22 | Need a Three: free throws from a fouled two, and steal-foul free throws | Score 0 (only threes count). `three_only_ft_on_twos=False` | They count | Scenario rules "only a three-point shot scores". |
| 23 | Coach's Call: which band, and does a forced shot count? | Band of the look (shot value, or the free throws if fouled). A forced shot by the target counts. `coach_bonus_on_forced=True` | Band of the possession total; forced shots excluded | Scenario rules "add the bonus for how good the look was". |
| 24 | Which defenders bind the carrier's arrow line | Those adjacent at the start of the movement action. `arrow_line_adjacent_at='start'` | Adjacent at any point of the path | Prompt "adjacent defender". |
| 25 | "Up to 2 diagonal" | A straight diagonal line. `diag_move_straight=True` | Any two diagonal steps (e.g. NE then NW) | Trackers "or 2 diagonal". |
| 26 | Steal-foul free throws when no shot is declared | 2 × the ball carrier's FT rating. (engine behaviour) | — | Rulebook "Free throws score 2 × the shooter's FT rating" names a shooter; for a steal foul there is none. |
| 27 | Inbound not in after two phases: tie for "furthest from the rim" | **RULED: the offence chooses.** A new offence decision (`pick`) among the tied players. `inbound_tie='offence'` | `'lowest'`: lowest piece number | Scenario rules "offence picks if tied". The off-court inbounder is excluded. |
| 28 | Where the inbounder goes once the ball is in | It stays on its off-court square until it moves; its movement steps onto the court. It can receive a pass there but can't shoot (no zone). (engine behaviour) | Place it on the edge square automatically | Scenario rules "the inbounder may step onto the court". |
| 29 | Re-screening and screener movement | A screener can't Screen again until it flips back, and can't Quick Step or Sprint either ("can't move"). Screens survive the phase reset and flip back after the offence's next turn. (engine behaviour) | Allow a refreshed screen | Offence tracker "Can't move; flips back". |
| 30 | Forced-shot type | The offence's best shot type for that zone, against the defence's contest choice. (engine behaviour) | Offence picks explicitly | Rulebook "the ball carrier takes a forced shot". |
| 31 | Arrow-across defender who moved onto the line but then doesn't Intercept | Allowed: the pass then lands. (engine behaviour) | Must Intercept | Prompt "must first reach the segment". |
| 32 | Lock token supply | **RULED: no cap.** At most 2 Dribbles and 2 Challenges per phase means at most 4 new locks; Star Locked can reach 5 in phase 1, and the printed token sheet has a spare. | Cap at 4 | Rulebook p1 "4 lock tokens". |
| 33 | Two or Three with free throws | A fouled three with 30+ in foul points counts as an Excellent three (win). (engine behaviour) | Only made shot values count | Scenario rules "an Excellent three wins". |
| 34 | **New rule: the and-one** | **RULED.** Once a shot is declared, or forced at clock 0, any foul (a contest foul, or a Steal foul during the reaction) scores the **higher of the free throws and the shot's uncontested value** (points × rating). `and_one=True` | `False`: free throws only | Fouling a good look can never help the defence. Checked pair by pair: 0 of 39,375 offence × defence × shot-type pairings break it; without it, 10,725 do. A side-on closeout pays in 72.1% of pairings; see REGRESSION.md. Steal fouls before a shot is declared are unchanged. |

## C. Where the reference PDFs and the prompt disagree

None of these block the engine; each is a setting or a wording question for the designer.

1. **Who contests.** *Ruled: the defence chooses; change the rulebook wording.* `Playmaker_Rulebook.pdf` p1, "The shot": "Contest: the nearest defender's rating against it." p2, "Shooting": "Then the nearest defender contests." The prompt and both trackers (`Defence_tracker.pdf`, CONTEST: "Then one adjacent defender contests") let the defence choose among adjacent defenders. Default follows the prompt; `contest_choice='nearest'` follows the rulebook.
2. **Sprint and Quick Step.** `Defence_tracker.pdf` / `Offence_tracker.pdf`, SPRINT: "Uses that player's Move and Quick Step." The prompt says it "counts toward Quick Step" (the side's limit of 2). The tracker wording suggests a per-player Quick Step; the limit column says "×2 Sprints count" (per side). Engine: per side, as the prompt says.
3. **The adjacent defender on a pass.** `Defence_tracker.pdf`, INTERCEPT: "On the passer: only a pass through you." `Offence_tracker.pdf`, PASS: "Your defender: only their arrow counts." The two describe the same defender differently (arrow pointing at the passer vs. any defender of the passer). Engine follows the prompt's merge: an adjacent defender whose arrow points at the passer can only stop a pass through its own square; any other adjacent defender counts only if its arrow crosses the pass (and must move onto the line first).
4. **What a lock means.** *Ruled: change the rulebook to "can't Move or Sprint".* `Playmaker_Rulebook.pdf` p1, components: lock tokens "Mark a player who can't move this phase." The trackers (LOCKED) and the prompt allow Quick Step while locked. Engine follows the trackers.
5. **Plain wood name.** `Offence_tracker.pdf`, SHOT: "never from plain maple"; everywhere else "plain wood". Wording only.
6. **Scenario 10 card text** (`Playmaker_Scenarios.pdf`, Late Clock Reset): "Both Screens are spent: O4's is down, O5's is still up. Offence has 4 tokens left, defence 4." The prompt only says "tokens already spent and O5's screen standing". Engine uses the card's numbers (4 and 4, Screen limit used).

Nothing in the PDFs contradicts the prompt's numbers (6 tokens, 2-second phases, −3, −5, +5, bands, bonus ladder, roll rule, free throw multipliers).

## D. Found by the solver (step 2)

Evidence is in `SOLVER_REPORT.md` and `solver_results/runs.json`. Priority labels follow the designer's order
(System Fidelity > Neutrality > Player Agency > Legibility > Accessibility). No rule was changed.

| # | Finding | Evidence | Affects | Options for the designer |
|---|---|---|---|---|
| 35 | **RULED (step 2b): an inbound pass works like any other pass.** `inbound_resolves='after_defence_turn'`: the defence gets its normal turn (1 or 2 actions: Move then Intercept, Sprint then Intercept, or move two players) and the pass resolves after it; then the phase resets to the card's clock, offence first. Found: a completed inbound pass gave the receiver a free turn. Under OQ-2 the pass lands at the start of the defence's turn, and the scenario rules then reset to a new phase with the offence first. The defence's turn is skipped, so the receiver gets a Move and a Shot against only the reaction. | Baseline Box: the defence's best line is to let the pass land (End turn), then O1 Sprints and shoots: 36, a Gift. Two setup fixes only cut it to 30 (still a Gift). | Fidelity, Neutrality | (a) After the ball is in, the defence acts first in the new phase. (b) The inbound pass resolves at the end of the defence's turn instead of the start (OQ-2 alternative for inbounds only). (c) Keep it and accept that inbound plays are about the catch. |
| 36 | **Pause appears in 10 of 16 principal lines** (the defence's most-used action). | Rule health 2. Typically the defence answers a pass or a drive by doing nothing. | Fidelity (possibly a solver effect) | Partly a solver effect: the evaluation does not score defensive positioning beyond the next shot, so standing still costs nothing. Widen the evaluation before reading it as a rule problem. If it persists, Pause may be too cheap a way to make the offence commit. |
| 37 | **Challenge, defensive Sprint closeouts and deliberate fouls never appear.** Steal appears on 2 lines, Hesitate on 1. | Rule health 2 and 3. | Fidelity | Challenge: only the defender on the T square may Challenge (OQ-16), and the solver's lines rarely contain a standing screen. Sprint closeouts lose to Move-then-Quick-Step (arrow on, no foul roll), which matches the and-one design. No foul outcomes on any line. |
| 38 | **Still open (re-tested at full budgets in step 2b).** OQ-7 (defence's last token ends the phase): no measurable effect at step-2 budgets. | 16 cards re-solved with the phase running on: one value changed (Need a Three, 24 → 30), and that card swings between 24 and 30 across seeds anyway. No opening changed. | Neutrality | No evidence the defence burns tokens to end phases at this depth. Re-test at the full budgets. |
| 39 | **CLOSED (step 2b): keep as built.** Clock expiry never happens under best play. | Every principal line shoots inside the horizon. A forced shot from the cards' starting positions is worth 0 on 12 of 16 cards (the carrier starts on plain wood), 14 to 19 on the others. | Neutrality | Because forced shots are floored at 0, "forced shot or −5, whichever is worse" is always just −5: the alternative removes the forced shot. |
| 40 | **Verdicts move with the search budget.** | 9 of 16 cards are unstable between 90 s and 240 s (spreads up to 7.5 points; One Phase Left 18 → 21, Baseline Stack 12 → 19.5). | Legibility of the results | Treat verdicts as provisional until re-run at the default 2 and 10 minutes with 5 seeds. |

## E. Solver round 2 (step 2b)

| # | Finding | Evidence | Affects |
|---|---|---|---|
| 41 | **The one-turn evaluation was blind to defensive position.** It scored only the offence's next shot, so a defender standing still cost nothing (the Pause result). The evaluation now looks over the offence's next two turns against the defence's best reply. | Agreement with the exact endgame solver on 50 positions: mean error 5.38 → 0.61, within 2 points 46% → 92%. Positional terms (open lane to a shooter, carrier on a shooting zone) did not improve agreement (0.65, 1.30) and are off. | Fidelity of every solver result |
