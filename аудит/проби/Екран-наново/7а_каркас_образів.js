/* Жива рука 7а: шапка й каркас екрана образів у Chromium 390×844 — пейджер (дотик по стрілках угорі й унизу), рядок
   випадку, «не ця» з «Повернути всі», зріз образів у стані екрана. Сторінка складена як у стенді показу; пакет образів —
   як у стенді (`П = …; рендер()`). Запуск: node 7а_каркас_образів.js <тека джерела> [знімок.png]. Друкує факти одним JSON. */
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
  const стан = () => с.evaluate(() => {
    const видимі = [...document.querySelectorAll('#картки .картка')].map((к, j) => к.hidden ? null : j).filter(j => j != null);
    const пж = ід => { const п = document.getElementById(ід); return {видно: !п.hidden && п.getBoundingClientRect().height > 0,
      лічба: п.querySelector('.пж-н').textContent, оцінено: п.querySelector('.пж-оц').textContent,
      вимкнено: [...п.querySelectorAll('button')].map(б => б.disabled)}; };
    return {режим: Екран.стан.режим, видимі, верх: пж('пейджер'), низ: пж('пейджер-низ'), гортання: Math.round(window.scrollY)}; });
  const факти = {після_показу: await стан()};
  факти.рядок_випадку = await с.evaluate(() => [...document.querySelectorAll('#обр-випадок span')].map(s => [s.textContent, !!s.querySelector('svg')]));
  await с.click('#пж-далі'); факти.дотик_далі_вгорі = await стан();
  await с.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
  await с.click('#пж-низ-далі'); факти.дотик_далі_внизу = await стан();
  await с.click('#пж-далі'); факти.остання = await стан();
  await с.click('#пж-назад'); факти.дотик_назад = await стан();
  /* «не ця»: відхилення словами (той самий набір, що після тапу) — рядок над картками й під переліком, «Повернути всі» дотиком */
  await с.evaluate(() => { позначитиНеЦюП('ж-4@g.com', 2); показатиНеЦю(); });
  const неЦя = () => с.evaluate(() => { const е = document.getElementById('обр-не-ця');
    return {видно: е.style.display !== 'none' && е.getBoundingClientRect().height > 0, текст: е.textContent,
            під_переліком: document.querySelector('#к-2 .не-ця-рядок').textContent, набір: НЕ_ЦЯ_П.знімок(),
            позначок: document.querySelectorAll('#картки button.замін.вибр').length,
            кнопка: (б => б && {напис: б.textContent, натиснута: б.getAttribute('aria-pressed')})(document.querySelector('#к-2 button.замін[data-id="ж-4@g.com"]')), у_відповіді: (В[2] || {}).замінити}; });
  факти.позначено = await неЦя();
  await с.waitForTimeout(700);   /* картка проступає плавно — знімок після появи */
  if (process.argv[3]) await с.screenshot({path: process.argv[3]});
  await с.click('#обр-не-ця-повернути'); факти.повернуто = await неЦя();
  факти.зріз_образів = await с.evaluate(() => JSON.parse(JSON.stringify(Екран.стан.образи)));
  console.log(JSON.stringify({факти, помилки}, null, 1)); await б.close();
})().catch(e => { console.error(e); process.exit(1); });
