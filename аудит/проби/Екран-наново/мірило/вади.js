/* Мірило наряду Екран-наново: вади «екран» розділу 1 і дані старої версії — ті самі дії жінки на зібраному повному
   показі ДО (`main`) й ПІСЛЯ (гілка) у Chromium 390×844 (сторінка складена з джерел, як у стенді показу; Python не піднімається).
   Модель і міст не потрібні: знайомство, мірки, пакет із чотирьох карток, вердикт
   словами. Знімки — вікно 390×844, як його бачить жінка, без гортання приладом.
   Запуск: NODE_PATH=джерела/node_modules node вади.js <тека джерела дерева> <префікс> [<тека джерела нової збірки>]
   З третім аргументом — проба «записати старою збіркою, відкрити новою»: після дій на першій збірці той самий браузер
   (та сама база `показ` і localStorage) відкриває сторінку другої. */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [збірка, префікс, нова] = process.argv.slice(2);   // збірка — тека `джерела` дерева ДО чи ПІСЛЯ; нова — тека `джерела` збірки, якою відкрити записане
const БАЗА = 'http://127.0.0.1:8765';
const ЖІНКА = JSON.parse(fs.readFileSync(path.join(__dirname, '../../жінки/ж1.json'), 'utf8'));
(async () => {
  const б = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM || undefined});
  const к = await б.newContext({viewport: {width: 390, height: 844}, hasTouch: true});
  let с = await к.newPage();
  const помилки = [], факти = {};
  с.on('pageerror', e => помилки.push(String(e).slice(0, 300)));
  /* сторінка складена як у стенді показу (`тест_показу.js`): шаблон з джерел, Pyodide не вантажиться — усе, що тут
     міряється, робить JS показу: знайомство, мірки, пакет карток, вердикт, журнал, база `показ` і localStorage */
  const скласти = дж => { const {прочитатиДовідникJSON, підставитиШаблон, зібратиШаблонПоказу} = require(path.join(дж, 'показ_шаблон.js'));
   return підставитиШаблон(зібратиШаблонПоказу(path.join(дж, 'показ.html')), {__МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'показ-тест',
    __ВІДБИТОК__: 'abc', __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'каталог_стенд.xml · 639 речей', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(дж)})
    .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"\n]*"[^>]*><\/script>/, '<script>window.loadPyodide=null;</script>'); };
  let html = скласти(збірка);
  await к.route('**/*', r => { const у = new URL(r.request().url());
    if (у.pathname === '/build.txt') return r.fulfill({contentType: 'text/plain', body: 'показ-тест\n'});
    return у.origin === БАЗА && у.pathname === '/' ? r.fulfill({contentType: 'text/html', body: html}) : r.abort(); });
  const знімок = ім => с.screenshot({path: префікс + '_' + ім + '.png'});
  const тихо = мс => с.waitForTimeout(мс || 400);
  /* що лежить у браузері: сховища бази `показ` (ключі й відбиток значень) і localStorage */
  const сховище = () => с.evaluate(async () => {
    const б = await new Promise((так, ні) => { const з = indexedDB.open('показ'); з.onsuccess = () => так(з.result); з.onerror = () => ні(з.error); });
    const вих = {версія: б.version, сховища: {}};
    for (const ім of [...б.objectStoreNames].sort()){
      const т = б.transaction(ім, 'readonly').objectStore(ім);
      const [ключі, значення] = await Promise.all([т.getAllKeys(), т.getAll()].map(з => new Promise(так => { з.onsuccess = () => так(з.result); })));
      вих.сховища[ім] = ключі.map((кл, і) => { const в = значення[і], р = в instanceof Blob ? 'Blob ' + в.size : JSON.stringify(в) || String(в);
        let х = 0; for (let j = 0; j < р.length; j++) х = (х * 31 + р.charCodeAt(j)) | 0;
        return {ключ: String(кл), довжина: р.length, відбиток: х, початок: р.slice(0, 80)}; });
    }
    б.close();
    return {база: вих, localStorage: Object.fromEntries(Object.keys(localStorage).sort().map(кл => [кл, localStorage.getItem(кл)]))};
  });
  const уВікні = сел => с.evaluate(сел => { const в = document.querySelector(сел); if (!в) return null; const р = в.getBoundingClientRect();
    return {верх: Math.round(р.top), низ: Math.round(р.bottom), видно_ціле: р.height > 0 && р.top >= 0 && р.bottom <= innerHeight,
      перекрито: р.height > 0 && document.elementFromPoint(р.left + р.width / 2, Math.min(innerHeight - 1, Math.max(0, р.top + р.height / 2))) !== в
        && !в.contains(document.elementFromPoint(р.left + р.width / 2, Math.min(innerHeight - 1, Math.max(0, р.top + р.height / 2)))),
      текст: (в.textContent || в.value || '').replace(/\s+/g, ' ').trim().slice(0, 160)}; }, сел);
  const готово = () => с.waitForFunction(() => { const д = document.getElementById('н-далі'); return д && д.getBoundingClientRect().height > 0
    && (typeof Екран === 'undefined' || !Екран.стан || !('запущено' in Екран.стан) || Екран.стан.запущено); }, null, {timeout: 180000});

  await с.goto(БАЗА + '/', {waitUntil: 'commit', timeout: 120000});
  await готово();
  /* перший екран знайомства наповнюється, щойно піднявся Python: чекаємо блок кольорів, як жінка */
  await с.waitForFunction(() => { const б = document.getElementById('кол-блок'); return б && б.getBoundingClientRect().height > 0; }, null, {timeout: 240000})
    .catch(async () => { await знімок('нема_першого_екрана'); throw new Error('перший екран не наповнився: ' + JSON.stringify(помилки)); });
  await тихо(1500);
  /* вада 13: чи видно шлях без фото на першому екрані без гортання */
  факти.в13 = {інший_шлях: await уВікні('#кол-блок details summary'), підказка: await уВікні('#кол-блок .підказка, .підказка')};
  await знімок('13_старт');
  /* кнопка шляху без портрета на першому екрані (після правки вади 13): дотик розкриває шлях і підводить до нього */
  факти.в13.кнопка_вгорі = await уВікні('#кол-без-портрета');
  if (факти.в13.кнопка_вгорі){
    await с.locator('#кол-без-портрета').tap(); await тихо(800);
    факти.в13.після_дотику = {інший_шлях: await уВікні('#кол-блок details summary'), запит: await уВікні('#кол-запит'),
      розкрито: await с.evaluate(() => document.querySelector('#кол-блок details').open)};
    await знімок('13_після_дотику');
    await с.evaluate(() => scrollTo(0, 0)); await тихо(300);
  }
  await с.locator('#н-далі').tap(); await тихо(1500);
  await знімок('крок_лице');
  await с.locator('#н-далі').tap(); await тихо(1500);
  /* вади 16 і 17: сірі підказки в полях фігури й поле «Зріст» у вікні без гортання */
  факти.в16 = await с.evaluate(() => { const п = document.getElementById('мр-плечі'); return {підказка: п.placeholder, колір_підказки: getComputedStyle(п, '::placeholder').color,
    прозорість_підказки: getComputedStyle(п, '::placeholder').opacity, колір_введеного: getComputedStyle(п).color, стиль_підказки: getComputedStyle(п, '::placeholder').fontStyle}; });
  факти.в17 = {зріст: await уВікні('#мр-зріст'), стегна: await уВікні('#мр-стегна'), далі: await уВікні('#н-далі'), вгорі: await с.evaluate(() => scrollY)};
  await знімок('16_17_мірки');
  for (const [м, ч] of [['плечі', '98'], ['груди', '92'], ['талія', '74'], ['стегна', '101'], ['зріст', '168']]){
    await с.locator('#мр-' + м).scrollIntoViewIfNeeded(); await с.locator('#мр-' + м).fill(ч); await с.locator('#мр-' + м).dispatchEvent('change'); }
  await тихо(800); await с.locator('#н-далі').scrollIntoViewIfNeeded(); await с.locator('#н-далі').tap(); await тихо(2500);
  факти.після_знайомства = await с.evaluate(() => ({видимі_екрани: [...document.querySelectorAll('[id^="е-"]')].filter(е => getComputedStyle(е).display !== 'none' && !е.hidden).map(е => е.id)}));
  await знімок('сценарій_після_знайомства');
  /* вади 1, 12, 19 і Н2: пакет із чотирьох карток, вердикт словами без відповіді на «Вдягнеш?» */
  await с.evaluate(() => {
    const реч = н => [{id: 'ж-' + н + '@g.com', назва: 'Сукня ' + н, ціна: 3000, слот: 'сукня', фото: null}, {id: 'п-' + н + '@g.com', назва: 'Пасок ' + н, ціна: 500, слот: 'пояс', фото: null}];
    const к = (рука, поз) => ({рука, ітерацій: 1, викликів: 1, текст: 'образ ' + рука, опис: 'образ ' + рука, підпис: 'образ ' + рука, речі: реч(рука), мітки: [], знахідки: [], питання: [],
      етапи: {викликів: 1, виклики: []}, свідомі: [], невиконано: null, різноманітність: null, мова: [], мова_спроб: 0, мова_видано: 'так', фото_не_ті: [], дібрав_код_слоти: [],
      збирання: {сід: 7, ключ: '2143', позиція: поз, рука}});
    П = {в: 'ПОКАЗ-V1', збірка: 'мірило', каталог: 'каталог_стенд.xml · 639 речей', профіль: 'Оля', розклад: '2143',
      випадок_шматки: [{ключ: 'нагода', текст: 'Робота'}, {ключ: 'місце', текст: 'офіс'}], пул: 100, прогін: новийІдПрогону(), картки: ['2', '1', '4', '3'].map(к)};
    рендер(); режим('образи');
  });
  await тихо(1500);
  const слова = 'Сукня гарна, але пасок я б зняла.\nКолір не мій — надто холодний для мене.\nДовжина добра.\nНа роботу вдягла б з іншим взуттям.\nА ще рукав закороткий.\nІ тканина, здається, мнеться.\nСьомий рядок.\nВосьмий рядок.\nДевʼятий рядок.\nДесятий рядок.\nОдинадцятий рядок.\nДванадцятий рядок.\nТринадцятий.\nЧотирнадцятий.\nПʼятнадцятий.\nШістнадцятий.\nСімнадцятий.\nВісімнадцятий.\nДевʼятнадцятий.\nДвадцятий.\nДвадцять перший.\nДвадцять другий.\nДвадцять третій.\nДвадцять четвертий.';
  await с.locator('#ком-0').scrollIntoViewIfNeeded(); await с.locator('#ком-0').tap(); await с.keyboard.insertText(слова); await тихо(600);
  const р = await с.locator('#ком-0').boundingBox(), доГорт = await с.evaluate(() => ({сторінка: scrollY, поле: document.getElementById('ком-0').scrollTop}));
  await с.mouse.move(р.x + р.width / 2, Math.min(800, р.y + р.height / 2)); await с.mouse.wheel(0, 240); await тихо(500);
  факти.в12 = Object.assign(await с.evaluate(() => { const т = document.getElementById('ком-0'); return {висота_поля: т.clientHeight, висота_тексту: т.scrollHeight, після_жесту: {сторінка: scrollY, поле: т.scrollTop}}; }), {до_жесту: доГорт});
  await знімок('12_поле_вердикту');
  /* вада 12 пальцем: жест дотику (CDP `Input.dispatchTouchEvent`: дотик, дванадцять рухів по 20 px, відпускання) починається посеред поля й тягне
     вгору на 240 px, як палець жінки; до жесту сторінка й поле — там, де були до колеса */
  await с.evaluate(д => { scrollTo(0, д.сторінка); document.getElementById('ком-0').scrollTop = 0; }, доГорт); await тихо(400);
  const р2 = await с.locator('#ком-0').boundingBox(), cdp = await к.newCDPSession(с);
  const деЖест = {x: Math.round(р2.x + р2.width / 2), y: Math.round(Math.max(р2.y + 20, Math.min(700, р2.y + р2.height / 2)))};
  const станГорт = () => с.evaluate(() => { const т = document.getElementById('ком-0'); return {сторінка: Math.round(scrollY), поле: Math.round(т.scrollTop), висота_поля: т.clientHeight, висота_тексту: т.scrollHeight}; });
  const пальцем = {жест: деЖест, до: await станГорт()};
  for (const ім of ['після_першого', 'після_другого']){
    await cdp.send('Input.dispatchTouchEvent', {type: 'touchStart', touchPoints: [деЖест]});
    for (let і = 1; і <= 12; і++){ await cdp.send('Input.dispatchTouchEvent', {type: 'touchMove', touchPoints: [{x: деЖест.x, y: деЖест.y - і * 20}]}); await тихо(16); }
    await cdp.send('Input.dispatchTouchEvent', {type: 'touchEnd', touchPoints: []}); await тихо(900);
    пальцем[ім] = await станГорт();
    if (ім === 'після_першого') await знімок('12_пальцем_після_першого_жесту');
  }
  факти.в12.пальцем = пальцем;
  await с.locator('#ком-0').evaluate(т => т.blur()); await тихо(1200);
  факти.в19 = await с.evaluate(() => ({поле_після_виходу: document.getElementById('ком-0').value.length, статус: document.getElementById('вст-0').textContent}));
  await с.locator('#зап-0').scrollIntoViewIfNeeded(); await с.locator('#зап-0').tap();
  await с.waitForFunction(() => document.getElementById('вст-0').textContent.length > 0, null, {timeout: 20000}).catch(() => {});
  await тихо(300); await знімок('1_вердикт_словами_одразу');
  факти.в1 = {статус: await уВікні('#вст-0'), записів: await с.evaluate(async () => (await усіВердикти()).length)};
  await тихо(3500);
  факти.н2 = {статус_через_4с: await уВікні('#вст-0'), запис_у_пейджері: await уВікні('#пейджер .пж-запис'), вгорі: await с.evaluate(() => scrollY),
    поле_на_місці: await с.evaluate(() => document.getElementById('ком-0').value.length), видима_картка: await с.evaluate(() => { for (let і = 0; і < 4; і++){ const к = document.getElementById('к-' + і); if (к && getComputedStyle(к).display !== 'none' && !к.hidden && к.getBoundingClientRect().height > 0) return і; } return null; })};
  await знімок('1_вердикт_словами_через_4с');
  /* Н4, Н7: журнал вердиктів — скільки названо й скільки рядків видно */
  await с.evaluate(() => { const ж = document.getElementById('журнал'); if (ж){ ж.open = true; ж.scrollIntoView(); } }); await тихо(1500);
  факти.н4 = await с.evaluate(() => ({ліч: document.getElementById('ж-ліч').textContent, рядків: document.getElementById('ж-список').children.length, список: document.getElementById('ж-список').textContent.replace(/\s+/g, ' ').trim().slice(0, 400)}));
  await знімок('н4_журнал');
  /* Н4 на восьми записах: той самий вердикт сім разів дописано в сховище під новими ключами; лічбу й рядки журналу
     читає `відкрити` нижче — на сторінці старої збірки й нової */
  await с.evaluate(async () => {
    const б = await new Promise((так, ні) => { const з = indexedDB.open('показ'); з.onsuccess = () => так(з.result); з.onerror = () => ні(з.error); });
    await new Promise((так, ні) => { const т = б.transaction('вердикти', 'readwrite'), с = т.objectStore('вердикти'), з = с.getAll();
      з.onsuccess = () => { for (let і = 0; і < 7; і++) с.add(Object.assign({}, з.result[0])); };
      т.oncomplete = так; т.onerror = () => ні(т.error); });
    б.close();
  });
  /* стара адреса мосту в localStorage — для проби «записати старою, відкрити новою» (маршрути глушать міст) */
  await с.evaluate(() => { localStorage.setItem('міст:адреса', 'https://mist.example/v1'); localStorage.setItem('міст:токен', 'токен-старої-збірки'); localStorage.setItem('міст:модель', 'gemini-стара');
    const т = document.getElementById('тема-кнопка'); if (т) т.click(); });
  await тихо(1500);
  факти.тема = await с.evaluate(() => ({ключ: localStorage.getItem('люстерко-тема')}));
  факти.сховище = await сховище();
  /* записане цією збіркою відкриває вона сама (контроль) і нова збірка — той самий браузер, ті самі база й localStorage.
     Адресу мосту з localStorage сторінка перепитує («Використовувати цю адресу?») — відповідаємо «Так», як жінка. */
  const відкрити = async (дж, мітка) => {
    html = скласти(дж); await с.close(); с = await к.newPage(); с.on('pageerror', e => помилки.push(мітка + ': ' + String(e).slice(0, 300)));
    await с.goto(БАЗА + '/', {waitUntil: 'commit', timeout: 120000});
    await с.waitForFunction(() => document.readyState === 'complete' && typeof рендер === 'function', null, {timeout: 180000}); await тихо(2500);
    const ф = {питання_адреси: await с.evaluate(() => { const к = [...document.querySelectorAll('button')].find(б => б.textContent === 'Так, використовувати');
      if (!к) return null; const в = к.closest('[role="dialog"], dialog, div'), з = в.querySelector('h2, h3, p, strong') || в;
      return {текст: в.textContent.replace(/\s+/g, ' ').trim().slice(0, 120), колір_тексту: getComputedStyle(з).color, тло: getComputedStyle(в).backgroundColor}; })};
    await знімок('відкрито_' + мітка + '_питання_адреси');
    if (ф.питання_адреси){ await с.getByText('Так, використовувати').tap(); await тихо(3000); }
    ф.сховище = await сховище();
    ф.екран = await с.evaluate(() => ({тема: localStorage.getItem('люстерко-тема'), клас_теми: document.documentElement.getAttribute('data-тема') || document.documentElement.className || document.body.className,
      мірки: Object.fromEntries(['плечі', 'груди', 'талія', 'стегна', 'зріст'].map(м => [м, (document.getElementById('мр-' + м) || {}).value])),
      видимі_екрани: [...document.querySelectorAll('[id^="е-"]')].filter(е => getComputedStyle(е).display !== 'none' && !е.hidden).map(е => е.id),
      вкладка: [...document.querySelectorAll('[id^="вк-"]')].filter(в => в.getAttribute('aria-current') || в.classList.contains('тут')).map(в => в.id)}));
    await знімок('відкрито_' + мітка);
    ф.вердикти = await с.evaluate(async () => (await усіВердикти()).map(в => JSON.stringify(в).length));
    await с.evaluate(() => { режим('бібліотека'); }); await тихо(2000);
    await с.evaluate(() => { const ж = document.getElementById('журнал'); if (ж){ ж.open = true; ж.scrollIntoView(); } }); await тихо(1500);
    ф.журнал = await с.evaluate(() => ({ліч: document.getElementById('ж-ліч').textContent, список: document.getElementById('ж-список').textContent.replace(/\s+/g, ' ').slice(0, 200),
      рядків: document.getElementById('ж-список').textContent.split('\n').filter(р => р.trim()).length, останній_рядок: document.getElementById('ж-список').textContent.split('\n').filter(р => р.trim()).pop(),
      усі_образи: document.getElementById('біб-список').textContent.replace(/\s+/g, ' ').trim().slice(0, 200)}));
    await знімок('відкрито_' + мітка + '_усі_образи');
    await с.evaluate(() => { режим('профіль'); }); await тихо(2000);
    ф.профіль = await с.evaluate(() => ({текст: (document.getElementById('е-огляд') || {textContent: ''}).textContent.replace(/\s+/g, ' ').trim().slice(0, 300)}));
    await знімок('відкрито_' + мітка + '_профіль');
    return ф;
  };
  if (нова){ факти.відкрито_старою = await відкрити(збірка, 'старою'); факти.відкрито_новою = await відкрити(нова, 'новою'); }
  факти.помилки = помилки;
  fs.writeFileSync(префікс + '_факти.json', JSON.stringify(факти, null, 1));
  await б.close();
})().catch(e => { console.error('ЗБІЙ ПРОБИ', e); process.exit(1); });
