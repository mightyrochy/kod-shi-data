/* Жива рука 7в у Chromium 390×844: вердикт і поле коментаря — дотик осі, рамка й порада поля, набір, вихід з поля,
   «Записати вердикт» без нічого, «Твій коментар», підказка непрочитаного коментаря, перемальована картка. Сторінка складена як у стенді показу.
   Запуск: NODE_PATH=джерела/node_modules node 7в_вердикт.js <тека джерела> [префікс знімків]. Факти — JSON. */
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
  const assert = require('assert').strict, факти = {};
  const стан = поз => с.evaluate(поз => ({
    питання: document.getElementById('пит-поля-' + поз).textContent,
    підказка_поля: document.getElementById('ком-' + поз).placeholder,
    порада: document.getElementById('порада-поля-' + поз).textContent,
    аспекти_видно: document.getElementById('аспекти-' + поз).style.display !== 'none',
    мітка_аспектів: document.getElementById('аспекти-мітка-' + поз).textContent,
    статус: document.getElementById('вст-' + поз).textContent,
    рамка: document.getElementById('ком-' + поз).classList.contains('в-фокус'),
    поле: document.getElementById('ком-' + поз).value,
    модель: {верд: В[поз].верд_код || '', коментар: В[поз].коментар || '', аспекти: В[поз].аспекти || []},
    записаний: (document.querySelector('#ком-запис-' + поз + ' p') || {}).textContent || null}), поз);
  факти.старт = await стан(0);
  assert.equal(факти.старт.аспекти_видно, false); assert.equal(факти.старт.рамка, false); assert.equal(факти.старт.статус, '');
  assert.ok(факти.старт.питання.length > 0);

  /* 1. «Записати вердикт» без жодного дотику — напис «нема що записати», запису нема */
  await с.locator('#зап-0').scrollIntoViewIfNeeded();
  await с.locator('#зап-0').click();
  await с.waitForFunction(() => document.getElementById('вст-0').textContent.length > 0);
  факти.нема_що = await с.evaluate(() => ({статус: document.getElementById('вст-0').textContent, очікувано: НЕМА_ЩО_ЗАПИСАТИ_П}));
  assert.equal(факти.нема_що.статус, факти.нема_що.очікувано);
  if (process.argv[3]) await с.screenshot({path: process.argv[3] + '_нема_що.png'});

  /* 2. дотик осі «Вдягнеш?» — вибір у моделі, аспекти під полем, рамка поля, запис і «Записано.» */
  await с.locator('#к-0 .ряд[data-поле="верд"] .чип[data-код="one_change"]').click();
  await с.waitForFunction(() => document.getElementById('вст-0').textContent === 'Записано.', null, {timeout: 20000});
  факти.після_осі = await стан(0);
  assert.equal(факти.після_осі.модель.верд, 'one_change'); assert.equal(факти.після_осі.аспекти_видно, true);
  await с.locator('#ком-0').scrollIntoViewIfNeeded(); await с.waitForTimeout(500);
  if (process.argv[3]) await с.screenshot({path: process.argv[3] + '_вісь.png'});

  /* 3. аспект: дотик → у моделі й на чипі */
  await с.locator('#к-0 .ряд[data-поле="аспекти"] .чип[data-код="colour"]').click();
  await с.waitForFunction(() => (В[0].аспекти || []).includes('colour'));
  факти.аспект = await с.evaluate(() => ({аспекти: В[0].аспекти,
    натиснутий: document.querySelector('#к-0 .ряд[data-поле="аспекти"] .чип[data-код="colour"]').classList.contains('вибр')}));
  assert.equal(факти.аспект.натиснутий, true);

  /* 4. набір у полі: слова — в моделі з першої літери, фокус знімає рамку, поле росте */
  const висотаДо = await с.locator('#ком-0').evaluate(т => т.offsetHeight);
  await с.locator('#ком-0').click();
  await с.keyboard.type('Колір не мій,\nа крій — так.\nЩе рядок\nі ще\nі ще один\nі сьомий\nі восьмий');
  факти.набір = await стан(0);
  факти.набір.висота = [висотаДо, await с.locator('#ком-0').evaluate(т => т.offsetHeight)];
  assert.equal(факти.набір.модель.коментар, факти.набір.поле); assert.match(факти.набір.поле, /^Колір не мій/);
  assert.equal(факти.набір.рамка, false); assert.ok(факти.набір.висота[1] >= факти.набір.висота[0]);
  if (process.argv[3]) await с.screenshot({path: process.argv[3] + '_набір.png'});

  /* 5. вихід з поля — запис сам; під статусом — «Твій коментар» її словами */
  await с.locator('#к-0 .ряд[data-поле="верд"] .чип[data-код="one_change"]').focus();
  await с.waitForFunction(() => document.querySelector('#ком-запис-0 p'), null, {timeout: 30000});
  факти.після_виходу = await стан(0);
  assert.equal(факти.після_виходу.записаний, факти.набір.поле.trim());
  assert.equal(факти.після_виходу.поле, факти.набір.поле);
  /* модель у стенді не відповідає: коментар записано її словами, а підказка каже, що прочитати його не вдалось */
  факти.підказка = await с.evaluate(() => ({текст: document.getElementById('верд-підказка-0').textContent,
    шаблон: ШАБЛОНИ_ЗБОЮ_П.comment_not_read}));
  assert.equal(факти.підказка.текст, факти.підказка.шаблон);
  await с.locator('#вст-0').scrollIntoViewIfNeeded(); await с.waitForTimeout(300);
  if (process.argv[3]) await с.screenshot({path: process.argv[3] + '_записано.png'});

  /* 6. перемальована картка: поле, вибір і «Твій коментар» — з моделі, слухачі поля живі */
  await с.evaluate(() => рендер());
  факти.після_рендеру = await стан(0);
  assert.equal(факти.після_рендеру.поле, факти.набір.поле); assert.equal(факти.після_рендеру.аспекти_видно, true);
  /* вада 12: перебудоване поле з її словами — на зріст тексту, внутрішньої прокрутки нема */
  факти.поле_після_рендеру = await с.locator('#ком-0').evaluate(т => ({висота: т.clientHeight, тексту: т.scrollHeight}));
  assert.ok(факти.поле_після_рендеру.тексту <= факти.поле_після_рендеру.висота + 2, JSON.stringify(факти.поле_після_рендеру));
  await с.locator('#ком-0').click(); await с.keyboard.press('Control+End'); await с.keyboard.type('!');
  факти.набір_після_рендеру = await с.evaluate(() => В[0].коментар.slice(-9));
  assert.equal(факти.набір_після_рендеру.slice(-1), '!');

  assert.deepEqual(помилки, []);
  console.log(JSON.stringify({факти, помилки}, null, 1)); await б.close();
})().catch(e => { console.error(e); process.exit(1); });
