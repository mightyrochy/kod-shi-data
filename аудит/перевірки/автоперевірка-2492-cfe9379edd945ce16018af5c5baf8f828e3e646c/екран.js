/* Контрольний екран голови PR, 390×844; усі зовнішні запити заблоковано. */
const fs = require('fs'), path = require('path');
const repo = path.resolve(process.argv[2]), code = path.join(repo, 'джерела');
const {chromium} = require(path.join(code, 'node_modules/playwright'));
const {підставитиШаблон, прочитатиДовідникJSON} = require(path.join(code, 'показ_шаблон.js'));
(async () => {
  const html = підставитиШаблон(fs.readFileSync(path.join(code, 'показ.html'), 'utf8'), {
    __МОДУЛІ_ПОКАЗУ__: 'офлайн', __ЗБІРКА_ПОКАЗУ__: 'перевірка-2492', __ВІДБИТОК__: 'перевірка-2492',
    __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(code)
  });
  const browser = await chromium.launch({headless: true, args: ['--disable-gpu']});
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
    await page.route('**/*', route => route.request().url() === 'http://offline.local/'
      ? route.fulfill({contentType: 'text/html', body: html}) : route.abort());
    await page.goto('http://offline.local/');
    await page.waitForFunction(() => !!document.getElementById('вк-сценарій').onclick);
    await page.evaluate(() => {
      режим('сценарій');
      ПАСПОРТ_П = {джерело:'модель', подія:'Співбесіда в офісі', нагода:'співбесіда', місце:'офіс',
        ошатність:[7,7], причина_ошатності:'evaluated', джерело_полів:{ошатність:'розмова'}};
      ВИПАДОК_ЗМІНЕНО_П = false;
      застосуватиПаспортДоЕкрана(ПАСПОРТ_П);
      малюватиКарткуСценарію();
      const card = document.getElementById('сц-картка');
      card.hidden = false;
      card.scrollIntoView({block:'center'});
    });
    await page.screenshot({path: path.join(__dirname, 'екран-390x844.png'), animations: 'disabled'});
    console.log('Знімок 390×844: екран-390x844.png; зовнішні запити заблоковано');
  } finally { await browser.close(); }
})().catch(error => {console.error(error); process.exitCode = 1;});
