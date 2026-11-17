// Step 19, stage 6 (Shaun, 17 Nov 2026): watch the computer play the computer.
//
//   "I would also like to restore the option for computer to play computer so that I can see how they set up, see
//   how they play, and audit the reports I download for insights to improve the computer systems."
//
//   The server plays both sides as the computer always does (the computer by side, ai {O, X}); this page steps
//   through what it played: the setup first, as its own step, with one line on what each side was planning (from the
//   map), then every action, at the speed chosen. Play and pause, one turn at a time, slow, normal or fast, the
//   coverage view, and each possession's report to download. The batch plays N possessions without showing them and
//   downloads all their reports and one data file. No engine setting is changed: it plays with the computer's
//   defaults and the report says which switches were on.
'use strict';
window.PMWatch = (function () {
  let playing = true, speed = 'normal', timer = null;
  const DELAY = { slow: 2600, normal: 1300, fast: 450 };
  const setupShown = {};
  function live() { return replay ? replay.live : st; }
  function on() { const s = live(); return !!(s && s.ai && s.ai.O && s.ai.X); }
  function clear() { if (timer) { clearTimeout(timer); timer = null; } }
  function later(fn, mult) { clear(); if (playing) timer = setTimeout(() => { timer = null; if (playing) fn(); }, DELAY[speed] * (mult || 1)); }
  // ---- the bar under the board --------------------------------------------------------------------------------
  function bar() {
    const box = $('watchBar'); if (!box) return;
    box.innerHTML = '';
    if (!on()) { box.classList.add('hidden'); return; }
    box.classList.remove('hidden');
    const s = live();
    const what = replay ? `Possession ${replay.entries[replay.k].possession}, phase ${replay.entries[replay.k].phase}, turn ${replay.entries[replay.k].turn}` : s && s.stage === 'over' ? `Possession ${s.possession} over` : 'Watching';
    box.append(el('p', { class: 'watchline', role: 'status', text: `${what}. ${playing ? 'Playing' : 'Paused'}, ${speed}.` }),
      el('div', { class: 'buttons' }, [
        el('button', { id: 'watchPlay', class: 'primary', 'aria-pressed': playing ? 'true' : 'false', text: playing ? 'Pause' : 'Play', onclick: () => { playing = !playing; if (!playing) clear(); bar(); kick(); } }),
        el('button', { id: 'watchTurn', text: 'Next turn', onclick: nextTurn, disabled: replay ? null : 'disabled' }),
        ...['slow', 'normal', 'fast'].map(sp => el('button', { class: 'small', 'aria-pressed': speed === sp ? 'true' : 'false', text: sp[0].toUpperCase() + sp.slice(1), onclick: () => { speed = sp; bar(); kick(); } })),
        el('button', { class: 'small', id: 'watchCov', 'aria-pressed': showCov() ? 'true' : 'false', text: showCov() ? 'Coverage: shown' : 'Coverage: hidden',
          onclick: () => { try { localStorage.setItem('pm_covmap', showCov() ? '0' : '1'); } catch (e) { /* ignore */ } covAsk = ''; render(); } }),
        s && s.possession ? el('button', { class: 'small', text: 'The report so far', onclick: () => showStory() }) : null]));
  }
  // ---- stepping: the step bar's OK, pressed for you at the chosen speed ----------------------------------------
  function onStep() { bar(); if (!on() || !replay) return; if (!$('modal').classList.contains('hidden')) return; later(() => { if (replay && $('modal').classList.contains('hidden')) stepOn(); }); }
  function kick() { if (!on()) return; if (replay) onStep(); }
  function nextTurn() {
    if (!replay) return;
    playing = false; clear();
    const e = replay.entries[replay.k], key = x => `${x.possession}:${x.phase}:${x.turn}`;
    while (replay && replay.k < replay.entries.length - 1 && key(replay.entries[replay.k + 1]) === key(e)) { replay.k += 1; }
    if (replay) stepOn();
    bar();
  }
  // ---- a phase's turn-by-turn view and the end of a possession: continue on their own while playing -----------
  function onModal(cont) { if (on()) later(() => { if (!$('modal').classList.contains('hidden')) cont(); }, 4); }
  function onEnd() {
    if (!on()) return;
    bar();
    const nxt = $('nextPoss'); if (!nxt) return;
    later(() => { const b = $('nextPoss'); if (b && !$('modal').classList.contains('hidden')) b.click(); }, 6);
  }
  // ---- the setup, as its own step, once a possession ----------------------------------------------------------
  async function maybeSetup(possession) {
    if (!on() || setupShown[possession]) return false;
    setupShown[possession] = true;
    let rep = null; try { rep = await api(`/api/report?code=${G.code}&possession=${possession}`); } catch (e) { return false; }
    if (!rep || !rep.setup) return false;
    const story = await api(`/api/story?code=${G.code}`);
    const dia = PM.phaseDiagram(st.zones, rep.setup.start, [], { title: `The setup, possession ${possession}`, subtitle: `${rep.teams[0]} v ${rep.teams[1]}`, arrowMode: story.arrow_mode });
    const done = () => { closeModal(); render(); kick(); };
    modal([el('h2', { text: `Possession ${possession}: the setup` }), el('div', { class: 'diagrambox' }, [dia]),
      rep.setup.offence ? el('p', { class: 'tline off', text: rep.setup.offence }) : null,
      rep.setup.defence ? el('p', { class: 'tline def', text: rep.setup.defence }) : null,
      el('div', { class: 'buttons' }, [el('button', { class: 'primary', id: 'setupGo', text: 'Tip off', onclick: done })])], done);
    later(() => { const b = $('setupGo'); if (b) b.click(); }, 3);
    return true;
  }
  // ---- the batch: N possessions without showing them, every report and one data file ----------------------------
  async function batch(n, body) {
    n = Math.max(1, Math.min(50, n));
    const box = $('batchOut'); if (box) box.innerHTML = '';
    const status = el('p', { role: 'status', class: 'note', text: `Playing possession 1 of ${n}…` });
    let stop = false;
    if (box) box.append(status, el('button', { text: 'Stop', onclick: () => { stop = true; } }));
    const reps = [], stories = [], games = [];
    let g = null, zones = null, left = 0;
    for (let k = 1; k <= n && !stop; k++) {
      if (!g || left === 0) {
        const per = 12;                                        // the longest digital match: 12 possessions each
        const r = await api('/api/new', Object.assign({}, body, { match_format: 'digital', per_side: per, full: true, seed: (body.seed || 1) + games.length }));
        g = { code: r.code, token: r.token }; games.push(g.code); left = per * 2;
        const s0 = await api(`/api/state?code=${g.code}&token=${g.token}`); zones = s0.zones;
      } else {
        await api('/api/next', { code: g.code, token: g.token });
      }
      const s = await api(`/api/state?code=${g.code}&token=${g.token}`);
      const rep = await api(`/api/report?code=${g.code}&possession=${s.possession}`);
      const story = await api(`/api/story?code=${g.code}`);
      reps.push(rep); stories.push({ story, zones, possession: s.possession });
      left -= 1;
      status.textContent = `Played ${k} of ${n}.`;
    }
    if (!reps.length) return;
    const data = { date: new Date().toISOString(), games, switches: reps[0].switches, possessions: reps.map((r, k) => ({ report: r, story: stories[k].story.phases.filter(p => p.possession === r.possession) })) };
    const save = (blob, name) => { const a = el('a', { href: URL.createObjectURL(blob), download: name }); document.body.append(a); a.click(); a.remove(); };
    const stamp = new Date().toISOString().slice(0, 10);
    save(new Blob([JSON.stringify(data, null, 1)], { type: 'application/json' }), `playmaker_watch_${reps.length}_possessions_${stamp}.json`);
    // every possession's report in one document: one section a possession
    const body2 = el('main', { class: 'reportdoc' }, [el('h1', { text: `Playmaker: the computer watched, ${reps.length} possessions` }),
      el('p', { class: 'note', text: `Played ${stamp}. Switches: ${JSON.stringify(reps[0].switches.eval)}; computer ${JSON.stringify(reps[0].switches.computer)}.` })]);
    for (const [k, rep] of reps.entries()) {
      body2.append(el('h2', { text: `Possession ${k + 1} (game ${rep.code}, possession ${rep.possession})` }));
      if (rep.setup && rep.setup.offence) body2.append(el('p', { class: 'tline off', text: rep.setup.offence }), el('p', { class: 'tline def', text: rep.setup.defence }));
      for (const t of rep.turns) body2.append(PMReport.turnBlock(stories[k].story, rep, t, stories[k].zones).el);
      for (const p of rep.phases) { const pb = PMReport.phaseBlock(p); if (pb) body2.append(pb); }
      const sb = PMReport.summaryBlock(rep.summary); if (sb) body2.append(sb);
    }
    save(new Blob([PMReport.page(body2, `Playmaker: ${reps.length} possessions watched`)], { type: 'text/html' }), `playmaker_watch_${reps.length}_possessions_${stamp}.html`);
    status.textContent = `Done: ${reps.length} possessions. The reports and the data file are downloading.`;
    if (box) box.querySelectorAll('button').forEach(x => x.remove());
  }
  return { on, bar, onStep, onModal, onEnd, maybeSetup, batch, kick, get playing() { return playing; } };
})();
