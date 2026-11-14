/* Chromium 390×844, решта зрізу 9: службовий блок (`#службове=1` в адресі й у пам'яті телефона), рядок шапки
   (збірка сторінки → збірка пакета образів) і «Зрозуміло» під сповіщенням збою — ті самі дії ДО й ПІСЛЯ.
   Нічого не підмінено, крім сховища в другій сторінці (IndexedDB недоступна — збій старту до першого входу).
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
    const стан = с => с.evaluate(() => {
      const в = document.getElementById('службове');
      return {службове_видно: getComputedStyle(в).display !== 'none', клас: в.className,
        памʼять: localStorage.getItem('міст:службове'), рядок: document.getElementById('ш-рядок').textContent,
        збій: document.getElementById('збій-стан').textContent, вхід: Екран.стан.вхід > 0,
        режим: Екран.стан.режим};
    });
    const знімок = async (с, назва) => { if (!пр) return;
      await с.evaluate(() => { const в = document.getElementById('службове'); в.open = true; в.scrollIntoView(); });
      await с.waitForTimeout(200); await с.screenshot({path: пр + '_' + назва + '.png'}); };
    const хеш = async (с, х, умова) => { await с.evaluate(х => { location.hash = х; }, х);
      await с.waitForFunction(умова, null, {timeout: 30000}); };

    /* 1. звичайний старт: службового блоку не видно, рядок збірки в ньому є */
    const с = await сторінка();
    await с.goto('http://stend.test/'); await запущено(с);
    факти.старт = await стан(с);
    /* 2. `#службове=1` без перезавантаження */
    await хеш(с, '#службове=1', () => localStorage.getItem('міст:службове') === '1'
      && getComputedStyle(document.getElementById('службове')).display !== 'none');
    факти.службове_з_адреси = await стан(с);
    await знімок(с, 'службове');
    /* 3. перезавантаження без хеша: прапорець — з пам'яті телефона */
    await с.goto('http://stend.test/'); await запущено(с);
    факти.службове_з_памʼяті = await стан(с);
    /* 4. пакет образів на екрані: рядок шапки каже збірку пакета */
    await с.evaluate(() => { П = {в: 'ПОКАЗ-V1', збірка: 'тест-9', каталог: 'каталог_стенд.xml · 639 речей',
      профіль: 'Оля', розклад: '2143', випадок_шматки: [{ключ: 'нагода', текст: 'Робота'}], пул: 100,
      прогін: новийІдПрогону(), картки: [{рука: '2', ітерацій: 1, викликів: 1, текст: 'образ 2', опис: 'образ 2',
        підпис: 'образ 2', як_носити: [], речі: [{назва: 'Сукня кольору вина', слот: 'сукня'}], мітки: [],
        знахідки: [], питання: [], етапи: {викликів: 1, виклики: []}, свідомі: [], невиконано: null,
        різноманітність: null, мова: [], мова_спроб: 0, мова_видано: 'так', фото_не_ті: [], дібрав_код_слоти: [],
        збирання: {сід: 7, ключ: '2143', позиція: 0, рука: '2'}}]}; рендер(); });
    await с.waitForSelector('#прмк-0');
    факти.пакет = await стан(с);
    await знімок(с, 'пакет');
    /* 5. `#службове=0` — блок сховано, пам'ять очищено */
    await хеш(с, '#службове=0', () => getComputedStyle(document.getElementById('службове')).display === 'none');
    факти.службове_вимкнено = await стан(с);
    /* 6. сповіщення збою й «Зрозуміло» */
    await с.evaluate(() => { режим('профіль'); збійЖінціП(document.getElementById('збій-стан'), 'not_saved', 'проба'); });
    факти.збій_показано = await стан(с);
    await с.locator('#збій-прибрати').tap();
    факти.збій_прибрано = await стан(с);
    факти.слідів_збою = await с.evaluate(() => ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П.map(з => з.вид));

    /* 7. сховище недоступне: старт не дійшов до першого входу, збій показано, «Зрозуміло» його прибирає */
    const д = await сторінка(() => { Object.defineProperty(window, 'indexedDB', {get(){
      return {open(){ throw new Error('проба: сховище недоступне'); }}; }}); });
    await д.goto('http://stend.test/');
    await д.waitForFunction(() => document.getElementById('збій-стан').textContent !== '', null, {timeout: 60000});
    факти.збій_старту = await д.evaluate(() => ({збій: document.getElementById('збій-стан').textContent,
      вхід: Екран.стан.вхід > 0, запущено: !!Екран.стан.запущено,
      сліди: ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П.map(з => з.вид)}));
    if (пр){ await д.waitForTimeout(200); await д.screenshot({path: пр + '_збій_старту.png'}); }
    await д.locator('#збій-прибрати').tap();
    факти.збій_старту_прибрано = await д.evaluate(() => document.getElementById('збій-стан').textContent);

    факти.помилок_сторінки = помилки;
    if (пр) fs.writeFileSync(пр + '_факти.json', JSON.stringify(факти, null, 1) + '\n');
    console.log(JSON.stringify(факти, null, 1));
    console.log(помилки.length ? 'ПОМИЛКИ СТОРІНКИ: ' + помилки.length : 'усі дії пройдено, помилок сторінки 0');
  } finally { await б.close(); }
})().catch(e => { console.error(e); process.exit(1); });
