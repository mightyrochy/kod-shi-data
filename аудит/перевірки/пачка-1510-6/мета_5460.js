/* Рядки 5210/5252: підказка-сценарій власника 14.10 15:39 на зібраній сторінці в Chromium 390×844.
   Модель — запис ходу з файлу 1551 (підміна виклику мосту `/міст`); Pyodide — справжній, з CDN (затримка PDELAY мс на файл).
   Змінні: PAGE (index.html), VKHID (hint|typed), KOLY (одразу|pyodide — міст піднято до дотику), MDELAY (мс моделі),
   DIYA=новий і DIYA_MS — «Новий сценарій» посеред ходу (друкує, за скільки мс новий сценарій на екрані й чи лишився чистим),
   RELOAD=1 — перевідкрити сторінку з наявним профілем, ZIBRATY=1 — «Зібрати образи» після ходу (вхід `запити`, відмова),
   ZMINENO=1 — перед збиранням екран «правлено» (шлях `паспортШаромП`), ZNIMOK — знімок, MOVA_OUT — входи шва паспорта.
   Запуск: node аудит/проби/хід_5252.js (потрібен playwright і HTTPS_PROXY для CDN Pyodide). */
const { chromium } = require(process.env.PLAYWRIGHT || 'playwright');
const fs = require('fs'), path = require('path');
const PAGE = process.env.PAGE || path.join(__dirname, '..', '..', 'index.html');
const ВХІД = process.env.VKHID || 'hint', КОЛИ = process.env.KOLY || 'одразу', ДІЯ = process.env.DIYA || 'нічого';
const MDELAY = +(process.env.MDELAY || 1500), PDELAY = +(process.env.PDELAY || 0);
/* відповідь мовної моделі на хід 15:39:26 з файлу 1551 — відтворена так, що `прийняти_розмову` дає рівно записані `внутрішня` й `частини` */
const ВІДП = JSON.stringify({"update": {"occasion": {"quote": "побачення", "value": "date"}, "occasion_part": {"quote": "побачення", "value": "other"}, "place": {"quote": "ресторан", "value": "restaurant_casual"}, "place_words": {"free_text": "Ресторан", "lang": "uk"}, "event": {"free_text": "побачення в ресторан", "lang": "uk"}, "part_of_day": "evening", "precipitation": {"quote": "дощ", "value": "rain"}, "formality": {"from": 5, "to": 6}, "open_zones": "one"}, "need": "none", "text": [{"about": ["occasion", "place", "part_of_day"], "says": "Записала вечірнє побачення в ресторані."}, {"about": ["precipitation"], "says": "Також враховую обіцяний дощ."}], "invite": "За бажанням можеш уточнити, які прикраси або стиль тобі ближчі для цього вечора, або ж пропустити це.", "invite_topics": ["jewelry", "register"]});
const БАЗА = 'http://lyusterko.test';
const пауза = мс => new Promise(р => setTimeout(р, мс));
(async () => {
  const б = await chromium.launch({ headless: true,
    proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined });
  const к = await б.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
  const с = await к.newPage();
  const жур = [], моделі = [];
  с.on('console', м => { if (/error|warn/i.test(м.type())) жур.push(м.type() + ': ' + м.text().slice(0, 200)); });
  с.on('pageerror', е => жур.push('pageerror: ' + String(е).slice(0, 300)));
  await с.route(u => u.href.startsWith(БАЗА) && !decodeURIComponent(u.pathname).endsWith('/міст'), r =>
    /index\.html$/.test(r.request().url()) ? r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: fs.readFileSync(PAGE) }) : r.fulfill({ status: 404, body: '' }));
  await с.route('https://cdn.jsdelivr.net/pyodide/**', async r => {
    const в = await r.fetch(); if (PDELAY) await пауза(PDELAY); await r.fulfill({ response: в }); });
  await с.route(u => decodeURIComponent(u.pathname).endsWith('/міст'), async r => {
    const т = r.request().postDataJSON() || {};
    const текст = ((т.messages || []).slice(-1)[0] || {}).content || [];
    const р = (Array.isArray(текст) ? текст.map(х => х.text || '').join('\n') : String(текст));
    const хід = /Іду на побачення/.test(р) && /"update"|update/.test(р);
    моделі.push({ t: Date.now(), тип: хід ? 'хід' : 'інше', симв: р.length, початок: р.slice(0, 90).replace(/\s+/g, ' ') });
    await пауза(MDELAY);
    await r.fulfill({ status: 200, contentType: 'application/json', headers: { 'x-model': 'gemini-3.8-flash' },
      body: JSON.stringify({ content: [{ type: 'text', text: хід ? ВІДП : '{}' }], usage: { input_tokens: 1, output_tokens: 1 }, stop_reason: 'end_turn' }) });
  });
  const t0 = Date.now();
  await с.goto(БАЗА + '/index.html#міст=' + БАЗА + '/міст&т=tok&модель_мови=gemini-3.8-flash', { waitUntil: 'load', timeout: 180000 });
  await с.click('dialog button:has-text("Так, використовувати")', { timeout: 30000 }).catch(() => console.log('діалогу мосту нема'));
  await с.waitForFunction(() => typeof РЕЖИМ !== 'undefined' && !!(document.getElementById('н-далі') || {}).onclick, null, { timeout: 180000 });
  /* знайомство руками — як стенд */
  await с.click('#кол-блок details.розкривач > summary');
  await с.fill('#кол-відповідь', 'шкіра 1 #d9a88f\nшкіра 2 #caa08b\nшкіра 3 #be8f7b\nволосся #d2b37c\nволосся #69513d\nочі #597d81\nкільце #30474c');
  await с.click('#кол-читати');
  await с.fill('[id="пр-імʼя"]', '1'); await с.check('#пр-згода');
  await с.click('#н-далі'); await с.waitForFunction(() => ЕКРАН === 1, null, { timeout: 30000 });
  await с.click('#н-далі'); await с.waitForFunction(() => ЕКРАН === 2, null, { timeout: 30000 });
  for (const [і, v] of [['мр-плечі', 108], ['мр-груди', 104], ['мр-талія', 78], ['мр-стегна', 106], ['мр-зріст', 167]]) await с.fill('#' + і, String(v));
  await с.click('#н-далі');
  await с.waitForFunction(() => РЕЖИМ === 'сценарій' && ПРОФІЛЬ_СТВОРЕНО, null, { timeout: 60000 });
  const Н = process.env.ZN || '/tmp/zn';
  await с.click('text=Або заповнити рукою'); await пауза(500);
  await с.evaluate(() => перемкнутиРедактор('ред-мета')); await пауза(800);
  const чипи = () => с.evaluate(() => { const к = document.getElementById('сц-мета-зони-плитки'); const r = к.getBoundingClientRect();
    return { hidden: к.hidden, display: getComputedStyle(к).display, h: Math.round(r.height), чипів_видно: [...к.querySelectorAll('.чип')].filter(x => x.getBoundingClientRect().height > 0).length }; });
  console.log('ДО дотику по плитці:', JSON.stringify(await чипи()));
  await с.screenshot({ path: Н + '/1034_без_плитки.png' });
  await с.click('#сц-мета-важливо-плитки >> text=/Відвести погляд/'); await пауза(500);
  console.log('ПІСЛЯ дотику:', JSON.stringify(await чипи()));
  await с.click('#сц-мета-зони-плитки .чип >> nth=0'); await пауза(400);
  console.log('після вибору чипа:', JSON.stringify(await чипи()), 'зони =', await с.inputValue('#сц-мета-зони'));
  await с.screenshot({ path: Н + '/1034_після_дотику.png' });
  await с.click('#сц-мета-важливо-плитки >> text=/Відвести погляд/'); await пауза(400);
  console.log('після зняття плитки:', JSON.stringify(await чипи()), 'зони =', JSON.stringify(await с.inputValue('#сц-мета-зони')));
  await б.close();
})();
