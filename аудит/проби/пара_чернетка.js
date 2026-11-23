/* Збережений образ змінюється лише після явного збереження чернетки.
   Запуск: NODE_PATH=джерела/node_modules node аудит/проби/пара_чернетка.js <index.html> */
const assert = require('node:assert/strict'), fs = require('node:fs');
const {chromium} = require('playwright');

(async () => {
  const браузер = await chromium.launch({...(process.env.CHROMIUM ? {executablePath: process.env.CHROMIUM} : {}), args: ['--no-sandbox']});
  try {
    const стор = await браузер.newPage({viewport: {width: 390, height: 844}, reducedMotion: 'reduce'});
    const адреса = 'http://localhost/';
    await стор.route('**/*', р => р.request().url() === адреса
      ? р.fulfill({contentType: 'text/html; charset=utf-8', body: fs.readFileSync(process.argv[2])}) : р.abort());
    const відкрити = async () => { await стор.goto(адреса); await стор.waitForFunction(() => window.MirrorRoom?.available()); };
    const дія = (ключ, значення) => стор.locator('[data-ux="' + ключ + '"]' +
      (значення === undefined ? '' : '[data-value="' + значення + '"]') + ':visible').first().click();
    const дані = () => стор.evaluate(() => читатиКв('дзеркало:речі:1:' + АКТИВНИЙ));
    await відкрити();
    await стор.evaluate(async () => {
      const речі = ['a', 'b', 'c'].map((id, i) => ({id, name: ['Сорочка', 'Спідниця', 'Штани'][i],
        color: '#f0ede5', price: null, image: '', url: '', shop: '', slot: i ? 'bottom' : 'top'}));
      await писатиКв('дзеркало:речі:1:' + АКТИВНИЙ, {version: 1, closet: речі,
        saved: [{id: 'saved', name: 'Збережений комплект', things: [речі[0]], worn: false, date: 1}],
        outfit: {name: '', side: 0, sets: [[], []], id: ''}, compare: {left: null, right: null, decision: ''}});
    });
    await відкрити();
    await дія('library'); await дія('rack-saved', 'saved'); await дія('rack-edit-saved', 'saved');
    await дія('rack-add-side', '0'); await дія('rack-set-own'); await дія('rack-item', 'b'); await дія('rack-add', 'b');
    await стор.waitForFunction(async () => (await читатиКв('дзеркало:речі:1:' + АКТИВНИЙ)).outfit.sets[0].length === 2);
    let стан = await дані();
    assert.deepEqual(стан.saved[0].things.map(р => р.id), ['a'], 'додавання до чернетки не змінює збережене');
    await відкрити();
    стан = await дані();
    assert.deepEqual(стан.saved[0].things.map(р => р.id), ['a'], 'початковий образ цілий після перезавантаження');
    assert.deepEqual(стан.outfit.sets[0].map(р => р.id), ['a', 'b'], 'чернетка збережена окремо');
    await дія('compose');
    await дія('rack-edit', '0|a'); await дія('rack-replace', '0|a'); await дія('rack-set-own');
    await дія('rack-item', 'c'); await дія('rack-add', 'c'); await дія('rack-accept-replacement');
    await стор.waitForFunction(async () => (await читатиКв('дзеркало:речі:1:' + АКТИВНИЙ)).outfit.sets[0][0].id === 'c');
    стан = await дані();
    assert.deepEqual(стан.saved[0].things.map(р => р.id), ['a'], 'підтверджена заміна теж лишається в чернетці');
    await дія('rack-save-outfit');
    await стор.locator('#rack-save-form button').click();
    await стор.waitForFunction(async () => (await читатиКв('дзеркало:речі:1:' + АКТИВНИЙ)).outfit.id === '');
    await відкрити();
    стан = await дані();
    assert.equal(стан.saved.length, 1, 'оновлено той самий образ');
    assert.deepEqual(стан.saved[0].things.map(р => р.id), ['c', 'b'], 'лише збереження переносить зміни до образу');
    console.log('Пара: додавання, заміна, перезавантаження та явне збереження — пройдено.');
  } finally { await браузер.close(); }
})().catch(помилка => { console.error(помилка); process.exitCode = 1; });
