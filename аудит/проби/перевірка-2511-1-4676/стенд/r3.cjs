// Стенд приймання Р3 #4676 (прилад перевірки, не код продукту).
// Сторінка (index.html) у Chromium 390×844; шов `/міст` → `claude -p` (ZHYVA=sonnet, як `рв6_стенд.js`:
// ті самі прапорці й системний рядок) з повним записом кожного виклику: init (модель, версія CLI), result
// (usage, modelUsage з contextWindow), тіло запиту сторінки. Повторів стенд не робить: один запит сторінки —
// один процес CLI; повтори самої сторінки видно числом записів.
// Ланцюг: від суду (`ланцюгПерелікуП`) з мінімальним входом `вхід.json` слово в слово (міст `суд` підмінено
// рівно цим входом — фото й переліку речей у синтетичних випадків нема).
// node r3.cjs <тека сторінки> <тека pyodide> <вхід.json> <тека виходу> <мітка>
const fs = require('fs'), path = require('path'), cp = require('child_process');
const {chromium} = require('playwright');
const [КОРІНЬ, PYO, ВХІД, ВИХІД, МІТКА] = process.argv.slice(2);
const ЕФОРТ = process.env.ZHYVA_EFFORT || 'low';
const КЛОД = process.env.ZHYVA || 'sonnet';
const БІН = '/opt/node22/bin/claude';
const БАЗА = 'http://127.0.0.1:8765';
const СИСТЕМНИЙ = 'You are the model behind a mobile styling app. The user message is the '
  + 'application prompt, verbatim. Do exactly what it asks and output only the answer it asks for: '
  + 'raw JSON with no code fence when it asks for JSON, plain prose when it asks for prose. '
  + 'No preamble, no commentary, no tools, no questions back.';
const ПРАПОРЦІ = ['-p', '--model', КЛОД, '--effort', ЕФОРТ, '--tools', '', '--strict-mcp-config',
  '--no-session-persistence', '--input-format', 'stream-json', '--output-format', 'stream-json', '--verbose',
  '--system-prompt', СИСТЕМНИЙ];
fs.mkdirSync(path.join(ВИХІД, 'обміни'), {recursive: true});
const ТЕКА_CLI = fs.mkdtempSync('/tmp/r3w/zhyva-');
const вхід = JSON.parse(fs.readFileSync(ВХІД, 'utf8'));
const журнал = [];
let номер = 0, уПольоті = 0;
const пиши = (ім, д) => fs.writeFileSync(path.join(ВИХІД, ім), typeof д === 'string' ? д : JSON.stringify(д, null, 1));

function клод(тіло){
  const блоки = [];
  const пов = тіло.messages || [];
  for (const м of пов){
    if (пов.length > 1) блоки.push({type: 'text', text: '[' + (м.role === 'assistant' ? 'assistant' : 'user') + ']'});
    if (!Array.isArray(м.content)){ блоки.push({type: 'text', text: String(м.content == null ? '' : м.content)}); continue; }
    for (const б of м.content){
      if (б.type === 'image') блоки.push(б); else блоки.push({type: 'text', text: б.text || ''});
    }
  }
  const рядок = JSON.stringify({type: 'user', message: {role: 'user', content: блоки}}) + '\n';
  return new Promise(рез => {
    const д = cp.spawn(БІН, ПРАПОРЦІ, {cwd: ТЕКА_CLI, stdio: ['pipe', 'pipe', 'pipe'],
      env: Object.assign({}, process.env, {CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: '1'})});
    let в = '', п = '';
    const т = setTimeout(() => { try { д.kill('SIGKILL'); } catch (_) {} }, 300000);
    д.stdout.on('data', x => в += x); д.stderr.on('data', x => п += x);
    д.on('close', код => { clearTimeout(т); рез({код, в, п}); });
    д.stdin.end(рядок, 'utf8');
  });
}

(async () => {
  const браузер = await chromium.launch();
  const конт = await браузер.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 1});
  const стор = await конт.newPage();
  стор.setDefaultTimeout(300000);
  const консоль = [];
  стор.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') консоль.push(m.type() + ': ' + m.text().slice(0, 400)); });
  стор.on('pageerror', e => консоль.push('pageerror: ' + String(e).slice(0, 400)));
  const цеМіст = u => decodeURIComponent(u.pathname).endsWith('/міст');
  await стор.route(u => u.origin === БАЗА && !цеМіст(u), async r => {
    const ім = decodeURIComponent(new URL(r.request().url()).pathname).replace(/^\//, '') || 'index.html';
    const ф = path.join(КОРІНЬ, ім);
    if (!fs.existsSync(ф)) return r.fulfill({status: 404, body: 'нема'});
    r.fulfill({status: 200, contentType: ім.endsWith('.html') ? 'text/html; charset=utf-8' : 'text/plain', body: fs.readFileSync(ф)});
  });
  await стор.route('https://cdn.jsdelivr.net/pyodide/**', async r => {
    const ім = new URL(r.request().url()).pathname.split('/').pop(), ф = path.join(PYO, ім);
    if (!fs.existsSync(ф)) return r.fulfill({status: 404, body: 'нема'});
    const тип = ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream';
    r.fulfill({status: 200, contentType: тип, body: fs.readFileSync(ф)});
  });
  await стор.route(u => u.origin !== БАЗА && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href), r => r.abort());
  await стор.route(u => цеМіст(u), async r => {
    const н = ++номер; уПольоті++;
    const тіло = r.request().postDataJSON() || {};
    const почато = new Date().toISOString(), ч0 = Date.now();
    const п = await клод(тіло);
    const події = п.в.split('\n').filter(Boolean).map(л => { try { return JSON.parse(л); } catch (_) { return null; } }).filter(Boolean);
    const init = події.find(о => о.type === 'system' && о.subtype === 'init') || {};
    const рез = події.find(о => о.type === 'result') || null;
    const текст = рез && !рез.is_error ? String(рез.result || '') : '';
    const модель = рез && рез.modelUsage ? Object.keys(рез.modelUsage).join(',') : null;
    const u = (рез && рез.usage) || {};
    const запис = {н, мітка: МІТКА, почато, с: (Date.now() - ч0) / 1000, rc: п.код,
      запит_сторінки: {model: тіло.model, max_tokens: тіло.max_tokens, поля_вибірки: Object.keys(тіло).filter(к => !['model', 'max_tokens', 'messages'].includes(к)),
        вибірка: Object.fromEntries(Object.entries(тіло).filter(([к]) => !['model', 'max_tokens', 'messages'].includes(к))),
        повідомлень: (тіло.messages || []).length, символів: JSON.stringify(тіло.messages || []).length},
      cli: {версія: init.claude_code_version || null, модель_init: init.model || null, apiKeySource: init.apiKeySource || null, прапорці: ПРАПОРЦІ.map(x => x === СИСТЕМНИЙ ? '<системний рядок рв6_стенд.js>' : x)},
      результат: рез ? {subtype: рез.subtype, is_error: рез.is_error, stop_reason: рез.stop_reason, num_turns: рез.num_turns,
        duration_ms: рез.duration_ms, duration_api_ms: рез.duration_api_ms, total_cost_usd: рез.total_cost_usd,
        usage: рез.usage, modelUsage: рез.modelUsage} : null,
      модель_фактична: модель, символів_відповіді: текст.length, stderr: п.п.slice(0, 500)};
    журнал.push(запис);
    пиши(path.join('обміни', String(н).padStart(2, '0') + '_запит.json'), тіло);
    пиши(path.join('обміни', String(н).padStart(2, '0') + '_відповідь.txt'), текст);
    пиши(path.join('обміни', String(н).padStart(2, '0') + '_cli.jsonl'), п.в);
    console.log('міст #' + н + ' · ' + запис.с.toFixed(1) + ' с · ' + модель + ' · вхід ' + (u.input_tokens || 0) + '+кеш ' + ((u.cache_read_input_tokens || 0) + (u.cache_creation_input_tokens || 0)) + ' · вихід ' + (u.output_tokens || 0) + ' · ' + (рез ? рез.subtype : 'НЕМА result rc ' + п.код));
    уПольоті--;
    if (!рез || рез.is_error)
      return r.fulfill({status: 599, contentType: 'application/json', body: JSON.stringify({error: {type: 'стенд', message: рез ? String(рез.result || рез.subtype) : 'claude -p без result'}})});
    r.fulfill({status: 200, contentType: 'application/json', headers: {'x-model': модель || '', 'x-attempts': '1', 'access-control-expose-headers': 'x-model,x-attempts'},
      body: JSON.stringify({id: 'стенд-' + н, type: 'message', role: 'assistant', model: модель, content: [{type: 'text', text: текст}],
        stop_reason: рез.stop_reason === 'max_tokens' ? 'max_tokens' : 'end_turn',
        usage: {input_tokens: u.input_tokens || 0, output_tokens: u.output_tokens || 0,
                cache_read_input_tokens: u.cache_read_input_tokens || 0, cache_creation_input_tokens: u.cache_creation_input_tokens || 0}})});
  });
  await стор.goto(БАЗА + '/index.html#міст=' + encodeURIComponent(БАЗА + '/міст') + '&т=stend-r3', {waitUntil: 'load'});
  const штамп = await стор.evaluate(() => (typeof ЗБІРКА_ПОКАЗУ !== 'undefined' ? ЗБІРКА_ПОКАЗУ : null));
  console.log('штамп', штамп);
  await стор.evaluate(async () => { if (!МІСТ_ГОТОВИЙ_П) await підняти_міст_показу(); });
  console.log('міст показу піднято');
  const підсумок = await стор.evaluate(async (вх) => {
    const питання = {free_text: 'Чи пасують довжини в цьому образі?', lang: 'uk'};
    const судів = [];
    const справжній = містП;
    // Синтетичний випадок: суд — рівно на мінімальному вході (фото, переліку й пікселів у випадку нема).
    містП = async function(ім, арг){
      if (ім === 'оцінка' && арг && арг.крок === 'суд'){ судів.push(1); return справжній(ім, JSON.parse(JSON.stringify(вх))); }
      return справжній(ім, арг);
    };
    ОЦ = новаОцінкаП();
    ОЦ.питання = питання.free_text; ОЦ.ід = 'r3'; ОЦ.іде = false;
    ОЦ.етапи = {почато: new Date().toISOString(), питання: питання.free_text, сценарій_екрана: {}, фото: [], виклики: [], мова_шару: [], з_розмови: false};
    ОЦ.перелік = {речі: вх.речі.map(р => Object.assign({}, р)), hex: {}, довідник: {слоти: [], кольори: []}, мініатюри: {}, назви: {},
      так: true, показано_о: Date.now(), звіт: {показано: вх.речі.length, дії: [], дотиків: 0}, ід_ланцюга: 'r3', біжить: false, готовий: true,
      лічильник: 0, для_слів: [], словаЙде: false,
      контекст: {база: {}, пікселі: {}, пікселі_фото: {}, питання, сценарій: {}}, імена: Promise.resolve()};
    режим('оцінка'); показатиОцінку();
    await ланцюгПерелікуП();
    return {стан: ОЦ.стан, судів: судів.length, помилка: (ОЦ.етапи || {}).помилка || null};
  }, вхід);
  console.log('ланцюг:', JSON.stringify(підсумок));
  // «Чого я не знаю» шар перекладає одразу за карткою — чекаю тиші моста
  for (let і = 0; і < 600; і++){ await стор.waitForTimeout(1000); if (уПольоті === 0 && і > 3){ await стор.waitForTimeout(3000); if (уПольоті === 0) break; } }
  const дані = await стор.evaluate(() => JSON.parse(JSON.stringify({етапи: ОЦ.етапи, результат: ОЦ.результат, стан: ОЦ.стан})));
  пиши('етапи.json', дані.етапи); пиши('результат.json', дані.результат);
  const к = await стор.$('#оц-картка');
  const видно = к ? await к.isVisible() : false;
  await стор.evaluate(() => window.scrollTo(0, 0));
  await стор.screenshot({path: path.join(ВИХІД, 'екран_390x844.png')});
  if (к && видно){
    const догори = () => стор.evaluate(() => { document.getElementById('оц-картка').scrollIntoView({block: 'start'}); });
    await догори(); await стор.waitForTimeout(300);
    await стор.screenshot({path: path.join(ВИХІД, 'картка_вікно_390x844.png')});
    await к.screenshot({path: path.join(ВИХІД, 'картка.png')});
    const д = await стор.$('#оц-картка details.оц-не-знаю > summary');
    if (д){ await д.click(); await стор.waitForTimeout(1500); await к.screenshot({path: path.join(ВИХІД, 'картка_не_знаю.png')});
      await стор.evaluate(() => { const е = document.querySelector('#оц-картка details.оц-не-знаю'); е.scrollIntoView({block: 'start'}); });
      await стор.waitForTimeout(300); await стор.screenshot({path: path.join(ВИХІД, 'не_знаю_вікно_390x844.png')}); }
    пиши('текст_картки.txt', await к.innerText());
  }
  пиши('журнал_моделі.json', журнал); пиши('консоль.txt', консоль.join('\n'));
  пиши('підсумок.json', {штамп, ...підсумок, картка_видно: видно, викликів_моделі: журнал.length, ефорт: ЕФОРТ, клод: КЛОД});
  console.log('картка видно:', видно, '· викликів:', журнал.length);
  await браузер.close();
})().catch(e => { console.error('ЗБІЙ СТЕНДА:', e); process.exit(2); });
