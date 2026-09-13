/* РВ-3 · РУЧНА ПРОБА ЧАТУ НА СТЕНДІ, справжнім браузером: зібраний показ (index.html з
   HEAD), справжній Pyodide із CDN і справжній `bridge` у ньому; модель — сценарна
   заглушка у форматі відповіді Anthropic (живих викликів у ревізії нема). Це шов, якого
   jsdom-батарея не міряє: там `містП` — заглушка. Запуск (сервер на корені репозиторію):
     python3 -m http.server 8765 --bind 127.0.0.1 &
     NODE_PATH=/opt/node22/lib/node_modules node аудит/проби/рв3_стенд_чат.js http://127.0.0.1:8765 /home/user/kod-shi-data <тека з файлами pyodide 0.26.4> */
const { chromium } = require('playwright');
const БАЗА = process.argv[2] || 'http://127.0.0.1:8765';
const с = мс => new Promise(р => setTimeout(р, мс));
(async () => {
  const т0 = Date.now(), ч = () => ((Date.now() - т0) / 1000).toFixed(1) + ' с';
  const браузер = await chromium.launch({ headless: true,
    proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY, bypass: 'localhost,127.0.0.1' } : undefined });
  const стор = await (await браузер.newContext({ ignoreHTTPSErrors: true })).newPage();
  const консоль = [];
  стор.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') консоль.push(m.type() + ': ' + m.text().slice(0, 300)); });
  стор.on('pageerror', e => консоль.push('pageerror: ' + String(e).slice(0, 300)));
  const промпти = [];
  let вето = ['підбори'];
  const паспортМоделі = () => JSON.stringify({подія: 'побачення в ресторані', нагода: 'побачення',
    місце: 'ресторан_районний', формат: 'приміщення', тривалість_год: 3, рух: 'сидіти', дрес_код: null,
    ошатність: null, година: 19, темп_c: 12, опади: 'так', намір: 'conventional', бажання: [],
    вето: {типи: вето.slice(), тканини: [], принти: [], кольори: [], зони: []}, ноги_вище_см: null,
    настрій: [], невідомо: ['дрес_код'], питання_людині: ['Наскільки ошатно там буде?'],
    відповідь_людині: 'Зрозуміла: побачення в ресторані ввечері, під дощем, без підборів.'});
  /* ЛОКАЛЬНЕ — З ДИСКА, НЕ ЧЕРЕЗ ПРОКСІ: Playwright знімає обхід loopback для проксі, і
     запит до 127.0.0.1 їхав у агентський проксі (405). Тому index.html і збирання.txt
     віддаються з кореня репозиторію тут же, а в мережу йде лише CDN Pyodide. */
  const fs = require('fs'), path = require('path'), КОРІНЬ = process.argv[3] || process.cwd();
  const цеМіст = u => decodeURIComponent(u.pathname).endsWith('/міст');   // шлях у URL закодований відсотками
  await стор.route(u => u.origin === new URL(БАЗА).origin && !цеМіст(u), async route => {
    const ім = decodeURIComponent(new URL(route.request().url()).pathname).replace(/^\//, '') || 'index.html';
    const ф = path.join(КОРІНЬ, ім);
    if (!fs.existsSync(ф)) return route.fulfill({ status: 404, body: 'нема ' + ім });
    const тип = ім.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/plain; charset=utf-8';
    await route.fulfill({ status: 200, contentType: тип, body: fs.readFileSync(ф) });
  });
  /* PYODIDE — ТЕЖ ІЗ ДИСКА: агентський проксі не пускає Chromium на CDN (у продукті на
     Pages файли йдуть із cdn.jsdelivr.net). Скачано curl-ом заздалегідь у теку argv[4];
     файл, якого там нема, лягає в лог — це і є перелік того, що показ справді тягне. */
  const ТЕКА_PYODIDE = process.argv[4] || '/tmp/pyodide', тягнув = [];
  await стор.route('https://cdn.jsdelivr.net/pyodide/**', async route => {
    const ім = new URL(route.request().url()).pathname.split('/').pop(); тягнув.push(ім);
    const ф = path.join(ТЕКА_PYODIDE, ім);
    if (!fs.existsSync(ф)) return route.fulfill({ status: 404, body: 'нема ' + ім });
    const тип = ім.endsWith('.wasm') ? 'application/wasm' : ім.endsWith('.js') || ім.endsWith('.mjs') ? 'application/javascript'
              : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream';
    await route.fulfill({ status: 200, contentType: тип, body: fs.readFileSync(ф) });
  });
  await стор.route(u => цеМіст(u), async route => {
    const тіло = route.request().postDataJSON() || {};
    const ост = (тіло.messages || []).slice(-1)[0] || {};
    промпти.push((ост.content || []).map(б => б.text || '').join('\n'));
    await route.fulfill({ status: 200, contentType: 'application/json',
      body: JSON.stringify({ content: [{type: 'text', text: паспортМоделі()}],
                             usage: {input_tokens: 1, output_tokens: 1}, stop_reason: 'end_turn' }) });
  });
  await стор.goto(БАЗА + '/index.html#міст=' + БАЗА + '/міст&т=tok-rv3', { waitUntil: 'load', timeout: 180000 });
  await с(2000);
  await стор.evaluate(() => {
    КОЛІР = {шкіра: '#f2d6c4', волосся: '#4a4644', очі: '#6b8cae', кільце: null, точки: null};
    for (const [і, v] of [['мр-плечі', 96], ['мр-груди', 92], ['мр-талія', 74], ['мр-стегна', 100]])
      document.getElementById(і).value = v;
    екран(2);
  });
  console.log('сторінка піднята за', ч(), '· збірка:', await стор.evaluate(() => ЗБІРКА_ПОКАЗУ),
              '· бракує до розмови:', await стор.evaluate(() => JSON.stringify(чогоБракує())));

  const стан = () => стор.evaluate(() => ({
    нагода: document.getElementById('сц-нагода').value, місце: document.getElementById('сц-місце').value,
    опади: document.getElementById('сц-опади').value, година: document.getElementById('сц-година').value,
    темп: document.getElementById('сц-темп').value,
    чипи: [...document.querySelectorAll('#сц-вето-інші .чип')].map(ч => ч.textContent.trim()),
    зрозуміла: document.getElementById('сц-зрозуміла').textContent,
    стрічка: [...document.querySelectorAll('#чат-стрічка .репліка')].map(р => р.textContent),
    стан: document.getElementById('чат-стан').textContent, поле_закрите: document.getElementById('чат-поле').disabled,
    паспорт: ПАСПОРТ_П && {джерело: ПАСПОРТ_П.джерело, нагода: ПАСПОРТ_П.нагода, місце: ПАСПОРТ_П.місце,
                          опади: ПАСПОРТ_П.опади, вето_типи: ПАСПОРТ_П.вето.типи, питання: ПАСПОРТ_П.питання_людині},
    випадок: ВИПАДОК_ПАСПОРТА_П, бракує: чогоБракує(), довідник_живий: ДОВІДНИК_ЖИВИЙ_П,
    змінено: ВИПАДОК_ЗМІНЕНО_П, діагноз: (typeof ЗБ !== 'undefined' && ЗБ) ? ЗБ.діагноз : null }));

  /* 1. перша репліка — піднімає Pyodide і міст */
  await стор.fill('#чат-поле', 'побачення в ресторані, дощ, без підборів');
  await стор.click('#чат-слати');
  await стор.waitForFunction(() => document.querySelectorAll('#чат-стрічка .репліка').length >= 2, null, { timeout: 480000 });
  console.log('\n1. перша відповідь стиліста за', ч(), '· pyodide тягнув:', JSON.stringify(тягнув));
  console.log(JSON.stringify(await стан(), null, 1));
  if (!промпти.length){ console.log('модель не викликалась — міст не піднявся; далі нема чого міряти'); await браузер.close(); process.exit(3); }
  console.log('промпт паспорта, який дістала «модель» (перші 600 символів):\n' + промпти[0].slice(0, 600));

  /* 2. те саме через справжній bridge у Pyodide: що поїде в міст із цим паспортом */
  const міст = await стор.evaluate(async () => {
    const вх = вхідМостаП();
    const р = await pyodideП.runPythonAsync('import json, bridge\n' +
      'd = bridge._застосувати_паспорт(json.loads(' + JSON.stringify(JSON.stringify(вх)) + '))\n' +
      'json.dumps(dict(сценарій=d.get("сценарій"), випадок=d.get("випадок"), жорстке_ні=d.get("жорстке_ні"), ' +
      'вимоги=d.get("вимоги"), намір=d.get("намір")), ensure_ascii=False, default=str)');
    return {плитка_опади: вх.сценарій.опади, міст: JSON.parse(р)};
  });
  console.log('\n2. справжній bridge._застосувати_паспорт над входом показу:');
  console.log(JSON.stringify(міст, null, 1));

  /* 3. зняти чип «підбори» рукою, сказати ще — межа не повертається */
  await стор.evaluate(() => [...document.querySelectorAll('#сц-вето-інші .чип')].find(ч => ч.textContent.trim() === 'підбори').click());
  await с(100);
  await стор.fill('#чат-поле', 'і ще: без блиску, все ж без підборів');
  await стор.click('#чат-слати');
  await стор.waitForFunction(() => document.querySelectorAll('#чат-стрічка .репліка').length >= 4, null, { timeout: 120000 });
  const с3 = await стан();
  console.log('\n3. після зняття чипа й другої репліки за', ч(), '· чипи:', JSON.stringify(с3.чипи),
              '· паспорт.вето.типи:', JSON.stringify((с3.паспорт||{}).вето_типи), '· остання репліка ші:', JSON.stringify(с3.стрічка.slice(-1)[0]));
  console.log('   промпт 2 несе «Паспорт досі»:', /Паспорт досі/.test(промпти[1]), '· «Розмова досі»:', /Розмова досі/.test(промпти[1]),
              '· реплік у промпті:', (промпти[1].match(/^\s+(Вона|Ти): /gm) || []).length);

  /* 4. третя репліка — стеля */
  await стор.fill('#чат-поле', 'о сьомій вечора');
  await стор.click('#чат-слати');
  await стор.waitForFunction(() => document.querySelectorAll('#чат-стрічка .репліка').length >= 6, null, { timeout: 120000 });
  const с4 = await стан();
  console.log('\n4. після третьої репліки за', ч(), '· поле закрите:', с4.поле_закрите, '· стан:', JSON.stringify(с4.стан),
              '· викликів моделі:', промпти.length, '· бракує:', JSON.stringify(с4.бракує), '· змінено рукою:', с4.змінено);
  console.log('\nконсоль (помилки/попередження):', консоль.length ? консоль.slice(0, 12) : 'порожня');
  await браузер.close();
})().catch(e => { console.error('стенд не піднявся:', e); process.exit(2); });
