/* Функції K-COL-03 у воркері повної збірки, без моделі.
   NODE_PATH=джерела/node_modules node цей_файл <index.html> <кеш Pyodide 0.26.4> [тека звіту] */
const fs = require('fs'), path = require('path'), http = require('http'), crypto = require('crypto');
const {chromium} = require('playwright');
const [сторінка, кеш, тека = __dirname] = process.argv.slice(2);
if (!сторінка || !кеш) throw Error('потрібні index.html і кеш Pyodide 0.26.4');
const html = fs.readFileSync(сторінка, 'utf8');
const штамп = (html.match(/const ЗБІРКА_ПОКАЗУ\s*=\s*"([^"]+)"/) || [])[1] || '';
const проба = fs.readFileSync(path.join(__dirname, 'схеми_конструктор.py'), 'utf8');
const входи = проба.slice(проба.indexOf('def випадки():'), проба.indexOf('\ndef старі_функції'));
const код = 'import json, palette as П, colorspace as К, areas as А, палітра_схеми as С\n' + входи +
  '\nрезультати = []\nfor назва, ім, args, kwargs in випадки():\n    з = getattr(С, ім)(*args, **kwargs)\n    for п in з:\n        assert п["сила"] == "default" and п["регістр"] == "репліка" and not п["блокує"], п\n        assert {"для_стиліста", "сила_нп_джерело", "блокує"} <= п.keys(), п\n    результати.append(dict(назва=назва, знахідки=з))\njson.dumps(результати,ensure_ascii=False)';
let сервер, браузер;
(async () => {
  сервер = http.createServer((запит, відповідь) => {
    if (запит.url === '/' || запит.url === '/index.html') {
      відповідь.setHeader('content-type', 'text/html; charset=utf-8'); відповідь.end(html);
    } else if (запит.url.startsWith('/build.txt')) відповідь.end(штамп);
    else { відповідь.statusCode = 404; відповідь.end(); }
  });
  await new Promise(р => сервер.listen(0, '127.0.0.1', р));
  браузер = await chromium.launch({headless: true});
  const стор = await браузер.newPage({viewport: {width: 390, height: 844}});
  const помилки = []; стор.on('pageerror', е => помилки.push(String(е)));
  await стор.route('https://cdn.jsdelivr.net/pyodide/**', async маршрут => {
    const ім = new URL(маршрут.request().url()).pathname.split('/').pop();
    const файл = path.join(кеш, ім);
    if (fs.existsSync(файл)) await маршрут.fulfill({path: файл, contentType: ім.endsWith('.wasm') ? 'application/wasm'
      : ім.endsWith('.js') ? 'application/javascript' : 'application/octet-stream'});
    else await маршрут.abort();
  });
  await стор.goto('http://127.0.0.1:' + сервер.address().port, {waitUntil: 'load', timeout: 120000});
  await стор.getByText('Люстерко покаже', {exact: false}).first().waitFor({state: 'visible', timeout: 30000});
  await стор.screenshot({path: path.join(тека, 'крок1_схеми_390x844.png')});
  const випадки = await стор.evaluate(async код => JSON.parse(await приладМостуП({}, код)), код);
  fs.writeFileSync(path.join(тека, 'крок1_схеми_браузер.json'), JSON.stringify({
    сторінка_sha256: crypto.createHash('sha256').update(html).digest('hex'), viewport: [390, 844], випадки, помилки}, null, 2));
  if (помилки.length) throw Error(помилки.join('\n'));
  console.log('ФАКТ · Chromium; воркер зібраного показу; випадків ' + випадки.length);
})().catch(е => { console.error(е); process.exitCode = 1; }).finally(async () => {
  if (браузер) await браузер.close();
  if (сервер) await new Promise(р => сервер.close(р));
});
