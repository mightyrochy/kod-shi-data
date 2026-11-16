// Вхідний екран наявного index.html голови, 390×844; без викликів моделі.
const path = require('path');
const {createRequire} = require('module');
const {pathToFileURL} = require('url');
const дерево = path.resolve(process.argv[2]);
const {chromium} = createRequire(path.join(дерево, 'джерела/package.json'))('playwright');
(async () => {
  const browser = await chromium.launch({headless: true, args: ['--disable-gpu']});
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
    await page.goto(pathToFileURL(path.join(дерево, 'index.html')).href, {waitUntil: 'domcontentloaded'});
    await page.evaluate(() => document.fonts.ready);
    await page.screenshot({path: path.join(__dirname, 'голова-390x844.png')});
    console.log('Знімок 390×844 записано; заголовок:', await page.title());
  } finally {
    await browser.close();
  }
})().catch(e => {console.error(e.message); process.exitCode = 1;});
