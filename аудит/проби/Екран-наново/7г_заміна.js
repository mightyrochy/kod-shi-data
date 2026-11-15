/* Жива рука 7г у Chromium 390×844: заміна речі на картці — дотик «замінити» (позначка, кнопки мовчать), «заміни нема»,
   скасування іншим режимом, відмова, вдала заміна, «Повернути всі», відхилення з коментаря. Міст — заглушка проби.
   Запуск: NODE_PATH=джерела/node_modules node 7г_заміна.js <тека джерела> [префікс знімків]. Факти — JSON. */
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
  await с.evaluate(() => {
    window.__черга = []; window.__відповідь = null; window.__показ = null;
    window.__пустити = () => { const з = window.__черга.shift(); if (з) з(); return !!з; };
    window.зберегтиОбраз = async () => {};
    П.знімок = {вхід: {}}; вхідМостаП = () => ({}); мовоюКарткуП = async () => {};
    містП = async що => {
      if (що === 'від_моделі') return new Promise(так => window.__черга.push(() => так({заміна: window.__відповідь})));
      if (що === 'показ') return window.__показ;
      return null; };
  });
  const стан = () => с.evaluate(() => { const к = document.getElementById('к-0'), кн = [...к.querySelectorAll('button.замін')];
    return {написи: кн.map(x => x.textContent), натиснуті: кн.map(x => x.getAttribute('aria-pressed')), мовчать: кн.map(x => x.disabled),
      позначених_рядків: к.querySelectorAll('.річ.замінити').length, під_переліком: {схований: к.querySelector('.не-ця-рядок').hidden,
        текст: к.querySelector('.не-ця-рядок').textContent}, нема: [...к.querySelectorAll('.заміни-нема')].map(x => x.textContent),
      речі: П.картки[0].речі.map(р => р.id), набір: НЕ_ЦЯ_П.знімок(), у_дорозі: ЗАМІНИ_П.has(П.картки[0]),
      відповідь: В[0] ? В[0].замінити : null}; });
  const дотик = async н => { await с.locator('#к-0 button.замін').nth(н).scrollIntoViewIfNeeded(); await с.locator('#к-0 button.замін').nth(н).click();
    await с.waitForFunction(() => window.__черга.length === 1); };
  const кінець = () => с.waitForFunction(() => !ЗАМІНИ_П.has(П.картки[0]) && [...document.querySelectorAll('#к-0 button.замін')].every(к => !к.disabled));
  const знімок = async назва => { if (process.argv[3]){ await с.locator('#к-0 .список').scrollIntoViewIfNeeded(); await с.waitForTimeout(250);
    await с.screenshot({path: process.argv[3] + '_' + назва + '.png'}); } };
  факти.старт = await стан();
  assert.deepEqual(факти.старт.написи, ['замінити', 'замінити']); assert.equal(факти.старт.під_переліком.текст, '');

  /* 1. дотик: річ позначено, кнопки мовчать, рядок під переліком схований — поки міст думає */
  await дотик(0);
  факти.у_дорозі = await стан(); await знімок('у_дорозі');
  assert.deepEqual(факти.у_дорозі.написи, ['на заміну', 'замінити']); assert.deepEqual(факти.у_дорозі.натиснуті, ['true', 'false']);
  assert.deepEqual(факти.у_дорозі.мовчать, [true, true]); assert.equal(факти.у_дорозі.позначених_рядків, 1);
  assert.equal(факти.у_дорозі.під_переліком.схований, true); assert.deepEqual(факти.у_дорозі.набір, {2: ['ж-2@g.com']});

  /* 2. міст: заміни нема — позначку знято, біля речі речення, кнопки живі */
  await с.evaluate(() => { window.__відповідь = {готово: true, річ: null, чому: 'кандидатів нема'}; window.__пустити(); });
  await с.waitForFunction(() => document.querySelector('#к-0 .заміни-нема')); await кінець();
  факти.заміни_нема = await стан(); await знімок('заміни_нема');
  assert.deepEqual(факти.заміни_нема.написи, ['замінити', 'замінити']); assert.equal(факти.заміни_нема.нема.length, 1);
  assert.ok(факти.заміни_нема.нема[0].length > 0); assert.deepEqual(факти.заміни_нема.набір, {});
  assert.equal(факти.заміни_нема.під_переліком.схований, false); assert.equal(факти.заміни_нема.позначених_рядків, 0);

  /* 3. дотик удруге прибирає речення; інший режим скасовує заміну — картка як до дотику, з реченням */
  await дотик(0);
  факти.другий_дотик_нема = (await стан()).нема.length;
  assert.equal(факти.другий_дотик_нема, 0);
  await с.evaluate(() => режим('профіль'));
  await с.waitForFunction(() => !ЗАМІНИ_П.has(П.картки[0]));
  await с.evaluate(() => { window.__відповідь = {готово: true, річ: null}; window.__пустити(); режим('образи'); });
  await кінець();
  факти.скасовано = await стан();
  assert.deepEqual({...факти.скасовано, відповідь: null}, {...факти.заміни_нема, відповідь: null});

  /* 4. міст мовчить — відмова: речення під переліком, позначка лишається, кнопки живі */
  await дотик(0);
  await с.evaluate(() => { window.__відповідь = null; window.__пустити(); });
  await кінець();
  факти.відмова = await стан(); await знімок('відмова');
  assert.deepEqual(факти.відмова.написи, ['на заміну', 'замінити']); assert.equal(факти.відмова.під_переліком.схований, false);
  assert.ok(факти.відмова.під_переліком.текст.length > 0); assert.deepEqual(факти.відмова.набір, {2: ['ж-2@g.com']});
  факти.етап_відмови = await с.evaluate(() => П.картки[0].етапи.заміни.at(-1).помилка);
  assert.equal(факти.етап_відмови, 'replacement_bridge_no_result');

  /* 5. вдала заміна: нова річ на місці старої, сторінка не стрибає, стара лишилась відхиленою */
  const прокруткаДо = await с.evaluate(() => { const нова = {id: 'н-1@g.com', назва: 'Сукня-футляр', ціна: 2800, слот: 'сукня', фото: null};
    window.__відповідь = {готово: true, річ: нова, ід: ['н-1@g.com', 'п-2@g.com'], вердикт: {знахідки: []}};
    window.__показ = [нова, П.картки[0].речі[1]]; return 0; });
  await дотик(0);
  const yДо = await с.evaluate(() => scrollY);
  await с.evaluate(() => window.__пустити());
  await с.waitForFunction(() => П.картки[0].речі[0].id === 'н-1@g.com'); await кінець();
  факти.замінено = await стан(); факти.замінено.прокрутка = [yДо, await с.evaluate(() => scrollY)]; await знімок('замінено');
  assert.deepEqual(факти.замінено.речі, ['н-1@g.com', 'п-2@g.com']); assert.deepEqual(факти.замінено.написи, ['замінити', 'замінити']);
  assert.deepEqual(факти.замінено.набір, {2: ['ж-2@g.com']}); assert.equal(факти.замінено.прокрутка[0], факти.замінено.прокрутка[1]);
  факти.назва_нової = await с.locator('#к-0 .список .річ').first().textContent();
  assert.match(факти.назва_нової, /Сукня-футляр/);

  /* 6. відхилення з коментаря — та сама позначка; «Повернути всі» знімає все */
  await с.evaluate(() => позначитиНеЦюП('п-2@g.com', 0));
  факти.з_коментаря = await стан();
  assert.deepEqual(факти.з_коментаря.написи, ['замінити', 'на заміну']); assert.equal(факти.з_коментаря.позначених_рядків, 1);
  await с.locator('#обр-не-ця-повернути').click();
  факти.повернуто = await стан();
  assert.deepEqual(факти.повернуто.набір, {}); assert.deepEqual(факти.повернуто.написи, ['замінити', 'замінити']);
  assert.equal(факти.повернуто.позначених_рядків, 0);

  assert.deepEqual(помилки, []);
  console.log(JSON.stringify({факти, помилки}, null, 1)); await б.close();
})().catch(e => { console.error(e); process.exit(1); });
