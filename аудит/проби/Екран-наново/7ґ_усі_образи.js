/* Жива рука 7ґ у Chromium 390×844: «Усі образи» (плитки за нагодою, вердикт на плитці), журнал вердиктів, вибір
   вивантаження (день → прогін → образ), «Зберегти позначене файлом», «Зберегти всі», копія в буфер, відкриття плитки.
   Лише дотики й читання DOM — той самий скрипт іде на коді ДО і ПІСЛЯ; сховище — справжній IndexedDB сторінки.
   Запуск: NODE_PATH=джерела/node_modules node 7ґ_усі_образи.js <тека джерела> [префікс знімків]. Факти — JSON. */
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
  await с.evaluate(async () => {
    const реч = н => [{id: 'ж-' + н + '@g.com', назва: 'Сукня ' + н, ціна: 3000, слот: 'сукня', фото: null},
                      {id: 'п-' + н + '@g.com', назва: 'Пасок ' + н, ціна: 500, слот: 'пояс', фото: null}];
    const к = (рука, поз) => ({рука, ітерацій: 1, викликів: 1, текст: 'образ ' + рука, опис: 'образ ' + рука, підпис: 'образ ' + рука,
      речі: реч(рука), мітки: [], знахідки: [], питання: [], етапи: {викликів: 1, виклики: []}, свідомі: [], невиконано: null,
      різноманітність: null, мова: [], мова_спроб: 0, мова_видано: 'так', фото_не_ті: [], дібрав_код_слоти: [],
      збирання: {сід: 7, ключ: '2143', позиція: поз, рука}});
    П = {в: 'ПОКАЗ-V1', збірка: 'тест-7ґ', каталог: 'каталог_стенд.xml · 639 речей', профіль: 'Оля', розклад: '2143',
         випадок_рядок: 'Робота · офіс · сніг',
         випадок_шматки: [{ключ: 'нагода', текст: 'Робота'}, {ключ: 'місце', текст: 'офіс'}],
         пул: 100, прогін: 'прогін-7ґ', картки: ['2', '1', '4', '3'].map(к)};
    рендер();
    await new Promise(р => setTimeout(р, 400));
    const d = await дб();
    const зап = (поз, день, верд, ком) => ({прогін: 'прогін-7ґ', збірка: 'тест-7ґ', розклад: '2143', профіль: 'Оля', позиція: поз,
      рука: String(поз), час: день + 'T10:0' + поз + ':00.000Z', вердикт_людини: верд, коментар: ком});
    for (const з of [зап(1, '2026-11-12', 'так', 'гарно сидить'), зап(2, '2026-11-12', 'ні', 'закоротке'), зап(3, '2026-11-13', 'так', '')])
      await tx(d, 'вердикти', 'readwrite', s => s.add(з));
    window.__файли = []; window.__буфер = [];
    URL.createObjectURL = б => { window.__файли.push(б); return 'blob:т'; }; URL.revokeObjectURL = () => {};
    Object.defineProperty(navigator, 'clipboard', {value: {writeText: async т => { window.__буфер.push(т); }}, configurable: true});
  });
  const assert = require('assert').strict, факти = {};
  /* ім'я файла несе випадковий ід пристрою й час — у фактах лишається форма */
  const числа = т => String(т || '').replace(/\s+/g, ' ').trim().replace(/[0-9]+/g, '#').replace(/verdykty-[a-z#]+/g, 'verdykty-<пристрій>');
  const рівний = т => String(т || '').replace(/\s+/g, ' ').trim();
  const знімок = async (назва, вузол) => { if (process.argv[3]){ if (вузол) await с.locator(вузол).scrollIntoViewIfNeeded(); await с.waitForTimeout(250);
    await с.screenshot({path: process.argv[3] + '_' + назва + '.png'}); } };
  const вибір = () => с.evaluate(() => ({
    днів: document.querySelectorAll('#жв-список .жв-день').length, прогонів: document.querySelectorAll('#жв-список .жв-прогін').length,
    образів: document.querySelectorAll('#жв-список .жв-образ').length,
    птахи: [...document.querySelectorAll('#жв-список input[type=checkbox]')].map(x => (x.checked ? 'так' : 'ні') + (x.indeterminate ? '~' : '')),
    текст: document.getElementById('жв-список').textContent.replace(/\s+/g, ' ').trim().replace(/останнє [0-9-]+ [0-9:]+/g, 'останнє <час>'),
    кнопка: document.getElementById('жв-файл').textContent.replace(/\s+/g, ' ').trim(), мовчить: document.getElementById('жв-файл').disabled}));
  const птах = н => с.locator('#жв-список input[type=checkbox]').nth(н);

  /* 1. «Усі образи»: чотири плитки під нагодою, вердикт останнього запису на плитці, журнал під ними */
  await с.locator('#до-бібліотеки').scrollIntoViewIfNeeded(); await с.locator('#до-бібліотеки').click();
  await с.waitForFunction(() => document.querySelectorAll('#біб-список .біб-образ').length === 4);
  await с.waitForFunction(() => /3/.test(document.getElementById('ж-ліч').textContent));
  факти.бібліотека = await с.evaluate(() => ({режим: Екран.стан.режим,
    заголовки: [...document.querySelectorAll('#біб-список h3, #біб-список h4, #біб-список .біб-нагода')].map(x => x.textContent.replace(/\s+/g, ' ').trim()),
    плитки: [...document.querySelectorAll('#біб-список .біб-образ')].map(x => x.textContent.replace(/\s+/g, ' ').trim()),
    стан: document.getElementById('біб-стан').textContent, лічба: document.getElementById('ж-ліч').textContent,
    журнал: document.getElementById('ж-список').textContent.replace(/\s+/g, ' ').trim()}));
  assert.equal(факти.бібліотека.плитки.length, 4); await знімок('бібліотека', '#біб-список');

  /* 2. вибір вивантаження: день → прогін → образ, типово позначено не вивантажене */
  await с.evaluate(() => { document.getElementById('журнал').open = true; });
  await с.locator('#ж-вибір summary').scrollIntoViewIfNeeded(); await с.locator('#ж-вибір summary').click();
  await с.waitForFunction(() => document.querySelectorAll('#жв-список .жв-образ').length === 3);
  факти.вибір = await вибір(); await знімок('вибір', '#жв-файл');
  assert.equal(факти.вибір.днів, 2); assert.equal(факти.вибір.образів, 3);

  /* 3. три кнопки й прапорці: зняти всі, позначити всі, один образ, цілий день */
  await с.locator('#жв-жодного').click(); факти.жодного = await вибір();
  assert.equal(факти.жодного.мовчить, true);
  await с.locator('#жв-всі').click(); факти.всі = await вибір();
  const образи = await с.evaluate(() => [...document.querySelectorAll('#жв-список input[type=checkbox]')]
    .map((x, i) => x.closest('.жв-образ') && !x.closest('.жв-образ').querySelector('.жв-образ') ? i : -1).filter(i => i >= 0));
  await птах(образи[образи.length - 1]).click(); факти.без_одного = await вибір(); await знімок('без_одного', '#жв-файл');
  await птах(0).click(); факти.день = await вибір();
  await птах(0).click(); факти.день_назад = await вибір();

  /* 4. «Зберегти позначене файлом»: у файлі рівно позначене, вивантажене дістає позначку */
  await с.locator('#жв-всі').click(); await птах(образи[образи.length - 1]).click();
  await с.locator('#жв-файл').click();
  await с.waitForFunction(() => window.__файли.length === 1 && document.getElementById('ж-стан').textContent.trim());
  await с.waitForTimeout(300);
  факти.позначене = {файл: await с.evaluate(async () => { const ф = JSON.parse(await window.__файли[0].text());
      return {вердиктів: ф.вердиктів, ключі: Object.keys(ф).sort(), позиції: (ф.вердикти || []).map(в => в.позиція)}; }),
    стан: числа(await с.locator('#ж-стан').textContent()), вибір: await вибір()};
  assert.equal(факти.позначене.файл.вердиктів, 2);
  await с.locator('#жв-нові').click(); факти.нові = await вибір();

  /* 5. «Зберегти всі вердикти файлом» і копія в буфер */
  await с.locator('#ж-файл').scrollIntoViewIfNeeded(); await с.locator('#ж-файл').click();
  await с.waitForFunction(() => window.__файли.length === 2); await с.waitForTimeout(300);
  факти.усі = {вердиктів: await с.evaluate(async () => JSON.parse(await window.__файли[1].text()).вердиктів),
    стан: числа(await с.locator('#ж-стан').textContent()), вибір: await вибір()};
  assert.equal(факти.усі.вердиктів, 3);
  await с.locator('#ж-копія').click();
  await с.waitForFunction(() => window.__буфер.length === 1); await с.waitForTimeout(200);
  факти.копія = {рядків: await с.evaluate(() => window.__буфер[0].split('\n').length),
    шапка: await с.evaluate(() => window.__буфер[0].split('\n')[0].replace(/пристрій=\S+/, 'пристрій=<ід>').replace(/дата=\S+/, 'дата=<час>')), стан: рівний(await с.locator('#ж-стан').textContent())};

  /* 6. дотик плитки: прогін запису стає показом на її картці, вердикти прогону підхоплено */
  await с.locator('#біб-список .біб-образ').nth(1).scrollIntoViewIfNeeded(); await с.locator('#біб-список .біб-образ').nth(1).click();
  await с.waitForFunction(() => Екран.стан.режим === 'образи'); await с.waitForTimeout(400);
  факти.відкрито = await с.evaluate(() => ({режим: Екран.стан.режим, поз: Number(Екран.стан.образ.поз), прогін: П.прогін, карток: П.картки.length,
    випадок: П.випадок_рядок, оцінені: [0, 1, 2, 3].map(i => !!(В[i] && (В[i].запис_ключ != null || В[i].верд))),
    пейджер: (document.getElementById('пейджер') || {textContent: ''}).textContent.replace(/\s+/g, ' ').trim()}));
  assert.equal(факти.відкрито.поз, 1); await знімок('відкрито');

  факти.помилки_сторінки = помилки;
  assert.deepEqual(помилки, []);
  console.log(JSON.stringify(факти, null, 1));
  await б.close();
})().catch(e => { console.error(e); process.exit(1); });
