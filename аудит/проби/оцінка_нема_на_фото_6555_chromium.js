/* Рядок 6555: «На фото нема …» картки оцінки — у справжньому Chromium, 390×844, на ЗІБРАНІЙ сторінці, без моделі.
   Друкує для наборів кодів: текст рядка, скільки рядків він займає, шрифт і кегль — його й тексту «Що вдало» над ним.
   Шрифти — з `шрифти/` поруч зі сторінкою, тож сторінку віддає свій http-сервер (з file:// Chromium шрифтів не вантажить).
   Запуск: NODE_PATH=джерела/node_modules node аудит/проби/оцінка_нема_на_фото_6555_chromium.js <index.html> */
const { chromium } = require('playwright'), fs = require('fs'), path = require('path'), http = require('http');
const СТОРІНКА = path.resolve(process.argv[2]), КОРІНЬ = path.dirname(СТОРІНКА);
const НАБОРИ = [['shoes', 'bag', 'gloves', 'tights', 'jewelry', 'necklace'], ['outerwear', 'headwear'], ['shoes', 'bag'], ['bag']];
const сервер = http.createServer((з, в) => fs.readFile(path.join(КОРІНЬ, decodeURIComponent(з.url.split('?')[0])),
  (п, д) => { в.writeHead(п ? 404 : 200); в.end(д); }));
сервер.listen(0, '127.0.0.1', async () => {
  const б = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium' });
  const с = await (await б.newContext({ viewport: { width: 390, height: 844 } })).newPage();
  await с.route(/^https?:\/\/(?!127\.0\.0\.1)/, р => р.abort());       // Pyodide картці не потрібен
  await с.goto('http://127.0.0.1:' + сервер.address().port + '/' + path.basename(СТОРІНКА), { waitUntil: 'load', timeout: 120000 });
  await с.waitForFunction(() => typeof малюватиКарткуОцінкиП === 'function');
  for (const коди of НАБОРИ) {
    const р = await с.evaluate(async коди => {
      document.querySelectorAll('section').forEach(е => е.style.display = 'none');
      for (let е = document.getElementById('оц-результат'); е; е = е.parentElement)
        if (getComputedStyle(е).display === 'none') е.style.display = 'block';
      ОЦ.перелік = {так: true}; ОЦ.фото = [];
      ОЦ.результат = {картка: {відповідь: 'Образ вдалий.', вдало: [{текст: 'Кольори тримають одну гаму.'}], нема_на_фото: {коди}}};
      await document.fonts.load('15.5px "KyivType Serif"');
      малюватиКарткуОцінкиП();
      const н = document.querySelector('.оц-нема-на-фото'), сн = getComputedStyle(н), св = getComputedStyle(document.querySelector('.оц-вдало div'));
      return {рядків: Math.round(н.getBoundingClientRect().height / parseFloat(сн.lineHeight)), текст: н.textContent, повний: н.title || null,
              шрифт: сн.fontFamily.split(',')[0] + ' ' + сн.fontSize, вдало: св.fontFamily.split(',')[0] + ' ' + св.fontSize};
    }, коди);
    console.log(коди.join(','), JSON.stringify(р));
  }
  await б.close(); сервер.close();
});
