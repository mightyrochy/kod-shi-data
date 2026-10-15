/* Рядки 5600/5601: «Новий сценарій» під час ходу розмови на зібраній сторінці в Chromium 390×844; модель — заглушка із затримкою.
   Змінні: PAGE (index.html), SCEN=1|2, MDELAY (мс моделі, типово 2500), DIYA_MS (за скільки мс після «Надіслати» тиснути «Новий сценарій»).
   SCEN=1: фото + «як мені цей образ?» (need: look), до відповіді — «Новий сценарій»: екран лишається сценарієм, викликів оцінки нема.
   SCEN=2: текстовий хід без мовної моделі (шлях виклику 0); «Новий сценарій» посеред виклику 0 (`паспортПоРозмовіП`): у новому сценарії `ВИКЛИКИ_РОЗМОВИ_П.length === 0`.
   Запуск: PAGE=/шлях/index.html SCEN=1 node аудит/проби/скасування_5600.js (playwright, HTTPS_PROXY для CDN Pyodide). */
const { chromium } = require(process.env.PLAYWRIGHT || 'playwright');
const fs = require('fs'), path = require('path');
const PAGE = process.env.PAGE || path.join(__dirname, '..', '..', 'index.html');
const SCEN = process.env.SCEN || '1', MDELAY = +(process.env.MDELAY || 2500), DIYA_MS = +(process.env.DIYA_MS || 400);
const ПИТАННЯ = 'як мені цей образ?';
const ВІДП1 = JSON.stringify({update: {question_about: 'look', question: {free_text: ПИТАННЯ, lang: 'uk'}}, need: 'look', text: [], invite: '', invite_topics: []});
const ВІДП2 = JSON.stringify({update: {occasion: {quote: 'побачення', value: 'date'}, occasion_part: {quote: 'побачення', value: 'other'},
  place: {quote: 'ресторан', value: 'restaurant_casual'}, part_of_day: 'evening'}, need: 'none',
  text: [{about: ['occasion', 'place', 'part_of_day'], says: 'Записала вечірнє побачення в ресторані.'}], invite: '', invite_topics: []});
/* 1×1 PNG — фото для чату */
const PNG = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==', 'base64');
const БАЗА = 'http://lyusterko.test';
const пауза = мс => new Promise(р => setTimeout(р, мс));
(async () => {
  const б = await chromium.launch({ headless: true, proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined });
  const к = await б.newContext({ viewport: { width: 390, height: 844 }, deviceScaleFactor: 2, hasTouch: true, isMobile: true });
  const с = await к.newPage();
  const моделі = [], жур = [];
  с.on('pageerror', е => жур.push('pageerror: ' + String(е).slice(0, 200)));
  await с.route(u => u.href.startsWith(БАЗА) && !decodeURIComponent(u.pathname).endsWith('/міст'), r =>
    /index\.html$/.test(r.request().url()) ? r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: fs.readFileSync(PAGE) }) : r.fulfill({ status: 404, body: '' }));
  await с.route('https://cdn.jsdelivr.net/pyodide/**', async r => { const в = await r.fetch(); await r.fulfill({ response: в }); });
  await с.route(u => decodeURIComponent(u.pathname).endsWith('/міст'), async r => {
    const т = r.request().postDataJSON() || {};
    const останній = ((т.messages || []).slice(-1)[0] || {}).content || [];
    const р = Array.isArray(останній) ? останній.map(х => х.text || '').join('\n') : String(останній);
    const хід = /"update"|update/.test(р) && (/побачення/.test(р) || /образ/.test(р));
    моделі.push({ t: Date.now(), тип: хід ? 'хід' : 'інше', початок: р.slice(0, 70).replace(/\s+/g, ' ') });
    await пауза(MDELAY);
    await r.fulfill({ status: 200, contentType: 'application/json', headers: { 'x-model': 'gemini-3.8-flash' },
      body: JSON.stringify({ content: [{ type: 'text', text: хід ? (SCEN === '1' ? ВІДП1 : 'не json') : (SCEN === '2' ? 'не json' : '{}') }], usage: { input_tokens: 1, output_tokens: 1 }, stop_reason: 'end_turn' }) });
  });
  await с.goto(БАЗА + '/index.html#міст=' + БАЗА + '/міст&т=tok', { waitUntil: 'load', timeout: 180000 });
  await с.click('dialog button:has-text("Так, використовувати")', { timeout: 30000 }).catch(() => {});
  await с.waitForFunction(() => typeof РЕЖИМ !== 'undefined' && !!(document.getElementById('н-далі') || {}).onclick, null, { timeout: 180000 });
  await с.click('#кол-блок details.розкривач > summary');
  await с.fill('#кол-відповідь', 'шкіра 1 #d9a88f\nшкіра 2 #caa08b\nшкіра 3 #be8f7b\nволосся #d2b37c\nволосся #69513d\nочі #597d81\nкільце #30474c');
  await с.click('#кол-читати');
  await с.fill('[id="пр-імʼя"]', '1'); await с.check('#пр-згода');
  await с.click('#н-далі'); await с.waitForFunction(() => ЕКРАН === 1, null, { timeout: 30000 });
  await с.click('#н-далі'); await с.waitForFunction(() => ЕКРАН === 2, null, { timeout: 30000 });
  for (const [і, v] of [['мр-плечі', 108], ['мр-груди', 104], ['мр-талія', 78], ['мр-стегна', 106], ['мр-зріст', 167]]) await с.fill('#' + і, String(v));
  await с.click('#н-далі');
  await с.waitForFunction(() => РЕЖИМ === 'сценарій' && ПРОФІЛЬ_СТВОРЕНО, null, { timeout: 60000 });
  /* лічильники: виклики шару оцінки образу й записи викликів розмови */
  await с.evaluate(() => { window.__оцінка = 0; const о = оцінитиОбразП; window.оцінитиОбразП = (...а) => { window.__оцінка++; return о(...а); }; });
  if (SCEN === '1'){
    await с.setInputFiles('#чат-фото-вхід', { name: 'образ.png', mimeType: 'image/png', buffer: PNG });
    await с.waitForFunction(() => document.querySelectorAll('#чат-вкладення > *').length > 0, null, { timeout: 20000 });
    await с.fill('#чат-поле', ПИТАННЯ);
  } else await с.fill('#чат-поле', 'Іду на побачення в ресторан, увечері');
  await с.click('#чат-слати');
  if (SCEN === '2'){
    /* шар відмовляє (відповідь не JSON) і розмова йде шляхом виклику 0: чекаємо, поки його запит справді летить, і скасовуємо */
    for (let i = 0; моделі.length < 3 && i < 3000; i++) await пауза(20);
    await пауза(DIYA_MS);
  } else await пауза(DIYA_MS);
  await с.evaluate(() => document.getElementById('сц-новий').onclick());
  await пауза(MDELAY * 3 + 1500);
  const ст = await с.evaluate(() => ({ режим: РЕЖИМ, чат: ЧАТ_П.length, паспорт: !!ПАСПОРТ_П, оцінка_викликів: window.__оцінка,
    оц_фото: (ОЦ.фото || []).length, виклики_розмови: ВИКЛИКИ_РОЗМОВИ_П.length,
    виклики_крок: ВИКЛИКИ_РОЗМОВИ_П.map(в => (в.запит || {}).чого || в.крок) }));
  console.log('СЦЕНА', SCEN, JSON.stringify(ст));
  console.log('моделі:', JSON.stringify(моделі.map(м => [м.тип, м.початок.slice(0, 40)])));
  if (жур.length) console.log('журнал:', жур.join(' | '));
  await б.close();
})().catch(е => { console.error('ЗБІЙ', е); process.exit(1); });
