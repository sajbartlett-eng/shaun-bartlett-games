const { chromium } = require('playwright');
(async () => {
  const [url, shot, wait] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 412, height: 900 }, deviceScaleFactor: 2 });
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.goto(url);
  await page.waitForFunction(() => window.PM_SPEEDTEST_DONE, null, { timeout: parseInt(wait, 10) });
  const rows = await page.evaluate(() => window.PM_SPEEDTEST_DONE);
  const text = await page.evaluate(() => document.querySelector('textarea') && document.querySelector('textarea').value);
  const loading = await page.evaluate(() => !!document.getElementById('loading'));
  if (shot) await page.screenshot({ path: shot, fullPage: true });
  console.log(JSON.stringify({ errors, pythonLoaderStarted: loading, copyButton: await page.locator('button', { hasText: 'Copy results' }).count(), rows: Array.isArray(rows) ? rows.length : rows }));
  console.log(text);
  await browser.close();
})();
