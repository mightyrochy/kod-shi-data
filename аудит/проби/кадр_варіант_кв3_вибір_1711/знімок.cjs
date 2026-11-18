// Вхідний екран відстеженого артефакту, 390×844, без викликів моделі.
const path = require('path');
const {createRequire} = require('module');
const {pathToFileURL} = require('url');
const дерево = path.resolve(process.argv[2] || '.');
const {chromium} = createRequire(path.join(дерево, 'джерела/package.json'))('playwright');
(async () => {
  const браузер = await chromium.launch({headless: true, args: ['--disable-gpu']});
  try {
    const сторінка = await браузер.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
    await сторінка.goto(pathToFileURL(path.join(дерево, 'index.html')).href, {waitUntil: 'domcontentloaded'});
    await сторінка.evaluate(() => document.fonts.ready);
    await сторінка.screenshot({path: path.join(__dirname, 'голова-390x844.png'), animations: 'disabled'});
    console.log('Знімок 390×844:', await сторінка.title());
  } finally {
    await браузер.close();
  }
})().catch(п => {console.error(п.message); process.exitCode = 1;});
