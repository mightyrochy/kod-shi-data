/* Жива рука 7б у Chromium 390×844: чипи й клавіатура, змінна пара, питання, полотно, файл і «не ця».
   Сторінка складена як у стенді показу, образи — підготовлені дані без викликів моделі.
   Запуск: NODE_PATH=джерела/node_modules node 7б_картка.js <тека джерела> [префікс знімків]. Факти — JSON. */
const path = require('path'), дж = path.resolve(process.argv[2]);
const { chromium } = require('playwright');
const { прочитатиДовідникJSON, підставитиШаблон, зібратиШаблонПоказу } = require(path.join(дж, 'показ_шаблон.js'));
(async () => {
  const html = підставитиШаблон(зібратиШаблонПоказу(path.join(дж, 'показ.html')), {
    __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'показ-тест', __ВІДБИТОК__: 'abc', __ФІД_ПОКАЗУ__: 'каталог_brief.xml',
    __КАТАЛОГ_ПОКАЗУ__: 'каталог_стенд.xml · 639 речей', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(дж)})
    .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"]*"[^>]*><\/script>/, '<script>window.loadPyodide=null;</script>');
  const б = await chromium.launch(), с = await б.newPage({viewport: {width: 390, height: 844}});
  const помилки = []; с.on('pageerror', e => помилки.push(String(e)));
  await с.route('**/*', r => { const у = new URL(r.request().url());
    if (у.pathname === '/build.txt') return r.fulfill({contentType: 'text/plain', body: 'показ-тест\n'});
    return у.pathname === '/' ? r.fulfill({contentType: 'text/html', body: html}) : r.abort(); });
  await с.goto('http://stend.test/');
  await с.waitForFunction(() => Екран.стан.вхід > 0 && Екран.стан.запущено, null, {timeout: 60000});
  await с.evaluate(() => {
    const реч = н => [{id: 'ж-' + н + '@g.com', назва: 'Сукня ' + н, ціна: 3000, слот: 'сукня', фото: null},
                      {id: 'п-' + н + '@g.com', назва: 'Пасок ' + н, ціна: 500, слот: 'пояс', фото: null}];
    const к = (рука, поз) => ({рука, ітерацій: 1, викликів: 1, текст: 'образ ' + рука, опис: 'образ ' + рука, підпис: 'образ ' + рука,
      речі: реч(рука), мітки: [], знахідки: [], питання: [], етапи: {викликів: 1, виклики: []}, свідомі: [], невиконано: null,
      різноманітність: null, мова: [], мова_спроб: 0, мова_видано: 'так', фото_не_ті: [], дібрав_код_слоти: [],
      збирання: {сід: 7, ключ: '2143', позиція: поз, рука}});
    П = {в: 'ПОКАЗ-V1', збірка: 'тест-7а', каталог: 'каталог_стенд.xml · 639 речей', профіль: 'Оля', розклад: '2143',
         випадок_шматки: [{ключ: 'нагода', текст: 'Робота'}, {ключ: 'місце', текст: 'офіс'}, {ключ: 'опади', текст: 'сніг', код: 'сніг'}],
         пул: 100, прогін: новийІдПрогону(), картки: ['2', '1', '4', '3'].map(к)};
    рендер();
  });

  await с.evaluate(() => {
    const кадр = 'data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="240" height="300"><rect width="240" height="300" fill="#eee7df"/><path d="M90 35h60l-12 55 45 170H57l45-170z" fill="#735449"/></svg>');
    П.картки.forEach(к => {
      к.носіння_жінці = 'Для довгої прогулянки візьми зручне взуття.';
      к.змінна_пара = {id: 'в-1@g.com', назва: 'Зручне взуття', підпис: 'Змінна пара на низькому ходу', ціна: 1200, фото: кадр};
      к.питання_жінці = ['Чи зручно тобі в цьому образі?']; к.питання_кнопка = 'Ще про цей образ';
    });
    рендер();
  });
  const assert = require('assert').strict;
  const факти = {змінних_пар: await с.locator('.змінна-пара').count(), силуетів: await с.locator('#к-0 .список .арка').count()};
  assert.equal(факти.змінних_пар, 4); assert.equal(факти.силуетів, 2);
  await с.waitForTimeout(700);
  if (process.argv[3]) await с.screenshot({path: process.argv[3] + '_картка.png'});
  const вісь = с.locator('#к-0 .ряд[data-поле="верд"] .чип[data-код="one_change"]');
  await вісь.click();
  факти.вибір = await с.evaluate(() => ({код: В[0].верд_код,
    обраних: document.querySelectorAll('#к-0 .ряд[data-поле="верд"] .чип.вибр').length,
    натиснута: document.querySelector('#к-0 .чип[data-код="one_change"]').getAttribute('aria-pressed')}));
  assert.equal(факти.вибір.код, 'one_change'); assert.equal(факти.вибір.обраних, 1); assert.equal(факти.вибір.натиснута, 'true');
  await с.locator('#к-0 .ряд[data-поле="аспекти"] .чип[data-код="colour"]').click();
  факти.аспекти = await с.evaluate(() => В[0].аспекти);
  assert.deepEqual(факти.аспекти, ['colour']);
  await с.locator('#к-0 .ряд[data-поле="верд"] .чип[data-код="as_is"]').focus();
  await с.keyboard.press('Enter');
  assert.equal(await с.evaluate(() => В[0].верд_код), 'as_is');
  await с.locator('#к-0 .питання-коду summary').click();
  await с.waitForFunction(() => [...document.querySelectorAll('#картки .питання-коду')].every(п => п.open));
  факти.питання_відкрито = await с.locator('#картки .питання-коду[open]').count();
  await с.locator('#к-0 .питання-коду summary').click();
  await с.waitForFunction(() => [...document.querySelectorAll('#картки .питання-коду')].every(п => !п.open));
  факти.питання_закрито = await с.locator('#картки .питання-коду[open]').count();
  await с.locator('#к-0 details').filter({has: с.locator('#ку-0')}).locator('summary').click();
  await с.locator('#ку-0').fill('data:image/svg+xml,' + encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="240" height="300"><rect width="240" height="300" fill="#ddd0c0"/><path d="M90 35h60l-12 55 45 170H57l45-170z" fill="#735449"/></svg>'));
  await с.evaluate(() => { П.картки[0].етапи.повернення = {символів: document.getElementById('ку-0').value.length}; });
  await с.locator('#куо-0').click();
  await с.waitForFunction(() => document.querySelector('#пол-0 img')?.naturalWidth > 0);
  факти.полотно = await с.locator('#пол-0 img').count();
  await с.locator('#пол-0').scrollIntoViewIfNeeded();
  if (process.argv[3]) await с.screenshot({path: process.argv[3] + '_полотно.png'});
  await с.locator('#кф-0').setInputFiles({name: 'Мій образ.png', mimeType: 'image/png',
    buffer: Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+j6X8AAAAASUVORK5CYII=', 'base64')});
  await с.waitForFunction(() => document.getElementById('кст-0').textContent.includes('Мій образ.png'));
  факти.локальний_файл = await с.locator('#кст-0').textContent();
  await с.locator('#к-0 button.замін').first().click();
  await с.waitForFunction(() => document.querySelector('#к-0 button.замін').getAttribute('aria-pressed') === 'true');
  факти.не_ця = await с.evaluate(() => ({натиснута: document.querySelector('#к-0 button.замін').getAttribute('aria-pressed'),
    напис: document.querySelector('#к-0 button.замін').textContent, набір: НЕ_ЦЯ_П.знімок()}));
  await с.locator('#к-0 .список').scrollIntoViewIfNeeded();
  if (process.argv[3]) await с.screenshot({path: process.argv[3] + '_не_ця.png'});
  assert.equal(факти.не_ця.натиснута, 'true'); assert.match(факти.не_ця.напис, /на заміну/);
  await с.evaluate(() => {
    const картинка = П.картки[0].картинка;
    П.картки.forEach(к => { к.картинка = картинка; });
    рендер();
  });
  факти.полотен_після_перемалювання = await с.locator('#картки .полотно img').count();
  assert.equal(факти.полотен_після_перемалювання, 4);
  await с.evaluate(() => {
    П.картки[0].питання = [{на_розгортання: true, повідомлення: {kind: 'card_colour'}}];
    питаннямиП = async () => { throw new Error('пробний збій допису'); };
    рендер();
  });
  await с.locator('#к-0 .питання-коду summary').click();
  await с.waitForFunction(() => document.querySelector('#к-0 .задум-збій'));
  факти.збій_питань_не_стер_перелік = (await с.locator('#к-0 .питання-коду .задум').textContent()).includes('Чи зручно тобі');
  assert.equal(факти.збій_питань_не_стер_перелік, true);
  await с.evaluate(() => {
    питаннямиП = async к => {
      await new Promise(так => setTimeout(так, 20));
      к.питання[0].текст = 'Дописано';
      к.питання_жінці.push('Чи хочеш інший колір?');
    };
  });
  await с.locator('#к-0 .питання-коду summary').click();
  await с.waitForFunction(() => !document.querySelector('#к-0 .питання-коду').open);
  await с.locator('#к-0 .питання-коду summary').click();
  await с.waitForFunction(() => document.querySelector('#к-0 .питання-коду .задум').textContent.includes('Чи хочеш інший колір?'));
  факти.повтор_питань = await с.locator('#к-0 .питання-коду summary').textContent();
  факти.збоїв_після_повтору = await с.locator('#к-0 .задум-збій').count();
  assert.equal(факти.збоїв_після_повтору, 0); assert.match(факти.повтор_питань, /2$/);
  assert.equal(помилки.length, 0);
  console.log(JSON.stringify({факти, помилки}, null, 1)); await б.close();
})().catch(e => { console.error(e); process.exit(1); });
