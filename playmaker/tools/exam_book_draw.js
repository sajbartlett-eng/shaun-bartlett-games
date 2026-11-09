// Step 8: draws the exam book's boards with the app's own drawing library (notation.js), to SVG text.
// Called by tools/exam_book.py: node tools/exam_book_draw.js <notation.js> <boards.json> <zones.json> <out.json>
const fs = require('fs');
const { chromium } = require('playwright');
const [notation, boardsPath, zonesPath, outPath] = process.argv.slice(2);
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setContent('<!doctype html><html><body></body></html>');
  await page.addScriptTag({ content: fs.readFileSync(notation, 'utf8') });
  const boards = JSON.parse(fs.readFileSync(boardsPath, 'utf8'));
  const zones = JSON.parse(fs.readFileSync(zonesPath, 'utf8'));
  const out = await page.evaluate(([boards, zones]) => {
    const N = window.PMNotation, res = {};
    for (const [key, v] of Object.entries(boards)) {
      res[key] = v.boards.map(b => {
        const root = N.svg('svg', { xmlns: 'http://www.w3.org/2000/svg', role: 'img', class: 'court' });
        N.court(root, zones, { rings: true });
        const pg = N.svg('g', { class: 'pieces' });
        b.o.forEach((q, i) => {
          const [x, y] = N.sqXY(q); const g = N.svg('g', { class: 'piece' });
          N.pieceO(g, x, y, i + 1, { ball: b.ball === i });
          N.tags(g, x, y, { move: b.moved_o[i], qs: b.qs_o[i] }, b.lock_o[i], null);
          pg.append(g);
        });
        b.x.forEach((q, i) => {
          const [x, y] = N.sqXY(q); const g = N.svg('g', { class: 'piece' });
          N.pieceX(g, x, y, i + 1, Array.isArray(b.arrows[i]) ? b.arrows[i] : [b.arrows[i]]);
          N.tags(g, x, y, { move: b.moved_x[i], qs: b.qs_x[i] }, b.lock_x[i], null);
          if (b.beaten.some(([xi]) => xi === i))
            g.append(N.svg('text', { x: N.cx(x), y: N.cy(y) - 22, 'text-anchor': 'middle', 'font-size': 10, 'font-weight': 'bold', fill: N.RED }, 'beaten'));
          pg.append(g);
        });
        root.append(pg);
        const avoid = [...b.o, ...b.x].map(q => { const [x, y] = N.sqXY(q); return [N.cx(x), N.cy(y)]; });
        if (v.marks) N.marks(root, v.marks, { numbers: true, tag: 1.25, avoid });
        return root.outerHTML;
      });
    }
    return res;
  }, [boards, zones]);
  fs.writeFileSync(outPath, JSON.stringify(out));
  await browser.close();
})();
