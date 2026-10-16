/* Рядки 5481/5482/5271 на зібраній сторінці в Chromium 390×844 (справжній Pyodide з CDN). PAGE=index.html.
   (а) холодна сторінка: два одночасні `містП` — скільки разів завантажено pyodide.asm.wasm;
   (б) «Зібрати образи» з порожнім сценарієм — скільки викликів `запити`, чи є питання про нагоду до натиску. */
const { chromium } = require(process.env.PLAYWRIGHT || 'playwright');
const fs = require('fs'), path = require('path');
const PAGE = process.env.PAGE || path.join(__dirname, '..', '..', 'index.html'), БАЗА = 'http://lyusterko.test';
(async () => {
  const б = await chromium.launch({ headless: true, proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined });
  const с = await (await б.newContext({ viewport: { width: 390, height: 844 }, hasTouch: true, isMobile: true })).newPage();
  let wasm = 0, запити = 0;
  await с.route(u => u.href.startsWith(БАЗА), r => /index\.html$/.test(r.request().url())
    ? r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: fs.readFileSync(PAGE) }) : r.fulfill({ status: 404, body: '' }));
  await с.route('https://cdn.jsdelivr.net/pyodide/**', r => { if (/asm\.wasm/.test(r.request().url())) wasm++; r.continue(); });
  await с.goto(БАЗА + '/index.html#міст=' + БАЗА + '/міст&т=tok', { waitUntil: 'load', timeout: 180000 });
  await с.click('dialog button:has-text("Так, використовувати")', { timeout: 30000 }).catch(() => {});
  await с.waitForFunction(() => typeof РЕЖИМ !== 'undefined' && !!(document.getElementById('н-далі') || {}).onclick, null, { timeout: 180000 });
  const ок = await с.evaluate(() => Promise.all([містП('довідник', {}), містП('довідник', {})]).then(р => р.every(х => х && !х.помилка)).catch(е => String(е).slice(0, 80)));
  console.log('(а) два холодні містП: ок =', ок, '· завантажень pyodide.asm.wasm =', wasm);
  await с.click('#кол-блок details.розкривач > summary');
  await с.fill('#кол-відповідь', 'шкіра 1 #d9a88f\nшкіра 2 #caa08b\nшкіра 3 #be8f7b\nволосся #d2b37c\nволосся #69513d\nочі #597d81\nкільце #30474c');
  await с.click('#кол-читати'); await с.fill('[id="пр-імʼя"]', '1'); await с.check('#пр-згода');
  for (const _ of [0, 1]) { await с.click('#н-далі'); await пауза(300); }
  for (const [і, v] of [['мр-плечі', 108], ['мр-груди', 104], ['мр-талія', 78], ['мр-стегна', 106], ['мр-зріст', 167]]) await с.fill('#' + і, String(v));
  await с.click('#н-далі');
  await с.waitForFunction(() => РЕЖИМ === 'сценарій' && ПРОФІЛЬ_СТВОРЕНО, null, { timeout: 60000 });
  await с.evaluate(() => { window.__з = 0; const о = містП; window.містП = (ім, д) => { if (ім === 'запити') window.__з++; return о(ім, д); }; });
  const питання0 = await с.evaluate(() => { const е = document.getElementById('зб-питання'); return е ? !е.hidden : 'нема елемента'; });
  await с.evaluate(() => { document.getElementById('сц-картка').hidden = false; });
  await с.evaluate(() => document.getElementById('зб-зібрати').onclick());
  await пауза(2500);
  console.log('(б) питання про нагоду видно до натиску:', питання0, '· викликів запити:', await с.evaluate(() => window.__з),
    '· статус збирання:', JSON.stringify(await с.evaluate(() => (document.getElementById('зб-статус').textContent || '').slice(0, 90))),
    '· режим:', await с.evaluate(() => РЕЖИМ), '· кнопка відкрита:', await с.evaluate(() => !document.getElementById('зб-зібрати').disabled));
  /* (в) слова є («на роботу»), полів нема — K-IO-01 доти приходив відмовою після натиску */
  await с.evaluate(() => { ЧАТ_П.push({ хто: 'людина', текст: 'Іду на роботу', тема: 'сценарій' }); window.__з = 0; малюватиКарткуСценарію(); });
  const п1 = await с.evaluate(() => (e => e ? !e.hidden : 'нема елемента')(document.getElementById('зб-питання')));
  await с.evaluate(() => document.getElementById('зб-зібрати').onclick()); await пауза(8000);
  console.log('(в) слова без полів: питання видно:', п1, '· викликів запити:', await с.evaluate(() => window.__з),
    '· статус:', JSON.stringify(await с.evaluate(() => (document.getElementById('зб-статус').textContent || '').slice(0, 110))),
    '· відмова K-IO-01 на екрані:', await с.evaluate(() => /сценарію нема|K-IO-01/.test(document.body.innerText)));
  await б.close();
})().catch(е => { console.error('ЗБІЙ', е); process.exit(1); });
function пауза(мс) { return new Promise(р => setTimeout(р, мс)); }
