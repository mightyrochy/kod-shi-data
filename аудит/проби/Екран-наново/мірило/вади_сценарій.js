/* Мірило наряду Екран-наново: вади 20 і 21 — картка сценарію з паспортом із розмови. Паспорт — записаний живим
   прогоном 14.11 (с5 «весілля сестри в серпні»: `паспорт_с5.json` — `спільне.паспорт` файла вердиктів), на екран він
   лягає тим самим входом логіки, що й після розмови (`застосуватиПаспортДоЕкрана`). Сторінка — зі шаблону без Python,
   як у `вади.js`; Chromium 390×844 з дотиком; рядки картки жінка відкриває дотиком.
   Запуск: NODE_PATH=джерела/node_modules CHROMIUM=/opt/pw-browsers/chromium node вади_сценарій.js <тека джерела дерева> <префікс> */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [дж, префікс] = process.argv.slice(2);
const БАЗА = 'http://127.0.0.1:8765';
const ПАСПОРТ = JSON.parse(fs.readFileSync(path.join(__dirname, 'паспорт_с5.json'), 'utf8'));
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
  await с.evaluate(п => { режим('сценарій'); ПАСПОРТ_П = п; ВИПАДОК_ЗМІНЕНО_П = false; застосуватиПаспортДоЕкрана(ПАСПОРТ_П); }, ПАСПОРТ);
  await тихо(1200);
  const рядки = () => с.evaluate(() => [...document.querySelectorAll('#е-випадок button.ряд-паспорта')].filter(р => !р.hidden && р.getBoundingClientRect().height > 0)
    .map(р => ({назва: (р.querySelector('span') || {}).textContent, значення: (р.querySelector('b') || {}).textContent.replace(/\s+/g, ' ').trim()})));
  факти.картка = await рядки();
  await с.locator('button.ряд-паспорта[data-редактор="ред-нагода"]').scrollIntoViewIfNeeded(); await тихо(300);
  await знімок('21_картка_сценарію');
  const відкрити = async (сел, ім, читати) => {
    await с.locator(сел).scrollIntoViewIfNeeded(); await с.locator(сел).tap(); await тихо(900);
    const ф = await с.evaluate(читати); await знімок(ім);
    if (await с.locator('#аркуш-готово').isVisible()){ await с.locator('#аркуш-готово').tap(); await тихо(600); }
    return ф;
  };
  /* вада 20: аркуш «Де це буде» — що стоїть у списку «Місце», коли місце назване словами в розмові */
  факти.в20 = await відкрити('button.ряд-паспорта[data-редактор="ред-місце"]', '20_аркуш_де', () => { const в = document.getElementById('сц-місце');
    return {значення: в.value, вибрано: (в.selectedOptions[0] || {}).textContent, пунктів: в.options.length, перший_пункт: (в.options[0] || {}).textContent}; });
  /* вада 21: аркуш «Нагода» (чи є «весілля»), аркуш «Коли й погода» (поле реагентів у серпні), рядок «Додати» */
  факти.в21_нагода = await відкрити('button.ряд-паспорта[data-редактор="ред-нагода"]', '21_аркуш_нагода', () => ({
    плитки: [...document.querySelectorAll('#аркуш .плитка, #аркуш .плитки button')].filter(п => п.getBoundingClientRect().height > 0).map(п => п.textContent.replace(/\s+/g, ' ').trim() + (п.classList.contains('вибр') || п.getAttribute('aria-pressed') === 'true' ? ' ✓' : ''))}));
  факти.в21_погода = await відкрити('button.ряд-паспорта[data-редактор="ред-коли"]', '21_аркуш_коли_й_погода', () => { const р = document.getElementById('сц-реагенти'), п = р.closest('label');
    return {смуга: document.getElementById('сц-смуга').value, реагенти_видно: !!п && !п.hidden && п.getBoundingClientRect().height > 0, підпис: п ? п.querySelector('span').textContent : null}; });
  факти.в21_додати = {до: (await рядки()).filter(р => р.назва === 'Додати')};
  if (await с.locator('#сц-ще').isVisible()){
    await с.locator('#сц-ще').scrollIntoViewIfNeeded(); await с.locator('#сц-ще').tap(); await тихо(900);
    факти.в21_додати.після = await рядки();
    await знімок('21_після_додати');
  }
  факти.помилки = помилки;
  fs.writeFileSync(префікс + '_сценарій_факти.json', JSON.stringify(факти, null, 1));
  console.log(JSON.stringify(факти));
  await б.close();
})().catch(e => { console.error('ЗБІЙ ПРОБИ', e); process.exit(1); });
