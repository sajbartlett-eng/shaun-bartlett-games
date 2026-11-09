// Step 3m Part C: players and records, stored in this browser (IndexedDB), no account or server.
// Schema version 1: stores 'profiles' (id) and 'matches' (id). Export and import go through one JSON file.
'use strict';
const PMRecords = (() => {
  const DB = 'playmaker', VERSION = 2, SCHEMA = 'playmaker-records';
  let dbp = null;
  function open() {
    if (dbp) return dbp;
    dbp = new Promise((res, rej) => {
      let req;
      try { req = indexedDB.open(DB, VERSION); } catch (e) { rej(e); return; }
      req.onupgradeneeded = () => {
        const db = req.result;
        if (!db.objectStoreNames.contains('profiles')) db.createObjectStore('profiles', { keyPath: 'id' });
        if (!db.objectStoreNames.contains('matches')) { const m = db.createObjectStore('matches', { keyPath: 'id' }); m.createIndex('date', 'date'); }
        // version 2 (step 3n F3): a pairing (two profiles, or a profile and a computer level) keeps its running quarter
        if (!db.objectStoreNames.contains('pairings')) db.createObjectStore('pairings', { keyPath: 'id' });
      };
      req.onsuccess = () => res(req.result);
      req.onerror = () => rej(req.error);
    });
    return dbp;
  }
  async function tx(store, mode, fn) {
    const db = await open();
    return new Promise((res, rej) => {
      const t = db.transaction(store, mode), s = t.objectStore(store);
      let out;
      Promise.resolve(fn(s)).then(v => { out = v; });
      t.oncomplete = () => res(out);
      t.onerror = () => rej(t.error);
    });
  }
  const req = r => new Promise((res, rej) => { r.onsuccess = () => res(r.result); r.onerror = () => rej(r.error); });
  const uid = p => `${p}${Date.now().toString(36)}${Math.random().toString(36).slice(2, 7)}`;

  // ---- profiles
  async function profiles() { return (await tx('profiles', 'readonly', s => req(s.getAll()))) || []; }
  async function profile(id) { return id ? tx('profiles', 'readonly', s => req(s.get(id))) : null; }
  async function createProfile(name) {
    const p = { id: uid('p'), name: String(name || 'Player').trim().slice(0, 24) || 'Player', created: new Date().toISOString(),
      rating: 1500, rd: 350, vol: 0.06, scores: [], suggestions: [], v: 1 };
    await tx('profiles', 'readwrite', s => req(s.put(p)));
    return p;
  }
  async function saveProfile(p) { await tx('profiles', 'readwrite', s => req(s.put(p))); return p; }
  async function renameProfile(id, name) { const p = await profile(id); if (!p) return null; p.name = String(name).trim().slice(0, 24) || p.name; return saveProfile(p); }
  async function deleteProfile(id) { await tx('profiles', 'readwrite', s => req(s.delete(id))); }

  // ---- matches
  async function matches() { return ((await tx('matches', 'readonly', s => req(s.getAll()))) || []).sort((a, b) => (a.date < b.date ? -1 : 1)); }
  async function match(id) { return tx('matches', 'readonly', s => req(s.get(id))); }
  async function saveMatch(m) { m.v = 1; await tx('matches', 'readwrite', s => req(s.put(m))); return m; }
  async function deleteMatch(id) { await tx('matches', 'readwrite', s => req(s.delete(id))); }

  // ---- pairings: the running quarter (team fouls and possessions) carries across their matches
  function pairingId(players) {
    const who = p => (p && p.profile) ? 'p:' + p.profile : (p && p.computer) ? 'c:' + p.computer : null;
    const a = who(players.A), b = who(players.B);
    return a && b ? [a, b].sort().join('|') : null;
  }
  async function pairing(id) { return id ? tx('pairings', 'readonly', s => req(s.get(id))) : null; }
  async function savePairing(id, quarter, players) {
    if (!id) return null;
    const p = { id, quarter, players: { A: players.A, B: players.B }, updated: new Date().toISOString() };
    await tx('pairings', 'readwrite', s => req(s.put(p)));
    return p;
  }
  async function pairings() { return (await tx('pairings', 'readonly', s => req(s.getAll()))) || []; }
  // ---- export / import (one JSON file; import reproduces the data exactly)
  async function exportAll() {
    return { schema: SCHEMA, version: VERSION, profiles: await profiles(), matches: await matches(), pairings: await pairings() };
  }
  async function importAll(data, replace) {
    if (!data || data.schema !== SCHEMA) throw new Error('This is not a Playmaker records file.');
    if (data.version > VERSION) throw new Error(`This file is from a newer version (${data.version}).`);
    if (replace) await clearAll();
    await tx('profiles', 'readwrite', s => Promise.all((data.profiles || []).map(p => req(s.put(p)))));
    await tx('matches', 'readwrite', s => Promise.all((data.matches || []).map(m => req(s.put(m)))));
    await tx('pairings', 'readwrite', s => Promise.all((data.pairings || []).map(p => req(s.put(p)))));
    return { profiles: (data.profiles || []).length, matches: (data.matches || []).length };
  }
  async function clearAll() { for (const st of ['profiles', 'matches', 'pairings']) await tx(st, 'readwrite', s => req(s.clear())); }

  // ---- head to head: totals are the sums of the stored matches
  function sideOf(m, pid) { return m.players && m.players.A && m.players.A.profile === pid ? 'A' : m.players && m.players.B && m.players.B.profile === pid ? 'B' : null; }
  async function headToHead(p1, p2) {
    const all = (await matches()).filter(m => m.done && sideOf(m, p1) && sideOf(m, p2) && sideOf(m, p1) !== sideOf(m, p2));
    const out = { matches: all.length, wins: { [p1]: 0, [p2]: 0 }, ties: 0, points: { [p1]: 0, [p2]: 0 }, possessions: { [p1]: 0, [p2]: 0 }, last: [] };
    for (const m of all) {
      const a = sideOf(m, p1), b = sideOf(m, p2);
      out.points[p1] += m.totals[a]; out.points[p2] += m.totals[b];
      out.possessions[p1] += m.per_side || 1; out.possessions[p2] += m.per_side || 1;
      if (m.winner === a) out.wins[p1]++; else if (m.winner === b) out.wins[p2]++; else out.ties++;
    }
    out.ppp = { [p1]: out.possessions[p1] ? out.points[p1] / out.possessions[p1] : 0, [p2]: out.possessions[p2] ? out.points[p2] / out.possessions[p2] : 0 };
    out.last = all.slice(-5).reverse().map(m => ({ id: m.id, date: m.date, [p1]: m.totals[sideOf(m, p1)], [p2]: m.totals[sideOf(m, p2)],
      winner: m.winner === sideOf(m, p1) ? p1 : m.winner === sideOf(m, p2) ? p2 : 'tie' }));
    return out;
  }
  // ---- against the computer: results by difficulty x age x standard
  async function versusComputer(pid) {
    const rows = {};
    for (const m of await matches()) {
      if (!m.done) continue;
      const me = sideOf(m, pid); if (!me) continue;
      const other = me === 'A' ? 'B' : 'A';
      const comp = m.players[other] && m.players[other].computer; if (!comp) continue;
      const k = `${comp}|${m.settings.age || 'senior'}|${m.settings.standard || 'pro'}`;
      const r = rows[k] || (rows[k] = { level: comp, age: m.settings.age || 'senior', standard: m.settings.standard || 'pro', played: 0, won: 0, lost: 0, tied: 0, for: 0, against: 0 });
      r.played++; r.for += m.totals[me]; r.against += m.totals[other];
      if (m.winner === me) r.won++; else if (m.winner === other) r.lost++; else r.tied++;
    }
    return Object.values(rows);
  }
  // ---- the trainer's turn groups for one profile (all its stored matches)
  async function groupsOf(pid) {
    const out = [];
    for (const m of await matches()) {
      const me = sideOf(m, pid); if (!me) continue;
      for (const [poss, t] of Object.entries(m.trainer || {})) {
        const mine = t.players && t.players[me]; if (!mine) continue;
        for (const g of mine.groups) out.push({ match: m.id, date: m.date, possession: Number(poss), side: mine.side,
          categories: g.categories, loss: g.grade.loss, band: g.grade.band, indirect: (g.credits || []).reduce((a, c) => a + Math.max(0, c.indirect), 0),
          first: g.actions[0] || '', phase: g.phase || null, turnover: g.grade.turnover });
      }
    }
    return out;
  }
  return { open, profiles, profile, createProfile, saveProfile, renameProfile, deleteProfile, matches, match, saveMatch, deleteMatch,
    exportAll, importAll, clearAll, headToHead, versusComputer, groupsOf, sideOf, pairingId, pairing, savePairing, pairings, SCHEMA, VERSION };
})();
if (typeof window !== 'undefined') window.PMRecords = PMRecords;
