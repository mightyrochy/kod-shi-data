// Стенд приймання Р3 #4724 (прилад перевірки, не код продукту): розмова зі стилісткою «як тестувальниця».
// Дії — черга ч3_фото_примірка проходу 21.11 (профіль із фото, фото речі, її слова, «Надіслати»), сторінка — локальна
// index.html у Chromium 390×844, Pyodide — з диска, шов /міст → `claude -p` (ZHYVA=sonnet), запис кожного виклику з usage.
// PERSHA=<файл> — ПЕРША відповідь перекладача репліки підставна (записана відповідь 21.11, обмін 5): повтор формату
// гарантовано, друга відповідь — справжня модель. Без PERSHA — усі відповіді справжні.
// node rozmova.cjs <тека сторінки> <тека pyodide> <тека виходу> <мітка> <текст її повідомлення>
const fs = require('fs'), path = require('path'), cp = require('child_process');
const {chromium} = require('playwright');
const [КОРІНЬ, PYO, ВИХІД, МІТКА, ЇЇ_ТЕКСТ] = process.argv.slice(2);
const БАЗА = 'http://127.0.0.1:8765';
const ФОТО = '/home/user/kod-shi-data/аудит/проби/Прохід-через-міст-2026-11-21/вхід/';
const ПЕРША = process.env.PERSHA ? fs.readFileSync(process.env.PERSHA, 'utf8') : null;
const джерело = fs.readFileSync('/home/user/kod-shi-data/аудит/проби/живий-як-людина-4/стенд/людина.js', 'utf8');
const екран = eval('(' + джерело.slice(джерело.indexOf('async function екран('), джерело.indexOf('const {знімокРук')).trim() + ')');
const ЕФОРТ = process.env.ZHYVA_EFFORT || 'low';
const КЛОД = process.env.ZHYVA || 'sonnet';
const БІН = '/opt/node22/bin/claude';

const СИСТЕМНИЙ = 'You are the model behind a mobile styling app. The user message is the '
  + 'application prompt, verbatim. Do exactly what it asks and output only the answer it asks for: '
  + 'raw JSON with no code fence when it asks for JSON, plain prose when it asks for prose. '
  + 'No preamble, no commentary, no tools, no questions back.';
const ПРАПОРЦІ = ['-p', '--model', КЛОД, '--effort', ЕФОРТ, '--tools', '', '--strict-mcp-config',
  '--no-session-persistence', '--input-format', 'stream-json', '--output-format', 'stream-json', '--verbose',
  '--system-prompt', СИСТЕМНИЙ];
fs.mkdirSync(path.join(ВИХІД, 'обміни'), {recursive: true});
const ТЕКА_CLI = fs.mkdtempSync('/tmp/r3w/zhyva-');
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


const сон = n => new Promise(r => setTimeout(r, n));
let підставлено = 0, перекладів = 0;
(async () => {
  const браузер = await chromium.launch();
  const конт = await браузер.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 1, isMobile: true, hasTouch: true, locale: 'uk-UA', timezoneId: 'Europe/Kyiv'});
  const стор = await конт.newPage();
  стор.setDefaultTimeout(15000);
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
    const текстЗапиту = JSON.stringify(тіло.messages || []);
    const переклад = текстЗапиту.includes('репліка стилістки') && текстЗапиту.includes('РЕПЛІКА:');
    if (переклад) перекладів++;
    const почато = new Date().toISOString(), ч0 = Date.now();
    let п, текст, рез, модель, u = {};
    if (переклад && ПЕРША && !підставлено){
      підставлено++; текст = ПЕРША; модель = 'ПІДСТАВНА-21.11-обмін-5'; рез = {subtype: 'підставна', stop_reason: 'end_turn'}; п = {код: 0, в: '', п: ''};
    } else {
      п = await клод(тіло);
      const події = п.в.split('\n').filter(Boolean).map(л => { try { return JSON.parse(л); } catch (_) { return null; } }).filter(Boolean);
      рез = події.find(о => о.type === 'result') || null;
      текст = рез && !рез.is_error ? String(рез.result || '') : '';
      модель = рез && рез.modelUsage ? Object.keys(рез.modelUsage).join(',') : null;
      u = (рез && рез.usage) || {};
      var init = події.find(о => о.type === 'system' && о.subtype === 'init') || {};
    }
    const запис = {н, мітка: МІТКА, почато, с: (Date.now() - ч0) / 1000, переклад_репліки: переклад, модель_фактична: модель,
      cli: init ? {версія: init.claude_code_version || null, модель_init: init.model || null} : null,
      результат: рез ? {subtype: рез.subtype, is_error: рез.is_error, stop_reason: рез.stop_reason, total_cost_usd: рез.total_cost_usd, usage: рез.usage, modelUsage: рез.modelUsage} : null,
      символів_відповіді: (текст || '').length};
    журнал.push(запис);
    const пф = (ім, д) => fs.writeFileSync(path.join(ВИХІД, 'обміни', String(н).padStart(2, '0') + ім), д);
    пф('_запит.json', JSON.stringify(тіло).replace(/"data":"[A-Za-z0-9+\/=]{200,}"/g, '"data":"<base64>"'));
    пф('_відповідь.txt', текст || '');
    console.log('міст #' + н + (переклад ? ' [переклад репліки]' : '') + ' · ' + запис.с.toFixed(1) + ' с · ' + модель + ' · ' + (рез ? рез.subtype : 'НЕМА result rc ' + п.код));
    уПольоті--;
    if (!рез || рез.is_error)
      return r.fulfill({status: 599, contentType: 'application/json', body: JSON.stringify({error: {type: 'стенд', message: рез ? String(рез.result || рез.subtype) : 'claude -p без result'}})});
    r.fulfill({status: 200, contentType: 'application/json', headers: {'x-model': модель || '', 'x-attempts': '1', 'access-control-expose-headers': 'x-model,x-attempts'},
      body: JSON.stringify({id: 'стенд-' + н, type: 'message', role: 'assistant', model: модель, content: [{type: 'text', text: текст}],
        stop_reason: 'end_turn', usage: {input_tokens: u.input_tokens || 0, output_tokens: u.output_tokens || 0}})});
  });
  const спокій = async (межа = 900) => { const т0 = Date.now(); while (Date.now() - т0 < межа * 1000){ await сон(1500);
      const думає = await стор.evaluate(() => /Думаю…/.test(document.body.innerText) || Array.from(document.querySelectorAll('input,textarea')).some(x => x.disabled && x.getBoundingClientRect().height > 0)).catch(() => true);
      if (!уПольоті && !думає){ await сон(3000); if (!уПольоті) return (Date.now() - т0) / 1000; } } return -1; };
  const знайти = async мітка => { for (let і = 0; і < 30; і++){ const ст = await екран(стор);
      const к = ст.елем.filter(s => s.replace(/^\[\d+\] /, '').replace(/\s+/g, ' ').trim().startsWith(мітка));
      if (к.length) return стор.locator(`[data-люд="${Number(к[0].match(/^\[(\d+)\]/)[1])}"]`);
      await стор.mouse.move(195, 422); await стор.mouse.wheel(0, і < 15 ? 600 : -600); await сон(250); } throw new Error('нема: ' + мітка); };
  await стор.goto(БАЗА + '/index.html#міст=' + encodeURIComponent(БАЗА + '/міст') + '&т=stend-rozmova', {waitUntil: 'load', timeout: 300000});
  await сон(5000); await спокій();
  const штамп = await стор.evaluate(() => (typeof ЗБІРКА_ПОКАЗУ !== 'undefined' ? ЗБІРКА_ПОКАЗУ : null));
  console.log('штамп', штамп);
  const кроки = [
    ['файлк', 'кнопка: Додати фото речі', [ФОТО + 'item.jpg']], ['друк', 'поле для тексту', ЇЇ_ТЕКСТ], ['тап', 'кнопка: Надіслати']];
  for (const [дія, ціль, д] of кроки){
    try{
      const лок = ціль.startsWith('#') ? стор.locator(ціль).first() : await знайти(ціль);
      if (дія === 'файл') await лок.setInputFiles(д);
      else if (дія === 'файлк'){ const тип = await лок.evaluate(x => x.tagName + ':' + (x.type || ''));
        if (/INPUT:file/.test(тип)) await лок.setInputFiles(д); else { const [fc] = await Promise.all([стор.waitForEvent('filechooser', {timeout: 8000}), лок.click()]); await fc.setFiles(д); } }
      else if (дія === 'тап') await лок.click({timeout: 15000});
      else if (дія === 'друк') await лок.fill(д);
      await сон(1200); const с = await спокій(); console.log('крок', дія, ціль, 'спокій', с);
    }catch(e){ console.log('крок', дія, ціль, 'ПОМИЛКА', String(e).split('\n')[0]); }
  }
  await спокій(); await сон(4000); await спокій();
  const чат = await стор.evaluate(() => JSON.parse(JSON.stringify((typeof ЧАТ_П !== 'undefined' ? ЧАТ_П : []).map(м => ({хто: м.хто, текст: м.текст,
    мова_шару: (м.мова_шару || []).map(з => ({де: з.де, напрям: з.напрям, повтор: з.повтор, причина: з.причина, відкинуто: з.відкинуто, вихід: з.вихід,
      запасний: з.запасний, запасний_текст: з.запасний_текст, запрошення_питанням: з.запрошення_питанням, required: ((з.вхід || {}).репліка || {}).required,
      recorded: ((з.вхід || {}).репліка || {}).recorded, запрошення: (з.вхід || {}).запрошення}))})))));
  const бульбашки = await стор.evaluate(() => Array.from(document.querySelectorAll('[class*="бульб"], .ші, .чат-ші, [data-хто="ші"]')).map(е => е.innerText).filter(Boolean));
  fs.writeFileSync(path.join(ВИХІД, 'чат.json'), JSON.stringify(чат, null, 1));
  fs.writeFileSync(path.join(ВИХІД, 'бульбашки.txt'), бульбашки.join('\n-----\n'));
  fs.writeFileSync(path.join(ВИХІД, 'видимий_текст.txt'), await стор.evaluate(() => document.body.innerText));
  await стор.screenshot({path: path.join(ВИХІД, 'екран_390x844.png')});
  try{
    const остання = [...чат].reverse().find(м => м.хто === 'ші' && м.текст);
    if (остання){ await стор.locator('#ші-пілюля').click({timeout: 8000}); await сон(2500);
      await стор.screenshot({path: path.join(ВИХІД, 'чат_390x844.png')});
      await стор.evaluate(() => { const е = [...document.querySelectorAll('*')].filter(x => x.scrollHeight > x.clientHeight + 20 && getComputedStyle(x).overflowY !== 'visible'); е.forEach(x => x.scrollTop = x.scrollHeight); });
      await сон(800); await стор.screenshot({path: path.join(ВИХІД, 'чат_низ_390x844.png')});
      fs.writeFileSync(path.join(ВИХІД, 'видимий_текст_чату.txt'), await стор.evaluate(() => document.body.innerText)); }
  }catch(e){ console.log('чат не відкрито:', String(e).split('\n')[0]); }
  await стор.screenshot({path: path.join(ВИХІД, 'екран_весь.png'), fullPage: true});
  fs.writeFileSync(path.join(ВИХІД, 'журнал_моделі.json'), JSON.stringify(журнал, null, 1));
  fs.writeFileSync(path.join(ВИХІД, 'консоль.txt'), консоль.join('\n'));
  fs.writeFileSync(path.join(ВИХІД, 'підсумок.json'), JSON.stringify({штамп, мітка: МІТКА, викликів: журнал.length, перекладів, підставлено}, null, 1));
  console.log('кінець · викликів', журнал.length, '· перекладів', перекладів, '· підставлено', підставлено);
  await браузер.close();
})().catch(e => { console.error('ЗБІЙ СТЕНДА:', e); process.exit(2); });
