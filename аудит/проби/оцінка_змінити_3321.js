/* Рядок 3321: стилі блоку «Що змінити» на картці оцінки у справжньому Chromium, на ЗІБРАНІЙ сторінці.
   Мережі нема. Картку малює сама сторінка (`малюватиКарткуОцінкиП`) з вигаданою відповіддю; `getComputedStyle`
   рядків блоку міряється РАЗ одразу після знімка (як стенд: малювання → знімок) і РАЗ через 1,5 с, поруч —
   текст «Що вдало» і предки рядка (opacity, колір, тло, анімація). Знімок картки — другим аргументом.
   Запуск: NODE_PATH=джерела/node_modules node аудит/проби/оцінка_змінити_3321.js <index.html> [знімок.png] */
const { chromium } = require('playwright');
const [, , СТОРІНКА, ЗНІМОК] = process.argv;
(async () => {
  const б = await chromium.launch({ headless: true, executablePath: process.env.CHROMIUM || undefined });
  const с = await (await б.newContext({ viewport: { width: 390, height: 844 } })).newPage();
  await с.route(u => !u.href.startsWith('file:'), r => r.abort());
  await с.goto('file://' + require('path').resolve(СТОРІНКА), { waitUntil: 'load', timeout: 180000 });
  await с.waitForFunction(() => typeof малюватиКарткуОцінкиП === 'function' && typeof ОЦ !== 'undefined', null, { timeout: 120000 });
  await с.waitForTimeout(4000); // запуск сторінки сам викликає режим('старт') — після нього вмикаємо екран
  await с.evaluate(() => { режим('оцінка'); window.scrollTo(0, 0); ОЦ.фото = [];
    const р = (ід, т, н) => ({ ід, текст: т, зміна: { звідки: 'shop', річ: { назва: н, крамниця: 'крамниця.ua', ціна: 1900 } } });
    ОЦ.результат = { сценарій: {}, суд: { речі: [] }, картка: { відповідь: 'Кольори поєднуються добре.', вдало: [{ текст: 'Куртка гарно стоїть до обличчя.' }], не_знаю: [],
      змінити: [р('c1', 'Бежева спідниця продовжить теплі відтінки куртки.', 'Спідниця бежева'), р('c2', 'Або атласна спідниця міді.', 'Спідниця атласна')] } };
    малюватиКарткуОцінкиП(); window.__t0 = performance.now(); });
  await (await с.$('#оц-картка')).screenshot({ path: ЗНІМОК || '/dev/null' });
  const міряти = () => с.evaluate(() => { const ст = е => { const k = getComputedStyle(e_ = е); return { opacity: +(+k.opacity).toFixed(2), color: k.color, bg: k.backgroundColor, anim: k.animationName }; };
    const ряди = [...document.querySelectorAll('.оц-зміни .річ')], текст = ряди[0].querySelector('.назва'), ланц = [];
    for (let x = текст; x && x !== document.body; x = x.parentElement) ланц.push((x.className || x.tagName) + ' op=' + getComputedStyle(x).opacity);
    return { мс_від_малювання: Math.round(performance.now() - window.__t0), річ_opacity: ряди.map(r => +(+getComputedStyle(r).opacity).toFixed(2)), річ_анімація: getComputedStyle(ряди[0]).animationName,
      текст_блоку: ст(текст), текст_вдало: ст(document.querySelector('.оц-вдало div')), ланцюг_opacity: ланц.join(' ‹ ') }; });
  const рано = await міряти(); await с.waitForTimeout(1500); const сталий = await міряти();
  console.log(JSON.stringify({ одразу_після_знімка: рано, через_1500мс: сталий }, null, 1));
  await б.close();
})();
