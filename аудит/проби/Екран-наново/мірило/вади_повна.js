/* Мірило наряду Екран-наново: вади 4 і 7 на ПОВНІЙ збірці (Chromium 390×844 з дотиком, Pyodide з диска — кольори
   читає Python). Шлях жінки без портрета: розкрити «Інший шлях», вставити відповідь чат-помічника, торкнути
   «Застосувати кольори» (вада 4: що видно поруч із кнопкою), далі «Далі» — крок «Що тобі до лиця» (вада 7: що екран
   каже про портрет). Знімки — вікно, як його бачить жінка; приладом після дотику не гортаємо.
   Запуск: NODE_PATH=джерела/node_modules CHROMIUM=/opt/pw-browsers/chromium node вади_повна.js <тека з index.html> <кеш Pyodide> <префікс> */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [збірка, піодід, префікс] = process.argv.slice(2);
const БАЗА = 'http://127.0.0.1:8765';
const ЖІНКА = JSON.parse(fs.readFileSync(path.join(__dirname, '../../жінки/ж1.json'), 'utf8'));
(async () => {
  const б = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM || undefined});
  const к = await б.newContext({viewport: {width: 390, height: 844}, hasTouch: true});
  const с = await к.newPage();
  const помилки = [], факти = {};
  с.on('pageerror', e => помилки.push(String(e).slice(0, 300)));
  /* маршрути — як у `аудит/проби/рв6_стенд.js`: сторінка з диска, Pyodide з кешу, решта мережі глуха */
  await с.route('**/*', r => { const у = new URL(r.request().url());
    if (у.origin === БАЗА){ const ф = path.join(збірка, decodeURIComponent(у.pathname).replace(/^\//, '') || 'index.html');
      return fs.existsSync(ф) ? r.fulfill({contentType: ф.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/plain; charset=utf-8', body: fs.readFileSync(ф)}) : r.fulfill({status: 404, body: 'нема'}); }
    if (/cdn\.jsdelivr\.net\/pyodide/.test(у.href)){ const ім = у.pathname.split('/').pop(), ф = path.join(піодід, ім);
      const тип = ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream';
      return fs.existsSync(ф) ? r.fulfill({contentType: тип, body: fs.readFileSync(ф)}) : r.fulfill({status: 404, body: 'нема'}); }
    return r.abort(); });
  const знімок = ім => с.screenshot({path: префікс + '_' + ім + '.png'});
  const тихо = мс => с.waitForTimeout(мс || 400);
  const уВікні = сел => с.evaluate(сел => { const в = document.querySelector(сел); if (!в) return null; const р = в.getBoundingClientRect();
    return {верх: Math.round(р.top), низ: Math.round(р.bottom), видно_ціле: р.height > 0 && р.top >= 0 && р.bottom <= innerHeight,
      текст: (в.textContent || в.value || '').replace(/\s+/g, ' ').trim().slice(0, 200)}; }, сел);
  await с.goto(БАЗА + '/index.html', {waitUntil: 'load', timeout: 180000});
  /* старт скінчився (на гілці — прапорець `Екран.стан.запущено`; на `main` його нема) і Python піднявся: блок кольорів видно */
  await с.waitForFunction(() => { const д = document.getElementById('н-далі'), б = document.getElementById('кол-блок');
    return д && д.getBoundingClientRect().height > 0 && б && б.getBoundingClientRect().height > 0
      && (typeof Екран === 'undefined' || !Екран.стан || !('запущено' in Екран.стан) || Екран.стан.запущено); }, null, {timeout: 300000});
  await тихо(1500);
  /* шлях без портрета: на гілці — кнопка на першому екрані (вада 13), на `main` — розкривач під гортанням */
  if (await с.locator('#кол-без-портрета').count()) await с.locator('#кол-без-портрета').tap();
  else { await с.locator('#кол-блок details.розкривач > summary').scrollIntoViewIfNeeded(); await с.locator('#кол-блок details.розкривач > summary').tap(); }
  await тихо(800);
  await с.locator('#кол-відповідь').scrollIntoViewIfNeeded();
  await с.locator('#кол-відповідь').fill(JSON.stringify({photo: 'usable', skin: ЖІНКА.skin, hair: ЖІНКА.hair, eyes: ЖІНКА.eyes, limbal_ring: ЖІНКА.ring}));
  /* кнопку жінка бачить і торкає; після дотику — нічого не гортаємо, чекаємо лише, поки Python прочитає */
  await с.locator('#кол-читати').scrollIntoViewIfNeeded(); await тихо(400);
  факти.до_дотику = {вгорі: await с.evaluate(() => Math.round(scrollY)), кнопка: await уВікні('#кол-читати')};
  await знімок('4_до_дотику');
  /* Python зайнятий, як у перші десятки секунд після відкриття сторінки в живому прогоні: читання відповіді чекає 3 с.
     Що жінка бачить біля кнопки, поки він читає, — знімок через 1,5 с після дотику */
  await с.evaluate(() => { const було = читатиВідповідьКольоруП; читатиВідповідьКольоруП = async в => { await new Promise(д => setTimeout(д, 3000)); return було(в); }; });
  await с.locator('#кол-читати').tap();
  await тихо(1500);
  факти.в4_поки_читає = {стан_кольору: await с.evaluate(() => (typeof СТАН_КОЛЬОРУ_П !== 'undefined' && СТАН_КОЛЬОРУ_П && СТАН_КОЛЬОРУ_П.стан) || null),
    кнопка: await уВікні('#кол-читати'), рядок_стану: await уВікні('#кол-стан'),
    рядок_під_кнопкою: await с.evaluate(() => { const р = document.getElementById('кол-читати').closest('.ряд'); return !!р && р.nextElementSibling === document.getElementById('кол-стан'); })};
  await знімок('4_поки_читає');
  await с.waitForFunction(() => typeof СТАН_КОЛЬОРУ_П !== 'undefined' && СТАН_КОЛЬОРУ_П && СТАН_КОЛЬОРУ_П.стан === 'готово', null, {timeout: 120000})
    .catch(() => помилки.push('стан кольору не став «готово»'));
  await тихо(1200);
  факти.в4 = {вгорі: await с.evaluate(() => Math.round(scrollY)), кнопка: await уВікні('#кол-читати'), стан: await уВікні('#кол-стан'), свотчі: await уВікні('#кол-свотчі'),
    /* усе з текстом між верхом кнопки − 160 px і її низом + 160 px, що видно у вікні, крім самої кнопки й поля відповіді */
    поруч: await с.evaluate(() => { const кн = document.getElementById('кол-читати').getBoundingClientRect();
      return [...document.querySelectorAll('#кол-блок *')].filter(е => !е.children.length && е.id !== 'кол-читати' && е.tagName !== 'TEXTAREA' && (е.textContent || '').trim())
        .map(е => [е, е.getBoundingClientRect()]).filter(([, р]) => р.height > 0 && р.top >= 0 && р.bottom <= innerHeight && р.bottom >= кн.top - 160 && р.top <= кн.bottom + 160)
        .map(([е, р]) => ({ід: е.id || е.className || е.tagName, верх: Math.round(р.top), текст: е.textContent.replace(/\s+/g, ' ').trim().slice(0, 120)})); }),
    колір: await с.evaluate(() => ({стан: СТАН_КОЛЬОРУ_П && СТАН_КОЛЬОРУ_П.стан, шкіра: КОЛІР.шкіра, джерело: КОЛІР.джерело || null}))};
  await знімок('4_після_застосувати');
  /* крок 2 «Що тобі до лиця» */
  await с.evaluate(() => scrollTo(0, 0)); await тихо(300);
  await с.locator('[id="пр-імʼя"]').fill('Оля'); await с.locator('#пр-згода').check();
  await с.locator('#н-далі').scrollIntoViewIfNeeded(); await с.locator('#н-далі').tap();
  await с.waitForFunction(() => { const е = document.getElementById('е-лице'); return е && е.getBoundingClientRect().height > 0; }, null, {timeout: 60000});
  await тихо(1500);
  факти.в7 = {вгорі: await с.evaluate(() => Math.round(scrollY)), напис: await уВікні('#др-нема')};
  await знімок('7_до_лиця');
  факти.помилки = помилки;
  fs.writeFileSync(префікс + '_повна_факти.json', JSON.stringify(факти, null, 1));
  console.log(JSON.stringify(факти));
  await б.close();
})().catch(e => { console.error('ЗБІЙ ПРОБИ', e); process.exit(1); });
