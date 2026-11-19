// Візуальний дим відбору, без виклику моделі: реальні речі з каталогу в картках показу.
// node знімки.cjs <дерево PR> <зібраний html> <тека даних>
const fs = require('fs');
const path = require('path');
const {pathToFileURL} = require('url');
const [tree, html, out] = process.argv.slice(2).map(x => path.resolve(x));
const {chromium} = require(path.join(tree, 'джерела/node_modules/playwright'));
const after = JSON.parse(fs.readFileSync(path.join(out, 'після.json'), 'utf8'));
const sample = ['сукня', 'низ'].map(s => {
  const r = after.каталог.форми.міді_без_слота[s].приклади[0];
  return {...r, фото: r.фото[0]};
});
const card = r => ({рука: '1', ітерацій: 1, викликів: 0, текст: r.назва, опис: r.назва, підпис: '',
  речі: [r], мітки: [], знахідки: [], питання: [], етапи: {викликів: 0, виклики: []}, свідомі: [],
  невиконано: null, різноманітність: null, мова: [], мова_спроб: 0, мова_видано: 'так', фото_не_ті: [], дібрав_код_слоти: []});
const packet = cards => ({в: 'ПОКАЗ-V1', збірка: 'перевірка 4031', каталог: 'каталог_повний.xml',
  профіль: 'Оля', розклад: '1234', прогін: 'перевірка-4031', випадок_рядок: 'Робота', пул: 27525, картки: cards});

let browser;
(async () => {
  browser = await chromium.launch({headless: true});
  const context = await browser.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(String(e)));
  await page.route(/^https?:/, r => r.request().resourceType() === 'image' ? r.continue() : r.abort());
  await page.goto(pathToFileURL(html).href);
  await page.waitForFunction(() => typeof рендер === 'function', null, {timeout: 60000});
  const result = {FOTO: process.env.FOTO, viewport: {width: 390, height: 844}, кадри: [], errors};
  for (const [name, cards, position] of [['до', [], 0], ['після', sample.map(card), 0], ['після-спідниця', sample.map(card), 1]]) {
    await page.evaluate(({p, position}) => { П = p; рендер(); if (window.показатиОбраз && П.картки.length) window.показатиОбраз(position); }, {p: packet(cards), position});
    if (cards.length) {
      await page.waitForSelector(`#к-${position} .список .річ`);
      await page.evaluate(async () => {
        await Promise.all([...document.querySelectorAll('#картки img')].map(img => img.complete ? null :
          new Promise(resolve => { img.onload = resolve; img.onerror = resolve; setTimeout(resolve, 20000); })));
      });
      await page.locator(`#к-${position}`).scrollIntoViewIfNeeded();
    }
    await page.screenshot({path: path.join(out, name + '.png')});
    result.кадри.push({назва: name, карток: cards.length,
      фото: await page.locator('#картки img').evaluateAll(images => images.map(i => ({src: i.currentSrc, width: i.naturalWidth}))),
      текст: await page.locator('#картки').innerText()});
  }
  fs.writeFileSync(path.join(out, 'знімки.json'), JSON.stringify(result, null, 2));
  await browser.close();
  console.log(JSON.stringify(result));
})().catch(async e => { console.error(e); if (browser) await browser.close(); process.exitCode = 1; });
