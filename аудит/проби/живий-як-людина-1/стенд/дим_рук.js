/* Дим стенда (не доказ продукту): справжня сторінка `index.html`, справжній `рендерКартку`, вигадані картки з відомим ключем і
   двома фото (жива адреса з обміну й мертва) — `знімокРук` має віддати позицію, руку, сід, src і стан завантаження.
   Другий аргумент — файл, куди дописати запис у форматі руки.jsonl (для `python3 звести.py руки`).
   Запуск: STOR=<тека з index.html> PYODIDE=/tmp/pyodide node дим_рук.js */
const { chromium } = require('playwright'); const path = require('path'), fs = require('fs');
const { знімокРук, доЗавантажитиФото } = require('./руки_зі_сторінки.js');
const КОРІНЬ = process.env.STOR || '/tmp/стенд', БАЗА = 'http://127.0.0.1:8765', ЖИВЕ = process.env.ЖИВЕ_ФОТО || 'https://upload.wikimedia.org/wikipedia/commons/4/47/PNG_transparency_demonstration_1.png';
(async () => {
  const б = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium',
    proxy: process.env.HTTPS_PROXY ? {server: process.env.HTTPS_PROXY, bypass: 'localhost,127.0.0.1'} : undefined});
  const к = await б.newContext({viewport: {width: 390, height: 844}, ignoreHTTPSErrors: true});
  const с = await к.newPage();
  await с.route(u => u.origin === БАЗА, r => r.fulfill({status: 200, contentType: 'text/html; charset=utf-8',
    body: fs.readFileSync(path.join(КОРІНЬ, 'index.html'))}));
  await с.route('https://cdn.jsdelivr.net/pyodide/**', r => r.abort());
  await с.route(u => u.origin !== БАЗА && /dead\.invalid/.test(u.href), r => r.abort());
  await с.goto(БАЗА + '/index.html', {waitUntil: 'load', timeout: 120000});
  const до = await знімокРук(с);
  const речі = (п, жива) => [{id: 'a' + п, назва: 'Верх ' + п, слот: 'top', фото: жива ? ЖИВЕ : 'https://dead.invalid/x.jpg', фото_усі: [жива ? ЖИВЕ : 'https://dead.invalid/x.jpg']}];
  await с.evaluate(({речі: р}) => {
    ЗБ = {картки: [{}, {}, {}, {}], ключ: ['3', '1', '2', '4'], діагноз: ['control · hand_2_broken=K-CRA-01 · drawn_from=K-CRA-01,K-SIL-03'],
          вхід_рук: {сід: 4242}, поломка: {коди: ['K-CRA-01']}, контроль: {поломка: 'K-CRA-01'}, готово: true};
    П = {прогін: 'тест-1', картки: [0, 1, 2, 3].map(п => ({речі: р[п], збій: null}))};
    const м = document.createElement('div'); м.id = 'дим'; document.body.appendChild(м);
    [0, 1, 2, 3].forEach(п => { try { м.appendChild(рендерКартку(п)); } catch (е) { м.dataset.помилка = String(е).slice(0, 200); } });
  }, {речі: [0, 1, 2, 3].map(п => речі(п, п !== 1))});
  await доЗавантажитиФото(с); await new Promise(р => setTimeout(р, 5000));
  const з = await знімокРук(с);
  console.log('до побудови:', JSON.stringify(до));
  console.log(JSON.stringify(з && {сід: з.сід, ключ: з.ключ, прогін: з.прогін, поломка: з.поломка_руки_2, поз: з.позиції.map(п => [п.позиція, п.ід_картки, п.рука, п.ф.map(ф => [ф.src.slice(0, 40), ф.завантажено, ф.силует || false]), п.дані_речей.length])}, null, 1));
  console.log('помилка рендера:', await с.evaluate(() => document.getElementById('дим').dataset.помилка || 'нема'));
  if (process.argv[2]) fs.appendFileSync(process.argv[2], JSON.stringify({крок: 1, мітка: 'кінець', час: new Date().toISOString(), ...з}) + '\n');
  await б.close();
})().catch(е => { console.error(е); process.exit(1); });
