/* Показ записаної картки її спідниці у справжньому Chromium, без мережі й моделей. */
const fs = require('node:fs');
const path = require('node:path');
const корінь = path.resolve(__dirname, '../../..');
const джерела = path.join(корінь, 'джерела');
const {chromium} = require(path.join(джерела, 'node_modules/playwright'));
const Ш = require(path.join(джерела, 'показ_шаблон.js'));

(async () => {
  const дані = JSON.parse(fs.readFileSync(process.argv[2], 'utf8').replace(/^\uFEFF/, ''));
  const запис = дані.записи.find(р => р.вхід.includes('/ж4_робота_спідниця_фото/'));
  if (!запис) throw new Error('немає запису її спідниці');
  const html = Ш.підставитиШаблон(Ш.зібратиШаблонПоказу(path.join(джерела, 'показ.html')), {
    __МОДУЛІ_ПОКАЗУ__: '', __ЗБІРКА_ПОКАЗУ__: 'офлайн', __ВІДБИТОК__: 'офлайн',
    __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '', __ДОВІДНИК_ПОКАЗУ__: Ш.прочитатиДовідникJSON(джерела),
  }).replace(/<script[^>]+src="https:[^"]+"[^>]*><\/script>/g, '');
  const браузер = await chromium.launch({headless: true});
  try {
    const сторінка = await браузер.newPage({viewport: {width: 390, height: 844}});
    await сторінка.route('**/*', р => р.request().url() === 'http://127.0.0.1:42176/'
      ? р.fulfill({contentType: 'text/html; charset=utf-8', body: html}) : р.abort());
    await сторінка.goto('http://127.0.0.1:42176/');
    await сторінка.waitForFunction(() => typeof document.getElementById('сцн-новий').onclick === 'function');
    await сторінка.evaluate(речі => {
      П = {картки: [{речі, опис: 'Образ із твоєю спідницею.', як_носити: [], свідомі: []}],
           збірка: 'офлайн', каталог: '', профіль: '', вердикти: []};
      рендер();
    }, запис.картки);
    await сторінка.evaluate(() => Promise.all(document.getAnimations().filter(а =>
      а.effect.getTiming().iterations !== Infinity).map(а => а.finished.catch(() => {}))));
    await сторінка.screenshot({path: process.argv[3]});
    console.log(await сторінка.locator('#картки').innerText());
  } finally {
    await браузер.close();
  }
})().catch(п => { console.error(п); process.exitCode = 1; });
