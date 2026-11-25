// Показ збереженої розмови стенда (тексти ЧАТ_П без зміни) на тій самій сторінці: розгорнута стрічка, 390×844.
// node render.cjs <тека сторінки> <тека pyodide> <тека виходу стенда>
const fs = require('fs'), path = require('path'); const {chromium} = require('playwright');
const [КОРІНЬ, PYO, ВИХІД] = process.argv.slice(2); const БАЗА = 'http://127.0.0.1:8765';
(async () => {
  const б = await chromium.launch(); const к = await б.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 2, isMobile: true, hasTouch: true, locale: 'uk-UA'});
  const с = await к.newPage(); с.setDefaultTimeout(120000);
  await с.route(u => u.origin === БАЗА, r => { const ім = decodeURIComponent(new URL(r.request().url()).pathname).replace(/^\//, '') || 'index.html'; const ф = path.join(КОРІНЬ, ім);
    if (!fs.existsSync(ф)) return r.fulfill({status: 404, body: ''}); r.fulfill({status: 200, contentType: 'text/html; charset=utf-8', body: fs.readFileSync(ф)}); });
  await с.route('https://cdn.jsdelivr.net/pyodide/**', r => { const ім = new URL(r.request().url()).pathname.split('/').pop(); const ф = path.join(PYO, ім);
    r.fulfill({status: 200, contentType: ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : 'application/octet-stream', body: fs.readFileSync(ф)}); });
  await с.route(u => u.origin !== БАЗА && !/pyodide/.test(u.href), r => r.abort());
  await с.goto(БАЗА + '/index.html', {waitUntil: 'load'}); await с.waitForTimeout(6000);
  const чат = JSON.parse(fs.readFileSync(path.join(ВИХІД, 'чат.json'), 'utf8')).map(м => ({хто: м.хто, текст: м.текст}));
  await с.evaluate(ч => { ЧАТ_П.length = 0; ч.forEach(м => ЧАТ_П.push(м)); показатиРозмову && показатиРозмову(); document.getElementById('ші-пілюля').dispatchEvent(new MouseEvent('click', {bubbles: true})); }, чат);
  await с.waitForTimeout(1500);
  await с.screenshot({path: path.join(ВИХІД, 'чат_390x844.png')});
  fs.writeFileSync(path.join(ВИХІД, 'стрічка_текст.txt'), await с.evaluate(() => document.getElementById('чат-стрічка').innerText));
  await б.close();
})().catch(e => { console.error(e); process.exit(2); });
