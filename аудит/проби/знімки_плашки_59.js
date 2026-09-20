/* Знімки екрана «Палітра» ДО і ПІСЛЯ градієнта плашок (рядок 59 дошки, 20.09.2026).

   Дорога — та сама, що в `рв6_стенд.js`: зібраний `index.html` у Chromium,
   справжній Pyodide з диска, знайомство руками (кольори ручним шляхом сторінки,
   мірки, «Готово») → репліка в чат → рядок «Палітра» в картці сценарію (до
   заповненого випадку картки з тим рядком на екрані ще нема). Модель — та сама
   заглушка паспорта, що в `рв6_стенд.js`, і тільки вона: САМУ ПАЛІТРУ рахує міст
   у Pyodide, а не мережа. Решта мережі заблокована без винятків.

   СІД ТУТ — ЦЕ ПРОФІЛЬ ЖІНКИ, а не сід моделі: екран палітри не залежить від
   відповідей моделі взагалі (він рахується з кольорів людини), тож єдине, чим
   його можна розрізнити, — колорит. Три сіди = три колорити.

   Крім знімка, друкує ФАКТ ПРО ВИБІР: `ВИБІР.вибір_кольору` після дотику до
   першої плашки-основи. Градієнт — лише показ, тож `база`, `база_hex` і
   `база_тип` мусять лишитись побайтово тими самими до і після правки.

   Запуск:
     CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=джерела/node_modules \
       node аудит/проби/знімки_плашки_59.js <корінь зі зібраним index.html> \
         <тека знімків> <мітка: до|після> <сіди через кому, типово 1,2,3> */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const КОРІНЬ = process.argv[2] || process.cwd();
const ТЕКА = process.argv[3] || '/tmp/знімки';
const МІТКА = process.argv[4] || 'після';
const СІДИ = String(process.argv[5] || '1,2,3').split(',').map(Number);
const ТЕКА_PYODIDE = process.env.PYODIDE_DIR || '/tmp/pyodide';
const БАЗА = 'http://127.0.0.1:8765';
/* Заглушка паспорта — копія `рв6_стенд.js`: сюди йде рівно один виклик (чат →
   `bridge.паспорт`), бо далі стенд знімків у збирання не заходить. */
const ПАСПОРТ = JSON.stringify({подія: 'робочий день в офісі', нагода: 'робота', місце: 'офіс_корпоративний',
  формат: 'приміщення', тривалість_год: 9, рух: 'сидіти', дрес_код: 'business_casual', ошатність: [4, 6],
  година: 9, темп_c: 18, опади: 'ні', намір: 'conventional', бажання: ['щось зі структурою'],
  вето: {типи: ['підбори'], тканини: [], принти: [], кольори: [], зони: []}, ноги_вище_см: null,
  настрій: ['зібрано'], невідомо: ['взуття'], питання_людині: ['Чи буде нарада з керівництвом?'],
  відповідь_людині: 'Зрозуміла: робочий день в офісі, без підборів.'});
/* Три колорити: світлий теплий, темний холодний, середній нейтральний. Формат —
   той самий текст «відповіді чату», який приймає розкривач «Інший шлях». */
const ПРОФІЛІ = {
  1: 'шкіра 1 #deb295\nшкіра 2 #d8a98c\nшкіра 3 #e2ba9f\nволосся #f1dbaa\nволосся #d9bf88\nочі #759087\nкільце #3f4f49',
  2: 'шкіра 1 #8d5a3b\nшкіра 2 #7c4d32\nшкіра 3 #9a6644\nволосся #1b1410\nволосся #2a1f18\nочі #3b2c22\nкільце #3f4f49',
  3: 'шкіра 1 #f0d5c8\nшкіра 2 #ecccbd\nшкіра 3 #f4dcd1\nволосся #6b5744\nволосся #7d6a4f\nочі #5b7f86\nкільце #3f4f49',
};

(async () => {
  fs.mkdirSync(ТЕКА, { recursive: true });
  const браузер = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM || undefined });
  for (const сід of СІДИ) {
    const стор = await (await браузер.newContext({ viewport: { width: 420, height: 1100 }, deviceScaleFactor: 1 })).newPage();
    const цеМіст = u => decodeURIComponent(u.pathname).endsWith('/міст');
    await стор.route(u => u.origin === new URL(БАЗА).origin && !цеМіст(u), async route => {
      const ім = decodeURIComponent(new URL(route.request().url()).pathname).replace(/^\//, '') || 'index.html';
      const ф_ = path.join(КОРІНЬ, ім);
      if (!fs.existsSync(ф_)) return route.fulfill({ status: 404, body: 'нема ' + ім });
      await route.fulfill({ status: 200, contentType: ім.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/plain; charset=utf-8', body: fs.readFileSync(ф_) });
    });
    await стор.route('https://cdn.jsdelivr.net/pyodide/**', async route => {
      const ім = new URL(route.request().url()).pathname.split('/').pop();
      const ф_ = path.join(ТЕКА_PYODIDE, ім);
      if (!fs.existsSync(ф_)) return route.fulfill({ status: 404, body: 'нема ' + ім });
      const тип = ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream';
      await route.fulfill({ status: 200, contentType: тип, body: fs.readFileSync(ф_) });
    });
    await стор.route(u => цеМіст(u), async route => route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ content: [{type: 'text', text: ПАСПОРТ}], usage: {input_tokens: 1, output_tokens: 1}, stop_reason: 'end_turn' }) }));
    await стор.route(u => !(u.origin === new URL(БАЗА).origin) && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href), r => r.abort());

    await стор.goto(БАЗА + '/index.html#міст=' + БАЗА + '/міст&т=tok-znimky', { waitUntil: 'load', timeout: 180000 });
    await стор.waitForFunction(() => typeof РЕЖИМ !== 'undefined' && !!(document.getElementById('н-далі') || {}).onclick, null, { timeout: 180000 });
    await стор.click('#кол-блок details.розкривач > summary');
    await стор.fill('#кол-відповідь', ПРОФІЛІ[сід] || ПРОФІЛІ[1]);
    await стор.click('#кол-читати');
    await стор.fill('[id="пр-імʼя"]', 'Знімок ' + сід);
    await стор.check('#пр-згода');
    await стор.click('#н-далі');
    await стор.waitForFunction(() => ЕКРАН === 1, null, { timeout: 30000 });
    await стор.click('#н-далі');
    await стор.waitForFunction(() => ЕКРАН === 2, null, { timeout: 30000 });
    for (const [і, v] of [['мр-плечі', 98], ['мр-груди', 92], ['мр-талія', 74], ['мр-стегна', 99], ['мр-зріст', 168]])
      await стор.fill('#' + і, String(v));
    await стор.click('#н-далі');
    await стор.waitForFunction(() => РЕЖИМ === 'сценарій' && ПРОФІЛЬ_СТВОРЕНО, null, { timeout: 120000 });
    /* Випадок — реплікою в чат, як у жінки: доти картка сценарію (а з нею рядок
       «Палітра») на екрані не стоїть, і клік падає на «element is not visible». */
    await стор.fill('#чат-поле', 'робочий день в офісі, дрес-код business casual, без підборів');
    await стор.click('#чат-слати');
    await стор.waitForFunction(() => document.querySelectorAll('#чат-стрічка .репліка').length >= 2, null, { timeout: 480000 });
    await стор.click('#пал-кнопка');
    await стор.waitForFunction(() => РЕЖИМ === 'палітра'
        && (document.querySelectorAll('#пал-основа .чип').length > 1
            || /не порахувалась|зчитай/.test((document.getElementById('пал-стан') || {}).textContent || '')),
      null, { timeout: 600000 });
    await стор.waitForTimeout(400);
    const файл = path.join(ТЕКА, 'плашки_59_' + МІТКА + '_сід' + сід + '.png');
    await стор.locator('#е-палітра').screenshot({ path: файл });
    /* ФАКТ ПРО ВИБІР: дотик до першої плашки-основи (не до «хай обере стилістка»). */
    const вибір = await стор.evaluate(() => {
      const ч = [...document.getElementById('пал-основа').children].filter(е => е.dataset && е.dataset.сімя);
      if (!ч[0]) return null;
      ч[0].click();
      const ст = getComputedStyle(ч[0].querySelector('.зразки i'));
      return {підпис: ч[0].textContent.replace(/\s+/g, ' ').trim(), вибір: ВИБІР.вибір_кольору,
              фон_колір: ст.backgroundColor, фон_градієнт: ст.backgroundImage.slice(0, 200),
              плашок: ч.length};
    });
    console.log('сід ' + сід + ' · ' + МІТКА + ' · ' + файл + ' (' + Math.round(fs.statSync(файл).size / 1024) + ' КБ)');
    console.log('   дотик: ' + JSON.stringify(вибір, null, 0));
    await стор.context().close();
  }
  await браузер.close();
})();
