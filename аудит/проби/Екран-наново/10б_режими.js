/* Chromium 390×844, частина 10б: вхід у кожен режим і на кожен крок знайомства, вкладки дотиком, аркуш, що
   знімається входом у режим, і те, що логіка читає про режим (`станДляШі`) — ті самі дії ДО й ПІСЛЯ.
   Нічого не підмінено. Очікувана різниця одна: голих імен `РЕЖИМ` / `ЕКРАН` / `АРКУШ` ПІСЛЯ нема.
   Запуск: NODE_PATH=джерела/node_modules node цей_файл <джерела> <префікс знімків і фактів>. */
const path = require('path'), fs = require('fs');
const {chromium} = require('playwright');
const дж = path.resolve(process.argv[2]), пр = process.argv[3];
const {прочитатиДовідникJSON, підставитиШаблон, зібратиШаблонПоказу} = require(path.join(дж, 'показ_шаблон.js'));
(async () => {
  const html = підставитиШаблон(зібратиШаблонПоказу(path.join(дж, 'показ.html')), {
    __МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'показ-тест', __ВІДБИТОК__: 'abc',
    __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'каталог_стенд.xml · 639 речей',
    __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(дж)})
    .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"\n]*"[^>]*><\/script>/, '<script>window.loadPyodide=null;</script>');
  const б = await chromium.launch();
  try {
    const помилки = [], факти = {};
    const сторінка = async підготувати => {
      const к = await б.newContext({viewport: {width: 390, height: 844}, hasTouch: true});
      const с = await к.newPage();
      с.on('pageerror', e => помилки.push(String(e)));
      if (підготувати) await с.addInitScript(підготувати);
      await с.route('**/*', r => { const у = new URL(r.request().url());
        if (у.pathname === '/build.txt') return r.fulfill({contentType: 'text/plain', body: 'показ-тест\n'});
        return у.pathname === '/' ? r.fulfill({contentType: 'text/html', body: html}) : r.abort(); });
      return с;
    };
    const запущено = с => с.waitForFunction(() => Екран.стан.запущено && Екран.стан.вхід > 0, null, {timeout: 60000});
    const зріз = с => с.evaluate(() => {
      const видно = в => !!в && getComputedStyle(в).display !== 'none' && !в.hidden;
      const п = document.getElementById('ші-панель'), ш = станДляШі();
      return {режим: Екран.стан.режим, крок: Екран.стан.крок, аркуш: !!Екран.стан.аркуш,
        екрани: [...document.querySelectorAll('[id^="е-"]')].filter(видно).map(е => е.id),
        панель: {видно: видно(п), клас: п.className, батько: п.parentNode.id || п.parentNode.tagName,
          поле: (document.getElementById('чат-поле') || {}).placeholder || '', стрічка: document.getElementById('чат-стрічка').children.length,
          вкладень: document.getElementById('чат-вкладення').children.length},
        розгорнуто: !!Екран.стан.розгорнуто, для_ші: {екран: ш.екран, крок: ш.крок},
        бібліотека: БІБЛІОТЕКА_П.стан, текст_бібліотеки: (document.getElementById('е-бібліотека') || {textContent: ''}).textContent.replace(/\s+/g, ' ').trim().slice(0, 160),
        вкладка: [...document.querySelectorAll('[id^="вк-"]')].filter(в => в.getAttribute('aria-current') || в.classList.contains('тут')).map(в => в.id),
        дії_знайомства: getComputedStyle(document.getElementById('ніг-дії')).display, далі: document.getElementById('н-далі-текст').textContent,
        вгорі: window.scrollY};
    });
    const тихо = с => с.waitForTimeout(250);

    /* 1. знайомство: три кроки вперед і назад — панель розмови й картка показують себе на кожен крок */
    const с = await сторінка();
    await с.goto('http://stend.test/'); await запущено(с);
    факти.старт = await зріз(с);
    await с.locator('#н-далі').tap(); await тихо(с); факти.крок_1 = await зріз(с);
    await с.locator('#н-далі').tap(); await тихо(с); факти.крок_2 = await зріз(с);
    await с.locator('#н-назад').tap(); await тихо(с); факти.назад_на_1 = await зріз(с);
    /* 2. кожен режим входом логіки `режим(р)` — те, що наповнює себе на вхід */
    for (const р of ['сценарій', 'профіль', 'сценарії', 'оцінка', 'бібліотека', 'образи', 'палітра', 'старт', 'сценарій']){
      await с.evaluate(р => { window.scrollTo(0, 400); режим(р); }, р);
      await с.waitForFunction(() => БІБЛІОТЕКА_П.стан !== 'читається', null, {timeout: 20000});
      await тихо(с); факти['режим_' + р + (факти['режим_' + р] ? '_вдруге' : '')] = await зріз(с);
      if (пр && (р === 'бібліотека' || р === 'профіль')) await с.screenshot({path: пр + '_' + р + '.png'});
    }
    /* 3. вкладки дотиком; розгорнута панель згортається на виході зі сценарію, вкладене фото скидається */
    await с.evaluate(() => { розгорнутиРозмову(); });
    await тихо(с); факти.розгорнуто = await зріз(с);
    for (const в of ['вк-образи', 'вк-оцінка', 'вк-сценарій']){
      await с.locator('#' + в).tap(); await тихо(с);
      await с.waitForFunction(() => БІБЛІОТЕКА_П.стан !== 'читається', null, {timeout: 20000});
      факти['дотик_' + в] = await зріз(с);
    }
    /* 4. аркуш знімається входом у режим */
    await с.evaluate(() => { режим('профіль'); відкритиПрофіль('кол-блок'); });
    await тихо(с); факти.аркуш = await зріз(с);
    await с.evaluate(() => режим('сценарій')); await тихо(с); факти.після_аркуша = await зріз(с);
    /* 5. логіка питає режим: тема репліки, профіль після перемикання, стан для помічниці */
    факти.логіка = await с.evaluate(() => ({гетерів: ['РЕЖИМ', 'ЕКРАН', 'АРКУШ'].map(і => typeof window[і]),
      для_ші_у_сценарії: (ш => ({екран: ш.екран, крок: ш.крок}))(станДляШі())}));

    факти.помилок_сторінки = помилки;
    if (пр) fs.writeFileSync(пр + '_факти.json', JSON.stringify(факти, null, 1) + '\n');
    console.log(JSON.stringify(факти, null, 1));
    console.log(помилки.length ? 'ПОМИЛКИ СТОРІНКИ: ' + помилки.length : 'усі дії пройдено, помилок сторінки 0');
  } finally { await б.close(); }
})().catch(e => { console.error(e); process.exit(1); });
