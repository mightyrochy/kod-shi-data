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
  if (process.env.RELOAD){
    await с.reload({ waitUntil: 'commit' });
    await с.click('dialog button:has-text("Так, використовувати")', { timeout: 5000 }).catch(() => {});
    await с.waitForSelector('#сц-приклади button.приклад', { state: 'visible', timeout: 180000 });
    console.log('перевідкрито, підказка видна за', Date.now() - t0, 'мс · режим', await с.evaluate(() => РЕЖИМ));
  }
  /* 4.1-Б-3: Python у воркері — підйом лічиться на `піднятиВоркерМостуП`, готовність — `МІСТ_ГОТОВИЙ_П` */
  await с.evaluate(() => { window.__підйоми = 0; window.__міст = []; const пп = піднятиВоркерМостуП;
    window.піднятиВоркерМостуП = (...а) => { window.__підйоми++; return пп(...а); };
    const м = містП; window.містП = async (ім, д, ...а) => { const з = {ім, t0: Math.round(performance.now())}; window.__міст.push(з);
      try { const р = await м(ім, д, ...а); з.мс = Math.round(performance.now()) - з.t0; return р; } catch (е) { з.збій = String(е).slice(0, 120); throw е; } }; });
  const готовийМіст = () => с.evaluate(() => typeof МІСТ_ГОТОВИЙ_П !== 'undefined' && МІСТ_ГОТОВИЙ_П);
  console.log('сценарій за', Date.now() - t0, 'мс · міст готовий:', await готовийМіст());
  if (КОЛИ === 'pyodide') await с.evaluate(() => підняти_міст_показу().then(() => 1));
  await с.evaluate(() => { window.__мова = []; const о = містП; window.містП = async (ім, д, ...а) => { const р = await о(ім, д, ...а);
    if (ім === 'мова' && д && д.паспорт_з) window.__мова.push({вхід: JSON.parse(JSON.stringify(д)), паспорт: р && р.паспорт ? {нагода: р.паспорт.нагода, місце: р.паспорт.місце, ош: р.паспорт.ошатність} : null});
    return р; }; });
  if (ВХІД === 'hint') await с.click('#сц-приклади button.приклад >> nth=0');
  else { await с.click('#чат-поле'); await с.keyboard.type('Іду на побачення в ресторан, увечері. Обіцяють дощ'); }
  await с.click('#чат-слати');
  const tS = Date.now();
  console.log('надіслано · міст готовий:', await готовийМіст());
  if (ДІЯ !== 'нічого'){
    await пауза(+(process.env.DIYA_MS || 50));
    if (ДІЯ === 'новий') await с.evaluate(() => { const к = document.getElementById('сц-новий'); к.onclick(); });
    const tД = Date.now();
    const мс = await с.evaluate(() => new Promise(ok => { const t = performance.now();
      (function чек(){ if (!ЧАТ_П.length && !ПАСПОРТ_П) ok(Math.round(performance.now() - t)); else if (performance.now() - t > 15000) ok(-1); else setTimeout(чек, 10); })(); }));
    console.log('новий сценарій на екрані за', мс, 'мс після дотику ·', JSON.stringify(await с.evaluate(() => ({чат: ЧАТ_П.length, паспорт: !!ПАСПОРТ_П,
      стан: (document.getElementById('чат-стан') || {}).textContent, поле_вимкнено: document.getElementById('чат-поле').disabled}))));
    /* хід дійшов до кінця моделі й моста — новий сценарій мусить лишитись чистим */
    await с.waitForFunction(() => window.__мова && window.__мова.length > 0, null, { timeout: 60000 }).catch(() => console.log('хід не дійшов до шва'));
    await пауза(3000);
  }
  await с.waitForFunction(() => !чиннаДіяП('чат'), null, { timeout: 180000 }).catch(() => console.log('хід не скінчився'));
  await пауза(+(process.env.PISLIA_MS || 1500));
  const стан = await с.evaluate(() => ({
    чат: ЧАТ_П.map(р => р.хто + ':' + String(р.текст).slice(0, 60)),
    паспорт: ПАСПОРТ_П ? {нагода: ПАСПОРТ_П.нагода, місце: ПАСПОРТ_П.місце, ош: ПАСПОРТ_П.ошатність, джерело: ПАСПОРТ_П.джерело} : null,
    поля: Object.fromEntries(['сц-нагода', 'сц-місце', 'сц-дрес', 'сц-опади', 'сц-пора'].map(і => [і, document.getElementById(і).value])),
    рядки: ['зн-нагода', 'зн-місце', 'зн-дрес'].map(і => (document.getElementById(і) || {}).textContent),
    змінено: ВИПАДОК_ЗМІНЕНО_П, стан: (document.getElementById('чат-стан') || {}).textContent,
    виклики: (typeof ВИКЛИКИ_РОЗМОВИ_П !== 'undefined') ? ВИКЛИКИ_РОЗМОВИ_П.length : null }));
  console.log('хід за', Date.now() - tS, 'мс:', JSON.stringify(стан));
  console.log('підйомів Pyodide:', await с.evaluate(() => window.__підйоми), '· міст:', JSON.stringify(await с.evaluate(() => window.__міст)));
  console.log('моделі:', JSON.stringify(моделі.map(м => [м.t - t0, м.тип, м.симв, м.початок.slice(0, 50)])));
  if (process.env.MOVA_OUT) fs.writeFileSync(process.env.MOVA_OUT, JSON.stringify(await с.evaluate(() => window.__мова), null, 1));
  if (process.env.ZIBRATY){
    if (process.env.ZMINENO) await с.evaluate(() => { ВИПАДОК_ЗМІНЕНО_П = true; });
    const tz = Date.now(); const було = моделі.length;
    await с.click('#зб-зібрати');
    await с.evaluate(() => { window.__запити = []; const о = містП; window.містП = async (ім, д, ...а) => { const р = await о(ім, д, ...а);
      if (ім === 'запити') window.__запити.push({сц: d2(д.сценарій), паспорт: д.паспорт ? {нагода: д.паспорт.нагода, місце: д.паспорт.місце, дрес: д.паспорт.дрес_код, ош: д.паспорт.ошатність, подія: д.паспорт.подія, джп: д.паспорт.джерело_полів} : null, помилка: р.помилка || null, правило: р.правило || null});
      return р; }; function d2(x){ return JSON.parse(JSON.stringify(x || null)); } });
    await с.waitForFunction(() => window.__запити.length > 0, null, { timeout: 90000 }).catch(() => {});
    await пауза(300);
    console.log('зібрати за', Date.now() - tz, 'мс:', JSON.stringify(await с.evaluate(() => ({режим: РЕЖИМ,
      статус: ((document.getElementById('зб-статус') || {}).textContent || '').slice(0, 160),
      поля: Object.fromEntries(['сц-нагода', 'сц-місце', 'сц-дрес'].map(і => [і, document.getElementById(і).value])),
      паспорт: !!ПАСПОРТ_П, запити: window.__запити, діагноз: (typeof ЗБ !== 'undefined' && ЗБ && ЗБ.діагноз) ? ЗБ.діагноз.slice(0, 8) : null }))),
      'моделі після:', моделі.slice(було).map(м => м.початок.slice(0, 40)).join(' | '));
  }
  if (process.env.ZNIMOK) await с.screenshot({ path: process.env.ZNIMOK });
  if (жур.length) console.log('журнал:', жур.slice(0, 12).join('\n  '));
  await б.close();
})().catch(е => { console.error('ЗБІЙ', е); process.exit(1); });
