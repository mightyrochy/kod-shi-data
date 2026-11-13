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
    П = {прогін: 'тест-1', розклад: '3124', картки: [0, 1, 2, 3].map(п => ({речі: р[п], збій: null}))};
    const м = document.createElement('div'); м.id = 'дим'; document.body.appendChild(м);
    [0, 1, 2, 3].forEach(п => { try { м.appendChild(рендерКартку(п)); } catch (е) { м.dataset.помилка = String(е).slice(0, 200); } });
  }, {речі: [0, 1, 2, 3].map(п => речі(п, п !== 1))});
  await доЗавантажитиФото(с); await new Promise(р => setTimeout(р, 5000));
  const з = await знімокРук(с);
  const ряд = [з];
  /* послідовність збирань: А готово → Б збирається (ЗБ уже нове, П і DOM ще А) → Б готово: руки старих карток не змінюються */
  await с.evaluate(() => { ЗБ = {картки: [], ключ: ['4', '2', '1', '3'], діагноз: [], вхід_рук: {сід: 777}, готово: false}; });
  const збираєтьсяБ = await знімокРук(с); ряд.push(збираєтьсяБ);
  await с.evaluate(() => {
    П = {прогін: 'тест-2', розклад: '4213', картки: [0, 1, 2, 3].map(() => ({речі: [], збій: null}))};
    ЗБ.картки = П.картки; ЗБ.готово = true;
    document.getElementById('дим').replaceChildren(...П.картки.map((_, п) => рендерКартку(п)));
  });
  const готовоБ = await знімокРук(с); ряд.push(готовоБ);
  const руки = з => з.позиції.map(п => п.рука).join('');
  const перевірки = [['без П запису нема', до === null], ['А: 3124 з сідом 4242', з.ключ === '3124' && руки(з) === '3124' && з.сід === 4242],
    ['Б збирається: руки старих карток А', руки(збираєтьсяБ) === '3124' && збираєтьсяБ.прогін === 'тест-1' && збираєтьсяБ.сід === null],
    ['Б готово: 4213 з сідом 777', руки(готовоБ) === '4213' && готовоБ.прогін === 'тест-2' && готовоБ.сід === 777]];
  for (const [н, ок] of перевірки) console.log((ок ? 'ТАК ' : 'НІ  ') + н);
  console.log('позиції А:', з.позиції.map(п => [п.позиція, п.ід_картки, п.рука, п.ф.map(ф => [ф.src.slice(0, 30), ф.завантажено, ф.силует || false]), п.дані_речей.length].join(' ')).join(' | '));
  if (process.argv[2]) fs.appendFileSync(process.argv[2], ряд.filter(Boolean).map(х => JSON.stringify({крок: 1, мітка: 'дим', час: new Date().toISOString(), ...х})).join('\n') + '\n');
  await б.close();
  if (перевірки.some(([, ок]) => !ок)) process.exit(1);
})().catch(е => { console.error(е); process.exit(1); });
