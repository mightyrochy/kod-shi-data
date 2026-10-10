/* Рядки 4103, 4106 · картка у справжньому Chromium на ЗІБРАНІЙ сторінці: що стоїть у рядку «Де» картки сценарію для
   місця поза плитками і що стоїть у рядках речей, коли шар не переклав назву (ЖИВІ-17 №5, №8, №11 рука 4).
   Запуск: NODE_PATH=<playwright> node аудит/проби/картка_тексти_4.js <тека з index.html> <тека pyodide> [знімок.png]
   Друкує JSON: «Де» і «Додати» трьох паспортів; рядки речей картки руки 4 після `мовоюКарткуП` із відповіддю шару,
   записаною в №11 («… із золота 18k»), і з англійською назвою, що лишилась; початок опису, де в першому відрізку стоїть «18k». */
const { chromium } = require('playwright'), fs = require('fs'), path = require('path');
const [КОРІНЬ, PYODIDE, ЗНІМОК] = process.argv.slice(2), БАЗА = 'http://127.0.0.1:8765';
(async () => {
  const браузер = await chromium.launch({ executablePath: process.env.CHROMIUM || undefined });
  const стор = await (await браузер.newContext({ viewport: { width: 390, height: 844 } })).newPage();
  await стор.route('**/*', async r => {
    const u = new URL(r.request().url());
    if (u.origin === БАЗА) return r.fulfill({ status: 200, contentType: 'text/html; charset=utf-8', body: fs.readFileSync(path.join(КОРІНЬ, 'index.html')) });
    if (/cdn\.jsdelivr\.net\/pyodide/.test(u.href)) {
      const ф = path.join(PYODIDE, u.pathname.split('/').pop());
      return fs.existsSync(ф) ? r.fulfill({ status: 200, body: fs.readFileSync(ф), contentType: ф.endsWith('.wasm') ? 'application/wasm' : ф.endsWith('.json') ? 'application/json' : 'application/javascript' }) : r.abort();
    }
    return r.abort();
  });
  await стор.goto(БАЗА + '/index.html');
  await стор.waitForFunction(() => typeof малюватиКарткуСценарію === 'function' && typeof рендер === 'function');
  const де = await стор.evaluate(() => {
    режим('сценарій');
    return [['ресторан_високий', 'Новорічна вечірка в ресторані'], ['домашня_вечірка', 'вечірка вдома'], ['ресторан_районний', 'контроль: плитка']].map(([місце, що]) => {
      $('сц-нагода').value = 'свято'; $('сц-місце').value = '';
      ПАСПОРТ_П = { джерело: 'модель', нагода: 'свято', місце, ошатність: [6, 8], джерело_полів: { нагода: 'розмова', місце: 'розмова', ошатність: 'розмова' },
                    вето: { типи: [], тканини: [], принти: [], кольори: [], зони: [] } };
      ВИПАДОК_ЗМІНЕНО_П = false; малюватиКарткуСценарію();
      return { що, місце, де: $('зн-місце').textContent, рядок_видно: !$('зн-місце').closest('.ряд-паспорта').hidden, додати: $('сц-ще').hidden ? null : $('зн-ще').textContent };
    });
  });
  console.log('ДЕ ' + JSON.stringify(де, null, 1));
  const речі = await стор.evaluate(async () => {
    const назви = ['Шовкова туніка з ледь помітним блиском', 'Вовняні штани широкого крою', 'Шкіряні туфлі-човники', 'Штучне хутро у вигляді шалі', 'Pearl-droplet pendant necklace'];
    const шар = { 'річ.4.назва': 'Перлова підвіска з ланцюжком із золота 18k' };
    const вих = {};
    for (const [ім, відповідь] of [['з_18k', шар], ['англійська_лишилась', { 'річ.4.назва': 'Pearl necklace' }]]) {
      мовоюП = async (т) => ({ тексти: Object.fromEntries(Object.keys(т).map(к => [к, відповідь[к] || т[к]])), записи: [{ де: 'проба' }] });
      const к = { рука: '4', текст: '', речі: назви.map((н, і) => ({ id: 'м-00' + (і + 1), назва: н, слот: ['верх', 'низ', 'взуття', 'верхній_шар', 'прикраса'][і], вигадана: true })) };
      await мовоюКарткуП(к, 'hand_4');
      П = { збірка: 'проба', каталог: '', профіль: '', картки: [к] }; рендер();
      вих[ім] = { мова_не_перекладено: к.мова_не_перекладено || [], рядки: Array.from(document.querySelectorAll('#картки .список .річ .н')).map(н => н.textContent.trim()) };
    }
    return вих;
  });
  console.log('РЕЧІ ' + JSON.stringify(речі, null, 1));
  console.log('ОПИС ' + JSON.stringify(await стор.evaluate(() => безЗайвоїЛатинкиП('Перлова підвіска з ланцюжком із золота 18k, ніжний мінімалістичний дизайн.', new Set()))));
  if (ЗНІМОК) { await стор.evaluate(() => document.querySelector('#картки .список').scrollIntoView()); await стор.waitForTimeout(1500); await стор.screenshot({ path: ЗНІМОК }); }
  await браузер.close();
})();
