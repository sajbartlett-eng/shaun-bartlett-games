// Step 19, stage 2 (Shaun, 17 Nov 2026): coaching and scouting in advantages; the numbers on tap.
//
//   By default every option shows its chance as a plain percentage and one short "why" in advantage words, the
//   cards read as words (the scout report's phrases, by the colour band), and the coach names the advantage. The
//   "Show the numbers" switch brings back the ratings and the "x versus y" lines. It is remembered for each player.
//   Every chance and every word comes from the server (advice.py): the engine's dice, the rules' pass chance, the
//   shot's value against the defence's best contest, and the bands on the cards.
'use strict';
window.PMAdvice = (function () {
  function who() {
    // the player whose choice this is: the human on the side to act, by his profile when the game knows it
    try {
      const pl = G && G.players, side = st && st.side_to_act;
      if (pl && side && st.attacker) { const letter = side === 'O' ? st.attacker : (st.attacker === 'A' ? 'B' : 'A'); const p = pl[letter]; if (p && p.profile) return p.profile; }
    } catch (e) { /* no game yet */ }
    return 'anyone';
  }
  function numbersOn() { try { return localStorage.getItem('pm_numbers:' + who()) === '1'; } catch (e) { return false; } }
  function setNumbers(on) { try { localStorage.setItem('pm_numbers:' + who(), on ? '1' : '0'); } catch (e) { /* private mode */ } }
  const pct = p => `${Math.round(p * 100)}%`;
  function chanceText(v) {
    if (!v) return '';
    if (v.value != null) return `worth ${v.value}${v.band ? ` (${v.band})` : ''}`;
    const bits = [];
    if (v.chance != null) bits.push(pct(v.chance));
    if (v.foul != null && v.foul > 0) bits.push(`foul risk ${pct(v.foul)}`);
    return bits.join(' · ');
  }
  // under each action in the list: "70% · Nobody can reach the passing lane."
  function brief(a) {
    const v = a.advice;
    const kids = [];
    const c = chanceText(v);
    if (c) kids.push(el('strong', { class: 'advchance', text: c }));
    if (v && v.why) kids.push(el('span', { class: 'advwhy', text: v.why }));
    if (numbersOn() && a.chips && a.chips.length) kids.push(el('span', { class: 'advnums', text: a.chips.join('; ') }));
    return kids.length ? el('span', { class: 'advbrief' }, kids) : null;
  }
  // the bar while an action waits for its confirm: the same, and the dice it will roll
  function detail(a) {
    const box = el('div', { class: 'advdetail' }, [brief(a)]);
    if (a.roll && a.roll.length) box.append(numbersOn() ? el('ul', {}, a.roll.map(t => el('li', { text: t.text })))
      : el('p', { class: 'note', text: a.roll.length > 1 ? 'It goes to the dice, twice.' : 'It goes to the dice.' }));
    return box;
  }
  // a card, folded: the player type and his strengths and weaknesses in words, coloured by band
  function cardWords(c) {
    const w = c.words; if (!w) return null;
    const bits = [];
    for (const t of w.plus) bits.push(el('span', { class: 'wplus', text: '▲ ' + t }));
    for (const t of w.minus) bits.push(el('span', { class: 'wminus', text: '▼ ' + t }));
    if (!bits.length) bits.push(el('span', { text: 'Average across the board: no edge to hunt, none to hide.' }));
    return el('div', { class: 'cardwords' }, [el('div', { class: 'tagline', text: w.tagline }), el('div', { class: 'wlist' }, bits)]);
  }
  // the matchup in words, both ways round
  function matchup(i) {
    const m = (st.advice || [])[i]; if (!m) return [];
    const out = [];
    for (const h of m.hunt) out.push(`Hunt: ${h} Get O${m.attacker + 1} the ball.`);
    for (const g of m.guard) out.push(`Defence edge: ${g}`);
    if (m.help) out.push(`Help: ${m.help}`);
    return out;
  }
  // Coach Vision (Learn level): the clearest advantage on the board, read for both sides in the same form, whoever
  // is to act. A selected player: his own matchup, both ways round.
  function coach(side, selected) {
    const ms = st.advice || []; if (!ms.length) return [];
    let pool = ms;
    if (selected != null) {
      const i = side === 'O' ? selected : ms.findIndex(m => m.defender === selected);
      if (i >= 0) pool = [ms[i]];
    }
    const carrier = (st.o.find(p => p.ball) || {}).i;
    const top = pool.slice().sort((a, b) => (b.hunt.length - a.hunt.length) || ((b.attacker === carrier) - (a.attacker === carrier))).find(m => m.hunt.length);
    const edge = pool.find(m => m.guard.length), help = pool.find(m => m.help);
    const off = top ? `Offence read: ${top.hunt[0]} Get O${top.attacker + 1} the ball.`
      : edge ? `Offence read: ${edge.guard[0]} Keep the ball away from that matchup.` : 'Offence read: no clear edge on the cards. Move the defence first: a cut or a screen that makes a defender choose.';
    const def = top ? `Defence read: keep an arrow on O${top.attacker + 1} before he catches it.` + (help ? ` ${help.help}` : '')
      : edge ? `Defence read: ${edge.guard[0]}` + (help ? ` ${help.help}` : '') : 'Defence read: no clear edge on the cards. Keep the shape: every lane answered, every arrow on a man.';
    return [off, def];
  }
  // a contest or forced-shot choice in words
  function choiceLabel(a) {
    const v = a.advice;
    if (a.kind === 'contest') {
      if (a.piece < 0) return "Don't contest";
      return `Contest with X${a.piece + 1}` + (a.clean ? ': clean, no foul risk' : v && v.foul != null ? `: foul risk ${pct(v.foul)}` : '');
    }
    if (a.kind === 'forced_shot') return `Forced shot: ${a.shot}` + (v && v.value != null ? `, worth ${v.value}` : '');
    return a.option || a.text;
  }
  return { numbersOn, setNumbers, brief, detail, cardWords, matchup, coach, choiceLabel, chanceText };
})();
