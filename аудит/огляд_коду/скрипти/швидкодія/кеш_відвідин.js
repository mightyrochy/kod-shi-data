/* loadPyodide при першій і повторних відвідинах: справжній HTTP-сервер (127.0.0.1) з Cache-Control, той самий
   профіль браузера (HTTP-кеш + кеш скомпільованого wasm у V8). node кеш_відвідин.js <тека pyodide> <порт> [затримка_мс_на_файл]
   Сервер — python3 -m http.server не дає Cache-Control, тож свій на node:http. */
const { chromium } = require('playwright'); const http = require('http'), fs = require('fs'), path = require('path'), os = require('os');
const [PYD, ПОРТ] = process.argv.slice(2);
const ст = http.createServer((q, r) => {
  const u = decodeURIComponent(q.url.split('?')[0]);
  if (u === '/' || u === '/index.html'){ r.writeHead(200, {'content-type': 'text/html', 'cache-control': 'no-store'});
    return r.end('<!doctype html><script src="/py/pyodide.js"></script>'); }
  const ф = path.join(PYD, u.replace(/^\/py\//, ''));
  if (!fs.existsSync(ф)){ r.writeHead(404); return r.end(); }
  const тип = ф.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ф) ? 'application/javascript' : ф.endsWith('.json') ? 'application/json' : 'application/octet-stream';
  r.writeHead(200, {'content-type': тип, 'cache-control': 'public, max-age=31536000, immutable'}); r.end(fs.readFileSync(ф));
}).listen(+ПОРТ, '127.0.0.1');
(async () => {
  const тека = fs.mkdtempSync(path.join(process.env.KESH_DIR, 'pw-'));
  const кон = await chromium.launchPersistentContext(тека, {headless: true, executablePath: process.env.CHROMIUM || undefined});
  const с = кон.pages()[0] || await кон.newPage();
  const рез = [];
  for (let i = 0; i < 4; i++){
    await с.goto('http://127.0.0.1:' + ПОРТ + '/?v=' + i, {waitUntil: 'load'});
    const м = await с.evaluate(async () => { const t0 = performance.now();
      const pd = await loadPyodide({indexURL: '/py/'}); const t1 = performance.now();
      pd.runPython('import json, re, zipfile, bz2'); const t2 = performance.now();
      const рес = performance.getEntriesByType('resource').map(e => [e.name.split('/').pop(), Math.round(e.duration), e.transferSize]);
      return {loadPyodide: t1 - t0, stdlib_імпорт: t2 - t1, рес}; });
    рез.push(м); console.log('відвідини', i + 1, 'loadPyodide', Math.round(м.loadPyodide), 'мс', JSON.stringify(м.рес));
    await new Promise(р => setTimeout(р, 1500));   // дати V8 записати кеш коду
  }
  await кон.close(); ст.close(); fs.rmSync(тека, {recursive: true, force: true});
  fs.writeFileSync(process.env.OUT || '/dev/null', JSON.stringify(рез));
})().catch(e => { console.error(e); process.exit(2); });
