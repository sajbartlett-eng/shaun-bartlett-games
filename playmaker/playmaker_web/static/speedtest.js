// Step 13C: the hidden speed test (D-126). Open the play link with ?speedtest=1 and it runs, instead of the game,
// the exam's decisions at each level, in the default game and with coverage as a budget, on this device, and shows the
// times to paste back. It uses the app's own search (engine.js) in a worker; nothing in the normal game changes.
'use strict';
(function () {
  const params = new URLSearchParams(location.search);
  if (!params.get('speedtest')) return;
  window.PM_SPEEDTEST = true;                               // app.js and the Python loader stand down
  const LEVELS = [['rookie', 'Rookie'], ['starter', 'Starter'], ['allstar', 'All-Star']];
  const SETTINGS = [[false, 'The game as it is'], [true, 'With the new defence reading']];
  const LIMIT_S = 270;                                      // the whole test must stay under 5 minutes
  const el = (tag, text, style) => { const e = document.createElement(tag); if (text) e.textContent = text; if (style) e.style.cssText = style; return e; };
  const p90 = v => { const s = v.slice().sort((a, b) => a - b); return s[Math.floor(0.9 * (s.length - 1) + 0.5)]; };
  const median = v => { const s = v.slice().sort((a, b) => a - b), m = s.length >> 1; return s.length % 2 ? s[m] : (s[m - 1] + s[m]) / 2; };

  async function run() {
    const box = el('div', '', 'position:fixed;inset:0;z-index:99999;background:#fff;color:#111;overflow:auto;padding:16px;font:16px/1.4 system-ui,sans-serif');
    document.body.append(box);
    box.append(el('h2', 'Playmaker speed test'));
    const device = `${navigator.userAgent} | cores: ${navigator.hardwareConcurrency || '?'} | screen: ${screen.width}x${screen.height}`;
    box.append(el('p', device, 'font-size:12px;color:#555;word-break:break-all'));
    const status = el('p', 'Loading…'), bar = el('progress', '', 'width:100%;height:20px');
    bar.max = 1; bar.value = 0;
    const out = el('div'), copy = el('button', 'Copy results', 'font-size:18px;padding:10px 16px;margin:12px 0;display:none');
    box.append(status, bar, out, copy);
    let worker;
    try {
      const bundle = window.PM_BUNDLE || await (await fetch('engine_bundle.json')).json();
      const data = bundle.speedtest || await (await fetch('speedtest_positions.json')).json();
      const file = n => JSON.parse(bundle.files['playmaker_engine/data/' + n]);
      const driver = `
        self.onmessage = e => {
          const m = e.data;
          try {
            if (m.type === 'init') { self.PMEngine.init({ zones: m.zones, config: m.config, vcoarse: m.vcoarse }); postMessage({ type: 'ready' }); return; }
            self.PMEngine.setBudget(m.newReading);
            const o = self.PMEngine.search(m.req);
            postMessage({ type: 'done', reached: o.reached, seconds: o.seconds, at: o.depth_seconds });
          } catch (err) { postMessage({ type: 'error', error: String(err && err.stack || err) }); }
        };`;
      worker = new Worker(URL.createObjectURL(new Blob([bundle.engine_js + '\n' + driver], { type: 'text/javascript' })));
      const ask = msg => new Promise((res, rej) => { worker.onmessage = e => (e.data.type === 'error' ? rej(new Error(e.data.error)) : res(e.data)); worker.postMessage(msg); });
      await ask({ type: 'init', zones: file('court_zones.json'), config: file('ai_profiles.json'), vcoarse: file('vcoarse.json') });
      const search = (pos, level, newReading, onClock) => {
        const prof = data.profiles[level];
        return ask({ type: 'run', newReading, req: { state: pos.state, ctx: data.contexts[pos.ctx], profile: prof, stale: null,
          budget: onClock ? prof.time_budget_s : null, max_depth: onClock ? prof.depth[1] : 2 } });
      };
      // how fast is this device? one decision, twice (the first warms the engine); then all 22 decisions, or the 8
      let all = data.positions;
      const cap = parseInt(params.get('n') || '0', 10);    // ?n=2: a short run, for checking the page
      status.textContent = 'Checking this device…';
      await search(all[0], 'allstar', false, false);
      const probe = (await search(all[0], 'allstar', false, false)).seconds;
      const perDecision = 2 * (2.2 * probe / 0.6 + 3.6);    // both settings: three levels with no limit, then on the clock
      let note = `All ${all.length} exam decisions.`;
      if (all.length * perDecision > LIMIT_S || params.get('short')) {       // ?short=1: the slower device's path, for checking
        all = all.filter(p => p.short);
        note = `This device is slower, so the test uses ${all.length} of the ${data.positions.length} exam decisions (boards 2, 7, 9, 10 and 16) to finish in under 5 minutes.`;
      }
      if (cap > 0) { all = all.slice(0, cap); note = `A short run: ${all.length} decisions only.`; }
      box.insertBefore(el('p', note, 'font-weight:600'), status);
      const total = SETTINGS.length * LEVELS.length * all.length * 2;
      let done = 0;
      const t0 = performance.now(), rows = [];
      for (const [newReading, settingName] of SETTINGS) {
        for (const [level, levelName] of LEVELS) {
          const pair = [], reached = [];
          for (const onClock of [false, true]) {
            for (const pos of all) {
              status.textContent = `${settingName}, ${levelName}: ${onClock ? 'on the clock' : 'timing one pair of turns'} (${done + 1} of ${total})`;
              const r = await search(pos, level, newReading, onClock);
              if (onClock) reached.push(r.reached);
              else { const two = (r.at || []).find(x => x[0] === 2); pair.push(two ? two[1] : r.seconds); }
              bar.value = ++done / total;
            }
          }
          rows.push({ setting: settingName, level: levelName, budget: data.profiles[level].time_budget_s, pair90: p90(pair), pairMedian: median(pair),
            finished: reached.filter(d => d >= 2).length, of: reached.length, turns: median(reached) });
        }
      }
      const took = Math.round((performance.now() - t0) / 1000);
      status.textContent = `Finished in ${took} seconds.`;
      const table = el('table', '', 'border-collapse:collapse;margin-top:8px;font-size:14px');
      const line = (cells, head) => { const tr = el('tr'); for (const c of cells) tr.append(el(head ? 'th' : 'td', String(c), 'border:1px solid #999;padding:4px 6px;text-align:left')); table.append(tr); };
      line(['Setting', 'Level', 'Time for one pair of turns, 9 in 10 (s)', 'Finished one pair in its time', 'Team turns ahead in its time (middle)'], true);
      const text = ['Playmaker speed test', new Date().toISOString(), device, note, `Took ${took} s`, ''];
      for (const r of rows) {
        line([r.setting, r.level, r.pair90.toFixed(2), `${r.finished} of ${r.of} (${r.budget} s)`, r.turns]);
        text.push(`${r.setting} | ${r.level} | one pair 9-in-10 ${r.pair90.toFixed(2)} s (middle ${r.pairMedian.toFixed(2)} s) | finished one pair ${r.finished} of ${r.of} in ${r.budget} s | team turns ahead ${r.turns}`);
      }
      out.append(table);
      const area = el('textarea', '', 'width:100%;height:140px;margin-top:12px;font:12px monospace');
      area.value = text.join('\n'); area.readOnly = true;
      out.append(area);
      copy.style.display = '';
      copy.onclick = async () => {
        try { await navigator.clipboard.writeText(area.value); } catch (e) { area.select(); document.execCommand('copy'); }
        copy.textContent = 'Copied';
      };
      window.PM_SPEEDTEST_DONE = rows;
    } catch (err) {
      status.textContent = 'The speed test could not run here: ' + (err && err.message || err) + ' It needs the playtest site (the play link), not the local server.';
      window.PM_SPEEDTEST_DONE = { error: String(err) };
    } finally { if (worker) worker.terminate(); }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run); else run();
})();
