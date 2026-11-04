/* Офлайн-знімок поточного шаблону показу; це не живе приймання. */
const path = require('path'), fs = require('fs');
const root = path.resolve(__dirname, '../../..');
const { chromium } = require(path.join(root, 'джерела/node_modules/playwright'));
const { зібратиШаблонПоказу } = require(path.join(root, 'джерела/показ_шаблон.js'));
(async () => {
  const browser = await chromium.launch({headless: true});
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
    await page.route('**/*', route => route.abort());
    const errors = [];
    page.on('pageerror', e => errors.push(String(e)));
    await page.setContent(зібратиШаблонПоказу(path.join(root, 'джерела/показ.html')), {waitUntil: 'domcontentloaded'});
    await page.screenshot({path: path.join(__dirname, 'портрет-390.png'), fullPage: true});
    fs.writeFileSync(path.join(__dirname, 'знімок.json'), JSON.stringify({ширина: 390, висота: 844,
      помилки: errors, джерело: 'поточний шаблон; мережа вимкнена'}, null, 2));
    console.log('знімок 390×844; помилок сторінки:', errors.length);
  } finally {
    await browser.close();
  }
})().catch(e => {console.error(e); process.exitCode = 1;});
