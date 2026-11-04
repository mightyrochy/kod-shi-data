/* Дим показу голови 390×844: локальна фікстура, без моделей і мережі. */
const fs = require('fs'), path = require('path');
const дерево = path.resolve(process.argv[2]);
const дж = path.join(дерево, 'джерела');
const {chromium} = require(path.join(дж, 'node_modules/playwright'));
const {прочитатиДовідникJSON, підставитиШаблон, зібратиШаблонПоказу} = require(path.join(дж, 'показ_шаблон.js'));
async function головна(){
  const html = підставитиШаблон(зібратиШаблонПоказу(path.join(дж, 'показ.html')), {
    __МОДУЛІ_ПОКАЗУ__: 'офлайн', __ЗБІРКА_ПОКАЗУ__: '7eec2983ca3f', __ВІДБИТОК__: '2866',
    __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'офлайн',
    __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(дж)
  });
  const б = await chromium.launch({headless: true, args: ['--disable-gpu'],
    ...(process.env.CHROME_PATH ? {executablePath: process.env.CHROME_PATH} : {})});
  try {
    const с = await б.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
    const помилки = [];
    с.on('pageerror', е => помилки.push(String(е)));
    await с.route('**/*', р => р.request().url() === 'http://offline.local/'
      ? р.fulfill({contentType: 'text/html', body: html}) : р.abort());
    await с.goto('http://offline.local/#model_mova=offline');
    await с.waitForFunction(() => typeof рендер === 'function' && !!document.getElementById('вк-сценарій').onclick);
    await с.evaluate(() => {
      П = {в: 'ПОКАЗ-V1', прогін: 'перевірка-2866', збірка: '7eec2983ca3f', профіль: 'Оля',
        картки: [{рука: '1', текст: 'Образ на прогулянку.', речі: [
          {id: 'її-джинси', назва: 'Світлі джинси кльош', слот: 'низ', власна: true, чия: 'моя'},
          {id: 'її-светр', назва: 'Кремовий светр', слот: 'верх', власна: true, чия: 'моя'},
          {id: 'її-черевики', назва: 'Чорні черевики', слот: 'взуття', власна: true, чия: 'моя'}
        ], мітки: [], знахідки: []}]};
      рендер();
      window.scrollTo(0, 0);
    });
    await с.locator('#к-0').waitFor({state: 'visible'});
    await с.screenshot({path: path.join(__dirname, 'картка-390x844.png'), animations: 'disabled'});
    fs.writeFileSync(path.join(__dirname, 'знімок.json'), JSON.stringify({viewport: [390, 844],
      помилки, текст: await с.locator('#к-0').innerText(), горизонтальний_вихід:
        await с.evaluate(() => document.documentElement.scrollWidth > 390)}, null, 2));
    console.log('Знімок 390×844; помилки сторінки: ' + помилки.length);
    if (помилки.length) process.exitCode = 1;
  } finally { await б.close(); }
}
головна().catch(е => {console.error(е); process.exitCode = 1;});
