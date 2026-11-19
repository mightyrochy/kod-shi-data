/* Мірило наряду Екран-наново: Н7 другого прогону «як людина» (рішення менеджера 14.11) — що тестувальниця бачить у
   «Вибрати, що вивантажити» і після «Зберегти позначене файлом». Прогін з чотирьох образів, чотири її вердикти записано
   шляхом показу (`записатиВердиктП`; перекладач і міст — заглушки, як у стенді показу); далі вона відкриває «Усі образи»
   → «Вердикти на цьому телефоні» → «Вибрати, що вивантажити» й торкає «Зберегти позначене файлом». Сторінка — зі шаблону
   без Python, як у `вади_сценарій.js`; Chromium 390×844 з дотиком.
   Запуск: NODE_PATH=джерела/node_modules CHROMIUM=/opt/pw-browsers/chromium node вади_н7.js <тека джерела дерева> <префікс> */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [дж, префікс] = process.argv.slice(2);
const БАЗА = 'http://127.0.0.1:8765';
(async () => {
  const б = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM || undefined});
  const к = await б.newContext({viewport: {width: 390, height: 844}, hasTouch: true, acceptDownloads: true});
  const с = await к.newPage();
  const помилки = [], факти = {};
  с.on('pageerror', e => помилки.push(String(e).slice(0, 300)));
  const {прочитатиДовідникJSON, підставитиШаблон, зібратиШаблонПоказу} = require(path.join(path.resolve(дж), 'показ_шаблон.js'));
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
  await тихо(1200);
  const річ = (н, назва, слот, ціна) => ({id: 'ж-н7-' + н + '@g.com', назва, ціна, слот, фото: null});
  const картка = рука => ({рука, ітерацій: 1, викликів: 1, текст: 'образ', опис: 'образ', підпис: 'образ',
    речі: [річ(рука + '1', 'Сукня міді', 'сукня', 3000), річ(рука + '2', 'Черевики', 'взуття', 2500)],
    мітки: [], знахідки: [], питання: [], етапи: {викликів: 1, виклики: []}, свідомі: [], невиконано: null,
    різноманітність: null, мова: [], мова_спроб: 0, мова_видано: 'так', фото_не_ті: [], дібрав_код_слоти: []});
  await с.evaluate(пакет => {
    П = пакет; П.прогін = новийІдПрогону(); рендер();
    П.знімок = {вхід: {}}; вхідМостаП = () => ({}); мовоюКарткуП = async () => {};
    перекластиП = async () => ({внутрішня: {reasons: ['fit']}, запис: {крок: 'verdict_comment'}});
    містП = async (що) => (що === 'вердикт' ? [] : {});
  }, {в: 'ПОКАЗ-V1', збірка: 'мірило-н7', каталог: 'каталог_стенд.xml · 639 речей', профіль: 'Оля', розклад: '2134',
      випадок_рядок: 'Театр', пул: 100, картки: ['2', '1', '3', '4'].map(картка)});
  for (let і = 0; і < 4; і++){
    await с.evaluate(і => { const в = відповідь(і); в.коментар = 'Гарний образ, сукня мені до лиця.'; позначитиЗмінуП(і); записатиВердиктП(і); }, і);
    await с.waitForFunction(і => !!(В[і] && В[і].записано && !В[і].пише && В[і].записана_зміна === В[і].зміна), і, {timeout: 60000});
  }
  /* шлях жінки: «Усі образи» → «Вердикти на цьому телефоні» → «Вибрати, що вивантажити» */
  await с.evaluate(() => режим('бібліотека')); await тихо(900);
  await с.locator('#журнал > summary').scrollIntoViewIfNeeded(); await с.locator('#журнал > summary').tap(); await тихо(700);
  await с.locator('#ж-вибір > summary').scrollIntoViewIfNeeded(); await с.locator('#ж-вибір > summary').tap(); await тихо(900);
  await с.waitForFunction(() => document.querySelectorAll('#жв-список .жв-образ').length === 4, null, {timeout: 30000});
  await с.evaluate(() => document.getElementById('ж-вибір').scrollIntoView({block: 'start'})); await тихо(400);
  const рядки = () => с.evaluate(() => ({день: [...document.querySelectorAll('#жв-список .жв-день > .жв-шапка span')].map(х => х.textContent),
    прогін: [...document.querySelectorAll('#жв-список .жв-прогін > .жв-шапка span')].map(х => х.textContent),
    образи: [...document.querySelectorAll('#жв-список .жв-образ span')].map(х => х.textContent)}));
  факти.вибір = await рядки();
  await знімок('Н7_вибір_вивантаження');
  const [файл] = await Promise.all([с.waitForEvent('download', {timeout: 30000}), с.locator('#жв-файл').tap()]);
  await тихо(900);
  факти.файл = файл.suggestedFilename();
  факти.після_збереження = await с.evaluate(() => document.getElementById('ж-стан').textContent);
  await с.evaluate(() => document.getElementById('ж-стан').scrollIntoView({block: 'center'})); await тихо(400);
  await знімок('Н7_після_збереження');
  /* службовий режим (`#службове=1`) — що лишилось власникові; на `main` рядок від режиму не залежить */
  await с.evaluate(() => { СЛУЖБОВЕ = true; if (typeof показатиСлужбове === 'function') показатиСлужбове(); }); await тихо(500);
  await с.evaluate(() => document.getElementById('ж-вибір').scrollIntoView({block: 'start'})); await тихо(400);
  await знімок('Н7_службове');
  факти.службове = {вибір: await рядки(), після_збереження: await с.evaluate(() => document.getElementById('ж-стан').textContent)};
  факти.помилки = помилки;
  fs.writeFileSync(префікс + '_н7_факти.json', JSON.stringify(факти, null, 1));
  console.log(JSON.stringify(факти));
  await б.close();
})().catch(e => { console.error('ЗБІЙ ПРОБИ', e); process.exit(1); });
