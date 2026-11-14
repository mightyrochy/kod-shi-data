/* Жива рука 6г: смужка «Є новіша версія Люстерка» в Chromium 390×844. Сторінка складена як у стенді показу, штамп
   `build.txt` віддає новіший. Запуск: node 6г_нова_збірка.js <тека джерела>. Друкує факти одним JSON. */
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
  let штамп = 'показ-тест', читань = 0;
  await с.route('**/*', r => { const у = new URL(r.request().url());
    if (у.pathname === '/build.txt'){ читань++; return r.fulfill({contentType: 'text/plain', body: штамп + '\n'}); }
    return у.pathname === '/' ? r.fulfill({contentType: 'text/html', body: html}) : r.abort(); });
  await с.goto('http://stend.test/#службове=1');
  await с.waitForFunction(() => Екран.стан.вхід > 0 && Екран.стан.запущено, null, {timeout: 60000});
  const видно = () => с.evaluate(() => { const е = document.getElementById('нова-версія'); return !е.hidden && е.getBoundingClientRect().height > 0; });
  const факти = {той_самий_штамп: {видно: await видно(), читань}};
  /* вкладка знову видима — штамп уже новіший */
  штамп = 'показ-новіший';
  await с.evaluate(() => document.dispatchEvent(new Event('visibilitychange')));
  await с.waitForFunction(() => !document.getElementById('нова-версія').hidden, null, {timeout: 10000});
  факти.новіший_штамп = {видно: await видно(), читань, текст: await с.evaluate(() => document.getElementById('нова-версія').textContent)};
  await с.click('#нова-версія-кн'); await с.waitForURL(/v=/, {timeout: 10000});
  факти.після_оновити = {адреса: decodeURIComponent(с.url())};
  console.log(JSON.stringify({факти, помилки}, null, 1)); await б.close();
})().catch(e => { console.error(e); process.exit(1); });
