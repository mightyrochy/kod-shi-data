/* Обгортка виконавця (не код продукту): штатний `рв6_стенд.js` дерева <корінь> до кінця розділу 2 (каталог, руки 1–4,
   фото), плюс її дія на картці руки 1, поки йдуть руки 2–4: «вдягну як є», слова в полі, екран прокручено до поля.
   Кожні 50 мс — вибірка: напис над картками, число карток на екрані, scrollY, верх поля слів; ДО й ПІСЛЯ шва — знімки
   390×844, дані `П`, запис бібліотеки й журнал прогону. Основа — `каталожний-стенд.cjs` автоперевірки #4350 ba43ce3e.
   Запуск: CHROMIUM=/opt/pw-browsers/chromium FOTO=1 ZATRYMKA=typy NODE_PATH=джерела/node_modules \
     node стенд_шва.cjs <корінь дерева> <тека зі зібраним index.html> <тека pyodide> <тека виходу> */
const fs = require('fs'), path = require('path'), pw = require('playwright'), Module = require('module');
const [root, site, pyodide, out] = process.argv.slice(2); fs.mkdirSync(out, {recursive: true});
const launch = pw.chromium.launch.bind(pw.chromium);
pw.chromium.launch = async (...a) => {
  const browser = await launch(...a), newContext = browser.newContext.bind(browser);
  browser.newContext = async (...a) => {
    const context = await newContext(...a), newPage = context.newPage.bind(context);
    context.newPage = async (...a) => {
      const page = await newPage(...a), wait = page.waitForFunction.bind(page);
      const observer = (async () => {
        await wait(() => typeof П !== 'undefined' && П && (П.картки || []).length === 1 && typeof ЗБ !== 'undefined' && ЗБ && !ЗБ.готово,
                   null, {timeout: 1200000, polling: 100});
        await page.setViewportSize({width: 390, height: 844});
        await page.getByText('вдягну як є', {exact: true}).first().click();
        await page.locator('textarea[placeholder^="Наприклад"]').first().fill('слова перевірки до кінця рук');
        await page.evaluate(() => {
          const поле = document.querySelector('textarea[placeholder^="Наприклад"]');
          поле.scrollIntoView({block: 'center'});
          window.__вузол = document.getElementById('к-0'); window.__прогін = П.прогін; window.__семпли = [];
          const семпл = () => { const п = document.querySelector('#к-0 textarea[placeholder^="Наприклад"]');
            const з = {t: Date.now(), готово: !!ЗБ.готово, карток: document.querySelectorAll('#картки > .картка').length,
              підпис: (document.getElementById('обр-підпис') || {}).textContent || '', scrollY: Math.round(scrollY * 100) / 100,
              поле_верх: п ? Math.round(п.getBoundingClientRect().top * 100) / 100 : null, режим: Екран.стан.режим};
            const ост = window.__семпли[window.__семпли.length - 1];
            if (!ост || ['готово','карток','підпис','scrollY','поле_верх','режим'].some(к => ост[к] !== з[к])) window.__семпли.push(з); };
          семпл(); window.__таймер = setInterval(семпл, 50); });
        const read = () => page.evaluate(async () => {
          const db = await дб(); const образи = await tx(db, 'образи', 'readonly', s => s.getAll());
          const вердикти = await tx(db, 'вердикти', 'readonly', s => s.getAll()); const свій = образи.find(x => x.прогін === window.__прогін);
          const поле = document.querySelector('#к-0 textarea[placeholder^="Наприклад"]');
          return {готово: ЗБ.готово, прогін_на_екрані: П.прогін === window.__прогін, руки_П: П.картки.map(x => x.рука),
            карток_на_екрані: document.querySelectorAll('#картки > .картка').length, режим: Екран.стан.режим,
            scrollY, поле_верх: поле ? поле.getBoundingClientRect().top : null, слова: поле ? поле.value : null,
            верд_В: (В[0] || {}).верд || null, коментар_В: (В[0] || {}).коментар || null,
            підпис: document.getElementById('обр-підпис').textContent, той_самий_DOM: document.getElementById('к-0') === window.__вузол,
            річ_0_П: ((П.картки[0].речі || [])[0] || {}).id || null,
            бібліотека: свій ? {руки: свій.П.картки.map(k => k.рука), час_збору: !!свій.П.час_збору,
              річ_0: ((свій.П.картки[0].речі || [])[0] || {}).id || null} : null,
            журнал: вердикти.filter(x => x.прогін === window.__прогін).map(x => ({рука: x.рука, впала: !!x.рука_впала,
              верд: x.вердикт_людини || '', коментар: x.коментар || ''}))}; });
        await page.evaluate(() => document.querySelectorAll('#к-0 img').forEach(i => i.loading = 'eager'));
        await wait(() => [...document.querySelectorAll('#к-0 img')].every(i => i.complete), null, {timeout: 30000}).catch(() => {});
        const before = await read(); await page.screenshot({path: path.join(out, 'до-кінця-рук.png')});
        await wait(() => ЗБ.готово, null, {timeout: 1200000, polling: 100});
        await new Promise(r => setTimeout(r, 1500));
        const after = await read(); await page.screenshot({path: path.join(out, 'після-кінця-рук.png')});
        const семпли = await page.evaluate(() => { clearInterval(window.__таймер); return window.__семпли; });
        fs.writeFileSync(path.join(out, 'шов.json'), JSON.stringify({ДО: before, ПІСЛЯ: after, семпли}, null, 1));
        console.log('СТЕНД ШВА: ' + JSON.stringify({ДО: before, ПІСЛЯ: after}));
      })();
      observer.catch(e => console.error('ПОМИЛКА ОБГОРТКИ', e));
      page.waitForFunction = async (fn, ...a) => { const r = await wait(fn, ...a);
        if (String(fn).includes('ЗБ.готово') && await page.evaluate(() => typeof ЗБ !== 'undefined' && ЗБ && ЗБ.готово)) await observer.catch(() => {});
        return r; };
      return page;
    }; return context;
  }; return browser;
};
process.argv = [process.argv[0], path.join(root, 'аудит', 'проби', 'рв6_стенд.js'), 'http://127.0.0.1:8765', site, pyodide, '3'];
const filename = process.argv[1], marker = '  /* 3. промпти між ітераціями';
const source = fs.readFileSync(filename, 'utf8'); if (!source.includes(marker)) throw Error('маркер розділу 3 не знайдено');
const instrumented = source.replace(marker, "  await браузер.close(); кінецьПрогону('ПРИЦІЛЬНО: каталог, руки 1–4, фото, шов', провалів ? 1 : 0); return;\n" + marker);
const helper = new Module(filename, module); helper.filename = filename; helper.paths = Module._nodeModulePaths(path.dirname(filename));
helper._compile(instrumented, filename);
