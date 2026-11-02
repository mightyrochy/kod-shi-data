/* Дим шаблону призначеної голови без викликів моделей. */
const fs = require('fs');
const path = require('path');
const корінь = path.resolve(process.argv[2]);
const джерела = path.join(корінь, 'джерела');
const { chromium } = require(path.join(джерела, 'node_modules/playwright'));
const { підставитиШаблон, прочитатиДовідникJSON } = require(path.join(джерела, 'показ_шаблон.js'));

(async () => {
  const html = підставитиШаблон(fs.readFileSync(path.join(джерела, 'показ.html'), 'utf8'), {
    __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'перевірка', __ВІДБИТОК__: 'перевірка',
    __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(джерела)
  });
  const браузер = await chromium.launch({ headless: true, args: ['--disable-gpu'] });
  try {
    const сторінка = await браузер.newPage({ viewport: { width: 390, height: 844 } });
    const помилки = [];
    сторінка.on('pageerror', e => помилки.push(String(e)));
    await сторінка.route('**/*', route => route.abort());
    await сторінка.route('http://localhost/', route => route.fulfill({ contentType: 'text/html', body: html }));
    await сторінка.goto('http://localhost/', { waitUntil: 'load' });
    await сторінка.waitForTimeout(1000);
    await сторінка.screenshot({ path: path.join(__dirname, '390x844.png') });
    console.log(JSON.stringify({ помилок: помилки.length, помилки }));
  } finally {
    await браузер.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
