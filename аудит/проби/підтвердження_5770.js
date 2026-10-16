/* Рядки 5770 і 5771: крок підтвердження переліку речей у справжньому Chromium на ЗІБРАНІЙ сторінці, справжній Pyodide,
   модель — заглушка (відповіді «речі» й «оцінка» з готових даних), мережі нема. Міряє:
   (А, 5770) дотик «Так, оцінюй», поки суд іде в Pyodide: затримка обробки дотику (`performance.now()` в обробнику −
       `event.timeStamp` дотику) і `етапи.підтвердження.мс_до_так`, поруч — `етапи.суд.мс`; дотик шле сам прилад
       (`mouse.click`), через ГЛЯНУЛА_МС (типово 1500 мс, env GLIANULA_MS) після першого малювання переліку, без жодного опитування сторінки (опитування стояло б у тій самій черзі);
   (В, 5841) екран «Роздивляюсь речі…» (від `оцінитиОбразП` до першого малювання переліку): крок мосту «каталог» і шматки,
       на які він розпадається (`кроки_мосту`), найдовша зупинка головного потоку (`макс_зупинка_до_переліку_мс`) і те, як
       довго `mouse.move` чекав сторінки (`відгук_на_рух_до_переліку_мс`) — заглушка моделі «речі» відповідає за 4 с;
   (Б, 5771) положення кнопки «Так, оцінюй» у вікні 390×844 при 5, 6 і 8 речах синтетичного переліку (без суду):
       нижній край кнопки проти верху нижньої панелі, без прокрутки й з нею; знімки вікна.
   Запуск: NODE_PATH=<тека з playwright> CHROMIUM=/opt/pw-browsers/chromium MITKA=<до|після> node аудит/проби/підтвердження_5770.js \
             <тека зі зібраним index.html> <тека pyodide v0.26.4> [тека знімків] */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [, , КОРІНЬ, ТЕКА_PYODIDE, ЗНІМКИ] = process.argv;
const БАЗА = 'http://127.0.0.1:8765';
/* скільки вона дивиться на перелік до дотику: суд тим часом уже йде */
const ГЛЯНУЛА_МС = Number(process.env.GLIANULA_MS || 1500);
const с = мс => new Promise(р => setTimeout(р, мс));
const ФІГУРИ = {
  'ф1': {ш: 600, в: 800, тло: '#efe9e1', фігури: [
    ['#7d7f63', [[170, 90], [430, 90], [480, 130], [480, 440], [430, 440], [430, 470], [170, 470], [170, 440], [120, 440], [120, 130]]],
    ['#cfd8e3', 250, 110, 350, 400], ['#6b1f2a', [[200, 520], [400, 520], [430, 760], [170, 760]]]]},
  'ф2': {ш: 600, в: 600, тло: '#8c96a0', фігури: [['#e6dfd2', '#6b5b4c', 0], ['#1d1c1c', '#4a4646', 260]].flatMap(([колір, підошва, зсув]) => [
    [колір, [[98, 170], [190, 170], [194, 336], [214, 370], [248, 393], [266, 418], [270, 446], [264, 462], [98, 462]]],
    [підошва, [[140, 462], [268, 462], [266, 470], [256, 474], [140, 474]]], [підошва, [[98, 462], [136, 462], [134, 480], [100, 480]]]]
    .map(([к, т]) => [к, т.map(([x, y]) => [x + зсув, y])]))}};
const РЕЧІ = [
  {photo: 'ф1', name: 'fitted blazer', slot: 'outerwear', color: 'khaki', cut: 'fitted', pattern: 'solid', formality: 6, in_outfit: true, frame: {left: 150, top: 80, right: 850, bottom: 620}},
  {photo: 'ф1', name: 'draped shirt', slot: 'top', color: 'light_blue', pattern: 'solid', formality: 5, in_outfit: true, frame: {left: 400, top: 130, right: 600, bottom: 510}},
  {photo: 'ф1', name: 'leather mini skirt', slot: 'bottom', color: 'burgundy', length: 'mini', pattern: 'solid', formality: 6, in_outfit: true, frame: {left: 240, top: 630, right: 760, bottom: 980}},
  {photo: 'ф2', name: 'cream ankle boots', slot: 'shoes', color: 'cream', pattern: 'solid', formality: 6, in_outfit: true, frame: {left: 80, top: 230, right: 490, bottom: 850}},
  {photo: 'ф2', name: 'black ankle boots', slot: 'shoes', color: 'black', pattern: 'solid', formality: 6, in_outfit: false, frame: {left: 510, top: 230, right: 920, bottom: 850}}];
(async () => {
  const б = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium' });
  const вих = {};
  /* прогін із дотиком: tap=true — прилад тисне «Так» у момент першого малювання переліку; tap=false — без дотику (лише суд) */
  async function готова(){
    const стор = await (await б.newContext({ viewport: { width: 390, height: 844 }, hasTouch: false })).newPage();
    await стор.route(u => u.origin === new URL(БАЗА).origin, r => {
      const ім = decodeURIComponent(new URL(r.request().url()).pathname).replace(/^\//, '') || 'index.html', ф = path.join(КОРІНЬ, ім);
      if (!fs.existsSync(ф)) return r.fulfill({ status: 404, body: 'нема' });
      r.fulfill({ status: 200, contentType: ім.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/plain; charset=utf-8', body: fs.readFileSync(ф) });
    });
    await стор.route('https://cdn.jsdelivr.net/pyodide/**', r => {
      const ім = new URL(r.request().url()).pathname.split('/').pop(), ф = path.join(ТЕКА_PYODIDE, ім);
      const тип = ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream';
      r.fulfill({ status: 200, contentType: тип, body: fs.readFileSync(ф) });
    });
    await стор.route(u => u.origin !== new URL(БАЗА).origin && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href), r => r.abort());
    await стор.goto(БАЗА + '/index.html#міст=' + БАЗА + '/міст&т=tok-5770', { waitUntil: 'load', timeout: 180000 });
    await стор.waitForFunction(() => typeof РЕЖИМ !== 'undefined' && !!(document.getElementById('н-далі') || {}).onclick, null, { timeout: 180000 });
    /* знайомство — кнопками, як у стенда: кольори ручним шляхом, мірки, «Готово» */
    await стор.click('#кол-блок details.розкривач > summary');
    await стор.fill('#кол-відповідь', 'шкіра 1 #deb295\nшкіра 2 #d8a98c\nшкіра 3 #e2ba9f\nволосся #f1dbaa\nволосся #d9bf88\nочі #759087\nкільце #3f4f49');
    await стор.click('#кол-читати');
    await стор.fill('[id="пр-імʼя"]', 'Проба 5770'); await стор.check('#пр-згода');
    await стор.click('#н-далі'); await стор.waitForFunction(() => ЕКРАН === 1, null, { timeout: 30000 });
    await стор.click('#н-далі'); await стор.waitForFunction(() => ЕКРАН === 2, null, { timeout: 30000 });
    for (const [і, v] of [['мр-плечі', 98], ['мр-груди', 92], ['мр-талія', 74], ['мр-стегна', 99], ['мр-зріст', 168]]) await стор.fill('#' + і, String(v));
    await стор.click('#н-далі'); await стор.waitForFunction(() => РЕЖИМ === 'сценарій' && ПРОФІЛЬ_СТВОРЕНО, null, { timeout: 60000 });
    await стор.evaluate(() => режим('оцінка')); await с(300);
    const фото = [];
    for (const ід of ['ф1', 'ф2']){
      const б64 = await стор.evaluate(о => {
        const к = document.createElement('canvas'); к.width = о.ш; к.height = о.в; const x = к.getContext('2d'); x.fillStyle = о.тло; x.fillRect(0, 0, о.ш, о.в);
        for (const [колір, л, в, п, н] of о.фігури){ x.fillStyle = колір;
          if (Array.isArray(л)){ x.beginPath(); л.forEach(([а, б], і) => і ? x.lineTo(а, б) : x.moveTo(а, б)); x.closePath(); x.fill(); } else x.fillRect(л, в, п - л, н - в); }
        return к.toDataURL('image/jpeg', 0.92).split(',')[1]; }, ФІГУРИ[ід]);
      фото.push({name: 'obraz_' + ід + '.jpg', mimeType: 'image/jpeg', buffer: Buffer.from(б64, 'base64')});
    }
    await стор.setInputFiles('#оц-файл', фото);
    await стор.waitForFunction(() => ОЦ.фото.length === 2, null, { timeout: 30000 });
    return стор;
  }
  async function прогін(дотик){
    const стор = await готова();
    /* модель — заглушка на рівні сторінки; Pyodide, міст і суд — справжні */
    /* відгук сторінки на ввід, поки суд іде: прилад водить мишею, кожен рух — окремий дотик до головного потоку,
       і `mouse.move` повертається, лише коли сторінка його прийняла; найдовше очікування — найгірший дотик жінки */
    let судЙде = true, доПереліку = true; const відгук = [], відгукДо = [];
    await стор.exposeFunction('__судКінець', () => { судЙде = false; });
    await стор.exposeFunction('__перелікМалюється', async (х, у) => {
      доПереліку = false;
      if (дотик === null) return;
      (async () => { let k = 0; while (судЙде) { const т = Date.now(); await стор.mouse.move(х + (k++ % 2), 5); відгук.push(Date.now() - т); await с(15); } })().catch(() => {});
      if (дотик) { await с(ГЛЯНУЛА_МС); await стор.mouse.click(х, у); } });
    await стор.evaluate(({РЕЧІ}) => {
      window.__ч = {};
      window.викликОцінкиП = async (крок, промпт) => {
        if (/^речі/.test(крок)){ await new Promise(р => setTimeout(р, 4000)); return JSON.stringify({items: РЕЧІ}); }   // модель дивиться на фото: каталог гріється
        let об = null; try { об = JSON.parse(промпт); } catch (_) {}
        const образ = (об && об.outfit) || [];
        return JSON.stringify({answer: 'Yes, these colors go together.', verdict: 'wear_as_is', works: [{about: 'contrast', items: образ.slice(0, 1), text: 'Contrast works.'}], change: [], unknown: []});
      };
      const мал = window.малюватиПерелікП;
      window.малюватиПерелікП = function(){
        const р = мал.apply(this, arguments), к = document.getElementById('оц-так');
        if (к && !window.__ч.показано){
          window.__ч.показано = performance.now(); к.scrollIntoView({block: 'center'});
          /* пульс: найдовша зупинка головного потоку, поки суд іде, — це найгірший дотик */
          window.__ч.пульс = {макс: 0, останній: performance.now(), зупинки: []};
          (function тік(){ const п = window.__ч.пульс, т = performance.now(); п.макс = Math.max(п.макс, т - п.останній); if (т - п.останній > 250) п.зупинки.push([Math.round(п.останній - window.__ч.показано), Math.round(т - п.останній)]); п.останній = т;
            if (!window.__ч.суд_кінець) setTimeout(тік, 4); })();
          const r = к.getBoundingClientRect(); window.__перелікМалюється(r.left + r.width / 2, r.top + r.height / 2);
          к.addEventListener('pointerdown', e => { window.__ч.pointerdown_ts = e.timeStamp; window.__ч.pointerdown_оброблено = performance.now(); }, {capture: true});
        }
        return р;
      };
      const кар = window.малюватиКарткуОцінкиП;
      window.малюватиКарткуОцінкиП = function(){ const р = кар.apply(this, arguments);
        if (document.getElementById('оц-картка') && !window.__ч.картка) window.__ч.картка = performance.now(); return р; };
      for (const ім_ of ['містП', 'містАП']){   // суд ходить `містАП` (після правки) або `містП` (до неї)
        const міст = window[ім_]; if (!міст) continue;
        window[ім_] = async function(ім, д){ const т0 = performance.now(), р = await міст.apply(this, arguments);
          if (д && д.крок === 'суд'){ window.__ч.суд_початок = т0; window.__ч.суд_кінець = performance.now(); window.__судКінець(); }
          (window.__ч.кроки = window.__ч.кроки || []).push([д && д.крок, Math.round(т0 - window.__ч.пуск), Math.round(performance.now() - window.__ч.пуск)]); return р; };
      }
    }, {РЕЧІ});
    /* екран «Роздивляюсь речі…»: той самий водій миші й пульс головного потоку, але від пуску й до малювання переліку */
    await стор.evaluate(() => { const ч = window.__ч; ч.пульс_до = {макс: 0, останній: performance.now()};
      (function тік(){ const п = ч.пульс_до, т = performance.now(); п.макс = Math.max(п.макс, т - п.останній); п.останній = т; if (!ч.показано) setTimeout(тік, 4); })(); });
    (async () => { let k = 0; while (доПереліку) { const т = Date.now(); await стор.mouse.move(100 + (k++ % 2), 5); відгукДо.push(Date.now() - т); await с(15); } })().catch(() => {});
    await стор.evaluate(() => { window.__ч.пуск = performance.now(); оцінитиОбразП(); });
    await стор.waitForFunction(() => !ОЦ.іде, null, { timeout: 300000, polling: 500 });
    if (!дотик) await с(0);
    const р = await стор.evaluate(() => { const ч = window.__ч, е = ОЦ.етапи || {};
      return {макс_зупинка_до_переліку_мс: ч.пульс_до && Math.round(ч.пульс_до.макс), макс_зупинка_потоку_мс: ч.пульс && Math.round(ч.пульс.макс), зупинки_понад_250мс_від_показу: ч.пульс && ч.пульс.зупинки, кроки_мосту: ч.кроки, суд_мс: (е.суд || {}).мс, мс_до_так: (е.підтвердження || {}).мс_до_так, відгук_мс_у_звіті: (е.підтвердження || {}).відгук_мс, дотиків: (е.підтвердження || {}).дотиків,
        перелік_показано_с: ч.показано && +((ч.показано - ч.пуск) / 1000).toFixed(1),
        суд_початок_с: ч.суд_початок && +((ч.суд_початок - ч.пуск) / 1000).toFixed(1), суд_кінець_с: ч.суд_кінець && +((ч.суд_кінець - ч.пуск) / 1000).toFixed(1),
        дотик_оброблено_с: ч.pointerdown_оброблено && +((ч.pointerdown_оброблено - ч.пуск) / 1000).toFixed(1),
        затримка_дотику_мс: ч.pointerdown_ts != null ? Math.round(ч.pointerdown_оброблено - ч.pointerdown_ts) : null,
        картка_с: ч.картка && +((ч.картка - ч.пуск) / 1000).toFixed(1), каталог_етап: е.каталог || null, помилка: е.помилка || null, картка_є: !!document.getElementById('оц-картка')}; });
    відгукДо.sort((a, b) => a - b);
    р.відгук_на_рух_до_переліку_мс = відгукДо.length ? {рухів: відгукДо.length, макс: відгукДо[відгукДо.length - 1], p95: відгукДо[Math.floor(відгукДо.length * 0.95)], медіана: відгукДо[Math.floor(відгукДо.length / 2)]} : null;
    відгук.sort((a, b) => a - b);
    р.відгук_на_рух_мс = відгук.length ? {рухів: відгук.length, макс: відгук[відгук.length - 1], p95: відгук[Math.floor(відгук.length * 0.95)], медіана: відгук[Math.floor(відгук.length / 2)]} : null;
    await стор.context().close();
    return р;
  }
  /* Б. РОЗКЛАДКА (5771): синтетичний перелік із N речей без суду; стан сторінки — як у жінки, що натиснула «Оцінити»
     (кнопка посеред вікна), далі — як перелік сам себе показав. Нижній край кнопки проти верху нижньої панелі. */
  async function розкладка(N, знімок){
    const стор = await готова();
    const р = await стор.evaluate(async N => {
      const слоти = Object.keys(СЛОТ_НАЗВ_П), речі = [];
      for (let i = 0; i < N; i++) речі.push({ід: (i % 2 ? 'ф2' : 'ф1') + (i > 1 ? '·' + (i + 1) : ''), фото: i % 2 ? 'ф2' : 'ф1', слот: слоти[i % слоти.length],
        колір: 'чорний', в_образі: i < 5, рамка: {ліво: 100, верх: 100, право: 700, низ: 800}});
      ОЦ.етапи = {мова_шару: []}; ОЦ.ід = 'x'; ОЦ.результат = null;
      document.getElementById('оц-оцінити').scrollIntoView({block: 'center'});
      await показатиПерелікП(речі);
      await new Promise(р => setTimeout(р, 400));
      const к = document.getElementById('оц-так').getBoundingClientRect(), п = document.getElementById('ніг').getBoundingClientRect();
      const рядки = [...document.querySelectorAll('#оц-речі .оц-річ')].map(е => е.getBoundingClientRect());
      return {речей: N, вікно: innerHeight, прокрутка: Math.round(scrollY), панель_верх: Math.round(п.top), кнопка_верх: Math.round(к.top), кнопка_низ: Math.round(к.bottom),
        кнопку_видно: к.top >= 0 && к.bottom <= п.top, рядків_видно: рядки.filter(r => r.top >= 0 && r.bottom <= п.top).length, рядків: рядки.length,
        висота_переліку: Math.round(document.getElementById('оц-речі').getBoundingClientRect().height)};
    }, N);
    if (ЗНІМКИ) { fs.mkdirSync(ЗНІМКИ, {recursive: true}); await стор.screenshot({path: path.join(ЗНІМКИ, 'перелік_' + N + '_' + (process.env.MITKA || 'зараз') + '.png')}); }
    await стор.context().close();
    return р;
  }
  if (process.env.TIL_RAZKLADKA !== '1') вих.з_дотиком = await прогін(true);
  вих.розкладка = [];
  for (const N of [5, 6, 8]) вих.розкладка.push(await розкладка(N));
  console.log(JSON.stringify(вих, null, 1));
  await б.close();
})();
