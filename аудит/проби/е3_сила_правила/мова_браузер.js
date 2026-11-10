/* Мовний гейт у воркері повної збірки й стартовий екран 390×844.
   NODE_PATH=джерела/node_modules node цей_файл <HTML> <кеш Pyodide> */
const fs = require('fs'), path = require('path'), http = require('http'), crypto = require('crypto');
const {chromium} = require('playwright');
const [файл, кеш] = process.argv.slice(2);
const html = fs.readFileSync(файл, 'utf8');
const штамп = (html.match(/const ЗБІРКА_ПОКАЗУ\s*=\s*"([^"]+)"/) || [])[1] || '';
const код = `import json, language_gate as м, реєстр_правил as р
результати = []
for текст, поле, правило, сила in [
    (м._КЕЙСИ[0][0], 'порушення', 'R-ONB-06', 'hard'),
    ('Для кольоротипу «літо» беріть приглушені відтінки', 'порушення', 'R-TYP-05', 'hard'),
    ('Рятуємо вас від перевантаження вибором', 'карантин', 'R-PSY-03/04', 'hint'),
    ('Красивое платье', 'порушення', м.ЯРУС_УКРАЇНСЬКОЇ, 'hard')]:
    for тір in [None, 'T3']:
        if тір:
            р.REGISTRY['__проба_мови_T3'] = dict(t=тір, val=1, прав=[правило])
        try:
            в = м._перевірити_обчислити(текст)
            з = next(з for з in в[поле] if з['правило'] == правило)
            оч = р.зн(правило, сила, з['суть'], [], '')
            assert з['сила'] == оч['сила']
            assert з.get('стеля_тіру') == оч.get('стеля_тіру')
            assert {'регістр', 'сила_нп', 'сила_нп_джерело', 'блокує'} <= з.keys()
            assert в['можна_видавати'] == (поле != 'порушення')
            результати.append(dict(правило=правило, тір=тір, знахідка=з))
        finally:
            if тір:
                del р.REGISTRY['__проба_мови_T3']
json.dumps(результати, ensure_ascii=False)`;
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
    const шлях = path.join(кеш, ім);
    if (fs.existsSync(шлях)) await маршрут.fulfill({path: шлях, contentType: ім.endsWith('.wasm') ? 'application/wasm'
      : ім.endsWith('.js') ? 'application/javascript' : 'application/octet-stream'});
    else await маршрут.abort();
  });
  await стор.goto('http://127.0.0.1:' + сервер.address().port, {waitUntil: 'load', timeout: 120000});
  await стор.getByText('Люстерко покаже', {exact: false}).first().waitFor({state: 'visible'});
  await стор.screenshot({path: path.join(__dirname, 'крок1_мова_390x844.png')});
  const випадки = await стор.evaluate(async код => JSON.parse(await приладМостуП({}, код)), код);
  const фото = await стор.evaluate(async () => await містП('показ', {каталог: ФІД_П, речі: [
    {id: 'ж-03408@25union.com.ua'}, {id: 'ж-09321@emmeliedelage.com'}, {id: 'ж-11585@theoriginals.com.ua'}]}));
  if (!Array.isArray(фото) || фото.length !== 3) throw Error('показ не повернув три контрольні картки');
  fs.writeFileSync(path.join(__dirname, 'крок1_мова_браузер.json'), JSON.stringify({
    сторінка_sha256: crypto.createHash('sha256').update(html).digest('hex'), viewport: [390, 844],
    випадки, фото, помилки}, null, 2) + '\n');
  if (помилки.length) throw Error(помилки.join('\n'));
  console.log('ФАКТ · Chromium; воркер повної збірки; випадків ' + випадки.length);
})().catch(е => { console.error(е); process.exitCode = 1; }).finally(async () => {
  if (браузер) await браузер.close();
  if (сервер) await new Promise(р => сервер.close(р));
});
