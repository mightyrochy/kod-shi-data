'use strict';
/* OFF-стенд Н2 (перевірка Claude, 25.11): під'єднання контракту `ПОРЯДОК.md` пакета Codex 4c324522 до браузера.
   Один хід = одна роль (джерело | база | кандидат) однієї сцени. Вхід — тека сцени за ПОРЯДОК.md.
   Вжиток: node off_стенд.cjs <OFF_PKG> <ТЕКА_СЦЕНИ> <роль> <index.html>
   Джерело: POST на канал воркера (127.0.0.1:8787) віддає адаптер поза браузером — `claude -p` (ZHYVA=sonnet) за
   підпискою; база й кандидат — лише читання запису `джерело/VIDPOVIDI/обмін` (off.джерелоВідповідей). */
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const {chromium} = require('playwright');
const [OFF_PKG, ТЕКА, РОЛЬ, HTML] = process.argv.slice(2);
const off = require(path.join(OFF_PKG, 'off.cjs'));
const {ключЗапиту} = require(path.join(OFF_PKG, 'записаний_обмін.js'));
const {штампиСторінки} = require(path.join(OFF_PKG, 'доказ_прогону.js'));
const sha256 = б => crypto.createHash('sha256').update(б).digest('hex');
const rj = ф => JSON.parse(fs.readFileSync(ф, 'utf8'));
const БАЗА = 'http://127.0.0.1:8765', МІСТ = 'http://127.0.0.1:8787';
const ФІКС = path.join(ТЕКА, 'фікстури');
const ВХІД = rj(path.join(ТЕКА, 'повтор.json'));
const КАНАЛ = rj(path.join(ТЕКА, 'канал.json'));
const ФІКСТУРА = rj(path.join(ТЕКА, 'фікстура.json'));
const ДІЇ = rj(path.join(ФІКС, 'дії.json'));
const СХОВИЩЕ = rj(path.join(ФІКС, 'сховище.json'));
const ГОДИННИК = rj(path.join(ФІКС, 'годинник.json'));
const СІД = ВХІД.сід;
const ВИХІД = path.join(ТЕКА, РОЛЬ);
fs.mkdirSync(ВИХІД); if (!process.env.OFF_SUHYI) fs.mkdirSync(path.join(ВИХІД, 'VIDPOVIDI'));
const html = fs.readFileSync(HTML);
const штампи = штампиСторінки(html.toString('utf8'));
const лог = [];
const пиши = (...а) => { const р = new Date().toISOString() + ' ' + а.join(' '); лог.push(р); console.log(р); };
const події = [];
let паузОбміну = 0, стор = null, cdp = null;
let знімокЗроблено = false, обмінДоЗнімка = false, запитів = 0, віддано = 0, викликівМоделі = 0;
const виклики = [];
const вПольоті = new Set();
let останнійОбмін = Date.now();
/* повтор теж пише свої обміни (запит, віддана відповідь): міра порівнює ряд кожної ролі з джерелом */
const писачПовтору = (РОЛЬ !== 'джерело' && !process.env.OFF_SUHYI) ? off.записувач(path.join(ВИХІД, 'VIDPOVIDI', 'обмін')) : null;
const писач = (РОЛЬ === 'джерело' && !process.env.OFF_SUHYI) ? off.записувач(path.join(ВИХІД, 'VIDPOVIDI', 'обмін')) : null;
const СУХИЙ = !!process.env.OFF_SUHYI;
const читач = (РОЛЬ === 'джерело' || СУХИЙ) ? null : off.джерелоВідповідей(path.join(ТЕКА, 'джерело', 'VIDPOVIDI', 'обмін'));
let зупинка = null;
const ТЕМП = читач ? rj(path.join(ТЕКА, 'джерело', 'виклики-каналу.json')).map(в => в.стіна_мс || 0) : [];

/* ── адаптер джерела: claude -p поза браузером (як `клодомCLI` стенда рв6, без зміни тексту запиту) ── */
const СИСТЕМНИЙ = 'You are the model behind a mobile styling app. The user message is the '
  + 'application prompt, verbatim. Do exactly what it asks and output only the answer it asks for: '
  + 'raw JSON with no code fence when it asks for JSON, plain prose when it asks for prose. '
  + 'No preamble, no commentary, no tools, no questions back.';
const КЛОД_ТЕКА = fs.mkdtempSync(path.join(require('os').tmpdir(), 'off-zhyva-'));
async function кадр(url) {
  try {
    const в = await fetch(url, {redirect: 'follow'});
    if (!в.ok) return null;
    const тип = (в.headers.get('content-type') || 'image/jpeg').split(';')[0].trim();
    const б = Buffer.from(await в.arrayBuffer());
    if (!б.length || б.length > 5 * 1024 * 1024 || !/^image\/(jpeg|png|gif|webp)$/.test(тип)) return null;
    return {type: 'image', source: {type: 'base64', media_type: тип, data: б.toString('base64')}};
  } catch (_) { return null; }
}
async function адаптер(тіло) {
  const пов = тіло.messages || [];
  const блоки = []; let дропи = 0, фото = 0;
  for (const м of пов) {
    if (пов.length > 1) блоки.push({type: 'text', text: '[' + (м.role === 'assistant' ? 'assistant' : 'user') + ']'});
    if (!Array.isArray(м.content)) { блоки.push({type: 'text', text: String(м.content == null ? '' : м.content)}); continue; }
    for (const б of м.content) {
      if (б.type !== 'image') { блоки.push({type: 'text', text: б.text || ''}); continue; }
      фото++;
      const дж = б.source || {};
      if (дж.type === 'base64') { блоки.push({type: 'image', source: {type: 'base64', media_type: дж.media_type || 'image/jpeg', data: дж.data}}); continue; }
      const к = await кадр(дж.url || '');
      if (к) блоки.push(к); else { дропи++; блоки.push({type: 'text', text: '(image not delivered)'}); }
    }
  }
  const рядок = JSON.stringify({type: 'user', message: {role: 'user', content: блоки}}) + '\n';
  const п = await new Promise(рез => {
    const дитя = require('child_process').spawn('/opt/node22/bin/claude',
      ['-p', '--model', 'sonnet', '--tools', '', '--strict-mcp-config', '--no-session-persistence',
       '--input-format', 'stream-json', '--output-format', 'stream-json', '--verbose', '--system-prompt', СИСТЕМНИЙ],
      {cwd: КЛОД_ТЕКА, stdio: ['pipe', 'pipe', 'pipe'], env: Object.assign({}, process.env, {CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: '1'})});
    let вивід = '', помилки = '', убито = false;
    const т = setTimeout(() => { убито = true; try { дитя.kill('SIGKILL'); } catch (_) {} }, 600000);
    дитя.stdout.on('data', д => { вивід += д; }); дитя.stderr.on('data', д => { помилки += д; });
    дитя.on('close', код => { clearTimeout(т); рез({код, вивід, помилки, убито}); });
    дитя.stdin.on('error', () => {}); дитя.stdin.end(рядок, 'utf8');
  });
  let підсумок = null, init = null;
  for (const л of п.вивід.split('\n')) { try { const о = JSON.parse(л); if (о.type === 'result') підсумок = о; if (о.type === 'system' && о.subtype === 'init') init = о; } catch (_) {} }
  let статус = 200, текст = '', помилка = null;
  if (п.убито || !підсумок) { статус = 599; помилка = п.убито ? 'claude -p понад 600 с' : 'claude -p без result: ' + (п.помилки || '').slice(0, 300); }
  else if (підсумок.is_error || підсумок.subtype !== 'success') { статус = /rate|limit|429/i.test(String(підсумок.result)) ? 429 : 599; помилка = String(підсумок.result || '').slice(0, 300); }
  else текст = String(підсумок.result || '');
  const u = (підсумок || {}).usage || {};
  const відповідь = статус === 200
    ? {status: 200, contentType: 'application/json', headers: {'x-model': 'claude:sonnet', ...(фото ? {'x-images-dropped': String(дропи)} : {})},
       body: JSON.stringify({content: [{type: 'text', text: текст}],
         usage: {input_tokens: (u.input_tokens || 0) + (u.cache_read_input_tokens || 0) + (u.cache_creation_input_tokens || 0), output_tokens: u.output_tokens || 0},
         stop_reason: (підсумок.stop_reason === 'max_tokens' ? 'max_tokens' : 'end_turn')})}
    : {status: статус, contentType: 'application/json', headers: {'x-model': 'claude:sonnet'}, body: JSON.stringify({error: {message: помилка}})};
  return {відповідь, підсумок, init, фото, дропи, помилка};
}

function етап(тіло) {
  const т = (((тіло.messages || []).slice(-1)[0] || {}).content || []);
  const текст = (Array.isArray(т) ? т.map(б => б.text || '').join('\n') : String(т));
  const м = /"(?:в|v|version|task|тип)"\s*:\s*"([^"]{1,40})"/.exec(текст);
  return (м ? м[1] : текст.replace(/\s+/g, ' ').slice(0, 40)) || 'невідомо';
}

(async () => {
  const браузер = await chromium.launch();
  const контекст = await браузер.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 1,
    locale: ГОДИННИК.локаль, timezoneId: ГОДИННИК.часовий_пояс, serviceWorkers: 'block', acceptDownloads: false});
  /* ізоляція й журнал — до будь-якої навігації */
  await контекст.routeWebSocket(/.*/, с => { події.push({url: с.url(), вид: 'заблоковано'}); return с.close({code: 1008}); });
  await контекст.route(/.*/, async route => {
    const з = route.request(), url = з.url(), u = new URL(url);
    if (u.origin === МІСТ) {
      if (з.method() !== 'POST') { події.push({url, вид: 'заблоковано'}); return route.abort('blockedbyclient'); }
      const тіло = з.postDataBuffer();
      const номер = ++запитів;
      if (!знімокЗроблено) обмінДоЗнімка = true;
      вПольоті.add(номер); останнійОбмін = Date.now();
      /* годинник сторінки стоїть, поки триває обмін: тривалість моделі не входить у видимий час, тож запис і повтор бачать однаковий */
      if (знімокЗроблено && !СУХИЙ && паузОбміну++ === 0) {
        const т = await стор.evaluate(() => Date.now()).catch(() => null);
        if (т) await контекст.clock.pauseAt(т + 1).catch(е => пиши('пауза годинника:', е.message));
        /* і JS сторінки стоїть: паралельні гілки (руки 2–4, переклад) не біжать, поки модель думає — порядок запитів той самий, що в повторі з миттєвими відповідями */
        await cdp.send('Debugger.enable').catch(е => пиши('налагоджувач:', е.message));
        await cdp.send('Debugger.pause').catch(е => пиши('пауза JS:', е.message));
      }
      const т0 = Date.now();
      try {
        let відповідь;
        if (СУХИЙ) throw new Error('сухий хід: перший обмін №' + номер + ' після знімка=' + знімокЗроблено + ' sha=' + sha256(тіло) + ' байт=' + тіло.length);
        if (писач) {
          const запит = JSON.parse(тіло.toString('utf8'));
          const а = await адаптер(запит);
          відповідь = а.відповідь; викликівМоделі++;
          const mu = (а.підсумок || {}).modelUsage || null;
          const ключі = mu ? Object.keys(mu) : [];
          const заміна = ключі.length !== 1 || ключі[0] !== КАНАЛ.модель;
          const компакція = !!(а.підсумок && а.підсумок.num_turns && а.підсумок.num_turns > 1);
          виклики.push({номер, етап: етап(запит), маршрут: КАНАЛ.маршрут, модель: КАНАЛ.модель, effort: КАНАЛ.effort,
            запит_sha256: sha256(тіло), max_output_запиту: запит.max_tokens ?? null,
            max_output_рушія: mu && ключі[0] ? (mu[ключі[0]].maxOutputTokens ?? null) : null,
            стіна_мс: Date.now() - т0, автоматична_компакція: компакція, заміна_моделі: заміна, модель_факт: ключі, фото: а.фото, фото_не_дійшло: а.дропи,
            ...(а.підсумок ? {usage: {usage: а.підсумок.usage || null, modelUsage: mu, stop_reason: а.підсумок.stop_reason || null,
              num_turns: а.підсумок.num_turns ?? null, duration_ms: а.підсумок.duration_ms ?? null, total_cost_usd: а.підсумок.total_cost_usd ?? null}}
              : {usage: null, usage_відсутній_через: а.помилка || 'нема result'})});
          пиши('обмін', номер, виклики.at(-1).етап, 'HTTP', відповідь.status, 'модель', ключі.join(','), 'фото', а.фото, 'не дійшло', а.дропи);
          if (заміна || компакція || відповідь.status !== 200) зупинка = зупинка || ('виклик ' + номер + ': ' + (заміна ? 'модель ' + ключі.join(',') : компакція ? 'num_turns>1' : 'HTTP ' + відповідь.status));
          писач(номер, тіло, відповідь);
        } else {
          const в = читач.взяти(тіло);
          if (в.номер !== номер) throw new Error('номер запису ' + в.номер + ' ≠ ' + номер);
          відповідь = в.відповідь;
          /* темп повтору — той самий, що в записі: відповідь через стільки ж мілісекунд стіни (робітник сторінки біжить у реальному часі) */
          const чекати = (ТЕМП[номер - 1] || 0) - (Date.now() - т0);
          if (чекати > 0) await new Promise(р => setTimeout(р, чекати));
          писачПовтору(номер, тіло, відповідь);
          пиши('обмін', номер, 'з запису', 'темп', ТЕМП[номер - 1]);
        }
        await route.fulfill({status: відповідь.status, contentType: відповідь.contentType, headers: відповідь.headers, body: відповідь.body});
        віддано++;
        події.push({url, вид: 'обмін', номер, запит_sha256: sha256(тіло), відповідь_sha256: sha256(Buffer.from(відповідь.body, 'utf8'))});
      } catch (е) {
        зупинка = зупинка || ('обмін ' + номер + ': ' + е.message);
        if (!писач && !СУХИЙ) fs.writeFileSync(path.join(ВИХІД, 'незбіг-' + String(номер).padStart(5, '0') + '.запит'), тіло);
        пиши('ЗУПИНКА', зупинка);
        await route.abort('blockedbyclient').catch(() => {});
      } finally {
        вПольоті.delete(номер); останнійОбмін = Date.now();
        if (знімокЗроблено && !СУХИЙ && --паузОбміну === 0) {
          /* disable знімає і паузу, і ще не спрацьовану заявку на неї */
          await cdp.send('Debugger.disable').catch(е => пиши('пуск JS:', е.message));
          await контекст.clock.resume().catch(е => пиши('пуск годинника:', е.message));
        }
      }
      return;
    }
    if (u.origin === БАЗА && з.method() === 'GET' && !u.search) {
      if (u.pathname === '/index.html') {
        події.push({url, вид: 'збірка', sha256: sha256(html)});
        return route.fulfill({status: 200, contentType: 'text/html; charset=utf-8', body: html});
      }
      if (decodeURIComponent(u.pathname) === '/засів.html') {
        const б = fs.readFileSync(path.join(ФІКС, 'засів.html'));
        події.push({url, вид: 'локально', файл: 'засів.html', sha256: sha256(б)});
        return route.fulfill({status: 200, contentType: 'text/html; charset=utf-8', body: б});
      }
    }
    if (u.origin === 'https://cdn.jsdelivr.net' && /^\/pyodide\/v0\.26\.4\/full\/[\w.-]+$/.test(u.pathname) && з.method() === 'GET') {
      const ім = 'pyodide/' + u.pathname.split('/').pop();
      if (ФІКСТУРА.файли[ім]) {
        const б = fs.readFileSync(path.join(ФІКС, ім));
        події.push({url, вид: 'локально', файл: ім, sha256: sha256(б)});
        const тип = ім.endsWith('.wasm') ? 'application/wasm' : /\.m?js$/.test(ім) ? 'application/javascript' : ім.endsWith('.json') ? 'application/json' : 'application/octet-stream';
        return route.fulfill({status: 200, contentType: тип, body: б});
      }
    }
    if (з.resourceType() === 'image' && з.method() === 'GET') {
      const б = fs.readFileSync(path.join(ФІКС, 'синт.png'));
      події.push({url, вид: 'локально', файл: 'синт.png', sha256: sha256(б)});
      return route.fulfill({status: 200, contentType: 'image/png', body: б});
    }
    події.push({url, вид: 'заблоковано'});
    return route.abort('blockedbyclient');
  });
  await контекст.addInitScript(с => { Math.random = () => с / 1e6; }, СІД);
  const P = ГОДИННИК.початок_ms;
  /* годинник стоїть від засіву до розбору сторінки: адреса штампу збірки (`build.txt?t=Date.now()`) однакова в кожній ролі */
  await контекст.clock.install({time: P - ГОДИННИК.запас_до_початку_ms - 1000});
  await контекст.clock.pauseAt(P - ГОДИННИК.запас_до_початку_ms);
  стор = await контекст.newPage();
  cdp = await контекст.newCDPSession(стор);
  const помилкиСторінки = [];
  стор.on('pageerror', е => помилкиСторінки.push(String(е).slice(0, 300)));
  /* початкове сховище — на тому самому origin до відкриття продукту */
  await стор.goto(БАЗА + '/засів.html');
  await стор.evaluate(async сх => {
    for (const [к, з] of Object.entries(сх.localStorage)) localStorage.setItem(к, з);
    for (const [к, з] of Object.entries(сх.sessionStorage)) sessionStorage.setItem(к, з);
    for (const б of сх.indexedDB) {
      const d = await new Promise((р, в) => { const з = indexedDB.open(б.name, б.version);
        з.onupgradeneeded = е => { const db = е.target.result; for (const с of б.сховища) if (!db.objectStoreNames.contains(с.ім)) db.createObjectStore(с.ім, {keyPath: с.keyPath ?? undefined, autoIncrement: с.autoIncrement}); };
        з.onsuccess = () => р(з.result); з.onerror = () => в(з.error); });
      for (const с of б.сховища) {
        await new Promise((р, в) => { const t = d.transaction(с.ім, 'readwrite'); const s = t.objectStore(с.ім);
          for (const [к, з] of с.записи) с.keyPath == null ? s.put(з, к) : s.put(з); t.oncomplete = р; t.onerror = () => в(t.error); });
      }
      d.close();
    }
  }, СХОВИЩЕ);
  пиши('сховище засіяно');
  await стор.goto(БАЗА + '/index.html' + ВХІД.змінні.хеш, {waitUntil: 'domcontentloaded'});
  await контекст.clock.resume();
  await стор.waitForFunction(() => typeof Екран !== 'undefined' && Екран.стан && Екран.стан.запущено, null, {timeout: 120000});
  await стор.waitForTimeout(ВХІД.змінні.тиша_до_знімка_мс);
  await контекст.clock.pauseAt(P);
  const стан = await стор.evaluate(off.початковийЗнімок, СІД);
  знімокЗроблено = true;
  fs.writeFileSync(path.join(ВИХІД, 'початковий-стан.json'), JSON.stringify(стан, null, 1) + '\n');
  пиши('початковий стан записано', 'обмін до знімка:', обмінДоЗнімка);
  await стор.screenshot({path: path.join(ВИХІД, 'до-дії-390x844.png')}).catch(() => {});
  пиши('екран до дії:', JSON.stringify((await стор.evaluate(() => document.body.innerText)).slice(0, 600)));
  const кроки = [];
  for (const [і, дія] of ДІЇ.entries()) {
    const т = P + ГОДИННИК.кроки_ms[і];
    if (т > P || і > 0) await контекст.clock.pauseAt(т);
    const дата = await стор.evaluate(() => Date.now());
    кроки.push({номер: і + 1, дата_ms: дата, дія_sha256: ключЗапиту(дія)});
    await контекст.clock.resume();
    /* дія — DOM-клік елемента (однаково в кожній ролі; кандидат несе з main інший видимий інтерфейс #4681, старий екран у ньому схований) */
    if (дія.вид === 'клік') await стор.$eval(дія.селектор, е => е.click());
    else throw new Error('невідома дія ' + JSON.stringify(дія));
    пиши('дія', і + 1, JSON.stringify(дія));
  }
  fs.writeFileSync(path.join(ВИХІД, 'кроки.json'), JSON.stringify(кроки, null, 1) + '\n');
  /* до всіх кінцевих карток і остаточних текстів */
  const кінецьДо = Date.now() + 45 * 60000;
  let попереднє = null, сталих = 0, готово = false;
  while (Date.now() < кінецьДо && !зупинка) {
    await new Promise(р => setTimeout(р, 5000));
    const с = await стор.evaluate(() => ({готово: typeof ЗБ !== 'undefined' && !!ЗБ && !!ЗБ.готово,
      збій: typeof ЗБ !== 'undefined' && !!ЗБ && (ЗБ.діагноз || []).some(р => /^build · failed/.test(р)),
      карток: document.querySelectorAll('#картки .картка').length,
      текст: [...document.querySelectorAll('#картки .картка')].map(к => к.innerText).join('\n§\n') + '\n¶\n' + document.body.innerText}));
    if ((с.готово || с.збій) && вПольоті.size === 0 && Date.now() - останнійОбмін > 30000) {
      if (с.текст === попереднє) сталих++; else сталих = 0;
      if (сталих >= 3) { готово = true; break; }
    }
    попереднє = с.текст;
  }
  const виходи = await стор.evaluate(() => {
    const кк = [...document.querySelectorAll('#картки .картка')];
    return {кк: кк.map(к => к.innerText), тіло: document.body.innerText};
  });
  const карток = виходи.кк.length;
  fs.writeFileSync(path.join(ВИХІД, 'картки.txt'), виходи.кк.map((т, і) => '═══ картка ' + (і + 1) + ' з ' + карток + ' · видимий текст ═══\n' + т).join('\n\n') + '\n');
  fs.writeFileSync(path.join(ВИХІД, 'текст_екранів.txt'), '═══ екран після збирання ═══\n' + виходи.тіло + '\n');
  await стор.screenshot({path: path.join(ВИХІД, 'екран-390x844.png')}).catch(() => {});
  let повтор = null;
  if (читач) { try { повтор = читач.завершити(); } catch (е) { зупинка = зупинка || ('завершити: ' + е.message); } }
  if (писач) fs.writeFileSync(path.join(ВИХІД, 'виклики-каналу.json'), JSON.stringify(виклики, null, 1) + '\n');
  fs.writeFileSync(path.join(ВИХІД, 'мережа.json'), JSON.stringify({встановлено_до_навігації: true, нагляд_усіх_запитів: true,
    ізольовано: true, знімок_до_першого_обміну: !обмінДоЗнімка, зовнішніх_доставок: 0,
    викликів_моделі: писач ? викликівМоделі : 0, події}, null, 1) + '\n');
  const доведено = готово && !зупинка && !обмінДоЗнімка && карток === ВХІД.змінні.карток && запитів === віддано;
  fs.writeFileSync(path.join(ВИХІД, 'доказ.json'), JSON.stringify({формат: 1, run_id: 'off-' + РОЛЬ + '-' + crypto.randomUUID(),
    подія: доведено ? 'OFF: видимі виходи збережено' : 'OFF: не завершено', кінець: new Date().toISOString(),
    вердикт: {доведено, ...(доведено ? {} : {чому: зупинка || (!готово ? 'не дочекався сталих текстів' : 'лічильники')})},
    обрив: зупинка, код: {збірка: штампи.збірка, відбиток: штампи.відбиток, каталог: штампи.каталог},
    входи: {сторінка: {sha256: sha256(html)}}, очікувано: {карток_кінцевих_OFF: ВХІД.змінні.карток},
    факт: {карток_кінцевих_OFF: карток}, помилки_сторінки: помилкиСторінки}, null, 1) + '\n');
  fs.writeFileSync(path.join(ВИХІД, 'лог.txt'), лог.join('\n') + '\n');
  await браузер.close();
  off.квитанція(ТЕКА, РОЛЬ, {rc: доведено ? 0 : 1, запитів, віддано, повтор});
  пиши('КІНЕЦЬ', РОЛЬ, 'доведено', доведено, 'запитів', запитів, 'віддано', віддано, 'карток', карток, 'повтор', JSON.stringify(повтор), 'зупинка', зупинка);
  fs.writeFileSync(path.join(ВИХІД, 'лог.txt'), лог.join('\n') + '\n');
  process.exit(доведено ? 0 : 1);
})().catch(е => { console.error(е); try { fs.writeFileSync(path.join(ВИХІД, 'лог.txt'), лог.join('\n') + '\nВИНЯТОК ' + (е.stack || е) + '\n'); } catch (_) {} process.exit(2); });
