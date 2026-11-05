# Inheritance: the aesthetic, asset and animation pass

The brief: decide between 2D, 2.5D and 3D; audit the assets for adequacy and size; and find the line between legibility and engagement in animation. Every call below is made against the design hierarchy (1 System Fidelity, 2 Neutrality, 3 Player Agency, 4 Legibility, 5 Accessibility): a lower tier may bend to a higher one, never break it.

## Where the game stands

| Fact | Now |
|---|---|
| Delivery | One HTML file, 855 KB raw, 189 KB gzipped. No build step, no image files. |
| Board | HTML canvas, 600 internal units, drawn at device pixel ratio up to 3. A 7×7 irregular estate shows at 390 px wide on a phone: 35 px per square on the live board, 25 px in the example on the welcome screen. |
| Pieces | 13 asset kinds, each a line icon drawn in code on a coloured disc, with a printed value badge. Zero bytes of image. Crisp at any pixel density. |
| Terrain | Flat fills: grass bands by value, water with ripple strokes, roads with a dashed centre line, rock and woodland glyphs. |
| Type | Fraunces (display and body), Caveat (hand notes), JetBrains Mono (numbers), from Google Fonts with system fallbacks. |
| Animation | Almost none on the board. Button transitions, a timer bar, a stamp on achievements, the red "loss arrives" scale-in on the consequence board, the replay's fence draw. One requestAnimationFrame loop, for the clock. |
| Style | Paper and ink: a surveyor's plan with hand annotations in the UI; a flatter, greener board that does not yet match it. |

## The decision: 2D, with weight

**Stay top-down 2D.** The game is adjacency, a fence drawn along grid lines, and a printed number on every square. Those three things are unambiguous only from directly above.

- **Legibility (4) breaks under 2.5D.** An isometric view puts tall pieces in front of the squares behind them, turns "beside" into a diagonal judgment, and makes drawing the fence with a thumb on a phone a harder motor task than it is today. The Cut phase is timed; nothing may make it harder to see where the line runs.
- **Neutrality (2) breaks under 3D.** A rendered manor that towers over a barn tells the player it is worth more before the number does. The badge is the value. A flat icon beside a flat badge keeps the number in charge.
- **Fidelity (1) gains nothing.** No rule depends on height, perspective or light.
- **Accessibility (5) and delivery.** One file, no WebGL, no asset pipeline, works on the phones people already have. 3D costs that for nothing the system needs.
- **The origin.** This was a table game. The table view is the face-to-face game.

**With weight** means the pieces and the land get the depth of a well-made board: a soft drop shadow under each disc, an inked edge on the fence, a hand-drawn texture on terrain, a paper board that matches the paper UI. The camera never moves.

## Assets: adequate, and what to improve

The icons in code are the right technology: vector, weightless, sharp at 3× density. Keep that. Three things to improve, in order of what they do for legibility:

1. **Silhouettes.** At 35 px, Barn and Stables, Workshop and Mill, Crops and Garden read as the same thing. Each kind needs one shape nobody mistakes at 24 px: a barn's gambrel roof, a horse's head over a stable door, a mill's sails, a hammer and anvil, rows for crops, a trellis for the vineyard, a round canopy for the orchard. Keep the two-tone rule (dark ink on light discs, light ink on dark) and the printed badge exactly as it is.
2. **One source, two surfaces.** Move the icons to an inline SVG symbol set and draw them on the canvas through `Path2D`. The same path then appears in the legend, the rules, the Legacy's catalogue and the chapter cards, so a Vineyard looks the same everywhere. Cost: about 1 to 2 KB per icon, 20 to 30 KB in all, inside the file. Raster sprites at 3× would cost 150 to 300 KB, blur on zoom, and need a pipeline. Not raster.
3. **The board as paper.** The UI is paper and ink; the board is a green grid. Give the land a paper tone with a hatch fill by value band (so the four values read as texture as well as colour, which helps colour-blind players and the Accessibility tier), ink the perimeter and fence like pen, letter the plot labels in Caveat like the notes around them, and keep water and roads as they are. The land value badges and the legend stay.

Not in scope: a new palette. The current palette passed its contrast checks and is the game's identity.

Budget: the file stays under 1 MB raw and 230 KB gzipped after all three.

## Animation: the ladder, and where legibility stops it

The rule for every animation: it must mean something the system just did, it must finish before the next decision, and it must never move a number that is not yet final. Every one respects `prefers-reduced-motion`.

| Moment | Animation | What it tells the player | Limit |
|---|---|---|---|
| **Place a piece** | The disc drops in (scale 1.15 → 1, 120 ms, shadow tightens). Any square whose value changed shows a small "+1" rising from it for 500 ms. | Where the piece landed, and that Better Together just paid. Teaches the neighbour rule without a sentence. | Only during Build. Nothing rises during Cut. |
| **Draw the fence** | Posts appear as you drag (as now). On commit the line thickens to ink in 200 ms, and gates swing open where it crosses a road. | The fence is final; roads stay open. | No motion while the Cut clock runs except the line itself. |
| **Choose** | The chosen plot brightens and the other dims, 200 ms. Then each plot's total counts up from 0 to its value over 400 ms. | Which plot is whose, and how the sum forms. Counting up is the one "engagement" animation that is also a legibility aid. | Totals only count after the choice; never before. |
| **Consequences** | Lost-value squares arrive red one at a time (as now), each with its reason. | Where the fence cost value. | As now. |
| **Legacy: the record** | A business pulses once when it pays and its "+N Capital" rises into the sibling's column. The gap strip draws left to right; the faces pop in. | What paid whom, and the arc. | 600 ms total. |
| **Ambient life** | Water ripples drift (1 px, 0.3 Hz). Crops and vines sway (1 px). Mill sails turn slowly. Smoke from the manor's chimney, three faint curls. | Nothing. This is the only animation that exists for engagement alone: the estate feels alive while you think. | Never on a badge, a plot boundary or a fence. Pauses while the Cut clock runs. Off under reduced motion. |

What is deliberately absent: camera moves, confetti, slow fades on overlays, and anything that plays while a timer is counting and a hand is drawing.

## The build order

Stage 3 shipped: ambient life at about twelve frames a second on the live board only. Water ripples drift and swell by a pixel or two; wheat, vines and the orchard crown sway a few hundredths of a radian about their base; the mill's sails turn slowly; the manor and cottage chimneys give three faint puffs. It never touches a badge, a plot boundary or a fence; it stops while the Cut clock runs, whenever an overlay is open, when the page is hidden, and under reduced motion; snapshots and legends are always the still drawing.

Stage 2 shipped: the renderer notices each event by comparing the live state with the previous frame, so human, bank, online and Legacy moves animate the same way with no hooks in the flows. A placed disc drops in over 180 ms (larger, higher, a looser shadow, then settled); a neighbour whose badge rose shows a "+1" rising for 650 ms, during Build only; the fence inks from 3.5 to 6 px over 320 ms as it becomes final and its gates appear with it; the chosen plot brightens and the other settles back over 260 ms; the final totals count up over 420 ms and end exact. The Legacy record's payment rows rise in sequence, the "+N Capital" pulses once, the gap strip draws left to right and the faces pop. All off under reduced motion; no number moves before it is final.

Stage 1 shipped: the thirteen silhouettes redrawn as path data drawn through Path2D on the canvas and emitted as inline SVG for HTML (the Legacy catalogue shows the piece it sells); a soft shadow under every disc; the board on paper with stippled land whose density follows the value band; plot labels in the hand font. Checked at 22, 26, 36, 48 and 68 px on a phone and a desktop. File size unchanged within a kilobyte.

1. **Icons and the paper board.** New silhouettes as one SVG symbol set, drawn through `Path2D`; hatch fills by value; ink perimeter and fence; Caveat plot labels. Screenshot every asset at 24, 35 and 68 px before shipping.
2. **Event animations.** Place, fence commit with gates, choose with the count-up, the Legacy record's payments and strip.
3. **Ambient life.** Water, crops, mill, chimney. Paused during Cut; off under reduced motion.

Each stage ships on its own and is checked on a 390 px phone and a desktop, with the existing test scripts and the simulator run afterwards.
