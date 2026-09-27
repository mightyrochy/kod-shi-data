/* Перевірка PR #413 (рядок 164): 30 ходів чату на стенді, справжній Pyodide + bridge,
   модель — заглушка Anthropic-формату. Виміряти:
   1) жінка бачить УСЮ розмову в стрічці (усі 60 реплік — її 30 + стилістки 30);
   2) паспорт_досі несе ранні важливі поля (нагоду, вето) і на 30 ході;
   3) довжина тіла запиту до "моделі" на кожному ході (симв). */
const { chromium } = require('playwright');
const БАЗА = process.argv[2] || 'http://127.0.0.1:8765';
const КОРІНЬ = process.argv[3] || process.cwd();
const ЗНІМКИ = process.env.ZNIMKY || '/tmp/claude-0/-home-user-kod-shi-data/f7241a93-2e87-5c0a-b18c-f5931d494139/scratchpad/znimky';
const FOTO = process.env.FOTO === '1';
const fs = require('fs'), path = require('path');
fs.mkdirSync(ЗНІМКИ, { recursive: true });
const с = мс => new Promise(р => setTimeout(р, мс));

(async () => {
  const т0 = Date.now(), ч = () => ((Date.now() - т0) / 1000).toFixed(1) + ' с';
  const браузер = await chromium.launch({
    executablePath: '/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
    headless: true,
    proxy: process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY, bypass: 'localhost,127.0.0.1' } : undefined,
  });
  const стор = await (await браузер.newContext({ ignoreHTTPSErrors: true, viewport: { width: 390, height: 844 } })).newPage();
  const консоль = [];
  стор.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') консоль.push(m.type() + ': ' + m.text().slice(0, 300)); });
  стор.on('pageerror', e => консоль.push('pageerror: ' + String(e).slice(0, 300)));

  const промпти = [];   // {хід, симв, паспорт_досі_є, нагода_в_паспорт_досі, вето_в_паспорт_досі, розмова_раніше_є}
  const НАГОДА0 = 'весілля подруги';
  const ВЕТО0 = 'підбори';

  const паспортМоделі = хід => JSON.stringify({
    подія: НАГОДА0, нагода: 'весілля', місце: 'ресторан_районний', формат: 'приміщення',
    тривалість_год: 4, рух: 'сидіти', дрес_код: 'ошатно', ошатність: 'урочисто', година: 18,
    темп_c: 14, опади: 'ні', намір: 'conventional', бажання: [],
    вето: { типи: [ВЕТО0], тканини: [], принти: [], кольори: [], зони: [] },
    ноги_вище_см: null, настрій: [], невідомо: [],
    питання_людині: хід < 3 ? ['Наскільки ошатно там буде?'] : [],
    відповідь_людині: 'Хід ' + хід + ': памʼятаю — весілля подруги, без ' + ВЕТО0 + '.',
  });

  const ТЕКА_PYODIDE = process.env.PYODIDE_DIR || '/tmp/claude-0/-home-user-kod-shi-data/f7241a93-2e87-5c0a-b18c-f5931d494139/scratchpad/pyodide';
  const тягнув = [];
  await стор.route('https://cdn.jsdelivr.net/pyodide/**', async route => {
    const ім = new URL(route.request().url()).pathname.split('/').pop();
    тягнув.push(ім);
    const ф = path.join(ТЕКА_PYODIDE, ім);
    if (!fs.existsSync(ф)) return route.fulfill({ status: 404, body: 'нема ' + ім });
    const тип = ім.endsWith('.wasm') ? 'application/wasm' : (ім.endsWith('.js') || ім.endsWith('.mjs')) ? 'application/javascript'
              : ім.endsWith('.json') ? 'application/json' : ім.endsWith('.zip') ? 'application/zip' : 'application/octet-stream';
    await route.fulfill({ status: 200, contentType: тип, body: fs.readFileSync(ф) });
  });

  const цеМіст = u => decodeURIComponent(u.pathname).endsWith('/міст');
  await стор.route(u => u.origin === new URL(БАЗА).origin && !цеМіст(u), async route => {
    const ім = decodeURIComponent(new URL(route.request().url()).pathname).replace(/^\//, '') || 'index.html';
    const ф = path.join(КОРІНЬ, ім);
    if (!fs.existsSync(ф)) return route.fulfill({ status: 404, body: 'нема ' + ім });
    const тип = ім.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/plain; charset=utf-8';
    await route.fulfill({ status: 200, contentType: тип, body: fs.readFileSync(ф) });
  });

  let поточнийХід = 0, викликівУХоді = 0;
  await стор.route(u => цеМіст(u), async route => {
    викликівУХоді++;
    const тіло = route.request().postDataJSON() || {};
    const ост = (тіло.messages || []).slice(-1)[0] || {};
    const текстЗапиту = (ост.content || []).map(б => б.text || '').join('\n');
    /* «паспорт_досі» — ЛІТЕРАЛЬНИЙ ключ поля (Cyrillic), як його оголошує паспорт_нагоди.py.
       Витягуємо саме ЙОГО об'єкт лічбою дужок (не жадібний регекс: вкладені {} у «вето»
       обривали захват передчасно). */
    const блокПаспортаДосі = (() => {
      const п = текстЗапиту.indexOf('"паспорт_досі"');
      if (п < 0) return '';
      const початок = текстЗапиту.indexOf('{', п);
      if (початок < 0) return '';
      let глибина = 0;
      for (let к = початок; к < текстЗапиту.length; к++) {
        if (текстЗапиту[к] === '{') глибина++;
        else if (текстЗапиту[к] === '}') { глибина--; if (глибина === 0) return текстЗапиту.slice(початок, к + 1); }
      }
      return '';
    })();
    if (/"розмова"\s*:/.test(текстЗапиту) && [1,5,15,30].includes(поточнийХід))
      fs.appendFileSync(path.join(ЗНІМКИ, `розмова_хід${поточнийХід}.txt`), текстЗапиту);
    промпти.push({
      хід: поточнийХід, виклик_у_ході: викликівУХоді,
      симв: текстЗапиту.length,
      паспорт_досі_є: /"паспорт_досі"\s*:/.test(текстЗапиту),
      нагода_в_паспорт_досі: блокПаспортаДосі.includes(НАГОДА0) || блокПаспортаДосі.includes('весілля'),
      вето_в_паспорт_досі: блокПаспортаДосі.includes(ВЕТО0),
      нагода_будь_де: текстЗапиту.includes(НАГОДА0) || текстЗапиту.includes('весілля'),
      вето_будь_де: текстЗапиту.includes(ВЕТО0),
      розмова_є: /"розмова"\s*:/.test(текстЗапиту),
      розмова_раніше_є: /"розмова_раніше"\s*:/.test(текстЗапиту),
      температура_тіла: тіло.temperature,
    });
    await route.fulfill({
      status: 200, contentType: 'application/json',
      body: JSON.stringify({ content: [{ type: 'text', text: паспортМоделі(поточнийХід) }],
                              usage: { input_tokens: Math.round(текстЗапиту.length / 4), output_tokens: 40 },
                              stop_reason: 'end_turn' }),
    });
  });

  await стор.goto(БАЗА + '/index.html#міст=' + БАЗА + '/міст&т=tok-30', { waitUntil: 'load', timeout: 180000 });
  await с(2000);
  await стор.evaluate(() => {
    КОЛІР = { шкіра: '#f2d6c4', волосся: '#4a4644', очі: '#6b8cae', кільце: null, точки: null };
    for (const [і, v] of [['мр-плечі', 96], ['мр-груди', 92], ['мр-талія', 74], ['мр-стегна', 100]])
      document.getElementById(і).value = v;
    /* «сценарій» — головний екран (CLAUDE.md п.7): режим('сценарій') веде слатиЧатП()
       у паспортПоРозмовіП() напряму (тема='сценарій'), а не в помічницю/переклад шару. */
    режим('сценарій');
  });
  console.log('сторінка піднята за', ч(), '· збірка:', await стор.evaluate(() => ЗБІРКА_ПОКАЗУ));
  console.log('pyodide тягнув (рано):', JSON.stringify([...new Set(тягнув)]));
  if (FOTO) await стор.screenshot({ path: path.join(ЗНІМКИ, '00_старт.png') });

  /* нагода й вето названі РІВНО РАЗ, ходом 1 — щоб перевірити, що на ході 30 вони
     живуть лише в паспорт_досі (Т-08), а не тому, що жінка щойно їх повторила:
     вікно розмови (10 ходів дослівно) і зведення старших (12 її реплік) до ходу 30
     туди вже не дістають (рядок 164). */
  const РЕПЛІКИ_ЖІНКИ = [
    'весілля подруги, без ' + ВЕТО0,
    'ресторан, ввечері', 'наскільки ошатно?', 'урочисто, значить',
    'а якщо буде прохолодно?', 'сукня чи спідниця — все одно',
    'колір — не чорний', 'сумка маленька', 'макіяж не дуже яскравий',
    'прикраси — срібло', 'а якщо спека?', 'хочу щось універсальне',
    'без блиску тканини', 'довжина — нижче коліна', 'рукав короткий',
    'зачіска — розпущене волосся', 'парфуми легкі', 'а взуття зручне?',
    'дякую', 'сумка через плече чи в руці', 'нехай буде елегантно',
    'а якщо піде дощ', 'взуття на невеликому підборі підійде', 'без прозорого',
    'ще щось порадиш', 'палітра тепла чи холодна', 'а зачіска гладка',
    'останній штрих', 'усе влаштовує', 'дякую, готово',
  ];

  for (let i = 0; i < РЕПЛІКИ_ЖІНКИ.length; i++) {
    поточнийХід = i + 1; викликівУХоді = 0;
    const очікЛічба = (i + 1) * 2;
    await стор.fill('#чат-поле', РЕПЛІКИ_ЖІНКИ[i]);
    await стор.click('#чат-слати');
    await стор.waitForFunction(о => document.querySelectorAll('#чат-стрічка .репліка').length >= о, очікЛічба, { timeout: 120000 });
    if (FOTO && (i + 1) % 10 === 0) {
      await стор.screenshot({ path: path.join(ЗНІМКИ, `хід_${i + 1}.png`), fullPage: true });
    }
  }

  const стрічка = await стор.evaluate(() => [...document.querySelectorAll('#чат-стрічка .репліка')].map(р => р.textContent.slice(0, 200)));
  const прокрутка = await стор.evaluate(() => {
    const е = document.getElementById('чат-стрічка');
    return { scrollHeight: е.scrollHeight, clientHeight: е.clientHeight, реплікВсього: е.querySelectorAll('.репліка').length };
  });

  console.log('\n=== ПІДСУМОК 30 ХОДІВ ===');
  console.log('ходів жінки:', РЕПЛІКИ_ЖІНКИ.length, '· викликів моделі:', промпти.length);
  console.log('реплік у стрічці DOM:', стрічка.length, '(очікувано', РЕПЛІКИ_ЖІНКИ.length * 2, ')');
  console.log('прокрутка стрічки:', JSON.stringify(прокрутка));
  console.log('\n--- перша репліка в стрічці (чи лишилась із ходу 1) ---');
  console.log(стрічка[0]);
  console.log('\n--- остання репліка в стрічці ---');
  console.log(стрічка[стрічка.length - 1]);

  /* Із чотирьох викликів ходу (переклад слів шаром, паспорт_нагоди.промпт_паспорта,
     переказ природною мовою…) саме РОЗМОВУ несе лише один — знаходимо його за ключем
     «розмова», а не «останній у ході» (останній — це переказ природною мовою, малий). */
  const заХодами = {};
  промпти.forEach(п => { if (п.розмова_є) заХодами[п.хід] = п; });
  const ходиЗПаспортом = Object.values(заХодами);

  console.log('\n--- паспорт_досі по ходах (останній виклик кожного ходу) ---');
  ходиЗПаспортом.forEach(п => console.log(
    `хід ${п.хід}: викликів=${п.виклик_у_ході}  симв=${п.симв}  паспорт_досі_ключ=${п.паспорт_досі_є}` +
    `  нагода∈паспорт_досі=${п.нагода_в_паспорт_досі}  вето∈паспорт_досі=${п.вето_в_паспорт_досі}` +
    `  нагода_будь_де=${п.нагода_будь_де}  вето_будь_де=${п.вето_будь_де}  розмова_раніше=${п.розмова_раніше_є}  temp=${п.температура_тіла}`
  ));

  console.log('\n--- довжина промпту (симв), останній виклик ходу: до/після стелі вікна ---');
  console.log('хід 1:', заХодами[1] && заХодами[1].симв, '· хід 10:', заХодами[10] && заХодами[10].симв,
              '· хід 20:', заХодами[20] && заХодами[20].симв, '· хід 30:', заХодами[30] && заХодами[30].симв);

  const хід1 = заХодами[1], хід30 = заХодами[30];
  console.log('\n=== ВЕРДИКТ ===');
  console.log('усю розмову бачить (DOM):', стрічка.length === РЕПЛІКИ_ЖІНКИ.length * 2 ? 'ТАК' : 'НІ — ' + стрічка.length + ' з ' + РЕПЛІКИ_ЖІНКИ.length * 2);
  console.log('на ході 30 нагода/вето — БУДЬ-ДЕ в промпті:', (хід30.нагода_будь_де && хід30.вето_будь_де) ? 'ТАК' : 'НІ');
  console.log('на ході 30 нагода/вето — САМЕ в паспорт_досі (не з повтору жінкою):', (хід30.нагода_в_паспорт_досі && хід30.вето_в_паспорт_досі) ? 'ТАК' : 'НІ (паспорт_досі_ключ=' + хід30.паспорт_досі_є + ')');
  console.log('температура доходить (усі виклики 0):', промпти.every(п => п.температура_тіла === 0) ? 'ТАК' : 'НІ (' + промпти.filter(п=>п.температура_тіла!==0).length + ' з ' + промпти.length + ' без 0)');
  console.log('консоль (помилки/попередження):', консоль.length ? консоль.slice(0, 15) : 'порожня');
  console.log('pyodide тягнув:', JSON.stringify([...new Set(тягнув)]));

  fs.writeFileSync(path.join(ЗНІМКИ, 'звіт_30_ходів.json'), JSON.stringify({ промпти, стрічка_довжина: стрічка.length, консоль }, null, 1));
  if (FOTO) await стор.screenshot({ path: path.join(ЗНІМКИ, '99_кінець.png'), fullPage: true });
  await браузер.close();
})().catch(e => { console.error('стенд не піднявся:', e); process.exit(2); });
