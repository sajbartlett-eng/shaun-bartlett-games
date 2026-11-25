// node [--max-old-space-size=N] mem4.js <root> <board> <search|stances|offence|value> [memo reads reach]
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const root = process.argv[2], board = process.argv[3], kind = process.argv[4];
const E = require(path.join(root, 'playmaker_web', 'static', 'engine.js'));
const load = n => JSON.parse(fs.readFileSync(path.join(root, 'playmaker_engine', 'data', n)));
E.init({ zones: load('court_zones.json'), config: load('ai_profiles.json'), vcoarse: load('vcoarse.json'), segments: load('segments.json'), learned: null });
if (process.argv[5]) E._memoSizes(+process.argv[5], +process.argv[6], +process.argv[7]);
const b = JSON.parse(fs.readFileSync(path.join(root, 'docs/runs/step31/boards.json')))[board];
const prof = load('ai_profiles.json').profiles[process.env.LEVEL || 'allstar'];
const t = Date.now();
let out, sum;
if (kind === 'search') { out = JSON.parse(E.searchJSON(JSON.stringify({ state: b.state, ctx: b.ctx, profile: prof, max_depth: +(process.env.DEPTH || 1) }))); sum = out.results[0]; }
else { out = JSON.parse(E.coverageJSON(JSON.stringify({ state: b.state, ctx: b.ctx, options: { only: kind === 'stances' ? 'stances' : kind === 'offence' ? 'offence_setup' : 'value' } }))); sum = kind === 'stances' ? [out.x, out.arrows, out.value] : kind === 'offence' ? [out.squares, out.ball, out.value] : [out.value]; }
console.log(JSON.stringify({ board, kind, sizes: E._memoSizes(), ms: Date.now() - t, rss_mb: Math.round(process.memoryUsage().rss / 1e6), sum: JSON.stringify(sum).slice(0, 150), md5: crypto.createHash('md5').update(JSON.stringify(kind === 'search' ? out.results : sum)).digest('hex').slice(0, 8) }));
