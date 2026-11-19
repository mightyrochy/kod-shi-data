/* Мірило кроку 15420 наряду Прогін-картка-сценарію: рядки картки сценарію на шляху БЕЗ розмови.
   Випадки: дотик до кожної плитки нагоди (аркуш «Нагода» → плитка → «Готово») і річ з фото без слів — паспорт, який
   ставить Python (`паспорт_нагоди._типова_нагода`), лягає входом після розмови (`застосуватиПаспортДоЕкрана`).
   Сторінка — зі шаблону дерева без Python у браузері, як `картка.js` поруч; кожен випадок — свіжа сторінка.
   Рядок «не її мовою» — значення рядка картки з висновком коду замість її слова: «типово/типове …», «для речі з фото».
   Для речі з фото — ще й дотик: рядок «Нагода» → плитка «Робота» → «Готово» (`після_дотику`).
   Друкує JSON: рядки картки, напис порожнього пункту списку «Місце», рядок «Візьмемо» і лічбу; останній рядок —
   «рядків не її мовою: N».
   Запуск: CHROMIUM=/opt/pw-browsers/chromium node без_розмови.js <тека джерела дерева> <вихід.json> */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const [дж, вихід] = process.argv.slice(2);
const БАЗА = 'http://127.0.0.1:8765';
const НЕ_ЇЇ = /типов|для речі з фото|для нагоди/i;
/* паспорт речі з фото без слів — тим самим кодом, що на живому шляху (тека дерева, а не цієї гілки) */
const пасФото = Object.assign({вето: {типи: [], тканини: [], принти: [], кольори: [], зони: []}, речі_з_фото: [{тип: 'спідниця'}]},
  JSON.parse(execFileSync('python3', ['-c', 'import json, паспорт_нагоди as п; print(json.dumps(п._типова_нагода({}), ensure_ascii=False))'],
    {cwd: дж, encoding: 'utf8'}).trim().split('\n').pop()));
(async () => {
  const {прочитатиДовідникJSON, підставитиШаблон, зібратиШаблонПоказу} = require(path.join(дж, 'показ_шаблон.js'));
  const довідник = прочитатиДовідникJSON(дж);
  const html = підставитиШаблон(зібратиШаблонПоказу(path.join(дж, 'показ.html')), {__МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'показ-тест',
    __ВІДБИТОК__: 'abc', __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'каталог_стенд.xml · 639 речей', __ДОВІДНИК_ПОКАЗУ__: довідник})
    .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"\n]*"[^>]*><\/script>/, '<script>window.loadPyodide=null;</script>');
  const плитки = JSON.parse(довідник).нагоди.filter(о => о.плитка).map(о => о.ключ);
  const випадки = плитки.map(к => ({випадок: 'плитка ' + к, плитка: к})).concat([{випадок: 'річ з фото без слів', паспорт: пасФото}]);
  const б = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM || undefined});
  const вих = [];
  for (const в of випадки){
    const к = await б.newContext({viewport: {width: 390, height: 844}, hasTouch: true});
    const с = await к.newPage();
    const помилки = [];
    с.on('pageerror', e => помилки.push(String(e).slice(0, 200)));
    await к.route('**/*', r => { const у = new URL(r.request().url());
      if (у.pathname === '/build.txt') return r.fulfill({contentType: 'text/plain', body: 'показ-тест\n'});
      return у.origin === БАЗА && у.pathname === '/' ? r.fulfill({contentType: 'text/html', body: html}) : r.abort(); });
    await с.goto(БАЗА + '/', {waitUntil: 'commit', timeout: 120000});
    await с.waitForFunction(() => { const д = document.getElementById('н-далі'); return д && д.getBoundingClientRect().height > 0
      && (typeof Екран === 'undefined' || !Екран.стан || !('запущено' in Екран.стан) || Екран.стан.запущено); }, null, {timeout: 180000});
    await с.waitForTimeout(800);
    await с.evaluate(() => { режим('сценарій'); if (typeof показатиСценарій === 'function') показатиСценарій(); });
    await с.waitForTimeout(400);
    if (в.плитка){
      /* її дотики: рядок «Нагода» відкриває аркуш, плитка, «Готово» */
      await с.evaluate(() => { const р = document.querySelector('button.ряд-паспорта[data-редактор="ред-нагода"]'); р.hidden = false; р.click(); });
      await с.waitForTimeout(300);
      await с.locator('#сц-нагода-плитки .плитка[data-ключ="' + в.плитка + '"]').click();
      await с.waitForTimeout(300);
      await с.evaluate(() => { const г = document.getElementById('аркуш-готово'); if (г && !document.getElementById('аркуш').hidden) г.click(); });
    } else await с.evaluate(пс => { ПАСПОРТ_П = пс; ВИПАДОК_ЗМІНЕНО_П = false; застосуватиПаспортДоЕкрана(ПАСПОРТ_П);
      if (typeof показатиСценарій === 'function') показатиСценарій(); }, в.паспорт);
    await с.waitForTimeout(800);
    const ф = await с.evaluate(() => {
      const картка = [...document.querySelectorAll('#сц-картка button.ряд-паспорта')].filter(р => !р.hidden && !р.closest('.редактор'))
        .map(р => [(р.querySelector('span') || {}).textContent, ((р.querySelector('b') || {}).textContent || '').replace(/\s+/g, ' ').trim()]);
      const м = document.getElementById('сц-місце'), д = document.getElementById('сц-діапазон');
      return {картка, місце_порожній_пункт: м && м.options[0] ? м.options[0].textContent : null, візьмемо: д ? д.textContent : null,
              нагода_поле: полеВипадкуП('сц-нагода'),
              /* поза кроком: шапка над картками образів (`випадокШматками`, `голос_помада.js`) — ЗНАХІДКА 15431 */
              шапка_образів: (() => { try { return випадокШматками().map(ш => ш.текст); } catch (e) { return String(e).slice(0, 80); } })()};
    });
    const не_її = ф.картка.filter(([н, з]) => н !== 'Твої слова' && НЕ_ЇЇ.test(з));
    /* річ з фото: нагоду, яку поставив код, вона змінює дотиком — рядок «Нагода» → плитка «Робота» → «Готово» */
    if (в.паспорт){
      await с.evaluate(() => document.querySelector('button.ряд-паспорта[data-редактор="ред-нагода"]').click());
      await с.waitForTimeout(300);
      await с.locator('#сц-нагода-плитки .плитка[data-ключ="робота"]').click();
      await с.waitForTimeout(300);
      await с.evaluate(() => { const г = document.getElementById('аркуш-готово'); if (г && !document.getElementById('аркуш').hidden) г.click(); });
      await с.waitForTimeout(500);
      ф.після_дотику = await с.evaluate(() => { const е = document.getElementById('зн-нагода');
        return {нагода: е.textContent, сірим: е.classList.contains('типово'), поле: полеВипадкуП('сц-нагода')}; });
    }
    вих.push(Object.assign({випадок: в.випадок}, ф, {не_її, помилки}));
    await к.close();
  }
  await б.close();
  fs.writeFileSync(вихід, JSON.stringify(вих, null, 1));
  for (const в of вих) console.log(в.випадок, JSON.stringify(в.картка), '| Місце:', в.місце_порожній_пункт, '|', в.візьмемо,
                                   в.помилки.length ? 'ПОМИЛКИ ' + в.помилки.length : '',
                                   в.після_дотику ? 'після дотику: ' + JSON.stringify(в.після_дотику) : '');
  console.log('рядків не її мовою: ' + вих.reduce((с, в) => с + в.не_її.length, 0));
})();
