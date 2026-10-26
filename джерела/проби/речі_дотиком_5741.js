/* Рядок 5741: перелік речей виправляється дотиками в справжньому Chromium 390×844 на зібраній сторінці (Pyodide з її кодом),
   БЕЗ моделі: `_дзвінокП` — заглушка, що читає промпт і чекає, поки її обірве `signal`. Відповідь «речі» — записана (Б4 seed3_02,
   6б seed3_11). Із джерела:  node проби/речі_дотиком_5741.js <html> <відповідь_Б4.json> <відповідь_6б.json> <тека знімків> */
const fs = require('fs'), path = require('path'), assert = require('assert'), { chromium } = require('playwright');
const { чекатиСтан } = require('./очікування.js');
const [, , html, б4Файл, б6бФайл, тека] = process.argv;
fs.mkdirSync(тека, { recursive: true });
const вивід = [];
const лог = (...а) => { const р = а.join(' '); вивід.push(р); console.log(р); };
(async () => {
  const browser = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined, args: ['--no-sandbox'] });
  try {
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, hasTouch: true, reducedMotion: 'reduce' });
    page.setDefaultTimeout(90000);
    await page.route('**/*', r => {
      const u = new URL(r.request().url());
      if (u.hostname === 'probe.invalid' && u.pathname === '/') return r.fulfill({ contentType: 'text/html', body: fs.readFileSync(html, 'utf8') });
      if (u.hostname === 'probe.invalid' || u.hostname === 'model.invalid') return r.abort();
      return r.continue();
    });
    page.on('pageerror', e => лог('PAGEERROR', e.message));
    page.on('console', m => { if (/error|warn/i.test(m.type())) лог('CONSOLE', m.type(), m.text().slice(0, 300)); });
    await page.goto('https://probe.invalid/#model_mova=none');
    await чекатиСтан(page, 'кнопка оц-оцінити готова', () => typeof document.getElementById('оц-оцінити').onclick === 'function');
    /* профіль, міст, фото (полотна — справжні JPEG), заглушка моделі */
    await page.evaluate(async ([б4, б6б]) => {
      КОЛІР = { шкіра: '#f2d6c4', волосся: '#4a4644', очі: '#6b8cae', кільце: null, точки: null };
      for (const [і, v] of [['мр-зріст', 167], ['мр-плечі', 96], ['мр-груди', 92], ['мр-талія', 74], ['мр-стегна', 100]]) document.getElementById(і).value = v;
      МІСТ_П.адреса = 'https://model.invalid/v1'; МІСТ_П.токен = 't';
      const jpeg = (ш, в, малювати) => { const к = document.createElement('canvas'); к.width = ш; к.height = в; малювати(к.getContext('2d'), ш, в);
        return к.toDataURL('image/jpeg', 0.92).split(',')[1]; };
      window.__фото = {
        ф1: jpeg(600, 800, (c, w, h) => { c.fillStyle = '#e9e4dc'; c.fillRect(0, 0, w, h); c.fillStyle = '#6f7348'; c.fillRect(w * .15, h * .1, w * .7, h * .8); }),
        ф2: jpeg(600, 800, (c, w, h) => { c.fillStyle = '#8c96a0'; c.fillRect(0, 0, w, h);
          c.fillStyle = '#e6dfd2'; c.fillRect(w * .12, h * .35, w * .3, h * .5); c.fillStyle = '#1d1c1c'; c.fillRect(w * .58, h * .35, w * .3, h * .5); })};
      window.__виклики = { речі: 0, оцінка: 0, обірвано: 0, вПольоті: 0, ігнорувати: false, відповідьРечі: б4 };
      window.__відповіді = { б4, б6б };
      const текстЗапиту = п => JSON.stringify(п);
      _дзвінокП = async (повідомлення, модель, вибірка, стеля, сигнал) => {
        const т = текстЗапиту(повідомлення), В = window.__виклики;
        const речі = /you list the items that make it up|PHOTO_ITEMS/.test(т);
        let текст;
        if (речі){ В.речі++; текст = В.відповідьРечі; }
        else { В.оцінка++; В.вПольоті++; текст = '{"answer":"Заглушка: образ оцінено.","verdict":"wear_with_change","works":[],"change":[],"unknown":[]}';
          await new Promise((рез, від) => {
            const т0 = setTimeout(рез, 1500);
            if (сигнал) сигнал.addEventListener('abort', () => { if (!В.ігнорувати){ clearTimeout(т0); В.обірвано++; від(new DOMException('aborted', 'AbortError')); } });
          }).finally(() => { В.вПольоті--; }); }
        return new Response(JSON.stringify({ content: [{ type: 'text', text: текст }], usage: { input_tokens: 1, output_tokens: 1 } }),
                            { status: 200, headers: { 'content-type': 'application/json', 'x-model': 'stub' } });
      };
      режим('оцінка');
    }, [fs.readFileSync(б4Файл, 'utf8'), fs.readFileSync(б6бФайл, 'utf8')]);
    const стан = () => page.evaluate(() => ({ рядки: [...document.querySelectorAll('#оц-речі .оц-річ')].map(x => x.dataset.ід + ':' + x.querySelector('.оц-слот').textContent
                                                       + ':' + (x.querySelector('.оц-кр').style.background || '-') + (x.querySelector('.оц-замість') ? ':замість' : '')),
      дотиків: ОЦ.перелік && ОЦ.перелік.звіт.дотиків, перезапущено: ОЦ.перелік && ОЦ.перелік.звіт.суд_перезапущено,
      обірвано: __виклики.обірвано, результат: !!ОЦ.результат, суд: ОЦ.етапи && ОЦ.етапи.суд ? ОЦ.етапи.суд.речі.map(р => р.ід) : null }));
    /* знімок блоку «Що я бачу на фото» (він під фото й питанням, у вікно 390×844 не влазить), картки — усієї сторінки */
    const знімок = async ім => { const б = page.locator('#оц-речі'); const видно = await б.isVisible();
      if (видно){ await б.scrollIntoViewIfNeeded(); await page.waitForTimeout(100); await б.screenshot({ path: path.join(тека, ім) }); }
      else await page.screenshot({ path: path.join(тека, ім), fullPage: true }); };
    const чекати = (назва, умова, арг) => чекатиСтан(page, назва, умова, арг, 90000);
    const сума = () => page.evaluate(() => { const с = ОЦ.етапи.суд; return с ? { рівень: с.рівень, блокери: (с.суд.blockers || []).map(б => б.код).sort(),
      правила: [...new Set((с.суд.findings || []).map(з => з.правило))].sort(), речі: с.речі.map(р => р.ід + ':' + ((р.вимір || {}).hex || '-') + ':' + (р.колір_її_слово ? 'її_слово' : 'вимір')) } : null; });
    const фото = (ід) => page.evaluate(([ід]) => ({ ід, тип: 'image/jpeg', дані: __фото[ід], ширина: 600, висота: 800 }), [ід]);
    const запустити = async (ф, відповідь) => {
      await page.evaluate(async ([ф, відповідь]) => { __виклики.відповідьРечі = відповідь; __виклики.речі = 0; __виклики.оцінка = 0; __виклики.обірвано = 0;
        ОЦ.фото = ф; малюватиОцінкуП(); window.__біг = оцінитиОбразП(); }, [ф, відповідь]);
      await чекати('поява переліку речей', () => !document.getElementById('оц-речі').hidden && document.querySelectorAll('#оц-речі .оц-річ').length > 0);
    };
    const тап = (селектор, позиція) => page.locator(селектор).first().tap(позиція ? { position: позиція } : undefined);
    /* дотик пальцем по фото в редакторі: список перемальовується часто, тож координати беремо свіжі й б'ємо touchscreen */
    const торкнутиФото = async (ід, fx, fy) => {
      const р = await page.evaluate(ід => { const і = document.querySelector('.оц-ред .оц-дотик-фото img[data-фото="' + ід + '"]');
        і.scrollIntoView({ block: 'center' }); const б = і.getBoundingClientRect(); return { x: б.x, y: б.y, w: б.width, h: б.height }; }, ід);
      await page.waitForTimeout(150);
      const р2 = await page.evaluate(ід => { const б = document.querySelector('.оц-ред .оц-дотик-фото img[data-фото="' + ід + '"]').getBoundingClientRect();
        return { x: б.x, y: б.y, w: б.width, h: б.height }; }, ід);
      await page.touchscreen.tap(р2.x + р2.w * fx, р2.y + р2.h * fy);
    };
    const чекатиОцінкуВПольоті = () => чекати('оцінка в польоті', () => __виклики.вПольоті > 0);
    const чекатиКартку = () => чекати('картка готова й суд готовий', () => !!ОЦ.результат && !ОЦ.перелік.біжить && !!(ОЦ.етапи && ОЦ.етапи.суд && ОЦ.етапи.суд.речі));

    /* ═══ Б4 (seed3_02): ✕ ф2 (1) · «+ Річ» (2) · «Взуття» (3) · кружечок «вершковий» (4) · «Так» (5) ═══ */
    лог('── Б4');
    await запустити([await фото('ф1'), await фото('ф2')], fs.readFileSync(б4Файл, 'utf8'));
    let с = await стан(); лог('перелік:', JSON.stringify(с.рядки)); assert.strictEqual(с.рядки.length, 2);
    await чекатиОцінкуВПольоті(); await чекати('наявність ОЦ.етапи.суд', () => !!ОЦ.етапи.суд);
    const доБ4 = await сума(); лог('ДО суд:', JSON.stringify(доБ4));
    await знімок('б4_1_перелік.png');
    await тап('#оц-речі .оц-річ[data-ід="ф2"] .оц-х');                       // 1
    await чекати('одна дія в звіті після хрестика', () => ОЦ.перелік.звіт.дії.length === 1);
    с = await стан(); лог('після ✕:', JSON.stringify(с)); assert.strictEqual(с.рядки.length, 1); assert.strictEqual(с.перезапущено, 1);
    assert.ok(с.обірвано >= 1, 'старий виклик ОЦІНКИ мав обірватись: ' + с.обірвано); assert.strictEqual(с.результат, false);
    await чекатиОцінкуВПольоті();
    await тап('#оц-плюс-річ');                                                // 2
    await знімок('б4_2_плюс_річ.png');
    await тап('#оц-додати .чип:has-text("Взуття")');                          // 3
    await чекати('поява н1 у переліку', () => ОЦ.перелік.речі.some(р => р.ід === 'н1'));
    с = await стан(); лог('після «Взуття»:', JSON.stringify(с.рядки)); assert.ok(с.рядки.some(р => /^н1:Взуття/.test(р)));
    await чекатиОцінкуВПольоті();
    await знімок('б4_3_редактор.png');
    await тап('.оц-ред .оц-коло[data-код="cream"]');                          // 4
    await чекати('колір вершковий для н1', () => ОЦ.перелік.речі.find(р => р.ід === 'н1').колір === 'вершковий');
    await чекатиКартку();
    с = await стан(); лог('перед «Так»:', JSON.stringify(с.рядки), 'перезапущено', с.перезапущено, 'обірвано', с.обірвано);
    const післяБ4 = await сума(); лог('ПІСЛЯ суд:', JSON.stringify(післяБ4));
    assert.ok(!післяБ4.речі.some(р => /^ф2/.test(р)), 'ф2 лишилась в суді'); assert.ok(післяБ4.речі.some(р => /^н1:-:її_слово/.test(р)), 'н1 не словом: ' + післяБ4.речі);
    await знімок('б4_4_перед_так.png');
    await тап('#оц-так');                                                     // 5
    await чекати('поява оц-картка', () => !!document.getElementById('оц-картка'));
    const звітБ4 = await page.evaluate(() => JSON.parse(JSON.stringify(ОЦ.етапи.підтвердження)));
    лог('етапи.підтвердження:', JSON.stringify(звітБ4));
    assert.strictEqual(звітБ4.дотиків, 5); assert.strictEqual(звітБ4.показано, 2); assert.ok(звітБ4.дії.length >= 3 && звітБ4.суд_перезапущено >= 3);
    assert.ok(звітБ4.суд_до_виправлення && звітБ4.суд_до_виправлення.рівень, 'суд до виправлення мав записатись');
    await знімок('б4_5_картка.png');
    await page.evaluate(() => window.__біг);

    /* ═══ відкидання результату: старий виклик НЕ слухає signal — його відповідь усе одно не стає карткою ═══ */
    лог('── результат старого ланцюга відкидається');
    await запустити([await фото('ф1'), await фото('ф2')], fs.readFileSync(б4Файл, 'utf8'));
    await page.evaluate(() => { __виклики.ігнорувати = true; }); await чекатиОцінкуВПольоті();
    await тап('#оц-речі .оц-річ[data-ід="ф2"] .оц-х');
    await чекати('перезапуск суду === 1', () => ОЦ.перелік.звіт.суд_перезапущено === 1);
    await page.evaluate(() => { __виклики.ігнорувати = false; });
    await чекатиКартку();
    const відкинуто = await page.evaluate(() => ({ речі: ОЦ.результат.суд.речі.map(р => р.ід), обірвано: __виклики.обірвано }));
    лог('після відкинутого:', JSON.stringify(відкинуто)); assert.deepStrictEqual(відкинуто.речі, ['ф1']);
    await тап('#оц-так'); await чекати('завершення оцінки перед 6б', () => !ОЦ.іде); await page.evaluate(() => window.__біг);

    /* ═══ дотик у ТЛО ф2 (#8c96a0) і виправлення кружечком ═══ */
    лог('── дотик у тло ф2');
    await запустити([await фото('ф1'), await фото('ф2')], fs.readFileSync(б4Файл, 'utf8'));
    await чекатиОцінкуВПольоті();
    await тап('#оц-плюс-річ'); await тап('#оц-додати .чип:has-text("Взуття")');
    await чекати('поява н1 у переліку', () => ОЦ.перелік.речі.some(р => р.ід === 'н1'));
    await торкнутиФото('ф2', .05, .05);                                          // тло ф2
    await чекати('дотик === true для н1', () => ОЦ.перелік.речі.find(р => р.ід === 'н1').дотик === true);
    await чекати('hex н1 === null (тло)', () => ОЦ.перелік.hex['н1'] === null);                            // рядок 5810: у тлі виміру нема, кружечок порожній
    const тло = await page.evaluate(() => ({ hex: ОЦ.перелік.hex['н1'], рамка: ОЦ.перелік.речі.find(р => р.ід === 'н1').рамка }));
    лог('дотик у тло → кружечок:', JSON.stringify(тло)); assert.strictEqual(тло.hex, null);
    await знімок('тло_1_промах.png');
    await чекатиКартку();
    лог('суд з промахом:', JSON.stringify((await сума()).речі));
    assert.strictEqual(await page.evaluate(() => ОЦ.етапи.суд.речі.find(р => р.ід === 'н1').вимір.причина), 'touch_on_background');
    await тап('.оц-ред .оц-коло[data-код="cream"]');                            // виправлення кружечком
    await чекати('колір вершковий для н1', () => ОЦ.перелік.речі.find(р => р.ід === 'н1').колір === 'вершковий');
    await чекати('hex н1 не сірий #8c96a0', () => ОЦ.перелік.hex['н1'] && ОЦ.перелік.hex['н1'] !== '#8c96a0');
    await чекатиКартку();
    const виправлено = await page.evaluate(() => ({ hex: ОЦ.перелік.hex['н1'], суд: ОЦ.етапи.суд.речі.find(р => р.ід === 'н1') }));
    лог('після кружечка:', JSON.stringify({ hex: виправлено.hex, колір: виправлено.суд.колір, слово: !!виправлено.суд.колір_її_слово,
      вимір: (виправлено.суд.вимір || {}).причина, ненадійний: ((виправлено.суд.вимір || {}).ненадійний || {}).hex }));
    assert.ok(виправлено.суд.колір_її_слово, 'її слово мусило перемогти вимір тла'); assert.strictEqual(виправлено.суд.колір, 'вершковий');
    assert.strictEqual(((виправлено.суд.вимір || {}).ненадійний || {}).hex, '#8c96a0');
    await знімок('тло_2_кружечок.png');
    /* дотик у вершковий ботильйон: вимір у межах слова лишається */
    await торкнутиФото('ф2', .27, .6);
    await чекати('рамка н1 змістилась після дотику в ботильйон', () => ОЦ.перелік.речі.find(р => р.ід === 'н1').рамка.ліво > 100);
    await чекати('картка готова після дотику в ботильйон', () => !!ОЦ.результат && !ОЦ.перелік.біжить && !!(ОЦ.етапи && ОЦ.етапи.суд && ОЦ.етапи.суд.речі && ОЦ.етапи.суд.речі.some(р => р.ід === 'н1' && (р.вимір || {}).причина !== 'touch_on_background')));
    const вБотильйон = await page.evaluate(() => ({ hex: ОЦ.перелік.hex['н1'], вимір: ОЦ.етапи.суд.речі.find(р => р.ід === 'н1').вимір }));
    лог('дотик у вершковий ботильйон:', JSON.stringify({ hex: вБотильйон.hex, слово: (вБотильйон.вимір || {}).слово, спір: (вБотильйон.вимір || {}).спір, гілка: (вБотильйон.вимір || {}).гілка }));
    await тап('#оц-так'); await page.evaluate(() => window.__біг);

    /* ═══ 6б (seed3_11): 8 рядків → 4; ботильйони 3+2, сорочка 3, «Так» 1 = 9 ═══ */
    лог('── 6б');
    await запустити([await фото('ф1'), await фото('ф2')], fs.readFileSync(б6бФайл, 'utf8'));
    с = await стан(); лог('перелік:', JSON.stringify(с.рядки)); assert.strictEqual(с.рядки.length, 4);
    await чекатиОцінкуВПольоті(); await чекати('наявність ОЦ.етапи.суд', () => !!ОЦ.етапи.суд);
    const до6 = await сума(); лог('ДО суд:', JSON.stringify(до6));
    await знімок('6б_1_перелік.png');
    await тап('#оц-речі .оц-річ[data-ід="ф2"]');                                // 1 (рядок «верх» бежевий)
    await тап('.оц-ред .чип:has-text("Взуття")');                               // 2
    await чекати('слот взуття для ф2', () => ОЦ.перелік.речі.find(р => р.ід === 'ф2').слот === 'взуття');
    await тап('.оц-ред .оц-коло[data-код="cream"]');                            // 3
    await чекати('колір вершковий для ф2', () => ОЦ.перелік.речі.find(р => р.ід === 'ф2').колір === 'вершковий');
    await тап('#оц-речі .оц-річ[data-ід="ф2·2"]');                              // 4
    await тап('.оц-ред .чип:has-text("Взуття")');                               // 5
    await чекати('слот взуття для ф2·2', () => ОЦ.перелік.речі.find(р => р.ід === 'ф2·2').слот === 'взуття');
    await знімок('6б_2_ботильйони.png');
    await тап('#оц-плюс-річ');                                                  // 6
    await тап('#оц-додати .чип:has-text("Верх")');                              // 7
    await чекати('поява н1 у переліку', () => ОЦ.перелік.речі.some(р => р.ід === 'н1'));
    await тап('.оц-ред .оц-коло[data-код="beige"]');                            // 8
    await чекати('колір бежевий для н1', () => ОЦ.перелік.речі.find(р => р.ід === 'н1').колір === 'бежевий');
    await чекатиКартку();
    с = await стан(); лог('перед «Так»:', JSON.stringify(с.рядки));
    const після6 = await сума(); лог('ПІСЛЯ суд:', JSON.stringify(після6));
    await тап('#оц-так');                                                       // 9
    await чекати('поява оц-картка', () => !!document.getElementById('оц-картка'));
    const звіт6 = await page.evaluate(() => JSON.parse(JSON.stringify(ОЦ.етапи.підтвердження)));
    лог('етапи.підтвердження: дотиків', звіт6.дотиків, 'дій', звіт6.дії.length, 'перезапущено', звіт6.суд_перезапущено, 'втрачено_мс', звіт6.втрачено_мс);
    assert.strictEqual(звіт6.дотиків, 9); assert.strictEqual(звіт6.показано, 4);
    await знімок('6б_3_картка.png');
    await page.evaluate(() => window.__біг);
    fs.writeFileSync(path.join(тека, 'вивід.txt'), вивід.join('\n') + '\n');
    лог('OK');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exit(1); });
