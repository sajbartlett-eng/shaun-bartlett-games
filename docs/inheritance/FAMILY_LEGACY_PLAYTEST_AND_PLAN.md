# Family Legacy: playtest and plan

A first-time playthrough of all six estates, read screen by screen, and a plan to make the campaign an experience worth the name. The plan is ordered by the design hierarchy: System Fidelity, Neutrality, Player Agency, Legibility, Accessibility. Lower tiers bend to higher ones and never break them.

Evidence: `legacy-playtest/playtest-log.txt` holds the text of every distinct screen in order, and the numbered screenshots beside it show the moments cited below.

## How it was played

Two named siblings, Ada and Ben, on a phone-sized screen, with the unlock open. The driver did only what a player can do: terrain tiles and pieces through the game's own input, buttons by clicking them, Rock Paper Scissors declared off screen, one purchase per investment turn when something was affordable, the cutter drawing the best straight fence, the chooser taking the higher plot. Every distinct screen was logged with its full text before the next action. The campaign ran to "Six estates recorded" with no errors.

What the run produced, as a baseline: Ada finished with 179 Property and 1 Capital, Ben with 193 and 8. Over six estates the family earned 21 Capital in holding income and spent 9. Final wealth was 182 to 205. Ada never had Capital at an investment phase.

## What the campaign is

Six estates. Cut and choose decides ownership as usual; inherited Property carries forward. Connected productive assets (a Barn beside Crops, two Orchards with a Beehive) form holdings that pay Capital to whoever inherits them intact, three times. Capital buys extra pieces or developments (Quarry, Logging) after Build and before roles, and purchases belong to whoever inherits their square. Options unlock as the most Capital a sibling has ever held rises. Estate 2 adds Meaningful Assets, Estate 5 adds resource sites, Estate 6 is the final settlement, and the ledger records shared gains, shared costs and individual distinctions.

The economy computed correctly throughout. Every number on every screen reconciled with the next. The problems are not in the arithmetic.

## What a first-time player sees

Findings are tagged by the tier they fall under: **F** fidelity, **N** neutrality, **A** agency, **L** legibility, **X** accessibility.

**1. "Start a new Legacy" drops you onto the terrain board.** No card names the estate, says what Family Legacy changes, or explains that you are about to shape water and roads together. The first words are "Ada is placing Water". The chapter's own description ("An old rural property. Before anything is built, the siblings shape its water and road access together.") exists in the code and only appears if you open the campaign menu mid-game. Screenshot 01. **L**

**2. The first real explanation arrives after Build.** "The Country Estate is built" is a good card: it shows the estate, names productive groups, and says there is no Capital yet. It is the right card, one phase too late. Screenshot 02. **L**

**3. Estate 1 ends with a holding, a payment and an unlock, each explained once in a table.** The between-estates screen is the strongest screen in the campaign: division, what changed, position, a box for the first holding payment. Screenshot 05. Two gaps: it says nothing about the sibling for whom nothing changed, and "About Estate 2" is collapsed, so the next chapter's new rule is read by nobody in a hurry. **L**

**4. A sibling with no Capital is skipped without a word.** From Estate 2 to Estate 6 the investment screen opened for Ben and never for Ada. Ada's device never said "you have no Capital; Ben is buying". The one line of narration about her was "Both siblings kept their Capital", which was not true in spirit. This is the system telling the truth (she had nothing to spend) while the interface hides the fact. **F, A, L**

**5. The investment screen is a catalogue, not a decision.** Thirteen cards with the identical sentence "Place later on an empty square · adds N Property before neighbour effects". The information a buyer needs (which purchase would join or complete a productive holding, what that holding would then pay, where it could be placed) is behind a collapsed "Inspect estate economics" panel and is not attached to any item. The real lever of the campaign is presented as a shop. Screenshot 03. **A, L**

**6. Purchases are placed before roles are known, and nobody says so.** This is the campaign's best idea: you spend Capital on an estate you may not inherit, under the same uncertainty as the Build. The copy admits it in the passive ("Paying for an addition does not mean you own it") after the fact. The moment of placement never states the stake. **A, L**

**7. The result screen is the ordinary result screen with a campaign bolted on.** Headline, division, "Property inherited: 65 of 81 theoretical maximum", a ceiling explainer, "Awards & achievements: No additional awards", then the Legacy section: who inherits, investment, holdings. The parts that matter for the campaign come last and the parts that matter least come first. Screenshot 04. **L**

**8. The "theoretical maximum" is not a system number.** Every result and the final ledger compare inherited Property to an "optimistic upper bound" that the copy itself says "some possible connections cannot coexist" with. A denominator that cannot be reached is a verdict dressed as a measurement. The real quantities are already on screen: built value before the fence, Property inherited, Property lost to the fence. **F, N**

**9. Holding cards are dense and partly unreadable.** "Grade C · 1 Capital after each estate" is set in monospace and overflows the card; "holding score 7: 5 from assets + 2 from productive links" is the scorer talking, not the game. Numbering restarts at 1 for each sibling. Screenshot 04. **L, X**

**10. Two primers never reach the player.** The resource primer for Estate 5 (quarries, logging, what a site is) is only in the collapsed next-chapter guide. The final-settlement primer for Estate 6 sits on the investment screen, which only a sibling with Capital sees. In this run Ada entered the last estate with no card telling her it was the last. **L**

**11. The final wealth table breaks on a phone.** Sibling names wrap one letter per line. Screenshot 06. **X**

**12. "Six estates recorded" is a good ending in the wrong order.** The ledger leads with the family total against the unreachable bound, then shared achievements, shared costs, individual distinctions, and only then "The family history", collapsed. The chronicle is the story; it should be the headline. Screenshot 07. **L**

**13. The campaign's central choice is real, and the chooser cannot see it.** The premise is that "the most valuable plot now may not be the best choice across the Legacy", and the run bears it out. In Estate 4 Ada chose Plot B at 36 Property; Plot A was 33 and carried two holdings, Working Farm and Connected Vineyard, each paying 1 Capital three times. Plot A was worth 39 across the Legacy against 36. The lower-Property plot was the better choice by 3 and the chooser took the other one. Nothing on the Choose screen told her: Property totals are rightly hidden, but which holdings each plot would carry, and what they pay, is structure on the board that the game already knows and shows only after the choice. With payments of 1, 2 or 3 Capital three times, a grade C holding outweighs a Property gap of up to 2, grade B up to 5, grade A up to 8, and a Quarry or Logging Operation 6. **F, A, L**

**14. A Legacy left during Estate 1's terrain shaping could not be resumed.** The autosave was written, "Resume autosave" was offered, and the loader rejected it as "not a valid current Family Legacy save", because the save validator assumed every pre-division save was in Build with investment complete, and Estate 1 opens with terrain shaping before Build. Found while testing the simulator; fixed in the same change (the validator now accepts terrain-phase saves) and verified by starting a Legacy, reloading the page, and resuming. **F, X**

What worked and should not be touched: the Meaningful Assets primer in Estate 2 (clear, placed at the right moment, and the story it produces is good), the between-estates "What changed" table, the position summary, "Paying does not mean you own it" as a rule, the save and backup flow, and the consequence replay, which ran correctly on every estate.

## The plan

### Tier 1: System Fidelity

**P1. Measure the economy to tune it, not to prove it. Done: see `LEGACY_SIMULATOR_RESULTS.md`.** Build a campaign simulator in the repository (the Playmaker solver programme is the model): seeded campaigns, scripted sibling policies (greedy chooser, holding-aware chooser, holding-builder, saver, spender), 200 runs. Report: how often the lower-Property plot is the better choice across the Legacy and by how much, income as a share of final wealth, how often a sibling reaches an investment phase with no Capital, how often a holding survives the fence, and how often the family closes its gap against how often it widens. The premise is confirmed by Estate 4 of the playtest; the numbers say how often the stakes bite and whether the payment schedule needs adjusting. Finding 13.

**P2. Replace the unreachable ceiling with real quantities.** On results and in the ledger: value before the fence, Property inherited, Property lost to the fence, Capital spent. Keep the bound only in the "how these values are calculated" explainer, labelled as a bound. When a true best-division referee exists for neighbour-scored estates it can return as "fairest possible"; until then nothing on screen should read as a target. Finding 8.

**P3. Account for every purchase.** After each estate, one line per purchase: what was paid, where it was placed, who inherited it, what Property it added, which holding it joined or formed and what that holding will pay. The ending's "7 inherited Property gained, of up to 11 possible" becomes the sum of lines the player has already read. Finding 5.

**P16. Show each plot's holdings at the moment of choice.** During Choose in Family Legacy, beside the board: "Plot A carries Working Farm and Connected Vineyard: 1 Capital each after this estate and two more. Plot B carries no holding." Property totals stay hidden, as they must; the holdings are visible structure the game already draws after the choice. This is the campaign's central decision made legible at the only moment it can be made. Finding 13.

**P4. Show the skipped turn.** When a sibling has no Capital at an investment phase, their screen says so, shows what the other sibling is buying as it happens, and states what their next unlock would cost. Finding 4.

### Tier 2: Neutrality

**P5. Strip verdict words.** "Optimistic", "theoretical maximum", "shortfalls", "but gained" give way to statements. Distinctions ("Wealthiest sibling", "Closest player-made cut") stay: they are records, not judgements. Findings 8 and 12.

### Tier 3: Player Agency

**P6. Make the investment screen a decision.** For each affordable item, the consequence on this board: "beside the Barn it would join Working Farm, score 7 to 9, grade C to B, 2 Capital per payment" or "no productive link on this estate; adds 2 Property wherever it stands". Developments show their sites on the board. The collapsed economics panel becomes the default view with the catalogue under it. Finding 5.

**P7. State the stake at placement.** The placement strip says "You are placing a Beehive you paid 1 Capital for. Roles are not decided yet. Whoever inherits this square owns it." Finding 6.

**P8. Give the Capital-less sibling a decision.** If P1 shows one sibling frequently shut out, consider a small floor: every sibling receives 1 Capital after each estate from the estate itself, so the investment phase is always a two-player phase. This is a rule change and belongs to the designer; the simulator says whether it is needed. Finding 4.

### Tier 4: Legibility

**P9. A chapter card at the start of every estate.** Name, character, what is new in the rules, what carries over, each sibling's position. The Training introduction pattern already exists and is the right shape. Estate 1's card also carries the campaign primer that currently arrives after Build. The next-chapter guide text moves here from the collapsed panel. Findings 1, 2, 3, 10.

**P10. Primers as phase cards, shown to both siblings.** Holdings (first payment), resources (Estate 5), final settlement (Estate 6) appear when the phase begins, on the board, for both players, not inside the investment screen of whoever has Capital. Finding 10.

**P11. A Legacy result screen.** Order: who inherited what; what changed for each sibling (Property, Capital, holdings, payments due), including "nothing changed" when that is true; purchases accounted (P3); then the ordinary breakdown behind a disclosure. The ordinary game's awards block and ceiling explainer do not appear in the campaign. Finding 7.

**P12. Holding cards in plain words.** "Working Farm: Barn and Crops. Grade C. Pays Ben 1 Capital after each of the next 3 estates." Grade thresholds and score arithmetic move to the rules. One running number per sibling, not a restart per sibling. Finding 9.

**P13. The chronicle as the ending.** "Six estates recorded" opens with the six-estate story, one estate per line, then the family totals in real quantities, then distinctions. Finding 12.

### Tier 5: Accessibility

**P14. Fix the two layout breaks.** The final wealth table (names wrapping letter by letter) and the holding card headings (monospace overflow). Findings 9, 11.

**P15. Pace the long screens.** The result and ending screens are long on a phone. The consequence replay's stepper is the proven pattern: one section at a time, Next, Skip to the end.

## The narrative engine

Family Legacy is a story that could be real: a competitive, stressful situation that leaves a family flourishing or broken, and what people remember afterwards is the story, not the ledger. Whether the disparity grew, or someone chose to close it. The game will not dictate actions. It will record how each sibling felt after each estate, on a scale of faces from angry to hysterical, and keep that beside the facts.

This changes the spine of the plan. The chronicle stops being the ending and becomes the thing every screen feeds.

**E1. The face prompt.** After "Record inheritance", each sibling picks one face (angry, upset, flat, content, delighted, hysterical). Faces only, no words: the ending paints the emotional journey from the faces beside the facts, and nobody is asked to write. Entered one at a time with the phone passed, or on each device across a distance. Skipping is allowed and recorded as a dash. Rules that keep it inside the hierarchy: no number ever changes because of a face; no copy ever comments on a face ("you seem angry"); no award or distinction is ever computed from faces; faces are shown exactly as recorded, by the sibling's name, nowhere else. The game records; it never reacts. Faces carry a text label for screen readers and never rely on colour alone.

**E2. The gap thread.** Every estate record carries the Property gap and the wealth gap between the siblings before and after, and the facts that moved them: the cut's gap and which plot it favoured, which plot the chooser took and by how much, whose purchases ended up in whose plot, income paid, Capital spent. Concessions are stated as facts ("Ada's fence favoured Plot B by 9; Ben took it", "Ben took the smaller plot, by 4"), never as generosity. Intentions are not guessed at; the acts are recorded, and a family reading six of them in a row knows what they meant.

**E3. The record screen.** After each estate, one screen replaces the between-estates "What changed" table: the facts of this estate in the family's own words (named assets from Meaningful Assets where they exist), the gap before and after, both faces, then position. It is the page of the family history being written, and it is what P11 becomes.

**E4. The chronicle as the ending, and as the thing you take away.** "Six estates recorded" opens with six lines, one per estate: estate name, what moved the gap, the gap after, the two faces. Then the totals in real quantities, then distinctions. The whole chronicle is downloadable as plain text and shareable as an image, separate from the backup file: a family record rather than a save.

**Recommended, and the designer's call.** Faces are entered privately and shown to both siblings immediately on the record screen. In a real family the unsaid feeling is the thing that breaks it, and a system about fairness between people should surface it. The alternative, hidden until the end, would test whether disclosure changes behaviour, and is a legitimate study design. Pick one deliberately.

**What this does to P1.** The simulator's question is how often the system produces each arc, families that close the gap and families that break open, and how often the choice between Property now and income later actually bites. Estate 4 of the playtest shows it does; the simulator says how often, so the payment schedule can be tuned for stakes that are felt in most campaigns, not some.

## After the simulator

Two runs so far, read in `LEGACY_SIMULATOR_RESULTS.md`. The first (600 campaigns, six profiles): the central choice exists in about one estate in five with deliberate play; income is at most a fifth of final wealth; an empty investment turn is common for naive pairs and rare for skilled ones; straight fences rarely break holdings; and the wealth gap widens in about three campaigns in four.

The designer then ruled: payments must be proportional to real yields with the years between estates as the only lever, and the gap is closed by play, not transfers. The second run (2,700 campaigns) measured both. Real yields put the campaign's existing payments at exactly five years per estate, so the game now carries the time scale as a stated rule (default five, every payment unchanged; ten doubles income and makes the central choice bite in about one estate in four). Deliberate losing keeps a family in check when it is measured to the lead, and oscillates when it is blunt; the rules already provide the levers, and the chooser needs P16 to use them well.

## Progress

- **Done:** P1 (simulator, two runs), E1 (faces after every estate, visible to both, faces only), E2 (the gap thread and concession facts), E3 (the record screen between estates), P16 (holdings visible at Choose and on the estate during Cut), P12 (holding cards in plain words), P2 and P5 on the campaign's own screens (the ceiling retired from the record screen and the ending; the ordinary game's ceiling and awards blocks hidden in the campaign), the two layout breaks in P14, the resume bug (finding 14), and the time scale as a stated rule. The next-chapter guide now opens by default on the record screen.
- **Done next:** P9 and P10 (a chapter card opens every estate for both siblings, naming it, stating what is new in rules, and showing what carries over; the resource and final-settlement primers live there), E4 and P13 (the family record is the headline of the ending: six lines with faces, the acts that moved the gap, the gap after each estate, final wealth; downloadable as text and shareable).
- **Done after that:** the investment screen as a decision (P6: each affordable piece says the best square for it, the holding it would form or raise, and what that would pay, or that it has no productive link here; the estate's holdings in one line above the catalogue; pieces that help listed first), P7 (the stake stated at purchase and at placement: roles are not decided yet, whoever inherits the square owns it), P4 (the sibling with no Capital is named on the screen both see, with the Capital at which their options open), P3 (every purchase accounted for on the record screen: paid, placed where, who inherited it, the Property it added, the holding it joined; developments intact or divided).
- **Done after that (E5, what could have been):** the ending now states what the family holds, the gap between the siblings, and what the family could have held, then where the difference went. Only four things reduce what a family holds; everything else moves wealth between the siblings. The four, each itemised by estate in the game's own numbers: Property built before a fence and not inherited; payments from holdings the fence divided (productive groups on the board before the cut against what was inherited intact, and developments cut in two); estates that left the family; and Capital a sibling held and did not spend, with the best purchase the game's own placement test found at the time and what it would have paid. A strip shows the gap after each estate with both faces beneath it. A table sets the fairest fence available against the fence drawn, estate by estate, with what the chooser took. Who took the larger plot is not on the list, and the section says so: choosing moves Property between siblings and changes nothing the family holds. Nouns and numbers only; nothing ranked, no verdict. Carried in the text record too.
- **Fixed on the way:** a fresh page starts on the base grid, and every saved Legacy board is the larger irregular grid. Validating a save on reload scored boundary roads on the wrong geometry, so a Legacy with any terrain estate recorded could not be resumed after the browser was closed. Saved boards are now read on their own geometry.
- **The lock retired (designer's call).** Family Legacy opens for any two named siblings. The setup checklist stays as a recommendation: the rules every estate uses, ticked per sibling as they play them, "recommended, not required". Onboarding lives inside the Legacy, where the chapter cards and first-time notes already are, and a switch on the Legacy panel turns them off for people who have been through it (on by default; off marks the notes not yet shown as seen and skips the remaining chapter cards; the rules, the record and the ending are unchanged).
- **Gates (fidelity).** A fence across a road has a gate, and the main road is public. Road access is never lost to a fence: a road reaches the outside through either plot, and land beside a road keeps its +1 whichever side the road lies. Water is unchanged: if the fence puts the shoreline in the other plot, the frontage is gone, as it is in life. The board draws a gate (a gap, two posts, a bar) where the fence crosses a road, and the main road simply carries on. Every rule line and training intro that said "cut off from the road" now says what is true.
- **Words.** "Holding" is gone from everything a player reads; it is a business: pieces that work together in the same plot, which pays its owner Capital. "Productive group" likewise. The rules panel opens with the story and a four-word glossary (Property, Business, Capital, Final wealth).
- **The story.** A prologue grounded in what is true of an estate without a will: equal shares under the law, a court-appointed administrator (the bank) that sets the deadlines, costs that mount while a house stands empty and tax falls due, agents writing with offers, a forced sale if nobody chooses in time. It opens the first chapter card, the Legacy panel and the rules. The six chapter blurbs carry the thread. No mechanic changed; the words now say what the mechanics already were.
- **The administrator speaks (P15, in a better form than the plan had).** The long blocks are gone from the campaign's screens. Mrs Hartley, the bank's administrator, opens every estate in person: a portrait, one line at a time at speech pace, tap to finish the line, tap to continue, Skip to end. Each estate arrives for a reason probate would produce: the farm's title is already clear; probate on the house clears; the working estate's tenant gives notice; the uncle's boundary claim on the waterside fails; the forestry survey of the uplands completes; the last title comes through. What carries over is one spoken line per sibling. The rules for each estate come one at a time. Now and then she takes a question ("Why can't we just split everything down the middle?"), and the reply changes only what she says next. She closes the Legacy with two lines before the record. The animate setting off makes each line appear whole. The in-screen primers are cut to a sentence or two.
- **Remaining from the plan:** P15 (pacing the long screens), P8 dropped, income size and gap-closing settled by the designer's rulings. The rest is play with people.

## Build order

1. **Instrument first (P1), with the arc question.** Done. P8 is dropped on its numbers; income size and the gap-closing lever are open decisions with a tool to test them.
2. **The record screen with faces and the gap thread (E1, E2, E3), absorbing P11, P12, P2 and P5, and holdings visible at Choose (P16).** The spine of the narrative engine, and cheap: a prompt, a table, the ceiling retired, and the central decision made visible.
3. **Cards and primers (P9, P10) and the layout fixes (P14).** So the story has a beginning and nobody meets a rule unannounced.
4. **The chronicle as the ending, downloadable and shareable (E4, P13, P15).**
5. **The investment screen (P6, P7, P4, P3).** The campaign's real lever, presented as one.
6. **Rule changes, if P1 says so (P8, income tuning).** Designer's call, with the simulator's numbers beside it.

## What this playthrough could not test

A single scripted run with simple policies. It did not exercise: a cutter who deliberately splits a holding, a sibling who saves for a Quarry and places it, the unresolved ending (nobody chooses in time), a loaded backup file, or two humans reading the screens at a table. The simulator in P1 covers the first two; the last needs people.
