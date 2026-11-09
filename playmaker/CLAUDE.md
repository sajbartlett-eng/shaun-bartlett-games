# Working on Playmaker

Playmaker ("Open Your Eyes") is a two-player half-court basketball game played at the table and in the browser. Shaun is the designer. You build the app. The game's design is his; your job is to carry out exactly the step you are given, and to make what you find visible to him.

## Priority order

When anything conflicts, this order decides: System Fidelity (it plays like real basketball) > Neutrality (no side or level favoured by the system) > Player Agency (players' decisions matter) > Legibility (players can see why) > Accessibility.

## Scope

- Do only what the current step's prompt asks. Touch only the files it names or clearly implies.
- If something else looks wrong, do not fix it. List it in your report under "Noticed, not touched".
- Never delete a file unless the step says so. Move retired files to `archive/` instead.
- Work on the branch the step names, open a pull request, and do not merge it.

## Design choices are Shaun's

You never choose a design value. Design values include: any rule or rule setting, any card rating or level profile, any engine or trainer constant (`ai_profiles.json`, `CONFIG`, phase tables), any exam board or test target, and any words a player sees.

If a step can't be finished without one of these choices:

1. stop at that point;
2. list the options, each with its effect in plain words and any numbers you measured;
3. say which one, if any, the step's evidence favours, and why;
4. leave the current value in place.

Never mark a test as an expected failure, loosen a threshold, or restate a test so that it passes, unless the step says so. A failing test is a finding: report it.

## Two formats, one game

The tabletop game and the app share the rules, the dice and the penalties. Any change to a rule marked Shared in the rules register changes the printed game. Say so at the top of your report, with the printed pages it affects. Any difference between the formats must be deliberate, marked Split in the register, and approved by Shaun.

## Sources of truth

- The rules: the rulebook and trackers in `reference/`, and the rules register (`docs/rules_register.md`).
- Decisions: what Shaun has ruled, recorded in the repo. Until a decisions log exists, `OPEN_QUESTIONS.md`.
- Engine behaviour that no ruling covers is not a ruling. Flag it; don't build on it.

## Plain language

Anything a player sees uses plain basketball words: no internal names, codes or symbols. The banned-terms test must stay green. Reports to Shaun follow the same standard: plain words, short sentences, no em dashes.

## Tests

Don't run the test suite, self-play, the exam or any long job unless the step tells you to. Steps that only move, rename, archive or document things need no test run. Testing happens once, at the end of a group of steps, when a whole part of the game can be tested in its final state. The step that closes the group says so and names the tests.

If a step changes behaviour, you may run the few tests that cover exactly the code you changed, as long as they finish in a few minutes. Report what you ran and the result. If a change would need a long run to check, say so in the report instead of running it.

## The report

Every step ends with `docs/reports/STEPn_REPORT.md`, one page, in this order:

1. **Changes to the printed game:** "None", or what and which pages.
2. **What changed:** files and behaviour, in a few lines.
3. **What it proves:** tests and numbers, each with the file it comes from.
4. **For Shaun to decide:** each open choice, with its options and effects. "None" if there are none.
5. **Noticed, not touched:** anything else you saw.
