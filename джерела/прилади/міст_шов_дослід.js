/* Дослід кроку 4.1-Б-1: записані входи `містП` (знімок 0.2) крізь СПРАВЖНІЙ `містП` зібраної сторінки в Chromium —
   те, що `міст_воркер_дослід.js` відтворював дослівно, тут іде кодом продукту, тож міряється саме шов транспорту.
   Мережі нема: Pyodide віддається з диска. Виклики йдуть по одному в порядку запису (як `знімок_мосту.py`).

   node джерела/прилади/міст_шов_дослід.js <index.html> <тека pyodide> <входи.jsonl[.gz]> <тека виходу> <назва> [лише N]
   далі: python3 джерела/прилади/знімок_мосту.py --з-сирих <тека виходу>/<назва>/сирі.jsonl --вихід <назва>.jsonl
         python3 джерела/прилади/знімок_мосту.py --діф до.jsonl після.jsonl && cmp до.jsonl після.jsonl

   Рядок відповіді береться там, де його отримує JS: з `транспортМостуП` (після Б-1) або з результату `runPythonAsync`
   (до Б-1, коли шва ще нема). `байтів_коду` — довжина коду Python, зібраного ПІСЛЯ підйому: до Б-1 це 1,98 МБ за
   прогін, після — 0. `розбіжностей_асинх` — виклики, де продукт обрав інший режим (`виклик` / `виклик_а`), ніж
   записаний.

   Після 4.1-Б-3 Python живе у воркері: `pyodide_показу` у сторінці нема, рядок береться з `транспортМостуП`, а
   `python_с` — з `ЖУРНАЛ_МОСТА_П` (`мс_python` воркера). Головний потік міряється в обох режимах: long tasks
   (`PerformanceObserver`) і пульс — таймер 10 мс, проміжки понад 50 мс (long tasks недолічують). */
const fs = require('fs'), path = require('path'), zlib = require('zlib'), http = require('http');
const { chromium } = require('playwright');
const [СТОРІНКА, ТЕКА_PYODIDE, ВХОДИ, ВИХІД, НАЗВА, ЛИШЕ] = process.argv.slice(2);

const сирі = fs.readFileSync(ВХОДИ);
let входи = (ВХОДИ.endsWith('.gz') ? zlib.gunzipSync(сирі) : сирі).toString('utf8').split('\n').filter(р => р.trim())
  .map(р => JSON.parse(р)).map(в => ({ім: в.ім, асинх: !!в['async'], вхід: в['вхід']}));
if (Number(ЛИШЕ)) входи = входи.slice(0, Number(ЛИШЕ));

const сервер = http.createServer((з, в) => {
  if (з.url.split('?')[0] === '/') { в.writeHead(200, {'content-type': 'text/html; charset=utf-8'}); return в.end(fs.readFileSync(СТОРІНКА)); }
  в.writeHead(404); в.end();
});

/* Виконується у сторінці (джерелом): воно бачить глобалі показу (`містП`, `транспортМостуП`, до Б-3 `pyodide_показу`) */
async function прогін(входи){
  const р = {вих: [], байтів_коду: 0, викликів_коду: 0, розбіжностей_асинх: 0, мс: [], лт: [], пульс: []};
  new PerformanceObserver(л => { for (const е of л.getEntries()) р.лт.push(е.duration); }).observe({type: 'longtask'});
  let мить = performance.now();
  const пульс = setInterval(() => { const т = performance.now(); if (т - мить > 50) р.пульс.push(т - мить); мить = т; }, 10);
  const т0 = performance.now();
  await підняти_міст_показу();
  р.підйом_мс = performance.now() - т0;
  р.лт_підйому = р.лт.length; р.пульс_підйому = р.пульс.length;
  let останній = null, асинхОстанній = null;
  const пд = typeof pyodide_показу !== 'undefined' ? pyodide_показу : null;
  const rpa = пд && пд.runPythonAsync.bind(пд);
  if (пд) пд.runPythonAsync = async function(код, ...а){
    р.байтів_коду += код.length; р.викликів_коду++;
    let в = await rpa(код, ...а);
    if (typeof в !== 'string' && в != null && в.toJs) в = JSON.stringify(в.toJs({dict_converter: Object.fromEntries}));
    останній = в; асинхОстанній = /await bridge\.виклик_а\(/.test(код);
    return в;
  };
  if (typeof транспортМостуП === 'function'){
    const т = транспортМостуП;
    window.транспортМостуП = async function(ім, рядок, асинх){ асинхОстанній = !!асинх; останній = await т(ім, рядок, асинх); return останній; };
  }
  for (let н = 0; н < входи.length; н++){
    const {ім, асинх, вхід} = входи[н];
    останній = null; асинхОстанній = null;
    const к0 = performance.now();
    let помилка = null;
    try { await містП(ім, JSON.parse(вхід)); } catch (е) { помилка = String((е && е.message) || е); }
    р.мс.push(performance.now() - к0);
    if (асинхОстанній !== null && асинхОстанній !== асинх) р.розбіжностей_асинх++;
    р.вих.push(помилка != null ? {н, ім, помилка} : {н, ім, вих: останній});
  }
  clearInterval(пульс);
  await new Promise(ок => setTimeout(ок, 100));
  р.python_воркера_мс = typeof ЖУРНАЛ_МОСТА_П !== 'undefined' ? ЖУРНАЛ_МОСТА_П.reduce((с, з) => с + (з.мс_python || 0), 0) : null;
  return р;
}

(async () => {
  await new Promise(ок => сервер.listen(0, '127.0.0.1', ок));
  const БАЗА = 'http://127.0.0.1:' + сервер.address().port;
  const браузер = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM || undefined});
  const стор = await (await браузер.newContext()).newPage();
  стор.on('console', п => { if (п.type() === 'error') console.error('  [сторінка]', п.text().slice(0, 300)); });
  await стор.route('https://cdn.jsdelivr.net/pyodide/**', м => {
    const ім = new URL(м.request().url()).pathname.split('/').pop(), ф = path.join(ТЕКА_PYODIDE, ім);
    const тип = ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : 'application/octet-stream';
    return fs.existsSync(ф) ? м.fulfill({status: 200, contentType: тип, body: fs.readFileSync(ф)}) : м.fulfill({status: 404});
  });
  await стор.route(у => у.origin !== БАЗА && !/cdn\.jsdelivr\.net\/pyodide/.test(у.href), м => м.abort());
  await стор.goto(БАЗА + '/');
  await стор.waitForFunction(() => typeof містП === 'function', null, {timeout: 60000});
  const т = Date.now();
  const р = await стор.evaluate(`(${прогін.toString()})(${JSON.stringify(входи)})`);
  const тека = path.join(ВИХІД, НАЗВА);
  fs.mkdirSync(тека, {recursive: true});
  fs.writeFileSync(path.join(тека, 'сирі.jsonl'), р.вих.map(в => JSON.stringify(в)).join('\n') + '\n');
  fs.writeFileSync(path.join(тека, 'час.json'), JSON.stringify({
    назва: НАЗВА, викликів: входи.length, стіна_с: (Date.now() - т) / 1000, підйом_мс: Math.round(р.підйом_мс),
    байтів_коду: р.байтів_коду, викликів_коду: р.викликів_коду, розбіжностей_асинх: р.розбіжностей_асинх,
    python_с: +(р.мс.reduce((с, x) => с + x, 0) / 1000).toFixed(1), помилок: р.вих.filter(в => в.помилка != null).length,
    не_рядків: р.вих.filter(в => в.помилка == null && typeof в.вих !== 'string').length,
    python_воркера_с: р.python_воркера_мс == null ? null : +(р.python_воркера_мс / 1000).toFixed(1),
    /* головний потік: підйом і виклики окремо (перші `лт_підйому` / `пульс_підйому` записів — підйом) */
    long_tasks_підйому: р.лт_підйому, long_tasks_підйому_с: +(р.лт.slice(0, р.лт_підйому).reduce((с, x) => с + x, 0) / 1000).toFixed(1),
    long_tasks_викликів: р.лт.length - р.лт_підйому,
    long_tasks_викликів_с: +(р.лт.slice(р.лт_підйому).reduce((с, x) => с + x, 0) / 1000).toFixed(1),
    long_task_найдовша_с: +((Math.max(0, ...р.лт.slice(р.лт_підйому))) / 1000).toFixed(2),
    пульс_підйому_с: +(р.пульс.slice(0, р.пульс_підйому).reduce((с, x) => с + x, 0) / 1000).toFixed(1),
    пульс_викликів: р.пульс.length - р.пульс_підйому,
    пульс_викликів_с: +(р.пульс.slice(р.пульс_підйому).reduce((с, x) => с + x, 0) / 1000).toFixed(1),
    пульс_найдовший_с: +((Math.max(0, ...р.пульс.slice(р.пульс_підйому))) / 1000).toFixed(2)}));
  console.log(НАЗВА + ': ' + fs.readFileSync(path.join(тека, 'час.json'), 'utf8'));
  await браузер.close();
  сервер.close();
})().catch(е => { console.error(е); process.exit(2); });
