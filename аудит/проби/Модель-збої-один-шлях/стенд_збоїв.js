/* СТЕНД «ВИД ЗБОЮ × ЕКРАН» (наряд «Модель-збої-один-шлях», мірило «на екрані»): зібрана сторінка (`index.html`) у
   Chromium телефона 390×844, а `/міст` — заглушка, що на КОЖЕН виклик моделі відповідає одним видом збою, як справжній
   міст: `кредити` — 402 `credits_exhausted`, `час` — 504, `вхід` — 400 invalid_request_error, `мережа` — обрив
   з'єднання. Справжнього моста й ключа тут нема; Pyodide — з диска (`стенд_pyodide_кеш.sh`).
   Кожен екран — своя сцена: що жінка бачить на місці відповіді, скільки викликів пішло до моста за сцену, що ліг у
   журнал збоїв (`ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П`), і знімок 390×844. Затримки повтору сторінки стиснуто до 0,3/0,6 с, щоб 504
   ДО (повтор 20 і 60 с) не тягнувся хвилинами: число повторів від цього не міняється.
   Знайомство — руками, як `аудит/проби/модель-текст-claude/скрипти/стенд_моста.js`; картку стенд кладе сам (фікстура
   `тест_показу.js`, розділ 1д-6а) і малює її `рендерКартку` — збирання образів не цей наряд. Рядки помади й
   повідомлення картки — текст, який сторінка віддала для рядка (`мовоюПомадиП`, `повідомленнямП`), у вузлі стенда.
   Запуск: NODE_PATH=/opt/node-tools/node_modules node стенд_збоїв.js <тека з index.html> <тека виводу> <вид> [/tmp/pyodide] */
const {chromium} = require('playwright');
const fs = require('fs'), path = require('path');
const [КОРІНЬ, ВИХІД, ВИД = 'кредити', ТЕКА_PYODIDE = '/tmp/pyodide'] = process.argv.slice(2);
const БАЗА = 'http://127.0.0.1:8798';
const с = мс => new Promise(р => setTimeout(р, мс));
const ВІДПОВІДІ = {
  кредити: {status: 402, body: {error: {type: 'credits_exhausted', message: 'API credits for this month are exhausted'}}},
  час: {status: 504, body: {error: {type: 'timeout', message: 'upstream did not answer in 85 s'}}},
  вхід: {status: 400, body: {type: 'error', error: {type: 'invalid_request_error', message: 'Unable to download the file'}}},
};
if (!ВІДПОВІДІ[ВИД] && ВИД !== 'мережа') throw new Error('вид: кредити | час | вхід | мережа');

(async () => {
  fs.mkdirSync(ВИХІД, {recursive: true});
  const браузер = await chromium.launch({headless: true});
  const стор = await (await браузер.newContext({viewport: {width: 390, height: 844}, isMobile: true, hasTouch: true,
    deviceScaleFactor: 2, locale: 'uk-UA', timezoneId: 'Europe/Kyiv'})).newPage();
  const консоль = []; стор.on('pageerror', e => консоль.push('pageerror: ' + String(e).slice(0, 300)));
  let викликів = 0;
  const цеМіст = u => decodeURIComponent(u.pathname).endsWith('/міст');
  await стор.route(u => u.origin === БАЗА && !цеМіст(u), async route => {
    const ім = decodeURIComponent(new URL(route.request().url()).pathname).replace(/^\//, '') || 'index.html';
    const ф = path.join(КОРІНЬ, ім);
    if (!fs.existsSync(ф)) return route.fulfill({status: 404, body: 'нема ' + ім});
    await route.fulfill({status: 200, contentType: ім.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/plain; charset=utf-8', body: fs.readFileSync(ф)});
  });
  await стор.route('https://cdn.jsdelivr.net/pyodide/**', async route => {
    const ім = new URL(route.request().url()).pathname.split('/').pop(), ф = path.join(ТЕКА_PYODIDE, ім);
    if (!fs.existsSync(ф)) return route.fulfill({status: 404, body: 'нема ' + ім});
    const тип = ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream';
    await route.fulfill({status: 200, contentType: тип, body: fs.readFileSync(ф)});
  });
  await стор.route(u => u.origin !== БАЗА && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href), route => route.abort());
  await стор.route(u => цеМіст(u), async route => {
    if (route.request().method() !== 'POST') return route.fulfill({status: 204, body: ''});
    викликів++;
    if (ВИД === 'мережа') return route.abort('connectionreset');
    const в = ВІДПОВІДІ[ВИД];
    await route.fulfill({status: в.status, contentType: 'application/json', headers: {'access-control-allow-origin': '*'},
      body: JSON.stringify(в.body)});
  });
  await стор.goto(БАЗА + '/index.html#міст=' + БАЗА + '/міст&т=tok-stend&модель=claude-sonnet-5-5&модель_мови=claude-sonnet-5-5',
    {waitUntil: 'load', timeout: 180000});
  const чекати = async (що, ф, арг, мс = 120000) => { try { await стор.waitForFunction(ф, арг, {timeout: мс, polling: 250}); }
    catch (е) { throw new Error('не дочекались: ' + що); } };
  await чекати('стартовий екран', () => typeof Екран !== 'undefined' && Екран.стан.вхід > 0 && !!Екран.стан.запущено
    && !!document.getElementById('н-далі'), null, 180000);
  await стор.evaluate(() => { ЗАТРИМКИ_ПОВТОРУ_П[0] = 300; ЗАТРИМКИ_ПОВТОРУ_П[1] = 600; });
  /* знайомство — руками: кольори вставленою відповіддю чату (без моделі), ім'я, згода, три кроки */
  await стор.click('#кол-блок details.розкривач > summary');
  await стор.fill('#кол-відповідь', JSON.stringify({photo: 'usable', skin: ['#f2d6c4', '#e9c7b0', '#dcb79f'],
    hair: ['#4a4644', '#5a524c'], eyes: '#6b8cae', limbal_ring: 'visible'}));
  await стор.click('#кол-читати');
  await чекати('кольори лягли', () => typeof СТАН_КОЛЬОРУ_П !== 'undefined' && СТАН_КОЛЬОРУ_П && СТАН_КОЛЬОРУ_П.стан === 'готово', null, 60000);
  await стор.fill('[id="пр-імʼя"]', 'Проба збою');
  await стор.check('#пр-згода');
  await стор.click('#н-далі'); await чекати('крок 2', () => Екран.стан.крок === 1, null, 30000);
  await стор.click('#н-далі'); await чекати('крок 3', () => Екран.стан.крок === 2, null, 30000);
  for (const [і, v] of [['мр-плечі', 98], ['мр-груди', 92], ['мр-талія', 74], ['мр-стегна', 99], ['мр-зріст', 168]]) await стор.fill('#' + і, String(v));
  await стор.click('#н-далі');
  await чекати('сценарій і профіль', () => Екран.стан.режим === 'сценарій' && ПРОФІЛЬ_СТВОРЕНО, null, 60000);
  /* фото для портрета, оцінки й примірки — однотонний кадр з полотна сторінки */
  await стор.evaluate(async () => {
    const п = document.createElement('canvas'); п.width = 600; п.height = 900;
    const к = п.getContext('2d'); к.fillStyle = '#c9a48a'; к.fillRect(0, 0, 600, 900); к.fillStyle = '#334'; к.fillRect(200, 250, 200, 500);
    window.__кадр = await new Promise(р => п.toBlob(р, 'image/jpeg', 0.9));
    await писатиКв(ключФото('портрет'), window.__кадр); await писатиКв(ключФото('зріст'), window.__кадр);
  });

  const рядки = [];
  const сцена = async (ім, дія, вузол) => {
    const було = викликів, збоївДо = await стор.evaluate(() => ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П.length);
    let помилка = null;
    try { await дія(); } catch (е) { помилка = String(е.message || е).slice(0, 300); }
    await с(800);
    const видно = await стор.evaluate(([сел, н]) => {
      const в = typeof сел === 'function' ? null : document.querySelector(сел);
      if (в) в.scrollIntoView({block: 'center'});
      return {текст: в ? в.innerText.trim().replace(/\s+/g, ' ').slice(0, 600) : '(вузла ' + сел + ' нема)',
              збої: ЖУРНАЛ_ЗБОЇВ_ЖІНЦІ_П.slice(н).map(з => [з.вид, з.місце || '', з.збій || ''].filter(Boolean).join(' · '))};
    }, [вузол, збоївДо]);
    await с(300);
    await стор.screenshot({path: path.join(ВИХІД, ВИД + '_' + ім + '.png')});
    const р = {екран: ім, викликів: викликів - було, видно: видно.текст, журнал_збоїв: видно.збої, помилка_стенда: помилка};
    рядки.push(р); console.log(JSON.stringify(р));
  };
  const чекатиПоки = (ф, мс = 120000) => стор.waitForFunction(ф, null, {timeout: мс, polling: 300});

  await сцена('чат', async () => {
    const до = await стор.evaluate(() => ЧАТ_П.filter(р => р.хто === 'ші').length);
    await стор.fill('#чат-поле', 'Новорічна вечірка в ресторані, надворі мороз');
    await стор.click('#чат-слати');
    await стор.waitForFunction(н => ЧАТ_П.filter(р => р.хто === 'ші').length > н && !document.getElementById('чат-поле').disabled,
      до, {timeout: 180000, polling: 300});
  }, '#чат-стрічка .репліка.ші:last-of-type');

  /* картка — фікстура `тест_показу.js` (1д-6а) з англійським описом; переклад прози йде через міст */
  const покластиКартку = () => стор.evaluate(() => {
    П = Object.assign(typeof П === 'object' && П ? П : {}, {картки: [{рука: '1', текст: 'Образ', опис: 'A soft knit dress with low boots keeps you warm and festive.',
      як_носити: ['Tuck the scarf under the coat collar.'], речі: [{id: 'ж-1@gepur.com', назва: 'Сукня трикотажна', ціна: 3000, слот: 'сукня', фото: null}],
      мітки: [], знахідки: [], питання: [], етапи: {}, свідомі: [], фото_не_ті: [], дібрав_код_слоти: []}]});
    let к = document.getElementById('стенд-картка');
    if (!к){ к = document.createElement('div'); к.id = 'стенд-картка';
      к.style.cssText = 'position:fixed;inset:0;overflow:auto;background:var(--тло,#fff);z-index:9999;padding:12px';
      document.body.appendChild(к); }
    к.innerHTML = ''; к.hidden = false;
  });
  const намалюватиКартку = () => стор.evaluate(() => { const к = document.getElementById('стенд-картка');
    к.innerHTML = ''; к.appendChild(рендерКартку(0)); });
  await сцена('проза_картки', async () => { await покластиКартку(); await стор.evaluate(() => мовоюКарткуП(П.картки[0], 'hand_1'));
    await намалюватиКартку(); }, '#стенд-картка');
  await сцена('повідомлення_картки', async () => { await покластиКартку(); await стор.evaluate(async () => {
    const мп = await повідомленнямП({неповний: {kind: 'card_incomplete', statements: [{code: 'look_incomplete'}]}}, 'hand_1');
    const к = document.getElementById('стенд-картка'); к.appendChild(рендерКартку(0));
    const р = document.createElement('p'); р.id = 'стенд-рядок'; р.className = 'не-вийшло';
    р.textContent = 'Чого бракує: ' + (мп.тексти.неповний || ''); к.prepend(р); }); }, '#стенд-картка');
  await сцена('примірка', async () => { await покластиКартку(); await намалюватиКартку();
    await стор.evaluate(() => приміряти(0));
    await стор.evaluate(() => { const к = document.getElementById('стенд-картка'); к.innerHTML = ''; к.appendChild(рендерКартку(0)); малюватиПримірку(0); });
  }, '#стенд-картка');
  await стор.evaluate(() => { const к = document.getElementById('стенд-картка'); if (к) к.remove(); });

  await сцена('помада', async () => { await стор.evaluate(async () => {
    const р = {поділ: {причини: {'1': {kind: 'lipstick_shade_note', statements: [{code: 'lipstick_lighter_than_skin'}]}}}};
    await мовоюПомадиП(р);
    const в = document.createElement('div'); в.id = 'стенд-помада';
    в.style.cssText = 'position:fixed;inset:0;background:#fff;z-index:9999;padding:16px';
    в.textContent = 'Рядок причини відтінку: ' + (р.поділ.причини['1'] == null ? '(рядка нема)' : р.поділ.причини['1']);
    document.body.appendChild(в); }); }, '#стенд-помада');
  await стор.evaluate(() => { const в = document.getElementById('стенд-помада'); if (в) в.remove(); });

  await сцена('палітра', async () => { await стор.evaluate(() => режим('палітра'));
    await чекатиПоки(() => Екран.стан.стан_палітри && ['збій', 'сказано'].includes(Екран.стан.стан_палітри.код)
      && !(typeof ВИБІР_СТИЛІСТКИ_П !== 'undefined' && ВИБІР_СТИЛІСТКИ_П && ВИБІР_СТИЛІСТКИ_П.стан === 'іде'), 240000); }, '#пал-стан');
  await сцена('портрет', async () => { await стор.evaluate(() => режим('сценарій'));
    await стор.evaluate(() => зчитатиКольориЗПортрета());
    await стор.evaluate(() => відкритиАркуш(document.getElementById('кол-блок'))); }, '#кол-стан');
  await сцена('оцінка', async () => { await стор.evaluate(() => режим('оцінка'));
    await стор.evaluate(async () => { await додатиФотоОцінкиП([new File([window.__кадр], 'образ.jpg', {type: 'image/jpeg'})]);
      await оцінитиОбразП(); });
    await чекатиПоки(() => !ОЦ.іде, 240000); }, '#оц-стан');
  /* питання до оцінки: без успішної оцінки суду нема, тож промпт допиту (крок Python `допит_промпт`) стенд підставляє
     сам; виклик моделі й обробка збою — справжні. Вузла стану допиту без картки оцінки на екрані нема — стенд кладе
     під рядок стану оцінки те, що екран малює за станом допиту (`стан_фото_оцінки.допит`). */
  await сцена('питання_до_оцінки', async () => { await стор.evaluate(async () => {
    ОЦ.результат = {допит: [], суд: {}, мова: 'uk', питання: ''}; ОЦ.етапи = ОЦ.етапи || {виклики: []};
    ОЦ.етапи.виклики = ОЦ.етапи.виклики || []; ОЦ.іде = false;
    const справжній = містП;
    містП = (ім, вх, ...р) => ім === 'оцінка' && вх && вх.крок === 'допит_промпт'
      ? Promise.resolve({промпт: 'Answer the follow-up question about the look in the photo.'}) : справжній(ім, вх, ...р);
    try { await допитОцінкиП('А з чорними чоботами пасує?'); } finally { містП = справжній; }
    const ст = (Екран.стан.стан_фото_оцінки || {}).допит || {};
    const в = document.createElement('div'); в.id = 'стенд-допит'; в.className = 'статус';
    if (ст.код === 'збій') показатиШаблонЗбоюП(в, ст.вид); else в.textContent = (НАПИСИ_ФОТО_ОЦІНКИ[ст.код] || ст.код || '');
    в.prepend(document.createTextNode('Відповідь на питання до оцінки: '));
    document.getElementById('оц-стан').after(в); }); }, '#стенд-допит');

  fs.writeFileSync(path.join(ВИХІД, ВИД + '.json'), JSON.stringify({вид: ВИД, корінь: КОРІНЬ, сцени: рядки,
    консоль: консоль.slice(0, 20)}, null, 1));
  await браузер.close();
})().catch(е => { console.error('стенд не піднявся:', е); process.exit(2); });
