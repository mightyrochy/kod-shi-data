/* Мірило наряду Прогін-картка-сценарію: рядки картки сценарію на записаних паспортах другого прогону «як людина»
   (14.11, вісім ситуацій по два проходи: `спільне.паспорт` кожного прогону у файлі вердиктів). Паспорт лягає на екран
   тим самим входом, що й після розмови (`застосуватиПаспортДоЕкрана`); сторінка — зі шаблону дерева без Python у
   браузері, як `аудит/проби/Екран-наново/мірило/вади_сценарій.js`. Кожен паспорт — свіжа сторінка.
   Друкує JSON: на кожен прохід — рядки картки, плитки аркуша «Нагода» (✓ — обрана) і чи видно поле реагентів.
   Запуск: CHROMIUM=/opt/pw-browsers/chromium node картка.js <тека джерела дерева> <вихід.json> */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const [дж, вихід] = process.argv.slice(2);
const БАЗА = 'http://127.0.0.1:8765';
const ПРОГІН = path.join(__dirname, '..', 'живий-як-людина-2');
const проходи = [];
for (const с of fs.readdirSync(ПРОГІН).filter(с => /^с\d/.test(с)).sort())
  for (const ф of fs.readdirSync(path.join(ПРОГІН, с)).filter(ф => /^verdykty-.*\.json$/.test(ф)))
    JSON.parse(fs.readFileSync(path.join(ПРОГІН, с, ф), 'utf8')).прогони
      .forEach((п, і) => проходи.push({сцена: с, прохід: і + 1, паспорт: п.спільне.паспорт}));
(async () => {
  const {прочитатиДовідникJSON, підставитиШаблон, зібратиШаблонПоказу} = require(path.join(дж, 'показ_шаблон.js'));
  const html = підставитиШаблон(зібратиШаблонПоказу(path.join(дж, 'показ.html')), {__МОДУЛІ_ПОКАЗУ__: 'ЗАГЛУШКА', __ЗБІРКА_ПОКАЗУ__: 'показ-тест',
    __ВІДБИТОК__: 'abc', __ФІД_ПОКАЗУ__: 'каталог_brief.xml', __КАТАЛОГ_ПОКАЗУ__: 'каталог_стенд.xml · 639 речей', __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(дж)})
    .replace(/<script [^>]*src="https:\/\/cdn\.jsdelivr\.net[^"\n]*"[^>]*><\/script>/, '<script>window.loadPyodide=null;</script>');
  const б = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM || undefined});
  const вих = [];
  for (const п of проходи){
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
    await с.evaluate(пс => { режим('сценарій'); ПАСПОРТ_П = пс; ВИПАДОК_ЗМІНЕНО_П = false; застосуватиПаспортДоЕкрана(ПАСПОРТ_П);
      if (typeof показатиСценарій === 'function') показатиСценарій(); }, п.паспорт);
    await с.waitForTimeout(800);
    const ф = await с.evaluate(() => {
      const картка = [...document.querySelectorAll('button.ряд-паспорта')].filter(р => !р.hidden && р.closest('#сц-картка, #е-випадок, .картка-сценарію') && !р.closest('.редактор'))
        .map(р => [(р.querySelector('span') || {}).textContent, ((р.querySelector('b') || {}).textContent || '').replace(/\s+/g, ' ').trim()]);
      const н = document.getElementById('сц-нагода-плитки');
      const плитки = н ? [...н.querySelectorAll('.плитка, button')].map(т => ((т.querySelector('.н, span') || т).textContent || '').trim()
        + (т.classList.contains('вибр') || т.getAttribute('aria-pressed') === 'true' ? ' ✓' : '')) : null;
      const р = document.getElementById('сц-реагенти'), л = р && р.closest('label');
      /* поле реагентів — у аркуші «Коли й погода», закритому до дотику: міряється, чи сховане саме поле (чи його блок) */
      const сховано = е => !!е && (е.hidden || getComputedStyle(е).display === 'none');
      return {картка, плитки, нагода_поле: typeof полеВипадкуП === 'function' ? полеВипадкуП('сц-нагода') : (document.getElementById('сц-нагода') || {}).value,
              реагенти_є: !!л, реагенти_сховано: !!л && (сховано(л) || сховано(л.parentElement)),
              смуга: typeof полеВипадкуП === 'function' ? полеВипадкуП('сц-смуга') : (document.getElementById('сц-смуга') || {}).value};
    });
    вих.push(Object.assign({сцена: п.сцена, прохід: п.прохід, причина_ошатності: п.паспорт.причина_ошатності}, ф, {помилки}));
    await к.close();
  }
  await б.close();
  fs.writeFileSync(вихід, JSON.stringify(вих, null, 1));
  for (const в of вих) console.log(в.сцена, в.прохід, JSON.stringify(в.картка), в.помилки.length ? 'ПОМИЛКИ ' + в.помилки.length : '');
})();
