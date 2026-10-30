/* Офлайн-знімок картки сценарію на голові PR #2274. */
const fs = require('fs'), path = require('path');
const корінь = path.resolve(process.argv[2]), тека = __dirname;
const {chromium} = require(path.join(корінь, 'джерела/node_modules/playwright'));
const {прочитатиДовідникJSON, підставитиШаблон, зібратиШаблонПоказу} =
  require(path.join(корінь, 'джерела/показ_шаблон.js'));
(async () => {
  const код = path.join(корінь, 'джерела');
  const html = підставитиШаблон(зібратиШаблонПоказу(path.join(код, 'показ.html')), {
    __МОДУЛІ_ПОКАЗУ__: 'офлайн', __ЗБІРКА_ПОКАЗУ__: 'перевірка-2274',
    __ВІДБИТОК__: 'перевірка-2274', __ФІД_ПОКАЗУ__: '', __КАТАЛОГ_ПОКАЗУ__: '',
    __ДОВІДНИК_ПОКАЗУ__: прочитатиДовідникJSON(код)
  });
  const браузер = await chromium.launch({headless: true, args: ['--disable-gpu'],
    ...(process.env.CHROME_PATH ? {executablePath: process.env.CHROME_PATH} : {})});
  try {
    const стор = await браузер.newPage({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
    await стор.route('**/*', маршрут => маршрут.abort());
    await стор.setContent(html, {waitUntil: 'domcontentloaded'});
    const факт = await стор.evaluate(() => {
      режим('сценарій');
      ПАСПОРТ_П = {джерело: 'модель', подія: 'Співбесіда в офісі', нагода: 'співбесіда',
        місце: 'офіс', ошатність: [7, 7], причина_ошатності: 'evaluated', джерело_полів: {ошатність: 'розмова'}};
      ВИПАДОК_ЗМІНЕНО_П = false;
      застосуватиПаспортДоЕкрана(ПАСПОРТ_П); малюватиКарткуСценарію();
      document.querySelectorAll('[id^="е-"]').forEach(е => {
        if (е.id !== 'е-випадок' && е.classList.contains('екран')) е.style.display = 'none';
      });
      const картка = document.getElementById('сц-картка');
      картка.hidden = false; картка.scrollIntoView({block: 'center'});
      return {розмір: [innerWidth, innerHeight], текст: картка.innerText};
    });
    await стор.screenshot({animations: 'disabled', path: path.join(тека, 'картка.png')});
    fs.writeFileSync(path.join(тека, 'знімок.json'), JSON.stringify(факт, null, 2));
    console.log(JSON.stringify(факт));
  } finally { await браузер.close(); }
})().catch(п => { console.error(п); process.exitCode = 1; });
