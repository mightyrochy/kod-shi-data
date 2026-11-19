/* СТЕНД ШЛЯХУ `claude-` МОСТА (наряд «Модель-текст-на-Claude», крок 2): зібрана сторінка (`index.html`) у Chromium
   телефона, а `/міст` — САМ КОД МОСТА (`джерела/worker_джерело.js`, `fetch` воркера в цьому ж процесі), і лише
   api.anthropic.com підмінено: справжнього ключа в сесії нема. Режим `кредити` відповідає так, як Anthropic відповідає
   акаунту без кредитів (400 invalid_request_error «Your credit balance is too low…»), — і стенд пише, що жінка бачить.
   Запуск: NODE_PATH=/opt/node22/lib/node_modules node стенд_моста.js <корінь репозиторію> <тека виводу> [кредити]
   Pyodide тягнеться з CDN curl-ом у /tmp/pyodide (Chromium за агентським проксі сам туди не ходить). */
const {chromium} = require('playwright');
const fs = require('fs'), path = require('path'), os = require('os'), {execFileSync} = require('child_process');
const {pathToFileURL} = require('url');
const [КОРІНЬ, ВИХІД, РЕЖИМ = 'кредити'] = process.argv.slice(2);
const БАЗА = 'http://127.0.0.1:8799', ТЕКА_PYODIDE = '/tmp/pyodide';
const с = мс => new Promise(р => setTimeout(р, мс));
const БЕЗ_КРЕДИТІВ = {type: 'error', error: {type: 'invalid_request_error',
  message: 'Your credit balance is too low to access the Anthropic API. Please go to Plans & Billing to upgrade or purchase credits.'}};

(async () => {
  fs.mkdirSync(ВИХІД, {recursive: true}); fs.mkdirSync(ТЕКА_PYODIDE, {recursive: true});
  const сир = fs.readFileSync(path.join(КОРІНЬ, 'джерела', 'worker_джерело.js'), 'utf-8').replace(/^export default/m, 'const М =');
  const мод = path.join(os.tmpdir(), '_стенд_моста.mjs'); fs.writeFileSync(мод, сир + '\nexport {М};');
  const {М} = await import(pathToFileURL(мод).href);
  const вихідні = [];
  globalThis.fetch = async (url, opts) => {          // лише те, що міст шле провайдеру
    вихідні.push({url: String(url), body: JSON.parse(opts.body)});
    if (РЕЖИМ === 'кредити') return new Response(JSON.stringify(БЕЗ_КРЕДИТІВ), {status: 400, headers: {'content-type': 'application/json'}});
    return new Response(JSON.stringify({content: [{type: 'text', text: '{}'}], stop_reason: 'end_turn', usage: {input_tokens: 1, output_tokens: 1}}), {status: 200});
  };
  const env = {ALLOWED_ORIGINS: БАЗА, TESTER_TOKENS: 'tok-stend', ANTHROPIC_API_KEY: 'sk-стенд'};

  const браузер = await chromium.launch({headless: true});
  const стор = await (await браузер.newContext({viewport: {width: 390, height: 844}, isMobile: true, hasTouch: true,
    deviceScaleFactor: 2, locale: 'uk-UA', timezoneId: 'Europe/Kyiv'})).newPage();
  const консоль = []; стор.on('console', m => консоль.push(m.type() + ': ' + m.text().slice(0, 300)));
  стор.on('pageerror', e => консоль.push('pageerror: ' + String(e).slice(0, 300)));
  const цеМіст = u => decodeURIComponent(u.pathname).endsWith('/міст');
  await стор.route(u => u.origin === БАЗА && !цеМіст(u), async route => {
    const ім = decodeURIComponent(new URL(route.request().url()).pathname).replace(/^\//, '') || 'index.html';
    const ф = path.join(КОРІНЬ, ім);
    if (!fs.existsSync(ф)) return route.fulfill({status: 404, body: 'нема ' + ім});
    await route.fulfill({status: 200, contentType: ім.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/plain; charset=utf-8', body: fs.readFileSync(ф)});
  });
  await стор.route('https://cdn.jsdelivr.net/pyodide/**', async route => {
    const u = route.request().url(), ім = new URL(u).pathname.split('/').pop(), ф = path.join(ТЕКА_PYODIDE, ім);
    if (!fs.existsSync(ф)) try { execFileSync('curl', ['-sSfL', '-o', ф, u], {timeout: 120000}); } catch (_) {}
    if (!fs.existsSync(ф)) return route.fulfill({status: 404, body: 'нема ' + ім});
    const тип = ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream';
    await route.fulfill({status: 200, contentType: тип, body: fs.readFileSync(ф)});
  });
  await стор.route(u => u.origin !== БАЗА && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href), route => route.abort());
  await стор.route(u => цеМіст(u), async route => {
    const з = route.request();
    const в = await М.fetch(new Request('https://lyusterko-mist.example/', {method: з.method(), headers: з.headers(),
      body: з.method() === 'POST' ? з.postData() : undefined}), env);
    const заг = {}; в.headers.forEach((з, і) => { заг[і] = з; });
    await route.fulfill({status: в.status, headers: заг, body: Buffer.from(await в.arrayBuffer())});
  });
  await стор.goto(БАЗА + '/index.html#міст=' + БАЗА + '/міст&т=tok-stend&модель=claude-sonnet-5-5&модель_мови=claude-sonnet-5-5',
    {waitUntil: 'load', timeout: 180000});
  const чекати = async (що, ф, арг, мс = 120000) => { try { await стор.waitForFunction(ф, арг, {timeout: мс, polling: 250}); }
    catch (е) { throw new Error('не дочекались: ' + що); } };
  await чекати('стартовий екран', () => typeof Екран !== 'undefined' && Екран.стан.вхід > 0 && !!Екран.стан.запущено
    && !!document.getElementById('н-далі'), null, 180000);
  /* знайомство — руками, як жінка без портрета (рецепт `аудит/проби/рв6_стенд.js`, «0. ЗНАЙОМСТВО»): кольори —
     розкривач «через чат-помічник», вставлена відповідь, «Застосувати»; три кроки «Далі» → «Далі» → «Готово» */
  await стор.click('#кол-блок details.розкривач > summary');
  await стор.fill('#кол-відповідь', JSON.stringify({photo: 'usable', skin: ['#f2d6c4', '#e9c7b0', '#dcb79f'],
    hair: ['#4a4644', '#5a524c'], eyes: '#6b8cae', limbal_ring: 'visible'}));
  await стор.click('#кол-читати');
  await чекати('кольори лягли', () => typeof СТАН_КОЛЬОРУ_П !== 'undefined' && СТАН_КОЛЬОРУ_П && СТАН_КОЛЬОРУ_П.стан === 'готово', null, 60000);
  await стор.fill('[id="пр-імʼя"]', 'Проба кредитів');
  await стор.check('#пр-згода');
  await стор.click('#н-далі');
  await чекати('крок 2', () => Екран.стан.крок === 1, null, 30000);
  await стор.click('#н-далі');
  await чекати('крок 3', () => Екран.стан.крок === 2, null, 30000);
  for (const [і, v] of [['мр-плечі', 98], ['мр-груди', 92], ['мр-талія', 74], ['мр-стегна', 99], ['мр-зріст', 168]]) await стор.fill('#' + і, String(v));
  await стор.click('#н-далі');
  await чекати('сценарій і профіль', () => Екран.стан.режим === 'сценарій' && ПРОФІЛЬ_СТВОРЕНО, null, 60000);
  await стор.fill('#чат-поле', 'Новорічна вечірка в ресторані, надворі мороз');
  await стор.click('#чат-слати');
  const т0 = Date.now();
  while (Date.now() - т0 < 240000) {
    await с(2000);
    const к = await стор.evaluate(() => [...document.querySelectorAll('#чат-стрічка .репліка')].length);
    if (вихідні.length && к >= 2) break;
    if (вихідні.length && Date.now() - т0 > 60000) break;
  }
  await с(4000);
  const видно = await стор.evaluate(() => ({
    стрічка: [...document.querySelectorAll('#чат-стрічка .репліка')].map(р => р.textContent.trim()),
    стан: (document.getElementById('чат-стан') || {}).textContent || '',
    поле_закрите: (document.getElementById('чат-поле') || {}).disabled,
    екран: document.body.innerText.split('\n').map(с => с.trim()).filter(Boolean).slice(0, 80),
    збої_жінці: (typeof ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П !== 'undefined') ? ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П : null}));
  await стор.screenshot({path: path.join(ВИХІД, 'чат_' + РЕЖИМ + '.png')});
  const звіт = {режим: РЕЖИМ, викликів_провайдера: вихідні.length,
    перше_тіло_провайдеру: вихідні[0] && {...вихідні[0].body, messages: '(' + JSON.stringify(вихідні[0].body.messages).length + ' симв)'},
    видно, консоль: консоль.filter(р => /error|warn|збій|кредит|credit/i.test(р)).slice(0, 20)};
  fs.writeFileSync(path.join(ВИХІД, 'чат_' + РЕЖИМ + '.json'), JSON.stringify(звіт, null, 1));
  console.log(JSON.stringify({викликів: вихідні.length, стрічка: видно.стрічка, стан: видно.стан, збої: видно.збої_жінці}, null, 1));
  await браузер.close();
})().catch(е => { console.error('стенд не піднявся:', е); process.exit(2); });
