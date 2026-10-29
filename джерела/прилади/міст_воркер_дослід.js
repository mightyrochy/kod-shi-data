/* Дослід кроку 4.1-А: записані входи `містП` (знімок 0.2) двічі в справжньому Chromium — ДО (Pyodide в головному
   потоці, дані літералом у коді Python, як `показ.html: містП`) і ПІСЛЯ (Pyodide у Web Worker `міст_воркер.js`,
   дані аргументом, клієнт `міст_воркер_клієнт.js`). Мережі нема: Pyodide і тіло показу віддає локальний сервер.

   node джерела/прилади/міст_воркер_дослід.js <index.html> <тека pyodide> <входи.jsonl[.gz]> <тека виходу> [до|арг|після|обидва] [лише N]
   далі: python3 джерела/прилади/знімок_мосту.py --з-сирих <тека виходу>/до/сирі.jsonl --вихід до.jsonl (так само «після»)
         python3 джерела/прилади/знімок_мосту.py --діф до.jsonl після.jsonl

   Виходи на режим: <тека>/<режим>/сирі.jsonl — рядок відповіді моста як його отримав JS ({н, ім, вих | помилка});
   час.json — підйом, кожен виклик (Python, обіг, розбір JSON у головному потоці, байти), long tasks головного потоку.
   Виклики йдуть по одному в порядку запису (як `знімок_мосту.py`): знімок порівнюваний, час — сума без перекриття. */
const fs = require('fs'), path = require('path'), zlib = require('zlib'), http = require('http');
const { chromium } = require('playwright');
const [СТОРІНКА, ТЕКА_PYODIDE, ВХОДИ, ВИХІД, РЕЖИМ = 'обидва', ЛИШЕ] = process.argv.slice(2);

const html = fs.readFileSync(СТОРІНКА, 'utf8');
const м = html.match(/МОДУЛІ_ПОКАЗУ\s*=\s*"([A-Za-z0-9+/=]+)"/);
if (!м) { console.error('у ' + СТОРІНКА + ' нема МОДУЛІ_ПОКАЗУ'); process.exit(2); }
const МОДУЛІ_B64 = м[1];
const сирі = fs.readFileSync(ВХОДИ);
let входи = (ВХОДИ.endsWith('.gz') ? zlib.gunzipSync(сирі) : сирі).toString('utf8').split('\n').filter(р => р.trim())
  .map(р => JSON.parse(р)).map(в => ({ім: в.ім, асинх: !!в['async'], вхід: в['вхід']}));
if (Number(ЛИШЕ)) входи = входи.slice(0, Number(ЛИШЕ));

const ФАЙЛИ = {
  '/': ['text/html', '<!doctype html><meta charset="utf-8"><title>дослід 4.1</title><script src="/client.js"></script>'],
  '/client.js': ['text/javascript', fs.readFileSync(path.join(__dirname, 'міст_воркер_клієнт.js'))],
  '/worker.js': ['text/javascript', fs.readFileSync(path.join(__dirname, 'міст_воркер.js'))],
  '/moduli.b64': ['text/plain', МОДУЛІ_B64],
};
const ТИПИ = {'.js': 'text/javascript', '.wasm': 'application/wasm', '.zip': 'application/zip', '.json': 'application/json'};
const сервер = http.createServer((з, в) => {
  const у = decodeURIComponent(з.url.split('?')[0]);
  if (ФАЙЛИ[у]) { в.writeHead(200, {'content-type': ФАЙЛИ[у][0] + '; charset=utf-8'}); return в.end(ФАЙЛИ[у][1]); }
  if (у.startsWith('/pyodide/')) {
    const ф = path.join(ТЕКА_PYODIDE, path.basename(у));
    if (fs.existsSync(ф)) { в.writeHead(200, {'content-type': ТИПИ[path.extname(ф)] || 'application/octet-stream'}); return в.end(fs.readFileSync(ф)); }
  }
  в.writeHead(404); в.end();
});

/* У сторінці: спостерігач long tasks від першого байта і пульс головного потоку (таймер 10 мс; проміжок понад 50 мс —
   потік був зайнятий). Пульс потрібен, бо Chromium не звітує long task на частину задач (розпакування модулів ДО
   — 3 с без запису), а дотик жінки чекає будь-яку зайняту задачу. Виклики пишуть [т0, т1] на головному потоці. */
function спостерігати(){
  window.__довгі = []; window.__пульс = [];
  new PerformanceObserver(с => { for (const е of с.getEntries()) window.__довгі.push([е.startTime, е.duration]); })
    .observe({type: 'longtask', buffered: true});
  let попер = performance.now();
  setInterval(() => { const т = performance.now(); if (т - попер > 50) window.__пульс.push([попер, т - попер]); попер = т; }, 10);
}

/* `арг` — головний потік, але дані аргументом функції (`_vyklyk`, як у воркері): відділяє виграш «не кодом» від
   виграшу «не в головному потоці» (крок 4.1-Б-1) */
async function прогінДО(входи, арг){
  const р = {підйом: {}, виклики: [], вих: []};
  const т0 = performance.now();
  await new Promise((ок, ні) => { const с = document.createElement('script'); с.src = '/pyodide/pyodide.js';
    с.onload = ок; с.onerror = ні; document.head.appendChild(с); });
  const пд = await loadPyodide({indexURL: '/pyodide/'});
  const т1 = performance.now();
  const b64 = await (await fetch('/moduli.b64')).text();
  const т1а = performance.now();
  /* рівно як `підняти_міст_показу` */
  const бін = Uint8Array.from(atob(b64), c => c.charCodeAt(0));
  const т1б = performance.now();
  пд.unpackArchive(бін.buffer, 'zip', {extractDir: '/показ'});
  const т2 = performance.now();
  await пд.runPythonAsync('import sys, os\nsys.path.insert(0, "/показ"); os.chdir("/показ")\nimport bridge\n');
  if (арг) await пд.runPythonAsync('import json\n' +
    'def _vyklyk(im, ryadok):\n    return bridge.виклик(im, json.loads(ryadok))\n' +
    'async def _vyklyk_a(im, ryadok):\n    return await bridge.виклик_а(im, json.loads(ryadok))\n');
  const виклик = арг && пд.globals.get('_vyklyk'), виклик_а = арг && пд.globals.get('_vyklyk_a');
  const т3 = performance.now();
  р.підйом = {від: т0, до: т3, pyodide: т1 - т0, base64: т1б - т1а, модулі: т2 - т1б, імпорт: т3 - т2};
  for (let н = 0; н < входи.length; н++){
    const {ім, асинх, вхід} = входи[н];
    const дані = JSON.parse(вхід);
    const к0 = performance.now();
    /* рівно як `містП`: дані літералом у коді Python */
    const код = арг ? '' : 'import json, bridge\n' + (асинх ? 'await bridge.виклик_а(' : 'bridge.виклик(')
      + JSON.stringify(ім) + ', json.loads(' + JSON.stringify(JSON.stringify(дані)) + '))';
    let вих = null, помилка = null;
    try { вих = арг ? await (асинх ? виклик_а : виклик)(ім, JSON.stringify(дані)) : await пд.runPythonAsync(код); }
    catch (е) { помилка = String((е && е.message) || е); }
    const к1 = performance.now();
    let розбір = 0, тип = typeof вих;
    if (тип === 'string') { const т = performance.now(); JSON.parse(вих); розбір = performance.now() - т; }
    else if (вих != null && вих.toJs) { вих = JSON.stringify(вих.toJs({dict_converter: Object.fromEntries})); }
    р.виклики.push({н, ім, від: к0, до: к1, мс_python: к1 - к0, мс_обіг: к1 - к0, мс_розбір: розбір,
                    байтів_коду: код.length, байтів_входу: вхід.length, байтів_виходу: вих ? вих.length : 0, тип});
    р.вих.push(помилка != null ? {н, ім, помилка} : {н, ім, вих});
  }
  return р;
}

async function прогінПІСЛЯ(входи){
  const р = {підйом: {}, виклики: [], вих: []};
  const т0 = performance.now();
  const воркер = new Worker('/worker.js');
  const b64 = await (await fetch('/moduli.b64')).text();
  const т0а = performance.now();
  const готово = new Promise((ок, ні) => воркер.addEventListener('message', е => {
    if (е.data.тип === 'готово') ок(е.data.мс); if (е.data.тип === 'збій') ні(new Error(е.data.помилка)); }));
  /* рядок base64 іде воркеру як є: розбір і розпакування — там, у головному потоці лише копія рядка */
  воркер.postMessage({тип: 'підйом', indexURL: location.origin + '/pyodide/', модулі: b64});
  const т0б = performance.now();
  const мс = await готово;
  const т1 = performance.now();
  р.підйом = Object.assign({від: т0, до: т1, передача_модулів: т0б - т0а, разом: т1 - т0}, мс);
  const міст = створитиМістВоркера(воркер);
  for (let н = 0; н < входи.length; н++){
    const {ім, асинх, вхід} = входи[н];
    const к0 = performance.now();
    let вих = null, помилка = null;
    try { вих = await міст.виклик(ім, JSON.parse(вхід), {асинх, сирий: true}); }
    catch (е) { помилка = String((е && е.message) || е); }
    const к1 = performance.now();
    const ж = міст.журнал[міст.журнал.length - 1];
    р.виклики.push({н, ім, від: к0, до: к1, мс_python: ж.мс_python, мс_обіг: ж.мс_обіг, мс_розбір: ж.мс_розбір || 0,
                    байтів_входу: вхід.length, байтів_виходу: вих ? вих.length : 0, тип: 'string'});
    р.вих.push(помилка != null ? {н, ім, помилка} : {н, ім, вих});
  }
  /* покоління (7311): три входи «палітри» поспіль з одним ключем — перші два відкинуто, третій прийнято */
  const пал = входи.map((в, і) => [в, і]).filter(([в]) => в.ім === 'палітри').map(([в]) => JSON.parse(в.вхід));
  if (пал.length){
    const наслідки = await Promise.all([0, 1, 2].map(і => міст.виклик('палітри', пал[і % пал.length], {ключ: 'палітри'})
      .then(() => 'прийнято', е => е.застаріло ? 'застаріло' : 'помилка: ' + е.message)));
    р.покоління = {наслідки, остання_чинна: міст.чинне('палітри', міст.покоління('палітри'))};
  }
  /* поза порядком: «суд» оцінки (`виклик_а`, поступається) і короткий виклик слідом — відповідь приходить раніше
     за суд, і кожна дістається своєму входу за `н`, а не за порядком приходу */
  const суд = входи.findIndex(в => в.асинх && JSON.parse(в.вхід).крок === 'суд');
  if (суд >= 0 && суд + 1 < входи.length){
    const було = міст.журнал.length;
    const пара = [входи[суд], входи[суд + 1]];
    const р2 = await Promise.all(пара.map(в => міст.виклик(в.ім, JSON.parse(в.вхід), {асинх: в.асинх})
      .then(о => 'ок', е => 'помилка: ' + е.message)));
    р.поза_порядком = {послано: пара.map(в => в.ім), прийшло: міст.журнал.slice(було).map(з => з.ім), наслідки: р2};
  }
  воркер.terminate();
  return р;
}

/* Тексти для `page.evaluate` (функції в сторінку йдуть джерелом) */
const ДЖЕРЕЛО = [спостерігати, прогінДО, прогінПІСЛЯ].map(ф => ф.toString() + '\nwindow.' + ф.name + ' = ' + ф.name + ';').join('\n');

function довгіУВікні(довгі, від, до){
  const у = довгі.filter(([с, т]) => с + т > від && с < до);
  return {штук: у.length, мс: Math.round(у.reduce((с, [, т]) => с + т, 0)), найдовша: Math.round(Math.max(0, ...у.map(([, т]) => т)))};
}

async function режим(браузер, назва){
  const стор = await (await браузер.newContext()).newPage();
  стор.on('console', п => { if (п.type() === 'error') console.error('  [сторінка]', п.text().slice(0, 300)); });
  await стор.addInitScript(ДЖЕРЕЛО + '\nспостерігати();');
  await стор.goto(БАЗА + '/');
  const т = Date.now();
  const р = await стор.evaluate(([назва, входи]) => (назва === 'після' ? прогінПІСЛЯ(входи) : прогінДО(входи, назва === 'арг')),
                                [назва, входи]);
  const [довгі, пульс] = await стор.evaluate(() => [window.__довгі, window.__пульс]);
  await стор.context().close();
  const тека = path.join(ВИХІД, назва);
  fs.mkdirSync(тека, {recursive: true});
  fs.writeFileSync(path.join(тека, 'сирі.jsonl'), р.вих.map(в => JSON.stringify(в)).join('\n') + '\n');
  const збір = р.виклики.filter(в => в.н >= ПОЧАТОК_ЗБОРУ && в.н < КІНЕЦЬ_ЗБОРУ);
  const сума = (м, к) => Math.round(м.reduce((с, в) => с + (в[к] || 0), 0));
  const час = {
    режим: назва, стіна_с: (Date.now() - т) / 1000, підйом: р.підйом, покоління: р.покоління || null,
    поза_порядком: р.поза_порядком || null,
    довгі: {підйом: довгіУВікні(довгі, р.підйом.від, р.підйом.до),
            виклики: довгіУВікні(довгі, р.виклики[0].від, р.виклики[р.виклики.length - 1].до),
            збір: збір.length ? довгіУВікні(довгі, збір[0].від, збір[збір.length - 1].до) : null},
    пульс: {підйом: довгіУВікні(пульс, р.підйом.від, р.підйом.до),
            виклики: довгіУВікні(пульс, р.виклики[0].від, р.виклики[р.виклики.length - 1].до),
            збір: збір.length ? довгіУВікні(пульс, збір[0].від, збір[збір.length - 1].до) : null},
    разом: {python: сума(р.виклики, 'мс_python'), обіг: сума(р.виклики, 'мс_обіг'), розбір: сума(р.виклики, 'мс_розбір'),
            байтів_коду: сума(р.виклики, 'байтів_коду'), байтів_входу: сума(р.виклики, 'байтів_входу'),
            байтів_виходу: сума(р.виклики, 'байтів_виходу')},
    збір: {викликів: збір.length, python: сума(збір, 'мс_python'), обіг: сума(збір, 'мс_обіг'), розбір: сума(збір, 'мс_розбір')},
    виклики: р.виклики.map(в => [в.н, в.ім, +в.мс_python.toFixed(1), +в.мс_обіг.toFixed(1), +в.мс_розбір.toFixed(2),
                                  в.байтів_коду || 0, в.байтів_входу, в.байтів_виходу, в.тип]),
    довгі_всі: довгі.map(([с, т]) => [Math.round(с), Math.round(т)]),
  };
  fs.writeFileSync(path.join(тека, 'час.json'), JSON.stringify(час));
  console.log(назва + ': ' + р.виклики.length + ' викликів · стіна ' + час.стіна_с.toFixed(1) + ' с · підйом ' +
    JSON.stringify(Object.fromEntries(Object.entries(р.підйом).filter(([к]) => !['від', 'до'].includes(к)).map(([к, v]) => [к, Math.round(v)]))) +
    '\n   разом ' + JSON.stringify(час.разом) + '\n   збір ' + JSON.stringify(час.збір) +
    '\n   long tasks ' + JSON.stringify(час.довгі) + '\n   пульс (проміжки > 50 мс) ' + JSON.stringify(час.пульс) + (час.покоління ? '\n   покоління ' + JSON.stringify(час.покоління) : '') +
    (час.поза_порядком ? '\n   поза порядком ' + JSON.stringify(час.поза_порядком) : ''));
}

/* Збір у записаних входах — від `запити` до першого `вердикт` (оцінка карток після збору) */
const ПОЧАТОК_ЗБОРУ = Math.max(0, входи.findIndex(в => в.ім === 'запити'));
const КІНЕЦЬ_ЗБОРУ = (і => і < 0 ? входи.length : і)(входи.findIndex((в, і) => і > ПОЧАТОК_ЗБОРУ && в.ім === 'вердикт'));
let БАЗА;

(async () => {
  await new Promise(ок => сервер.listen(0, '127.0.0.1', ок));
  БАЗА = 'http://127.0.0.1:' + сервер.address().port;
  const браузер = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM || undefined});
  for (const н of (РЕЖИМ === 'обидва' ? ['до', 'після'] : [РЕЖИМ])) await режим(браузер, н);
  await браузер.close();
  сервер.close();
})().catch(е => { console.error(е); process.exit(2); });
