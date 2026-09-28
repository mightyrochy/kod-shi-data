/* ПРОБА (28.09.2026, доповнення до наряду І-1): що саме жінка бачить, коли на екрані
   «Оціни мій образ» відкриває список «Нагода». Друкує перелік рядок за рядком — групу,
   слово й те, чи це слово людське, — і знімає список РОЗГОРНУТИМ, щоб його дивились очима.

   Нативний список `<select>` headless-Chromium знімком не бере: його малює не сторінка,
   а оболонка. Тому на час знімка полю ставиться `size` — той самий вузол і ті самі рядки,
   лише розгорнуті в сторінці. Жодного іншого втручання в показ проба не робить.

   Запуск:  CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=джерела/node_modules \
              node аудит/проби/нагода_список.js <корінь зі зібраним index.html> <тека знімків> <мітка>
   `<мітка>` йде в назву знімка (напр. `do` / `pislia`). */
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
const КОРІНЬ = process.argv[2] || process.cwd();
const ЗНІМКИ = process.argv[3] || null;
const МІТКА = process.argv[4] || 'zараз';
const с = мс => new Promise(р => setTimeout(р, мс));

(async () => {
  if (ЗНІМКИ) fs.mkdirSync(ЗНІМКИ, {recursive: true});
  const бр = await chromium.launch({executablePath: process.env.CHROMIUM || undefined});
  const кон = await бр.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 2});
  const стор = await кон.newPage();
  await стор.goto('file://' + path.join(КОРІНЬ, 'index.html') + '#міст=https://m.workers.dev&т=tok-a1&модель_мови=нема');
  await стор.waitForFunction(() => typeof РЕЖИМ !== 'undefined', null, {timeout: 60000});
  await стор.evaluate(() => { КОЛІР = {шкіра:'#f2d6c4', волосся:'#4a4644', очі:'#6b8cae', кільце:null, точки:null}; });
  await стор.click('#н-далі'); await с(120);
  await стор.click('#н-далі'); await с(120);
  for (const [і, v] of [['мр-зріст',167],['мр-плечі',96],['мр-груди',92],['мр-талія',74],['мр-стегна',100]])
    await стор.fill('#' + і, String(v));
  await стор.click('#н-далі'); await с(400);
  /* Вхід в оцінку: вкладка панелі, а де її ще нема (збірка «до») — стара кнопка. */
  await стор.evaluate(() => { const в = document.getElementById('вк-оцінка') || document.getElementById('оц-кнопка');
                              if (в) в.click(); else режим('оцінка'); });
  await с(400);
  const список = await стор.evaluate(() => {
    const н = document.getElementById('оц-нагода');
    const рядки = [];
    for (const д of н.children){
      if (д.tagName === 'OPTGROUP'){ рядки.push({група: д.label});
        for (const о of д.children) рядки.push({група: д.label, слово: о.textContent, ключ: о.value}); }
      else рядки.push({слово: д.textContent, ключ: д.value});
    }
    return {груп: н.querySelectorAll('optgroup').length, рядків: н.querySelectorAll('option').length, рядки};
  });
  const слова = список.рядки.filter(р => р.слово !== undefined);
  const голих = слова.filter(р => р.ключ && (р.слово.indexOf('_') >= 0 || р.слово === р.ключ.replace(/_/g, ' ')));
  const змалої = слова.filter(р => р.слово && /^[а-яіїєґ]/.test(р.слово));
  console.log('груп: %d · рядків: %d · слів із голого ключа: %d · з малої літери: %d',
              список.груп, список.рядків, голих.length, змалої.length);
  let ост = null;
  for (const р of список.рядки){
    if (р.слово === undefined){ console.log('  ── ' + р.група); ост = р.група; continue; }
    console.log('     ' + (р.група && р.група !== ост ? '' : '') + р.слово + (р.ключ ? '   [' + р.ключ + ']' : '   [—]'));
  }
  if (голих.length) console.log('  ГОЛИЙ КЛЮЧ У СЛОВАХ: ' + голих.map(р => р.слово).join(', '));
  if (змалої.length) console.log('  З МАЛОЇ ЛІТЕРИ: ' + змалої.map(р => р.слово).join(', '));
  if (ЗНІМКИ){
    /* `size` розгортає той самий список у сторінці — інакше знімок дає лише згорнуте поле */
    await стор.evaluate(н => { const е = document.getElementById('оц-нагода');
      е.size = н; е.scrollIntoView({block: 'center'}); }, Math.min(список.рядків + список.груп, 26));
    await с(200);
    const ш = path.join(ЗНІМКИ, 'nahoda_spysok_' + МІТКА + '_390x844.png');
    await (await стор.$('#оц-нагода')).screenshot({path: ш});
    console.log('   знімок:', ш, fs.statSync(ш).size, 'Б');
    await стор.evaluate(() => { document.getElementById('оц-нагода').removeAttribute('size'); });
  }
  await бр.close();
  process.exit(0);
})();
