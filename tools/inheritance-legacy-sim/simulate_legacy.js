#!/usr/bin/env node
// Family Legacy campaign simulator.
//
// Runs the real campaign code (Inheritance.html, unmodified) in a headless
// browser and plays whole six-estate Legacies with scripted siblings, many
// times, then reports what the economy actually does. Nothing is
// reimplemented: every number comes from the game's own functions, and the
// siblings act only through the game's inputs and buttons.
//
// Usage:
//   node simulate_legacy.js --runs 50 --profile all --out results
//   node simulate_legacy.js --runs 5 --profile greedy --seed 7
//
// Profiles pair two sibling policies; see PROFILES below. The report answers:
//   - how often the lower-Property plot is the better choice across the Legacy, and by how much
//   - whether choosers took it, by policy
//   - income as a share of final wealth
//   - how often a sibling reaches an investment phase with no Capital
//   - how often a holding on the board survives the fence
//   - whether the family's wealth gap closed or widened over six estates
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const args = Object.fromEntries(process.argv.slice(2).map((a, i, all) => a.startsWith('--') ? [a.slice(2), all[i + 1] && !all[i + 1].startsWith('--') ? all[i + 1] : true] : []).filter(Boolean));
const RUNS = Number(args.runs || 20);
const SEED = Number(args.seed || 1);
const OUT = path.resolve(args.out || path.join(__dirname, 'results'));
const GAME_FILE = path.resolve(args.game || path.join(__dirname, '..', '..', 'Inheritance.html'));
const YEARS = Number(args.years || 5);   // years between estates; 5 reproduces the campaign's original payments
fs.mkdirSync(OUT, { recursive: true });

// A sibling policy: how they build, invest, cut, choose, and which role they want.
//   build:   random | cluster        (cluster: beside a productive partner when possible)
//   invest:  saver | spender | builder | developer
//   cut:     fairProperty | fairWealth | random   (straight fences; wealth counts holdings' payments)
//   choose:  greedy | aware | closer | random     (closer: takes the smaller plot when it costs 2 or less)
//   role:    cutter | chooser | random
//   steward: a wealth lead (Property plus Capital) at or above which the sibling deliberately loses the
//            estate to keep the family in check: as cutter, the most lopsided straight fence; as chooser,
//            the plot worth less across the Legacy. Below the lead they play their normal policy.
//   measured: with steward set, concede by about the size of the lead instead of the whole estate: as
//            cutter, the straight fence whose long-term gap is closest to the lead; as chooser, the smaller
//            plot only when the loss does not exceed the lead.
const P = (build, invest, cut, choose, role = 'random', steward = null, measured = false) => ({ build, invest, cut, choose, role, steward, measured });
const PROFILES = {
  greedy:   { a: P('random', 'spender', 'fairProperty', 'greedy'), b: P('random', 'spender', 'fairProperty', 'greedy') },
  aware:    { a: P('cluster', 'builder', 'fairProperty', 'aware'), b: P('cluster', 'builder', 'fairProperty', 'aware') },
  mixed:    { a: P('cluster', 'builder', 'fairProperty', 'aware'), b: P('random', 'spender', 'fairProperty', 'greedy') },
  savers:   { a: P('cluster', 'saver', 'fairProperty', 'aware'), b: P('cluster', 'saver', 'fairProperty', 'aware') },
  closer:   { a: P('cluster', 'builder', 'fairWealth', 'closer'), b: P('cluster', 'builder', 'fairWealth', 'closer') },
  chaos:    { a: P('random', 'developer', 'random', 'random'), b: P('random', 'developer', 'random', 'random') },
  // Keeping the family in check: both siblings concede the estate once ahead by the given lead.
  steward10: { a: P('cluster', 'builder', 'fairProperty', 'aware', 'random', 10), b: P('cluster', 'builder', 'fairProperty', 'aware', 'random', 10) },
  steward0:  { a: P('cluster', 'builder', 'fairProperty', 'aware', 'random', 0), b: P('cluster', 'builder', 'fairProperty', 'aware', 'random', 0) },
  // One steward against one greedy sibling.
  stewardVsGreedy: { a: P('cluster', 'builder', 'fairProperty', 'aware', 'random', 10), b: P('random', 'spender', 'fairProperty', 'greedy') },
  // Measured stewards: concede by about the lead, not the whole estate.
  measured10: { a: P('cluster', 'builder', 'fairProperty', 'aware', 'random', 10, true), b: P('cluster', 'builder', 'fairProperty', 'aware', 'random', 10, true) },
  measured0:  { a: P('cluster', 'builder', 'fairProperty', 'aware', 'random', 1, true), b: P('cluster', 'builder', 'fairProperty', 'aware', 'random', 1, true) },
  measuredVsGreedy: { a: P('cluster', 'builder', 'fairProperty', 'aware', 'random', 10, true), b: P('random', 'spender', 'fairProperty', 'greedy') },
};
const chosenProfiles = args.profile && args.profile !== 'all' ? String(args.profile).split(',') : Object.keys(PROFILES);

// Everything below `IN_PAGE` runs inside the game page.
const IN_PAGE = async ({ profile, runIndex, seed }) => {
  const rng = makeRng((seed * 1000003 + runIndex * 7919) >>> 0);
  const pick = list => list[Math.floor(rng() * list.length)];
  const key = p => `${p.c},${p.r}`;
  const log = { profile, runIndex, estates: [], investPhases: [], errors: [] };

  // Speed: drawing is not part of the rules.
  RENDER.render = () => {};
  RENDER.renderSnapshot = () => {};
  window.confirm = () => true;
  try { localStorage.removeItem('inheritance.familyLegacy.current'); localStorage.removeItem('inheritance.familyLegacy.foundation.v1'); } catch (e) {}

  const campaignState = () => { LEGACY.save(); return JSON.parse(localStorage.getItem('inheritance.familyLegacy.current')).campaign; };
  const clickButton = sel => { const b = document.querySelector(sel); if (!b || b.disabled || b.hidden) return false; b.click(); return true; };
  const policyOf = idx => (idx === 0 ? profile.a : profile.b);
  const productiveKeys = new Set(LEGACY.PRODUCTIVITY.productiveKeys);
  const productiveLink = (kind, other) => (CONFIG.BETTER_TOGETHER[kind] || []).some(rel => productiveKeys.has(rel.key) && rel.with.includes(other))
    || (CONFIG.BETTER_TOGETHER[other] || []).some(rel => productiveKeys.has(rel.key) && rel.with.includes(kind));
  const buildable = () => GAME.activeCells(STATE.estateMask).filter(p => GAME.isBuildableCell(p.c, p.r, STATE.grid, STATE.terrain, STATE.estateMask));
  const neighbours = p => [{ c: p.c + 1, r: p.r }, { c: p.c - 1, r: p.r }, { c: p.c, r: p.r + 1 }, { c: p.c, r: p.r - 1 }].filter(n => GAME.isActiveCell(n.c, n.r, STATE.estateMask));
  const placeFor = (kind, how) => {
    const spots = buildable();
    if (!spots.length) return null;
    if (how === 'cluster') {
      const good = spots.filter(p => neighbours(p).some(n => GAME.isAssetKind(STATE.grid[n.r][n.c]) && productiveLink(kind, STATE.grid[n.r][n.c])));
      if (good.length) return pick(good);
    }
    return pick(spots);
  };
  // Long-term value of a plot: Property plus every payment its holdings would make.
  const plotValue = (cells, devs) => {
    const property = GAME.scorePlot(cells, STATE.grid, STATE.settings.betterTogether, STATE.terrain, STATE.estateMask).total;
    const groups = LEGACY.findProductiveGroups(cells, STATE.grid);
    let income = groups.reduce((sum, g) => sum + g.income * (g.permanent === false ? g.remainingPayments : 3), 0);
    const inPlot = new Set(cells.map(key));
    for (const dev of devs || []) if (dev.placed && dev.cells.length && dev.cells.every(c => inPlot.has(key(c)))) income += dev.income * dev.payments;
    return { property, income, total: property + income, groups: groups.length };
  };

  let guard = 0, estateStart = null;
  UI.closeAllOverlays();
  FLOW.resetToSetup();
  UI.el.inputP1.value = 'Ada'; UI.el.inputP2.value = 'Ben';
  LEGACY.newCampaign();
  const started = performance.now();
  while (guard++ < 4000) {
    const top = UI.topOverlayKey();
    const phase = STATE.phase;
    if (top === 'legacyOverlay') {
      const c = campaignState();
      if (c.status === 'complete') break;
      if (c.status === 'unresolved') { log.unresolved = true; break; }
      if (clickButton('[data-legacy="next"]')) continue;
      if (clickButton('[data-legacy="continue"]')) continue;
      if (clickButton('[data-legacy="close"]')) continue;
      log.errors.push('legacy overlay stuck'); break;
    }
    if (top === 'legacyInvestOverlay') {
      if (clickButton('[data-legacy="beginFirstEstate"]')) continue;
      if (clickButton('[data-legacy="beginFamilyHomeChoice"]')) continue;
      const c = campaignState();
      const turn = c.current.investmentTurn;
      if (!c.current.investmentComplete && document.querySelector('[data-legacy="finishInvesting"]')) {
        const me = policyOf(turn);
        const round = c.round;
        const phaseRec = log.investPhases.find(x => x.round === round) || (() => { const x = { round, capital: c.players.map(p => p.capital), skipped: c.players.map(p => p.capital <= 0), bought: [[], []] }; log.investPhases.push(x); return x; })();
        const enabledAssets = () => [...document.querySelectorAll('[data-legacy-buy-asset]')].filter(b => !b.disabled).map(b => ({ kind: b.dataset.legacyBuyAsset, cost: CONFIG.ASSET_VALUE[b.dataset.legacyBuyAsset] || 0, el: b }));
        const enabledDevs = () => [...document.querySelectorAll('[data-legacy-buy-development]')].filter(b => !b.disabled).map(b => ({ type: b.dataset.legacyBuyDevelopment, el: b }));
        let bought = 0;
        if (me.invest !== 'saver') {
          for (let i = 0; i < 6; i++) {
            const assets = enabledAssets(), devs = enabledDevs();
            if (!assets.length && !devs.length) break;
            let choice = null;
            if (me.invest === 'developer' && devs.length) { devs[0].el.click(); phaseRec.bought[turn].push(devs[0].type); bought++; continue; }
            if (me.invest === 'spender') choice = assets.sort((x, y) => y.cost - x.cost)[0];
            else if (me.invest === 'builder' || me.invest === 'developer') {
              const onBoard = GAME.activeCells(STATE.estateMask).map(p => STATE.grid[p.r][p.c]).filter(k => GAME.isAssetKind(k));
              const attachable = assets.filter(a => onBoard.some(k => productiveLink(a.kind, k)));
              const productive = assets.filter(a => (CONFIG.BETTER_TOGETHER[a.kind] || []).some(rel => productiveKeys.has(rel.key)));
              choice = (attachable.length ? attachable : productive).sort((x, y) => y.cost - x.cost)[0] || null;
            }
            if (!choice) break;
            choice.el.click(); phaseRec.bought[turn].push(choice.kind); bought++;
          }
        }
        clickButton('[data-legacy="finishInvesting"]');
        continue;
      }
      if (clickButton('[data-legacy="finishInvesting"]')) continue;
      log.errors.push('invest overlay stuck'); break;
    }
    if (top === 'rpsOverlay') {
      if (document.querySelector('#rpsP1Btn') && !UI.el.rpsWinnerButtons.hidden) { (rng() < 0.5 ? UI.el.rpsP1Btn : UI.el.rpsP2Btn).click(); continue; }
      if (!UI.el.rpsRoleButtons.hidden) { const w = STATE.rpsWinnerIdx; const pref = policyOf(w).role; const role = pref === 'random' ? (rng() < 0.5 ? 'cutter' : 'chooser') : pref; (role === 'cutter' ? UI.el.rpsCutBtn : UI.el.rpsChooseBtn).click(); continue; }
    }
    if (top === 'passOverlay') { UI.el.passContinueBtn.click(); continue; }
    if (top === 'tutorialOverlay') { UI.el.tutorialPrimaryBtn.click(); continue; }
    if (top === 'legacyFacesOverlay') {
      // A face from the estate's result for whoever is being asked: ahead by 3 or more delighted, ahead content,
      // level flat, behind upset, behind by 3 or more angry. Scripted feeling, so the record strip has data.
      const c = campaignState();
      const asked = document.getElementById('legacyFacesTitle').textContent.trim();
      const idx = c.players.findIndex(p => p.name === asked);
      const picker = STATE.choiceActor === 'cutter' ? STATE.cutterIdx : STATE.chooserIdx;
      const mine = (idx === picker) === (STATE.chosenPlotId === 'A') ? STATE.outcome.scoreA.total : STATE.outcome.scoreB.total;
      const theirs = STATE.outcome.scoreA.total + STATE.outcome.scoreB.total - mine;
      const d = mine - theirs, face = d >= 3 ? 4 : d > 0 ? 3 : d === 0 ? 2 : d > -3 ? 1 : 0;
      if (!clickButton(`[data-legacy-face="${face}"]`)) { log.errors.push('faces overlay stuck'); break; }
      continue;
    }
    if (top === 'revealOverlay') { ESTATE_REVIEW.finishReveal(); continue; }
    if (top === 'meaningfulOverlay') { FLOW.confirmMeaningfulDefault(); continue; }
    if (top === 'finalOverlay') {
      const c = campaignState();
      const rec = estateStart || {};
      rec.round = c.round;
      rec.scores = [STATE.outcome.scoreA.total, STATE.outcome.scoreB.total];
      rec.chosenPlotId = STATE.chosenPlotId; rec.chooserIdx = STATE.chooserIdx; rec.cutterIdx = STATE.cutterIdx;
      rec.groupsAfterCut = LEGACY.findProductiveGroups(STATE.plotA, STATE.grid).length + LEGACY.findProductiveGroups(STATE.plotB, STATE.grid).length;
      log.estates.push(rec); estateStart = null;
      document.getElementById('legacyRecordBtn').click();
      continue;
    }
    if (top) { log.errors.push(`unknown overlay ${top}`); break; }

    if (phase === 'terrain') {
      const kind = STATE.terrainPool[0];
      const spots = GAME.activeCells(STATE.estateMask).filter(p => GAME.canPlaceTerrain(kind, p.c, p.r, STATE.grid, STATE.terrain, STATE.estateMask));
      if (spots.length) INPUT.terrainCell(pick(spots)); else FLOW.endTerrain();
      continue;
    }
    if (phase === 'build') {
      const c = campaignState();
      const sel = c.current.buildSelection;
      if (c.current.investmentComplete && sel && sel.source === 'development') {
        const kind = sel.kind === 'quarry' ? 'X' : 'L';
        const used = new Set(c.current.developments.filter(d => d.placed).flatMap(d => d.cells.map(key)));
        const free = GAME.activeCells(STATE.estateMask).filter(p => STATE.grid[p.r][p.c] === kind && !used.has(key(p)));
        const adj = (a, b) => Math.abs(a.c - b.c) + Math.abs(a.r - b.r) === 1;
        let placed = false;
        if (sel.kind === 'quarry') { outer: for (const a of free) for (const b of free) if (adj(a, b)) { INPUT.buildCell(a); INPUT.buildCell(b); placed = true; break outer; } }
        else { outer2: for (const a of free) for (const b of free) for (const d of free) if (a !== b && b !== d && a !== d && adj(a, b) && (adj(b, d) || adj(a, d))) { INPUT.buildCell(a); INPUT.buildCell(b); INPUT.buildCell(d); placed = true; break outer2; } }
        if (!placed) { log.errors.push(`no site for ${sel.kind} r${c.round}`); FLOW.endBuild(); }
        continue;
      }
      const kind = sel && sel.source !== 'ordinary' ? sel.kind : STATE.pool[0];
      const spot = placeFor(kind, policyOf(STATE.turn).build);
      if (!spot) { FLOW.endBuild(); continue; }
      INPUT.buildCell(spot);
      continue;
    }
    if (phase === 'meaningful') {
      const assets = GAME.activeCells(STATE.estateMask).filter(p => GAME.isAssetKind(STATE.grid[p.r][p.c]));
      if (assets.length) INPUT.meaningfulCell(pick(assets)); else FLOW.skipMeaningful();
      continue;
    }
    if (phase === 'cut') {
      const c = campaignState();
      const devs = c.current.developments;
      estateStart = { groupsBeforeCut: LEGACY.findProductiveGroups(GAME.activeCells(STATE.estateMask), STATE.grid).length, capitalBefore: c.players.map(p => p.capital), propertyBefore: c.players.map(p => p.property) };
      const me = policyOf(STATE.cutterIdx);
      const fences = COMPUTER.straightFences().map(f => { const split = GAME.validateCut(f.edges, STATE.estateMask); const a = plotValue(split.plotA, devs), b = plotValue(split.plotB, devs); return { ...f, wealthGap: Math.abs(a.total - b.total) }; });
      const leadOf = idx => (c.players[idx].property + c.players[idx].capital) - (c.players[1 - idx].property + c.players[1 - idx].capital);
      const conceding = me.steward !== null && me.steward !== undefined && leadOf(STATE.cutterIdx) >= me.steward;
      let fence = null;
      if (conceding && me.measured) { const lead = leadOf(STATE.cutterIdx); fence = fences.sort((x, y) => Math.abs(x.wealthGap - lead) - Math.abs(y.wealthGap - lead))[0]; estateStart.cutterConceded = true; }
      else if (conceding) { fence = fences.sort((x, y) => y.wealthGap - x.wealthGap)[0]; estateStart.cutterConceded = true; }
      else if (me.cut === 'random') fence = pick(fences);
      else if (me.cut === 'fairWealth') fence = fences.sort((x, y) => x.wealthGap - y.wealthGap || x.gap - y.gap)[0];
      else fence = fences.sort((x, y) => x.gap - y.gap || x.wealthGap - y.wealthGap)[0];
      const nodes = fence ? COMPUTER.nodePath(fence.edges) : null;
      if (nodes) nodes.forEach(n => INPUT.cutNode(n)); else FLOW.bankCut();
      continue;
    }
    if (phase === 'choose') {
      const c = campaignState();
      const devs = c.current.developments;
      const a = plotValue(STATE.plotA, devs), b = plotValue(STATE.plotB, devs);
      const me = policyOf(STATE.chooserIdx);
      const propertyBetter = a.property === b.property ? null : (a.property > b.property ? 'A' : 'B');
      const longTermBetter = a.total === b.total ? null : (a.total > b.total ? 'A' : 'B');
      const bites = propertyBetter && longTermBetter && propertyBetter !== longTermBetter;
      let choice;
      const lead = (c.players[STATE.chooserIdx].property + c.players[STATE.chooserIdx].capital) - (c.players[1 - STATE.chooserIdx].property + c.players[1 - STATE.chooserIdx].capital);
      const conceding = me.steward !== null && me.steward !== undefined && lead >= me.steward;
      if (conceding && me.measured) { const smaller = a.total <= b.total ? 'A' : 'B'; const loss = Math.abs(a.total - b.total); choice = loss <= lead ? smaller : (longTermBetter || propertyBetter || 'A'); }
      else if (conceding) choice = a.total <= b.total ? 'A' : 'B';
      else if (me.choose === 'random') choice = rng() < 0.5 ? 'A' : 'B';
      else if (me.choose === 'aware') choice = longTermBetter || propertyBetter || 'A';
      else if (me.choose === 'closer') {
        // Takes the smaller plot when that costs 2 or less and the sibling is behind.
        const meIdx = STATE.chooserIdx, other = 1 - meIdx;
        const behind = c.players[other].property + c.players[other].capital < c.players[meIdx].property + c.players[meIdx].capital;
        const smaller = a.total <= b.total ? 'A' : 'B';
        choice = behind && Math.abs(a.total - b.total) <= 2 ? smaller : (longTermBetter || propertyBetter || 'A');
      } else choice = propertyBetter || 'A';
      Object.assign(estateStart || (estateStart = {}), {
        plotA: a, plotB: b, propertyGapOfCut: Math.abs(a.property - b.property), bites: !!bites, biteMagnitude: bites ? Math.abs(a.total - b.total) : 0,
        propertyBetter, longTermBetter, choice, tookLongTermBetter: longTermBetter ? choice === longTermBetter : null, tookSmallerProperty: propertyBetter ? choice !== propertyBetter : false,
        chooserConceded: conceding,
      });
      FLOW.completeChoice(choice);
      continue;
    }
    if (phase === 'final' && !top) { UI.open('finalOverlay'); continue; }
    log.errors.push(`stuck in ${phase}`); break;
  }
  const c = campaignState();
  log.seconds = Math.round((performance.now() - started) / 100) / 10;
  log.status = c.status;
  log.players = c.players.map(p => ({ name: p.name, property: p.property, capital: p.capital, holdings: p.holdings.length }));
  log.history = c.history.map(h => ({ round: h.round, scores: h.scores, winner: h.winner, capitalAfter: h.capitalAfter, income: (h.incomePayments || []).reduce((s, x) => s + x.amount, 0), holdingsAwarded: (h.holdingsAwarded || []).map(g => g.length), invested: h.investedBy }));
  log.finalResult = c.finalResult ? c.finalResult.players.map(p => ({ property: p.property, capital: p.capital, futureIncome: p.scheduledIncome, projected: p.projected })) : null;
  log.totals = c.totals;
  try { log.save = localStorage.getItem('inheritance.familyLegacy.current'); } catch (e) { log.save = null; }
  // What could have been, by the game's own ledger (the fairest fence per estate is solved in the background; wait for it).
  await LEGACY.ensureFairestGaps();
  const w = LEGACY.couldHaveBeen();
  log.couldHaveBeen = { total: w.total, gap: w.gap, potential: w.potential, lost: w.lost, losses: w.losses,
    estates: w.estates.map(e => ({ round: e.round, fence: e.fence, dividedLost: e.dividedLost, unspentLost: e.unspentLost, fenceGap: e.fenceGap, fairestGap: e.fairest ? e.fairest.gap : null, chosenSmaller: e.chosenSmaller, gapAfter: e.gapAfter })) };
  return log;
};

// ---- Aggregation ---------------------------------------------------------------
function summarise(profileName, runs) {
  const ok = runs.filter(r => r.status === 'complete');
  const estates = ok.flatMap(r => r.estates);
  const decisions = estates.filter(e => e.propertyBetter !== undefined);
  const bites = decisions.filter(e => e.bites);
  const mean = xs => xs.length ? xs.reduce((a, b) => a + b, 0) / xs.length : 0;
  const pct = (n, d) => d ? Math.round(100 * n / d) : 0;
  const incomeShare = ok.map(r => { const wealth = r.finalResult.reduce((s, p) => s + p.projected, 0); const paid = r.history.reduce((s, h) => s + h.income, 0) + r.finalResult.reduce((s, p) => s + p.futureIncome, 0); return wealth ? paid / wealth : 0; });
  const gapAfter1 = ok.map(r => Math.abs(r.history[0].scores[0] - r.history[0].scores[1]));
  const finalGap = ok.map(r => Math.abs(r.finalResult[0].projected - r.finalResult[1].projected));
  const arcs = ok.map(r => { const g1 = Math.abs((r.history[0].scores[0] + r.history[0].capitalAfter[0]) - (r.history[0].scores[1] + r.history[0].capitalAfter[1])); const g6 = Math.abs(r.finalResult[0].projected - r.finalResult[1].projected); return g6 - g1 >= 3 ? 'widened' : g1 - g6 >= 3 ? 'closed' : 'steady'; });
  const investPhases = ok.flatMap(r => r.investPhases);
  const skipped = investPhases.flatMap(p => p.skipped);
  const groupsBefore = estates.map(e => e.groupsBeforeCut || 0), groupsAfter = estates.map(e => e.groupsAfterCut || 0);
  return {
    profile: profileName, runs: runs.length, completed: ok.length, errors: runs.flatMap(r => r.errors).slice(0, 10), secondsPerRun: mean(ok.map(r => r.seconds)),
    choice: {
      decisions: decisions.length,
      lowerPropertyPlotWasBetter: { count: bites.length, pct: pct(bites.length, decisions.length), meanMargin: mean(bites.map(e => e.biteMagnitude)), maxMargin: Math.max(0, ...bites.map(e => e.biteMagnitude)) },
      chooserTookLongTermBetter: pct(decisions.filter(e => e.tookLongTermBetter === true).length, decisions.filter(e => e.tookLongTermBetter !== null).length),
      chooserTookSmallerProperty: pct(decisions.filter(e => e.tookSmallerProperty).length, decisions.length),
      meanPropertyGapOfCut: mean(decisions.map(e => e.propertyGapOfCut)),
      estatesConceded: pct(estates.filter(e => e.cutterConceded || e.chooserConceded).length, estates.length),
    },
    income: { shareOfFinalWealth: mean(incomeShare), meanTotalPaidPerCampaign: mean(ok.map(r => r.history.reduce((s, h) => s + h.income, 0))), meanFutureIncome: mean(ok.map(r => r.finalResult.reduce((s, p) => s + p.futureIncome, 0))) },
    investment: { phases: investPhases.length, siblingSkippedForNoCapital: pct(skipped.filter(Boolean).length, skipped.length), purchasesPerCampaign: mean(ok.map(r => r.investPhases.reduce((s, p) => s + p.bought[0].length + p.bought[1].length, 0))), capitalSpentPerCampaign: mean(ok.map(r => r.totals.invested)) },
    holdings: { groupsOnBoardBeforeCut: mean(groupsBefore), groupsSurvivingCut: mean(groupsAfter), survivalPct: pct(groupsAfter.reduce((a, b) => a + b, 0), groupsBefore.reduce((a, b) => a + b, 0)), holdingsPerSiblingAtEnd: mean(ok.flatMap(r => r.players.map(p => p.holdings))) },
    gap: { meanWealthGapAfterEstate1: mean(gapAfter1), meanFinalWealthGap: mean(finalGap), arcs: { closed: pct(arcs.filter(a => a === 'closed').length, arcs.length), steady: pct(arcs.filter(a => a === 'steady').length, arcs.length), widened: pct(arcs.filter(a => a === 'widened').length, arcs.length) } },
    couldHaveBeen: (() => {
      const ws = ok.map(r => r.couldHaveBeen).filter(Boolean), es = ws.flatMap(w => w.estates), known = es.filter(e => e.fairestGap !== null);
      return {
        meanFamilyWealth: mean(ws.map(w => w.total)), meanCouldHaveHeld: mean(ws.map(w => w.potential)), meanLost: mean(ws.map(w => w.lost)),
        lostPctOfPotential: pct(ws.reduce((s, w) => s + w.lost, 0), ws.reduce((s, w) => s + w.potential, 0)),
        losses: { fence: mean(ws.map(w => w.losses.fence)), holdingsDivided: mean(ws.map(w => w.losses.divided)), lostEstates: mean(ws.map(w => w.losses.lostEstates)), unspent: mean(ws.map(w => w.losses.unspent)) },
        fairestKnownPct: pct(known.length, es.length), meanFairestGap: mean(known.map(e => e.fairestGap)), meanFenceGap: mean(known.map(e => e.fenceGap)),
        fenceAtFairestPct: pct(known.filter(e => e.fenceGap === e.fairestGap).length, known.length),
      };
    })(),
    wealth: { meanFinal: mean(ok.flatMap(r => r.finalResult.map(p => p.projected))), meanProperty: mean(ok.flatMap(r => r.finalResult.map(p => p.property))), meanCapital: mean(ok.flatMap(r => r.finalResult.map(p => p.capital))), siblingAWinsPct: pct(ok.filter(r => r.finalResult[0].projected > r.finalResult[1].projected).length, ok.length), tiesPct: pct(ok.filter(r => r.finalResult[0].projected === r.finalResult[1].projected).length, ok.length) },
  };
}

function markdown(summaries) {
  const r1 = x => Math.round(x * 10) / 10;
  const lines = ['# Family Legacy simulator results', '', `${summaries.reduce((s, x) => s + x.completed, 0)} completed campaigns across ${summaries.length} profiles, played by the real game code with scripted siblings. Generated by tools/inheritance-legacy-sim/simulate_legacy.js.`, ''];
  lines.push('| Profile | Runs | Lower-Property plot was better | Mean margin when it was | Choosers took long-term better | Took smaller plot | Income share of final wealth | Skipped invest turn (no Capital) | Holdings surviving the cut | Gap closed / steady / widened | Mean final gap | Sibling A wins | Estates conceded |');
  lines.push('|---|---|---|---|---|---|---|---|---|---|---|---|---|');
  for (const s of summaries) {
    lines.push(`| ${s.profile} | ${s.completed} | ${s.choice.lowerPropertyPlotWasBetter.pct}% of ${s.choice.decisions} | ${r1(s.choice.lowerPropertyPlotWasBetter.meanMargin)} (max ${s.choice.lowerPropertyPlotWasBetter.maxMargin}) | ${s.choice.chooserTookLongTermBetter}% | ${s.choice.chooserTookSmallerProperty}% | ${Math.round(s.income.shareOfFinalWealth * 100)}% | ${s.investment.siblingSkippedForNoCapital}% | ${s.holdings.survivalPct}% | ${s.gap.arcs.closed} / ${s.gap.arcs.steady} / ${s.gap.arcs.widened} | ${r1(s.gap.meanFinalWealthGap)} | ${s.wealth.siblingAWinsPct}% | ${s.choice.estatesConceded}% |`);
  }
  lines.push('', '## What could have been', '', 'Family wealth is both siblings\' final wealth together. "Could have held" adds back the four losses the game can account for: Property not inherited because of the fence, payments from holdings the fence divided, estates that left the family, and the best available purchase a sibling with Capital did not make. The fairest fence is the solver\'s smallest possible gap on that estate; "not available" estates are too large for the plot-by-plot search.', '');
  lines.push('| Profile | Family wealth | Could have held | Lost | Lost % | Fence | Holdings divided | Lost estates | Unspent Capital | Fairest known | Mean fairest gap | Mean fence gap | Fence at fairest |');
  lines.push('|---|---|---|---|---|---|---|---|---|---|---|---|---|');
  for (const s of summaries) {
    const c = s.couldHaveBeen;
    lines.push(`| ${s.profile} | ${r1(c.meanFamilyWealth)} | ${r1(c.meanCouldHaveHeld)} | ${r1(c.meanLost)} | ${c.lostPctOfPotential}% | ${r1(c.losses.fence)} | ${r1(c.losses.holdingsDivided)} | ${r1(c.losses.lostEstates)} | ${r1(c.losses.unspent)} | ${c.fairestKnownPct}% | ${r1(c.meanFairestGap)} | ${r1(c.meanFenceGap)} | ${c.fenceAtFairestPct}% |`);
  }
  lines.push('', '## Per profile', '');
  for (const s of summaries) {
    lines.push(`### ${s.profile}`, '', '```', JSON.stringify(s, null, 1), '```', '');
  }
  return lines.join('\n');
}

function makeRngSrc() {
  return `function makeRng(seed){let s=seed>>>0;return function(){s=(s+0x6D2B79F5)>>>0;let t=s;t=Math.imul(t^(t>>>15),t|1);t^=t+Math.imul(t^(t>>>7),t|61);return((t^(t>>>14))>>>0)/4294967296;};}`;
}

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 600, height: 900 } });
  page.on('dialog', d => d.accept());
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  await page.goto('file://' + GAME_FILE + '?legacy=open&years=' + YEARS);
  await page.waitForTimeout(300);
  await page.evaluate(makeRngSrc());
  const all = [];
  const summaries = [];
  for (const name of chosenProfiles) {
    const profile = PROFILES[name];
    if (!profile) { console.error(`unknown profile ${name}`); continue; }
    const runs = [];
    const t0 = Date.now();
    for (let i = 0; i < RUNS; i++) {
      const log = await page.evaluate(IN_PAGE, { profile, runIndex: i, seed: SEED });
      runs.push(log);
      if ((i + 1) % 5 === 0 || i === RUNS - 1) console.log(`${name}: ${i + 1}/${RUNS} (${((Date.now() - t0) / 1000).toFixed(0)}s)${log.errors.length ? ' errors: ' + log.errors.join('; ') : ''}`);
    }
    all.push(...runs);
    summaries.push(summarise(YEARS === 5 ? name : `${name} @ ${YEARS}y`, runs));
  }
  const tag = YEARS === 5 ? '' : `-${YEARS}y`;
  const keep = all.find(r => r.status === 'complete' && r.save);
  if (keep) fs.writeFileSync(path.join(OUT, `save${tag}.json`), keep.save);
  all.forEach(r => { delete r.save; });
  fs.writeFileSync(path.join(OUT, `runs${tag}.json`), JSON.stringify(all));
  fs.writeFileSync(path.join(OUT, `summary${tag}.json`), JSON.stringify(summaries, null, 1));
  fs.writeFileSync(path.join(OUT, `RESULTS${tag}.md`), markdown(summaries));
  console.log(markdown(summaries).split('\n').slice(0, 6 + summaries.length).join('\n'));
  if (errors.length) console.log('page errors:', errors.slice(0, 5));
  await browser.close();
})().catch(e => { console.error(e); process.exit(1); });
