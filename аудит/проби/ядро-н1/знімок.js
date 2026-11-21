/* Мірило (в) наряду Ядро-Н1-каркас: екран «Твої образи» 390×844 з `#ядро=1` на заглушці моделі (с5).
   Сторінка — зібраний показ (`index.html`), Pyodide — з диска; міст сторінки перехоплено: на запит ядра виду
   «складання», «вибір», «опис» заглушка віддає записаний текст проходу с5 через міст 20.11 (рядки 6, 12, 19
   `обміни.jsonl`, як `джерела/ядро/тести/обвязка.py`), а руці 2 на «вибір» — текст не за формою: її картка мусить
   стати збоєм, а решта три — лишитись. Знімок — після того, як збір скінчився; поруч — JSON зі станом карток.
   Мірило (г) — той самий прохід, але кожен запит ядра йде справжній моделі через стенд моста за підпискою
   (`аудит/проби/живий-як-людина-3/стенд/міст_claude.py`): MIST_PORT=<порт моста>.
   Запуск: STOR=/tmp/стенд PYODIDE=/tmp/pyodide [MIST_PORT=8791] node аудит/проби/ядро-н1/знімок.js <тека виходу> */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const КОРІНЬ = path.resolve(__dirname, '..', '..', '..');
const СТОР = process.env.STOR || '/tmp/стенд', ТЕКА_PYODIDE = process.env.PYODIDE || '/tmp/pyodide';
const ВИХІД = path.resolve(process.argv[2] || path.join(__dirname, 'знімки')); fs.mkdirSync(ВИХІД, {recursive: true});
const БАЗА = 'http://127.0.0.1:8765';
const МІСТ_ПОРТ = process.env.MIST_PORT || '';   /* задано — запити ядра йдуть стенду моста, а не заглушці */
const ЗАПИС = path.join(КОРІНЬ, 'аудит/проби/Живий-через-міст/стенд/службове/с5_весілля_сестри/обміни.jsonl');
const рядки = fs.readFileSync(ЗАПИС, 'utf8').split('\n').filter(р => р.trim());
const текст = н => JSON.parse(JSON.parse(рядки[н]).відповідь).content.filter(б => б.type === 'text').map(б => б.text).join('');
const ЗАПИСАНЕ = {складання: текст(6), вибір: текст(12), опис: текст(19)};
const с = мс => new Promise(р => setTimeout(р, мс));

(async () => {
  const браузер = await chromium.launch();
  const стор = await браузер.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 2});
  const консоль = [];
  стор.on('console', м => { if (м.type() === 'error') консоль.push(м.text().slice(0, 300)); });
  const запити = [];
  await стор.route(u => u.origin === БАЗА, async route => {
    const ім = decodeURIComponent(new URL(route.request().url()).pathname).replace(/^\//, '') || 'index.html';
    if (ім === 'міст'){
      const тіло = JSON.parse(route.request().postData() || '{}');
      const зміст = (тіло.messages || []).slice(-1)[0].content;
      const промпт = (Array.isArray(зміст) ? зміст.filter(б => б.type === 'text').map(б => б.text).join('') : зміст);
      let з = {}; try { з = JSON.parse(промпт); } catch (_) {}
      const цей = {вид: з.вид, рука: з.рука, час: Date.now()}; запити.push(цей);
      if (МІСТ_ПОРТ){
        /* мірило (г): той самий запит — справжній моделі через стенд моста за підпискою (`міст_claude.py`) */
        const т0 = Date.now();
        const в = await fetch('http://127.0.0.1:' + МІСТ_ПОРТ + '/', {method: 'POST', body: route.request().postData(),
          headers: {'content-type': 'application/json', 'x-prohid': encodeURIComponent('ядро-н1-с5')}, signal: AbortSignal.timeout(960000)});
        const т = await в.text();
        цей.с = (Date.now() - т0) / 1000; цей.статус = в.status;
        const заг = {}; for (const к of ['x-model']) if (в.headers.get(к)) заг[к] = в.headers.get(к);
        return route.fulfill({status: в.status, contentType: 'application/json', headers: заг, body: т});
      }
      const відповідь = (з.рука === 2 && з.вид === 'вибір') ? 'не за формою: заглушка ламає руку 2' : (ЗАПИСАНЕ[з.вид] || '');
      return route.fulfill({status: 200, contentType: 'application/json', headers: {'x-model': 'заглушка-ядра'},
        body: JSON.stringify({content: [{type: 'text', text: відповідь}], stop_reason: 'end_turn',
                              usage: {input_tokens: 0, output_tokens: 0}})});
    }
    const ф = path.join(СТОР, ім);
    if (!fs.existsSync(ф)) return route.fulfill({status: 404, body: 'нема ' + ім});
    await route.fulfill({status: 200, contentType: ім.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/plain; charset=utf-8', body: fs.readFileSync(ф)});
  });
  await стор.route('https://cdn.jsdelivr.net/pyodide/**', async route => {
    const ім = new URL(route.request().url()).pathname.split('/').pop(), ф = path.join(ТЕКА_PYODIDE, ім);
    if (!fs.existsSync(ф)) return route.fulfill({status: 404, body: 'нема ' + ім});
    const тип = ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream';
    await route.fulfill({status: 200, contentType: тип, body: fs.readFileSync(ф)});
  });
  await стор.route(u => u.origin !== БАЗА && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href), route => route.abort());
  await стор.goto(БАЗА + '/index.html#ядро=1&міст=' + БАЗА + '/міст&т=tok-yadro-n1', {waitUntil: 'load', timeout: 180000});
  /* Pyodide піднявся, коли вхід «ядро» мосту відповідає */
  for (let і = 0; і < 120; і++){
    const ок = await стор.evaluate(() => typeof містП === 'function'
      ? містП('ядро', {дія: 'перевірка'}).then(в => !!в.кінець, () => false) : false).catch(() => false);
    if (ок) break;
    await с(2000);
  }
  const т0 = Date.now();
  const стан = await стор.evaluate(async () => {
    await зібратиОбразиП();
    return {ядро: ЯДРО_П, готово: ЗБ.готово, діагноз: ЗБ.діагноз,
            картки: ((П || {}).картки || []).map(к => ({рука: к.рука, позиція: к.збирання.позиція, збій: к.збій || null,
                                                        речей: (к.речі || []).length, неповний: к.неповний}))};
  });
  стан.секунд_від_натиску = (Date.now() - т0) / 1000;
  стан.запити = запити.map(з => ({вид: з.вид, рука: з.рука, с: з.с, статус: з.статус}));
  стан.міст = МІСТ_ПОРТ ? 'стенд моста за підпискою, порт ' + МІСТ_ПОРТ : 'заглушка: записаний прохід с5';
  стан.помилки_консолі = консоль;
  await с(1500);
  await стор.screenshot({path: path.join(ВИХІД, 'твої-образи-ядро-с5-390x844.png'), animations: 'disabled'});
  /* наступні картки — тим самим екраном, кнопкою «наступний», як гортала б вона */
  for (let п = 2; п <= стан.картки.length; п++){
    await стор.getByText('наступний', {exact: false}).last().click({timeout: 5000}).catch(() => {});
    await с(800);
    await стор.screenshot({path: path.join(ВИХІД, `твої-образи-ядро-с5-картка-${п}-390x844.png`), animations: 'disabled'});
  }
  fs.writeFileSync(path.join(ВИХІД, 'стан.json'), JSON.stringify(стан, null, 1) + '\n');
  console.log(JSON.stringify({готово: стан.готово, карток: стан.картки.length, збоїв: стан.картки.filter(к => к.збій).length,
                              запитів: стан.запити.length, секунд: стан.секунд_від_натиску}));
  await браузер.close();
})().catch(е => { console.error(е); process.exit(1); });
