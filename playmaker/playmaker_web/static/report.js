// Step 19, stage 3 (Shaun, 17 Nov 2026): the whiteboard turn by turn, the coach's assessments, the report to keep.
//
//   "Turn 1", "Turn 2": the offence's turn and the defence's answer, each on its own diagram, with one line for
//   what each team did. At the end of each phase the coach's assessment for both teams, leading into the next. At the
//   end of the possession the whole possession's, with the shot-quality breakdown. Download it as a report (one HTML
//   file that prints cleanly; print to PDF from the browser) and as a data file (JSON) with every number behind it.
//   Every line comes from the server (report.py): the coverage map and the strength measure, never a guess.
'use strict';
window.PMReport = (function () {
  async function load(possession, phase) {
    const q = `/api/report?code=${G.code}&possession=${possession}` + (phase ? `&phase=${phase}` : '');
    const [rep, story] = await Promise.all([api(q), api(`/api/story?code=${G.code}`)]);
    return { rep, story };
  }
  function entriesOf(story, possession, phase, turn) {
    const p = story.phases.find(x => x.possession === possession && x.phase === phase);
    return p ? p.entries.filter(e => e.turn === turn) : [];
  }
  function turnDiagram(story, rep, t) {
    const entries = entriesOf(story, rep.possession, t.phase, t.turn);
    return PM.phaseDiagram(st.zones, t.start, entries, { title: `Turn ${t.turn}`, subtitle: `Phase ${t.phase}`, arrowMode: story.arrow_mode });
  }
  function turnBlock(story, rep, t) {
    const dia = turnDiagram(story, rep, t);
    return { dia, el: el('section', { class: 'turnblock' }, [el('h3', { text: `Phase ${t.phase}, turn ${t.turn}` }), el('div', { class: 'diagrambox' }, [dia]),
      el('p', { class: 'tline off', text: t.offence }), el('p', { class: 'tline def', text: t.defence })]) };
  }
  function phaseBlock(pa) {
    if (!pa) return null;
    return el('section', { class: 'phaseassess' }, [el('h3', { text: `The coach on phase ${pa.phase}` }),
      pa.offence.length ? el('div', {}, [el('h4', { text: 'Offence' }), el('ul', {}, pa.offence.map(x => el('li', { text: x })))]) : null,
      pa.defence.length ? el('div', {}, [el('h4', { text: 'Defence' }), el('ul', {}, pa.defence.map(x => el('li', { text: x })))]) : null,
      pa.next ? el('p', { class: 'nextline', text: pa.next }) : null]);
  }
  function summaryBlock(sm) {
    if (!sm) return null;
    const lines = [sm.verdict, sm.shot, sm.score, sm.best, sm.trend].filter(Boolean);
    const side = (name, o) => (o.keep || o.change) ? el('div', {}, [el('h4', { text: name }), el('ul', {}, [o.keep, o.change].filter(Boolean).map(x => el('li', { text: x })))]) : null;
    return el('section', { class: 'possassess' }, [el('h3', { text: "The coach on the possession" }), el('ul', { class: 'assess' }, lines.map(x => el('li', { text: x }))),
      side('Offence', sm.offence), side('Defence', sm.defence)]);
  }
  // ---- the phase's turns, as the phase ends (replaces the one diagram of the whole phase) ----
  async function phaseView(due) {
    const { rep, story } = await load(due.possession, due.phase);
    const mine = rep.turns.filter(t => t.phase === due.phase);
    if (!mine.length) return null;
    const blocks = mine.map(t => turnBlock(story, rep, t));
    return { blocks, assess: phaseBlock(rep.phases.find(p => p.phase === due.phase)), rep };
  }
  // ---- the coach's assessment on the end screen ----
  async function endBlock(possession) {
    try {
      const { rep } = await load(possession);
      const box = el('div', { id: 'possAssess' }, [summaryBlock(rep.summary),
        el('div', { class: 'buttons' }, [el('button', { class: 'primary', id: 'dlReport', text: 'Download the report', onclick: () => download(possession, 'html') }),
          el('button', { id: 'dlData', text: 'Download the data (JSON)', onclick: () => download(possession, 'json') })])]);
      return box;
    } catch (e) { return null; }
  }
  // ---- the report to keep ----
  function cssText() {
    let out = '';
    for (const sh of document.styleSheets) { try { for (const r of sh.cssRules) out += r.cssText + '\n'; } catch (e) { /* another site's sheet */ } }
    return out;
  }
  function stamp() { return new Date().toISOString().slice(0, 10); }
  function fileName(possession, ext) { return `playmaker_${G.code}_possession${possession}_${stamp()}.${ext}`; }
  async function build(possession) {
    const { rep, story } = await load(possession);
    const body = el('main', { class: 'reportdoc' }, [el('h1', { text: `Playmaker: ${rep.teams[0]} v ${rep.teams[1]}` }),
      el('p', { class: 'note', text: `Game ${rep.code} · possession ${possession} · ${stamp()}. One diagram a turn: the offence's turn and the defence's answer, numbered in order. Black: offence. Red: defence.` })]);
    const phases = [...new Set(rep.turns.map(t => t.phase))];
    for (const ph of phases) {
      body.append(el('h2', { text: `Phase ${ph}` }));
      for (const t of rep.turns.filter(x => x.phase === ph)) body.append(turnBlock(story, rep, t).el);
      const pb = phaseBlock(rep.phases.find(p => p.phase === ph)); if (pb) body.append(pb);
    }
    const sb = summaryBlock(rep.summary); if (sb) body.append(sb);
    return { rep, story, body };
  }
  async function download(possession, kind) {
    try {
      const { rep, story, body } = await build(possession);
      let blob;
      if (kind === 'json') {
        const data = { game: G.code, possession, date: stamp(), teams: rep.teams, report: rep,
          story: story.phases.filter(p => p.possession === possession), scores: story.scores };
        blob = new Blob([JSON.stringify(data, null, 1)], { type: 'application/json' });
      } else {
        const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Playmaker report: game ${rep.code}, possession ${possession}</title><style>${cssText()}
body { background: #fff; font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; } .reportdoc { max-width: 860px; margin: 20px auto; padding: 0 16px; }
.turnblock, .phaseassess, .possassess { break-inside: avoid; page-break-inside: avoid; margin: 14px 0; }
@media print { body { background: #fff; font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Arial, sans-serif; } .reportdoc { margin: 0; } h2 { break-before: auto; } }
</style></head><body>${body.outerHTML}</body></html>`;
        blob = new Blob([html], { type: 'text/html' });
      }
      const a = el('a', { href: URL.createObjectURL(blob), download: fileName(possession, kind === 'json' ? 'json' : 'html') });
      document.body.append(a); a.click(); a.remove();
      announce(kind === 'json' ? 'The data file is downloading.' : 'The report is downloading.');
    } catch (e) { alert(e.message); }
  }
  return { phaseView, endBlock, download, build, summaryBlock, phaseBlock, turnBlock, load };
})();
