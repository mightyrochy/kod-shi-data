/* Мірило наряду Екран-паспорт-один-писач: три вади третього живого прогону «як людина» на стенді показу в Chromium.
   №11 — ті самі слова вдруге дають іншу картку (с8 «Де: Офіс» → «Додати», с7 «Зал» → «Театр, вистава»);
   Т3 — «Ошатне» стає «не обрано», поки відкрито аркуш іншого поля (с6, аркуш «Макіяж»);
   15862 — банер «У профілі ще потрібні свої кольори» після застосованих кольорів.
   Паспорти — записані живим прогоном 15.11 (`паспорти_живого_3.json` = `прогони[*].спільне.паспорт` файлів вердиктів
   с6–с8). На екран паспорт лягає тим самим шляхом, що після ходу розмови (`мовний_шар.js`): писач паспорта, потім
   `застосуватиПаспортДоЕкрана`. Писач — `змінитиПаспортП` на голові, присвоєння `ПАСПОРТ_П` на базі (до наряду).
   Хід плиток мовної моделі на стенді не відповідає (міст «у дорозі»), як і за відкритого аркуша в живому прогоні.
   Сторінка — зі шаблону без Python, як `аудит/проби/Екран-наново/мірило/вади_сценарій.js`; Chromium 390×844 з дотиком.
   Запуск: NODE_PATH=джерела/node_modules node вади.js <тека джерела дерева> <префікс> */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [дж, префікс] = process.argv.slice(2);
const БАЗА = 'http://127.0.0.1:8765';
const П = JSON.parse(fs.readFileSync(path.join(__dirname, 'паспорти_живого_3.json'), 'utf8'));
(async () => {
  const б = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM || undefined});
  const к = await б.newContext({viewport: {width: 390, height: 844}, hasTouch: true});
  const с = await к.newPage();
  const помилки = [], факти = {};
  с.on('pageerror', e => помилки.push(String(e).slice(0, 300)));
  const {прочитатиДовідникJSON, підставитиШаблон, зібратиШаблонПоказу} = require(path.join(дж, 'показ_шаблон.js'));
  const html = підставитиШаблон(зібратиШаблонПоказу(path.join(дж, 'показ.html')), {__МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'показ-тест',
    __ВІДБИТОК__: 'abc', __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'каталог_стенд.xml · 639 речей', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(дж)})
    .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"\n]*"[^>]*><\/script>/, '<script>window.loadPyodide=null;</script>');
  await к.route('**/*', r => { const у = new URL(r.request().url());
    if (у.pathname === '/build.txt') return r.fulfill({contentType: 'text/plain', body: 'показ-тест\n'});
    return у.origin === БАЗА && у.pathname === '/' ? r.fulfill({contentType: 'text/html', body: html}) : r.abort(); });
  const знімок = ім => с.screenshot({path: префікс + '_' + ім + '.png'});
  const тихо = мс => с.waitForTimeout(мс || 400);
  await с.goto(БАЗА + '/', {waitUntil: 'commit', timeout: 120000});
  await с.waitForFunction(() => { const д = document.getElementById('н-далі'); return д && д.getBoundingClientRect().height > 0
    && (typeof Екран === 'undefined' || !Екран.стан || !('запущено' in Екран.стан) || Екран.стан.запущено); }, null, {timeout: 180000});
  await тихо(1500);
  /* міст «у дорозі»: хід плиток після дотику не відповідає, як за відкритого аркуша в живому прогоні */
  await с.evaluate(() => { містП = () => new Promise(() => {}); });
  const стан = () => с.evaluate(() => ({паспорт: JSON.stringify(ПАСПОРТ_П),
    журнал: typeof журналПаспортаП === 'function' ? журналПаспортаП() : null, змінено: ВИПАДОК_ЗМІНЕНО_П}));
  const новий = async () => { await с.evaluate(() => { застосуватиСценарій({}); режим('сценарій'); }); await тихо(600); };
  const покласти = async п => { await с.evaluate(п => {
      if (typeof змінитиПаспортП === 'function') змінитиПаспортП('проба', 'замінити', п); else ПАСПОРТ_П = п;
      ВИПАДОК_ЗМІНЕНО_П = false; застосуватиПаспортДоЕкрана(ПАСПОРТ_П); показатиМежі(); }, JSON.parse(JSON.stringify(п)));
    await тихо(1000); };
  const рядки = () => с.evaluate(() => Object.fromEntries([...document.querySelectorAll('#е-випадок button.ряд-паспорта')]
    .filter(р => !р.hidden && р.getBoundingClientRect().height > 0)
    .map(р => [(р.querySelector('span') || {}).textContent, ((р.querySelector('b') || {}).textContent || '').replace(/\s+/g, ' ').trim()])));
  /* №11: той самий паспорт двічі — та сама картка; паспорти двох проходів (ті самі слова) — різні картки */
  for (const сц of ['с8', 'с7']){
    const ф = факти['№11_' + сц] = {};
    for (const [ім, і] of [['прохід1', 0], ['прохід2', 1], ['прохід1_вдруге', 0]]){
      await новий(); await покласти(П[сц][і]);
      ф[ім] = {картка: await рядки(), місце: П[сц][і].місце ?? null, місце_слова: П[сц][і].місце_слова ?? null};
      /* картка сценарію цілою (рядки «Нагода», «Де»…), а не верх сторінки: знімок на scroll=0 рядків не показував */
      await с.evaluate(() => { const р = document.querySelector('#е-випадок button.ряд-паспорта:not([hidden])');
        if (р) р.scrollIntoView({block: 'start'}); window.scrollBy(0, -16); });
      await тихо(300); await знімок('11_' + сц + '_' + ім);
    }
    ф.той_самий_паспорт_та_сама_картка = JSON.stringify(ф.прохід1.картка) === JSON.stringify(ф.прохід1_вдруге.картка);
    ф.картки_проходів_різні = JSON.stringify(ф.прохід1.картка) !== JSON.stringify(ф.прохід2.картка);
  }
  /* Т3: с6, прохід 1 — «Ошатність» до аркуша, аркуш «Макіяж» відкрито й обрано «хай обере стилістка», після «Готово» */
  {
    const ф = факти.Т3 = {};
    await новий(); await покласти(П.с6[0]);
    ф.до = (await рядки()).Ошатність; const с0 = await стан();
    if (await с.locator('#сц-ще').isVisible()){ await с.locator('#сц-ще').tap(); await тихо(600); }
    await с.locator('button.ряд-паспорта[data-редактор="ред-макіяж"]').scrollIntoViewIfNeeded();
    await с.locator('button.ряд-паспорта[data-редактор="ред-макіяж"]').tap(); await тихо(900);
    const плитка = с.locator('#ред-макіяж button:visible', {hasText: 'хай обере стилістка'}).first();
    ф.плитка_є = await плитка.count() > 0;
    if (ф.плитка_є){ await плитка.tap(); await тихо(900); }
    ф.з_відкритим_аркушем = (await рядки()).Ошатність; await знімок('Т3_аркуш_макіяж');
    const с1 = await стан();
    if (await с.locator('#аркуш-готово').isVisible()){ await с.locator('#аркуш-готово').tap(); await тихо(900); }
    ф.після_готово = (await рядки()).Ошатність; await знімок('Т3_після_готово');
    ф.паспорт_не_змінено = с0.паспорт === с1.паспорт;
    ф.змінено_після_дотику = с1.змінено;
    ф.записів_журналу = с0.журнал ? [с0.журнал.length, с1.журнал.length] : 'журналу нема (база)';
  }
  /* 15862: банер на сценарії, потім кольори застосовано (стан, який лишає `застосуватиКольори`), повернення на сценарій */
  {
    const ф = факти['15862'] = {};
    await новий(); await покласти(П.с6[0]);
    const банер = () => с.evaluate(() => { const е = document.getElementById('сц-увага');
      return е && !е.hidden && е.getBoundingClientRect().height > 0 ? е.textContent.replace(/\s+/g, ' ').trim() : ''; });
    await с.evaluate(() => { КОЛІР = {шкіра:null, волосся:null, очі:null, кільце:null, точки:null}; показатиСценарій(); });
    await тихо(600); ф.без_кольорів = await банер(); const с0 = await стан();
    await с.evaluate(() => { режим('профіль'); }); await тихо(600);
    await с.evaluate(() => { КОЛІР = Object.assign({}, КОЛІР, {шкіра: '#f2d6c4', волосся: '#4a4644', очі: '#6b8cae'}); показатиПрофіль(); });
    await тихо(600);
    await с.evaluate(() => { режим('сценарій'); }); await тихо(900);
    ф.після_кольорів = await банер(); ф.чого_бракує = await с.evaluate(() => чогоБракує());
    await с.locator('#сц-увага').scrollIntoViewIfNeeded().catch(() => {}); await знімок('15862_після_кольорів');
    const с1 = await стан();
    ф.паспорт_не_змінено = с0.паспорт === с1.паспорт;
    await с.evaluate(() => показатиСценарій()); await тихо(600);
    ф.після_перемальовки_картки = await банер();
  }
  факти.помилки = помилки;
  fs.writeFileSync(префікс + '_факти.json', JSON.stringify(факти, null, 1));
  console.log(JSON.stringify(факти));
  await б.close();
})().catch(e => { console.error('ЗБІЙ ПРОБИ', e); process.exit(1); });
