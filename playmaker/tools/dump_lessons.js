// Dump the course's lesson boards as JSON so the engine can check every drawn move is legal (tests/test_course_boards.py).
const path = require('path');
const stub = new Proxy(function () {}, { get: () => stub, apply: () => stub, construct: () => stub });
global.window = {}; global.document = { createElementNS: () => stub, createElement: () => stub, addEventListener() {}, removeEventListener() {} };
global.localStorage = { getItem: () => null, setItem() {} };
require(path.join(__dirname, '..', 'playmaker_web', 'static', 'notation.js'));
require(path.join(__dirname, '..', 'playmaker_web', 'static', 'coach.js'));
const L = window.PMCoach.LESSONS.map(l => ({ id: l.id, title: l.title, board: l.board && { o: l.board.o, x: l.board.x, marks: l.board.marks || [], reach: l.board.reach || [] } }));
process.stdout.write(JSON.stringify(L));
