// Step 19, stage 5 (Shaun, 17 Nov 2026): learn by playing the first game.
//
//   Coach Vision teaches one idea at the moment it first matters, in this order: tap a player and move him; the arrow;
//   the pass; reading the colours; the shot and its value; the contest; the screen; the phase and the clock; the
//   coverage view. Each tip shows once, is short, can be dismissed, and can be switched off ("I know the rules").
//   The words follow the rules as the app plays them (the rule reminders in app.js and RULES_CURRENT.md).
//   The old course stays as "Rules, step by step" on the home screen.
'use strict';
window.PMTips = (function () {
  const mine = () => st && st.can_act && !replay && !st.placing;
  const hasAct = kind => (st.legal || []).some(a => a.kind === kind);
  const TIPS = [
    { id: 'setup', when: () => st && st.placing && st.placing.mine,
      text: 'First, set up your side. Tap a player, then tap his new square, or press "Computer sets up the offence" (or the defence), then Confirm.' },
    { id: 'move', when: () => mine() && st.side_to_act === 'O' && sel.side == null,
      text: 'Tap one of your players. The squares he can reach light up. Tap one, then tap it again to move him there.' },
    { id: 'arrow', when: () => mine() && sel.side != null,
      text: 'The red arrows on each X show where that defender faces. He guards best along his arrows: a clean contest, a steal, a jump into a passing lane.' },
    { id: 'pass', when: () => mine() && sel.side === 'O' && enderActs(sel.side, sel.i).some(a => a.kind === 'pass'),
      text: 'His passes are in the list under the board, each with its chance. A defender who can reach the passing lane can intercept it.' },
    { id: 'colours', when: () => st && st.turn_n === 0 && (st.feed || []).length >= 2,
      text: 'The cards in words: green is a strength, red a weakness. Your edge is a green strength against a red weakness. Tap a card for the numbers.' },
    { id: 'shot', when: () => mine() && sel.side === 'O' && enderActs(sel.side, sel.i).some(a => a.kind === 'shot'),
      text: 'A shot is never rolled. It is worth its points times the shooter\'s rating less the contest. Thirty or more is an Excellent look.' },
    { id: 'contest', when: () => st && st.can_act && ['reaction', 'contest'].includes(st.stage),
      text: 'The shot is up, or is it? The defence replies with 2 actions, and contesting or blocking is one of them: press Contest (never a foul) or Block (a turnover if it works, with the foul risk) with a defender next to the shooter, or it goes up open. If it was a fake, that reply was your turn, and going for the block locks him.' },
    { id: 'fake', when: () => st && st.can_act && st.stage === 'play' && st.side === 'O' && st.fake && st.fake.open,
      text: 'After Shoot or Pass you choose Real or Fake in private. A fake ends your turn and uses the phase\'s Hesitate or fake: the defence replies as if it were real, and then it is shown. Not when he is rushed.' },
    { id: 'screen', when: () => mine() && sel.side === 'O' && enderActs(sel.side, sel.i).some(a => a.kind === 'screen'),
      text: 'A screen puts a T on a square beside the screener. No defender steps across its corner, and only the one standing on the T can challenge it.' },
    { id: 'phase', when: () => st && st.phase >= 2 && !st.placing,
      text: 'A phase is two seconds of play. Each side has six actions a phase, and the shot clock runs down two seconds a phase.' },
    { id: 'coverage', when: () => st && st.phase >= 2 && st.match_format === 'digital' && !st.placing,
      text: 'Try "Coverage: shown" under the board. It colours where the offence can get a shot next phase, and says whether the defence got stronger.' },
  ];
  function on() { try { return localStorage.getItem('pm_tips') !== '0'; } catch (e) { return true; } }
  function seen(id) { try { return localStorage.getItem('pm_tip_' + id) === '1'; } catch (e) { return false; } }
  function mark(id) { try { localStorage.setItem('pm_tip_' + id, '1'); } catch (e) { /* private mode */ } }
  let showing = null;
  function next() {
    // the first tip in the order whose moment has come; one at a time, and only once each
    for (const t of TIPS) { if (seen(t.id)) continue; try { if (t.when()) return t; } catch (e) { /* the moment can't be read yet */ } return null; }
    return null;
  }
  function check() {
    const box = $('tipBox'); if (!box) return;
    if (!on() || !st || $('modal') && !$('modal').classList.contains('hidden')) { box.innerHTML = ''; box.classList.add('hidden'); return; }
    if (showing && !seen(showing.id)) return draw(box, showing);
    showing = next();
    if (!showing) { box.innerHTML = ''; box.classList.add('hidden'); return; }
    draw(box, showing);
    announce('Tip: ' + showing.text);
  }
  function draw(box, t) {
    box.innerHTML = ''; box.classList.remove('hidden');
    const n = TIPS.indexOf(t) + 1;
    box.append(PMCoach.line('coach', t.text, { compact: true, speak: false, live: false }),
      el('div', { class: 'buttons' }, [
        el('button', { class: 'small', id: 'tipOk', text: `Got it (${n} of ${TIPS.length})`, onclick: () => { mark(t.id); showing = null; check(); } }),
        el('button', { class: 'small', id: 'tipOff', text: 'I know the rules: no more tips', onclick: () => { try { localStorage.setItem('pm_tips', '0'); } catch (e) { /* ignore */ } showing = null; check(); announce('Tips off. Turn them back on from the home screen.'); } })]));
  }
  function firstGame() { try { return localStorage.getItem('pm_played') !== '1'; } catch (e) { return false; } }
  function played() { try { localStorage.setItem('pm_played', '1'); } catch (e) { /* ignore */ } }
  function reset() { try { localStorage.removeItem('pm_tips'); for (const t of TIPS) localStorage.removeItem('pm_tip_' + t.id); } catch (e) { /* ignore */ } }
  return { check, firstGame, played, reset, on, TIPS };
})();
