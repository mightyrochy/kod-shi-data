/* Повтор показу записаних карток на зібраній голові, точне вікно 390×844; без моделей. */
const {chromium} = require('playwright');
const fs = require('fs'), path = require('path'), zlib = require('zlib');
const [html, verdicts, cache, out] = process.argv.slice(2).map(x => path.resolve(x));
(async () => {
  const report = JSON.parse(zlib.gunzipSync(fs.readFileSync(verdicts)));
  const cards = report.прогони[0].вердикти.filter(r => r.рука === '1').map(r => ({рука: r.рука, речі: r.речі_образу,
    текст: r.опис, як_носити: [], про_речі: []}));
  const browser = await chromium.launch({headless: true});
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    await page.route('http://127.0.0.1:8765/**', r => r.request().url().endsWith('/index.html')
      ? r.fulfill({status: 200, contentType: 'text/html; charset=utf-8', body: fs.readFileSync(html)})
      : r.fulfill({status: 404, body: ''}));
    await page.route('https://cdn.jsdelivr.net/pyodide/**', r => {
      const name = new URL(r.request().url()).pathname.split('/').pop();
      return r.fulfill({status: 200, body: fs.readFileSync(path.join(cache, name)),
        contentType: name.endsWith('.wasm') ? 'application/wasm' : name.endsWith('.js') ? 'application/javascript' : 'application/octet-stream'});
    });
    await page.goto('http://127.0.0.1:8765/index.html');
    await page.waitForFunction(() => typeof рендер === 'function');
    await page.evaluate(cards => {
      П = {збірка: 'перевірка записаного показу', картки: cards, каталог: '', профіль: ''};
      рендер(); режим('образи');
    }, cards);
    await page.locator('#к-0').scrollIntoViewIfNeeded();
    await page.screenshot({path: out, fullPage: false});
    console.log(JSON.stringify({viewport: page.viewportSize(), карток: cards.length, файл: out}));
  } finally { await browser.close(); }
})().catch(e => {console.error(e); process.exitCode = 1;});
