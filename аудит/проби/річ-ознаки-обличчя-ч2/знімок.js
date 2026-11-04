/* Офлайн-знімок поточного шаблону показу; це не живе приймання. */
const path = require('path'), fs = require('fs');
const root = path.resolve(__dirname, '../../..');
const { chromium } = require(path.join(root, 'джерела/node_modules/playwright'));
const { підставитиШаблон, прочитатиДовідникJSON } = require(path.join(root, 'джерела/показ_шаблон.js'));
(async () => {
  const browser = await chromium.launch({headless: true});
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
    await page.route('**/*', route => route.abort());
    const errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    const html = підставитиШаблон(fs.readFileSync(path.join(root, 'джерела/показ.html'), 'utf8'), {
      __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'офлайн-ч2', __ВІДБИТОК__: 'ч2',
      __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'офлайн-шаблон',
      __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(path.join(root, 'джерела')),
    }).replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"\n]*"[^>]*><\/script>/,
      '<script>window.loadPyodide=null;</script>');
    await page.route('http://127.0.0.1:8765/', route => route.fulfill({
      contentType: 'text/html; charset=utf-8', body: html,
    }));
    await page.goto('http://127.0.0.1:8765/', {waitUntil: 'domcontentloaded'});
    await page.screenshot({path: path.join(__dirname, 'портрет-390.png'), fullPage: true, animations: 'disabled'});
    fs.writeFileSync(path.join(__dirname, 'знімок.json'), JSON.stringify({ширина: 390, висота: 844,
      помилки: errors, джерело: 'поточний шаблон; мережа вимкнена'}, null, 2));
    console.log('знімок 390×844; помилок сторінки:', errors.length);
  } finally {
    await browser.close();
  }
})().catch(e => {console.error(e); process.exitCode = 1;});
