/* ПРОБА (28.09.2026, наряд І-1): чи вміщуються ЧОТИРИ вкладки панелі швидкого доступу
   (Сценарій · Образи · Оцінити · Профіль) на телефонних ширинах, і чи нічого не обрізано.
   Друкує факт — рамку кожної вкладки, чи напис в один рядок, чи смуга не ширша за вікно —
   і кладе знімки САМОЇ ПАНЕЛІ й ВІКНА, щоб їх дивились очима (CLAUDE.md п.10).

   Запуск:  CHROMIUM=/opt/pw-browsers/chromium NODE_PATH=джерела/node_modules \
              node аудит/проби/панель_вкладки.js <корінь зі зібраним index.html> <тека знімків> [сід]
   Pyodide й каталог не потрібні: міряється розкладка панелі, не збирання. */
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');
const КОРІНЬ = process.argv[2] || process.cwd();
const ЗНІМКИ = process.argv[3] || null;
const СІД = Number(process.argv[4] || process.env.SEED || 3);
const ВІКНА = [{width: 390, height: 844}, {width: 360, height: 800}];
const с = мс => new Promise(р => setTimeout(р, мс));
let збоїв = 0;
const ф = (що, добре, дані) => { if (!добре) збоїв++;
  console.log('  ' + (добре ? '✓' : '✗') + ' ' + що + (дані === undefined ? '' : ' · ' + JSON.stringify(дані))); };

(async () => {
  if (ЗНІМКИ) fs.mkdirSync(ЗНІМКИ, {recursive: true});
  const бр = await chromium.launch({executablePath: process.env.CHROMIUM || undefined});
  for (const вікно of ВІКНА){
    const ім = вікно.width + 'x' + вікно.height;
    console.log('\n' + ім + ' (сід ' + СІД + ')');
    const кон = await бр.newContext({viewport: вікно, deviceScaleFactor: 2});
    const стор = await кон.newPage();
    await стор.goto('file://' + path.join(КОРІНЬ, 'index.html') + '#міст=https://m.workers.dev&т=tok-a1&модель_мови=нема');
    await стор.waitForFunction(() => typeof РЕЖИМ !== 'undefined', null, {timeout: 60000});
    /* Шлях жінки: три кроки знайомства. Кольори кладемо як після зчитаного портрета —
       Pyodide тут не підіймається, а розкладці панелі портрет ні до чого. */
    await стор.evaluate(() => { КОЛІР = {шкіра:'#f2d6c4', волосся:'#4a4644', очі:'#6b8cae', кільце:null, точки:null}; });
    await стор.click('#н-далі'); await с(120);
    await стор.click('#н-далі'); await с(120);
    for (const [і, v] of [['мр-зріст',167],['мр-плечі',96],['мр-груди',92],['мр-талія',74],['мр-стегна',100]])
      await стор.fill('#' + і, String(v));
    await стор.click('#н-далі'); await с(400);
    for (const екран of ['сценарій', 'оцінка']){
      if (екран === 'оцінка'){ await стор.click('#вк-оцінка'); await с(300); }
      const м = await стор.evaluate(() => {
        const н = document.getElementById('вкладки');
        const кн = [...н.querySelectorAll('button')];
        return {режим: РЕЖИМ, видно: !!н.offsetParent, смуга: Math.round(н.getBoundingClientRect().width),
                вікно: window.innerWidth, обрізано_смугу: н.scrollWidth > н.clientWidth,
                тут: кн.filter(б => б.classList.contains('тут')).map(б => б.id),
                вкладки: кн.map(б => { const п = б.querySelector('span'), р = б.getBoundingClientRect();
                  const рп = п.getBoundingClientRect();
                  return {ід: б.id, напис: п.textContent.trim(), ш: Math.round(р.width), в: Math.round(р.height),
                          напис_ш: Math.round(рп.width), рядків: Math.round(рп.height / parseFloat(getComputedStyle(п).lineHeight || 14)),
                          обрізано: п.scrollWidth > п.clientWidth + 1, за_краєм: р.left < -0.5 || р.right > window.innerWidth + 0.5}; })};
      });
      console.log('   ' + екран + ': ' + JSON.stringify(м));
      ф(ім + ' · ' + екран + ': вкладок чотири, у своєму порядку',
        м.вкладки.map(в => в.ід).join(',') === 'вк-сценарій,вк-образи,вк-оцінка,пф-кнопка', м.вкладки.map(в => в.напис));
      ф(ім + ' · ' + екран + ': смуга не ширша за вікно і не прокручується',
        м.видно && м.смуга <= м.вікно && !м.обрізано_смугу, {смуга: м.смуга, вікно: м.вікно});
      ф(ім + ' · ' + екран + ': жоден напис не обрізано, кожен в один рядок, ніхто не виїхав за край',
        м.вкладки.every(в => !в.обрізано && !в.за_краєм && в.рядків <= 1), м.вкладки.map(в => [в.напис, в.ш, в.напис_ш, в.рядків]));
      ф(ім + ' · ' + екран + ': поточна вкладка — ' + (екран === 'оцінка' ? 'вк-оцінка' : 'вк-сценарій'),
        м.тут.join(',') === (екран === 'оцінка' ? 'вк-оцінка' : 'вк-сценарій'), м.тут);
      if (екран === 'сценарій')
        ф('390/360 · сценарій: старої кнопки «Оціни мій образ» на екрані нема (вхід один)',
          await стор.evaluate(() => !document.getElementById('оц-кнопка') && !document.getElementById('оц-вхід-місце')), null);
      if (ЗНІМКИ){
        for (const [сел, хвіст] of [['#вкладки', 'panel'], [null, 'vikno']]){
          const ш = path.join(ЗНІМКИ, 'vkladky_' + ім + '_' + (екран === 'оцінка' ? 'otsinyty' : 'scenarii') + '_' + хвіст + '_seed' + СІД + '.png');
          await (сел ? await стор.$(сел) : стор).screenshot({path: ш, ...(сел ? {} : {fullPage: false})});
          console.log('   знімок:', ш, fs.statSync(ш).size, 'Б');
        }
      }
    }
    await кон.close();
  }
  await бр.close();
  console.log('\n' + (збоїв ? 'ЗБОЇВ: ' + збоїв : 'ПАНЕЛЬ: усе вміщується'));
  process.exit(збоїв ? 1 : 0);
})();
