// Прицільна проба справжніх помічників PR у Chromium на керованому стані.
// node <цей файл> <тимчасове дерево з blob PR> <тека залежностей>
const fs = require('fs'), path = require('path'), vm = require('vm'), assert = require('assert/strict');
const root = path.resolve(process.argv[2]);
const {chromium} = require(path.join(path.resolve(process.argv[3]), 'node_modules/playwright'));
const {чекатиСтан} = require(path.join(root, 'джерела/проби/очікування.js'));
const source = fs.readFileSync(path.join(root, 'аудит/проби/рв6_стенд.js'), 'utf8');
const log = [];
(async () => {
  const browser = await chromium.launch({headless: true});
  try {
    const page = await browser.newPage({viewport: {width: 390, height: 844}});
    await page.setContent('<div id="к-0"><button class="замін" data-id="1" disabled>на заміну</button></div>');
    await page.evaluate(() => {
      window.П = {картки: [{рука: '1', речі: [{id: '1', слот: 'верх'}], етапи: {заміни: []}}]};
      window.активна = true;
      window.ЗАМІНИ_П = {has: () => window.активна};
      window.НЕ_ЦЯ_П = {size: 1, знімок: () => ({'1': ['1']})};
      window.ЧЕКАЮТЬ_МОСТА_П = new Map([[1, {асинх: false}]]);
      window.ПІДЙОМ_МОСТА_П = false;
      window.РЕЖИМ = 'образи'; window.ОСТАННЯ_ДІЯ_П = null; window.ДІЇ_П = new Map();
    });
    const context = vm.createContext({стор: page, чекатиСтан, Date, fs, path,
      console: {log: (...x) => log.push(x.join(' ')), error: (...x) => log.push(x.join(' '))},
      ЗНІМКИ: root, консоль: []});
    const wrapStart = source.indexOf('  const МІСТ_ТИХИЙ =');
    const wrapEnd = source.indexOf('  /* ЗАГЛУШКА РОЗПІЗНАВАННЯ', wrapStart);
    const helperStart = source.indexOf('  async function діагностикаОчікування(');
    const helperEnd = source.indexOf('  /* ── ЧОМУ ФОТО', helperStart);
    assert(wrapStart > 0 && wrapEnd > wrapStart && helperEnd > helperStart);
    vm.runInContext('const МЕЖА_МОСТУ = 900000;\n' + source.slice(wrapStart, wrapEnd) +
      source.slice(helperStart, helperEnd) + '\nthis.probe = {чекатиКартку, чекатиЗаміну};', context);
    const {чекатиКартку, чекатиЗаміну} = context.probe;
    await assert.rejects(чекатиСтан(page, 'стара умова з тишею', () => НЕ_ЦЯ_П.size > 0, null, 100), /ТАЙМАУТ/);
    await чекатиКартку(0, 'позначка під час моста', () => НЕ_ЦЯ_П.size > 0, null, 1000);
    log.push('ДО: тайм-аут при наявній позначці; ПІСЛЯ: позначку прочитано під час моста');
    const pending = чекатиЗаміну(0, 0);
    await page.показПідЧасМоста.evaluate(() => setTimeout(() => {
      П.картки[0].етапи.заміни.push({закінчено: Date.now()}); window.активна = false;
    }, 150));
    assert.equal(await pending, true);
    log.push('Завершений етап: true після звільнення дії');
    await page.показПідЧасМоста.evaluate(() => { П.картки[0].етапи.заміни = []; window.активна = false; });
    assert.equal(await чекатиЗаміну(0, 0), false);
    log.push('Скасована дія без етапу: false');
    await assert.rejects(чекатиКартку(0, 'навмисний тайм-аут', () => false, null, 100), /навмисний тайм-аут/);
    const diagnostic = JSON.parse(fs.readFileSync(path.join(root, 'очікування.json'), 'utf8'));
    assert.equal(diagnostic.стан.міст.length, 1);
    assert.equal(diagnostic.стан.не_ця['1'][0], '1');
    assert(fs.statSync(path.join(root, 'таймаут.png')).size > 0);
    log.push('Тайм-аут: первісна помилка збережена, JSON і знімок створені під час моста');
    assert.equal((source.match(/await чекатиЗаміну\(/g) || []).length, 2);
    assert.equal((source.match(/await чекатиКартку\(/g) || []).length, 2);
    console.log(log.join('\n'));
    console.log('ПРОЙДЕНО 5 перевірок; модель і продукт не запускалися');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
