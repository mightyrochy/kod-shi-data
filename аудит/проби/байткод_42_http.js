/* Крок 4.2 / 7231: 3 окремі профілі × cold/warm, справжній HTTP-кеш, жодного route().
   node аудит/проби/байткод_42_http.js <index.html> <тека Pyodide 0.26.4> <звіт.json>
   Зібрана сторінка й незмінні ресурси з диска віддаються HTTP-сервером; CDN origin у сторінці
   замінено лише на адресу цього сервера. Це контроль cache semantics, не вимір швидкості CDN.
   ІСТОРИЧНА (4.1-Б-3): прилад гачить `window.loadPyodide` і `pyodide_показу` головного потоку; з Python у воркері
   їх у сторінці нема — міряє лише збірки до 4.1-Б-3. Підйом воркера — `міст_шов_дослід.js` (`підйом_мс`). */
const fs = require('fs'), path = require('path'), os = require('os'), http = require('http'), crypto = require('crypto');
const { chromium } = require('playwright');
const [СТОРІНКА, PYODIDE, ВИХІД] = process.argv.slice(2);
if (!СТОРІНКА || !PYODIDE || !ВИХІД) throw new Error('потрібні index.html, тека Pyodide, звіт.json');
const html = fs.readFileSync(СТОРІНКА, 'utf8');
const файли = new Set(['pyodide.js', 'pyodide.asm.js', 'pyodide.asm.wasm', 'python_stdlib.zip', 'pyodide-lock.json']);
const запити = [];
let база;
const сервер = http.createServer((запит, відповідь) => {
  const адреса = new URL(запит.url, база);
  if (адреса.pathname === '/') {
    відповідь.writeHead(200, {'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store'});
    return відповідь.end(html.replaceAll('https://cdn.jsdelivr.net', база));
  }
  const імя = адреса.pathname.replace('/pyodide/v0.26.4/full/', '');
  if (!адреса.pathname.startsWith('/pyodide/v0.26.4/full/') || !файли.has(імя)) {
    відповідь.writeHead(404); return відповідь.end();
  }
  const дані = fs.readFileSync(path.join(PYODIDE, імя));
  запити.push({імя, байтів: дані.length});
  відповідь.writeHead(200, {'content-type': імя.endsWith('.wasm') ? 'application/wasm'
    : імя.endsWith('.js') ? 'text/javascript' : 'application/octet-stream',
    'cache-control': 'public, max-age=31536000, immutable', 'content-length': дані.length});
  відповідь.end(дані);
});
(async () => {
  await new Promise(р => сервер.listen(0, '127.0.0.1', р));
  база = 'http://127.0.0.1:' + сервер.address().port;
  const звіт = {сторінка_sha256: crypto.createHash('sha256').update(html).digest('hex'),
    версія_pyodide: '0.26.4', розмір_html: Buffer.byteLength(html), viewport: [390, 844], пари: []};
  for (let пара = 0; пара < 3; пара++) {
    const профіль = fs.mkdtempSync(path.join(os.tmpdir(), 'pyc42-'));
    let контекст;
    try {
      контекст = await chromium.launchPersistentContext(профіль, {headless: true, viewport: {width: 390, height: 844},
        executablePath: process.env.CHROMIUM || undefined});
      const стор = контекст.pages()[0] || await контекст.newPage();
      const cdp = await контекст.newCDPSession(стор);
      await cdp.send('Network.enable');
      const кеш = new Set();
      cdp.on('Network.requestServedFromCache', п => кеш.add(п.requestId));
      const відвідини = [];
      for (const стан of ['cold', 'warm']) {
        кеш.clear();
        const початокЗапитів = запити.length, початок = Date.now();
        await стор.goto(база + '/', {waitUntil: 'load', timeout: 180000});
        const вимір = await стор.evaluate(async () => {
          const метрики = {};
          const первинний = window.loadPyodide;
          window.loadPyodide = async (...арг) => {
            const т0 = performance.now(), пд = await первинний(...арг);
            метрики.loadPyodide_ms = performance.now() - т0;
            пд.runPython('import sys\nкомпіляції42 = []\nsys.addaudithook(lambda e, a: компіляції42.append(a[1]) if e == "compile" and isinstance(a[1], str) and a[1].startswith("/показ/") else None)\n');
            const виконати = пд.runPythonAsync.bind(пд);
            пд.runPythonAsync = async (код, ...решта) => {
              const т = performance.now(), результат = await виконати(код, ...решта);
              if (код.includes('import bridge\n')) метрики.import_bridge_ms = performance.now() - т;
              return результат;
            };
            return пд;
          };
          const т0 = performance.now();
          const пд = await підняти_міст_показу();
          метрики.підйом_ms = performance.now() - т0;
          метрики.python = JSON.parse(пд.runPython('import json, importlib.util, bridge\njson.dumps({"version":sys.version,"magic":importlib.util.MAGIC_NUMBER.hex(),"cache_tag":sys.implementation.cache_tag,"compiled":компіляції42,"bytecode":globals().get("БАЙТКОД_СТАН"),"bridge_cached":bridge.__cached__,"result":bridge.виклик("чипи","{}")},ensure_ascii=False)'));
          метрики.ресурси = performance.getEntriesByType('resource').filter(e => e.name.includes('/pyodide/v0.26.4/full/'))
            .map(e => ({імя: e.name.split('/').pop(), мс: e.duration, transferSize: e.transferSize,
              encodedBodySize: e.encodedBodySize, decodedBodySize: e.decodedBodySize}));
          return метрики;
        });
        вимір.від_навігації_ms = Date.now() - початок;
        вимір.стан = стан;
        вимір.cdp_cache_hits = кеш.size;
        вимір.http_requests = запити.slice(початокЗапитів);
        відвідини.push(вимір);
        await стор.waitForTimeout(1500); // час запису кешу коду V8 між відвідинами
      }
      звіт.пари.push(відвідини);
    } finally {
      if (контекст) await контекст.close();
      fs.rmSync(профіль, {recursive: true, force: true});
    }
  }
  const медіана = а => [...а].sort((x, y) => x - y)[Math.floor(а.length / 2)];
  звіт.підсумок = {};
  for (const стан of ['cold', 'warm']) {
    const р = звіт.пари.map(п => п.find(в => в.стан === стан));
    звіт.підсумок[стан] = {};
    for (const ключ of ['loadPyodide_ms', 'import_bridge_ms', 'підйом_ms', 'від_навігації_ms']) {
      const всі = р.map(в => в[ключ]);
      звіт.підсумок[стан][ключ] = {медіана: медіана(всі), мін: Math.min(...всі), макс: Math.max(...всі), всі};
    }
  }
  звіт.тотожність_результату = new Set(звіт.пари.flat().map(в => в.python.result)).size === 1;
  звіт.warm_кеш = звіт.пари.map(п => ({cdp: п[1].cdp_cache_hits,
    усі_transfer_zero: п[1].ресурси.length > 0 && п[1].ресурси.every(р => р.transferSize === 0),
    http_requests: п[1].http_requests.length}));
  fs.writeFileSync(ВИХІД, JSON.stringify(звіт, null, 2));
  console.log('ЗАПИСАНО: ' + ВИХІД + '; cache-hit, компіляції й тотожність читати у звіті; це не PASS');
})().catch(е => { console.error(е); process.exitCode = 2; }).finally(() => сервер.close());
