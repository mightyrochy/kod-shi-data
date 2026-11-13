/* Прилад проби «Живий-як-людина-1» (не код продукту): жінку грає окрема сесія `claude -p`, яка знає лише свою
   ситуацію (`ситуація.md`) і пам'ятку тестувальниці (`пам'ятка.md`), а не код, реєстр сцен, записані репліки чи
   питання правок. Цей скрипт — лише її телефон: зібрана сторінка `index.html` у справжньому Chromium 390×844,
   справжній Pyodide з диска, міст сторінки — на місцевий `міст_claude.py` (модель продукту за підпискою).
   Кожен крок: знімок екрана (те, що вона бачить) + текст видимої частини екрана + перелік того, що можна натиснути
   чи заповнити → її відповідь JSON (що бачить і думає, і одна дія) → дія пальцем. Більше скрипт нічого не робить.
   Запуск: node людина.js <тека ситуації> <порт моста> [кроків, типово 320]
   Змінні: STOR=/tmp/стенд (index.html), PYODIDE=/tmp/pyodide, ZHINKA_MODEL (типово claude-sonnet-5-5). */
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { spawn } = require('child_process'), os = require('os');
const ТЕКА = path.resolve(process.argv[2]), ПОРТ = Number(process.argv[3] || 8791), КРОКІВ = Number(process.argv[4] || 320);
const КОРІНЬ = process.env.STOR || '/tmp/стенд', ТЕКА_PYODIDE = process.env.PYODIDE || '/tmp/pyodide';
const БАЗА = 'http://127.0.0.1:8765', БІН = process.env.ZHYVA_BIN || '/opt/node22/bin/claude';
const МОДЕЛЬ_ЖІНКИ = process.env.ZHINKA_MODEL || 'claude-sonnet-5-5';
const ПРОХІД = path.basename(ТЕКА);
const ЗНІМКИ = path.join(ТЕКА, 'знімки'); fs.mkdirSync(ЗНІМКИ, {recursive: true});
const СЛУЖБОВЕ = path.join(path.dirname(ТЕКА), 'стенд', 'службове', ПРОХІД); fs.mkdirSync(СЛУЖБОВЕ, {recursive: true});
const ХІД = path.join(ТЕКА, 'хід.md');
const ЖУРНАЛ_ЖІНКИ = path.join(СЛУЖБОВЕ, 'жінка_виклики.jsonl');
const ТЕКА_ЖІНКИ = fs.mkdtempSync(path.join(os.tmpdir(), 'жінка-'));  // нейтральна тека: CLAUDE.md репозиторію не підхоплюється
const с = мс => new Promise(р => setTimeout(р, мс));
const ситуація = fs.readFileSync(path.join(ТЕКА, 'ситуація.md'), 'utf8');
const пам = fs.readFileSync(path.join(path.dirname(ТЕКА), "пам'ятка.md"), 'utf8');

const СИСТЕМНИЙ = `Ти — жінка, описана нижче. Ти тестувальниця застосунку-стилістки «Люстерко» і проходиш його на своєму телефоні
так, як пройшла б жива людина. Ти не програмістка: коду не бачиш і не знаєш, бачиш лише екран.

${ситуація}

${пам}

Як іде робота. На кожному кроці ти отримуєш знімок екрана телефона, текст тієї частини екрана, яку зараз видно, і
перелік того, що на цьому екрані можна натиснути чи заповнити (номер у квадратних дужках). Відповідаєш лише одним
JSON-об'єктом, без жодного тексту поза ним:
{"бачу": "<що ти зараз бачиш і думаєш — одне-два речення від першої особи, як нотатка в процесі; помітила щось дивне, незрозуміле чи зламане — так і напиши>",
 "дія": <одна дія>}
Дії:
  {"тап": N}                                — натиснути елемент N;
  {"ввести": N, "текст": "..."}            — надрукувати текст у поле N (те, що в полі було, заміниться);
  {"гортати": "вниз"} або {"гортати": "вгору"} — прогорнути екран;
  {"чекати": секунд}                        — почекати (до 120), коли щось вантажиться чи збирається;
  {"готово": true}                          — ти пройшла все, що мала, і вивантажила файл вердиктів.
Пиши українською. Дій лише через екран. Не вигадуй того, чого на екрані нема.`;

let сесія = null, викликівЖінки = 0, доларівЖінки = 0;  /* total_cost_usd у відновленій сесії — наростаючий: беру останній */
function жінка(блоки){
  return new Promise(рез => {
    const арг = ['-p', '--model', МОДЕЛЬ_ЖІНКИ, '--tools', '', '--strict-mcp-config', '--input-format', 'stream-json',
                '--output-format', 'stream-json', '--verbose', '--system-prompt', СИСТЕМНИЙ];
    if (сесія) арг.push('--resume', сесія);
    const т0 = Date.now();
    const д = spawn(БІН, арг, {cwd: ТЕКА_ЖІНКИ, env: Object.assign({}, process.env, {CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC: '1'})});
    let вих = '', пом = '';
    const таймер = setTimeout(() => д.kill('SIGKILL'), 600000);
    д.stdout.on('data', х => вих += х); д.stderr.on('data', х => пом += х);
    д.on('close', код => {
      clearTimeout(таймер);
      let ітог = null;
      for (const л of вих.split('\n')) { try { const о = JSON.parse(л); if (о.type === 'result') ітог = о; } catch (_) {} }
      викликівЖінки++;
      const було = доларівЖінки; if (ітог) { сесія = ітог.session_id || сесія; доларівЖінки = Math.max(доларівЖінки, ітог.total_cost_usd || 0); }
      fs.appendFileSync(ЖУРНАЛ_ЖІНКИ, JSON.stringify({н: викликівЖінки, с: (Date.now() - т0) / 1000, usd_наростаюче: ітог && ітог.total_cost_usd, usd_виклику: +(доларівЖінки - було).toFixed(5),
        usage: ітог && ітог.usage, модель: ітог && Object.keys(ітог.modelUsage || {}), помилка: ітог ? (ітог.is_error ? ітог.result : null) : ('rc ' + код + ' ' + пом.slice(-300))}) + '\n');
      рез(ітог && !ітог.is_error ? String(ітог.result || '') : null);
    });
    д.stdin.end(JSON.stringify({type: 'user', message: {role: 'user', content: блоки}}) + '\n');
  });
}
function розібрати(т){
  if (!т) return null;
  const п = т.indexOf('{'), к = т.lastIndexOf('}');
  if (п < 0 || к < п) return null;
  try { return JSON.parse(т.slice(п, к + 1)); } catch (_) { return null; }
}

/* Що бачить людина: текст видимої частини екрана і те, що можна натиснути (лише не закрите іншим шаром). */
async function екран(стор){
  return стор.evaluate(() => {
    document.querySelectorAll('[data-люд]').forEach(е => е.removeAttribute('data-люд'));
    const В = innerWidth, Н = innerHeight;
    const видно = е => {
      const р = е.getBoundingClientRect();
      if (р.width < 2 || р.height < 2 || р.bottom <= 0 || р.top >= Н || р.right <= 0 || р.left >= В) return null;
      const ст = getComputedStyle(е);
      if (ст.visibility === 'hidden' || ст.display === 'none' || Number(ст.opacity) === 0) return null;
      return р;
    };
    /* текст видимої частини */
    const рядки = []; let попБлок = null, рядок = '';
    const хід = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    while (хід.nextNode()){
      const в = хід.currentNode, т = в.textContent.replace(/\s+/g, ' ').trim();
      if (!т) continue;
      const б = в.parentElement; if (!б || /^(SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(б.tagName)) continue;
      const діап = document.createRange(); діап.selectNodeContents(в);
      const пр = Array.from(діап.getClientRects()).filter(р => р.width > 0 && р.bottom > 0 && р.top < Н && р.right > 0 && р.left < В);
      if (!пр.length) continue;
      let п = б, схов = false;
      while (п && п !== document.body){ const ст = getComputedStyle(п); if (ст.visibility === 'hidden' || ст.display === 'none' || Number(ст.opacity) === 0){ схов = true; break; } п = п.parentElement; }
      if (схов) continue;
      const блок = б.closest('p,li,div,section,button,label,h1,h2,h3,h4,td,summary,a') || б;
      if (блок !== попБлок && рядок){ рядки.push(рядок); рядок = ''; }
      рядок += (рядок ? ' ' : '') + т; попБлок = блок;
    }
    if (рядок) рядки.push(рядок);
    /* поля вводу: значення теж видно на екрані */
    /* що можна натиснути */
    const усі = Array.from(document.querySelectorAll('body *'));
    const тиснеться = е => {
      const тег = е.tagName;
      if (/^(BUTTON|A|INPUT|TEXTAREA|SELECT|SUMMARY|LABEL)$/.test(тег)) return true;
      if (е.onclick || е.hasAttribute('onclick') || е.isContentEditable && е.getAttribute('contenteditable') !== null) return true;
      const роль = е.getAttribute('role'); if (/^(button|tab|option|checkbox|radio|switch|link|menuitem|slider)$/.test(роль || '')) return true;
      const ст = getComputedStyle(е);
      if (ст.cursor === 'pointer' && (!е.parentElement || getComputedStyle(е.parentElement).cursor !== 'pointer')) return true;
      return false;
    };
    const елем = []; let н = 0;
    for (const е of усі){
      if (!тиснеться(е)) continue;
      if (е.tagName === 'INPUT' && е.type === 'hidden') continue;
      const р = видно(е); if (!р) continue;
      if (е.tagName === 'LABEL' && е.querySelector('input,select,textarea') && е.control && видно(е.control)) continue;
      /* не закрите іншим шаром: точка в центрі видимої частини належить елементу */
      const x = Math.min(Math.max(р.left + р.width / 2, 1), В - 1), y = Math.min(Math.max(р.top + р.height / 2, 1), Н - 1);
      const верх = document.elementFromPoint(x, y);
      if (!(верх && (верх === е || е.contains(верх) || (е.tagName === 'INPUT' && верх.tagName === 'LABEL' && верх.control === е)))) {
        if (!(е.tagName === 'INPUT' && /^(checkbox|radio|file)$/.test(е.type))) continue;
      }
      /* вкладений у вже взятий тиснучий елемент без власного обробника — пропускаю */
      const пред = е.parentElement && е.parentElement.closest('[data-люд]');
      if (пред && !е.onclick && !/^(INPUT|TEXTAREA|SELECT|BUTTON|A)$/.test(е.tagName)) continue;
      н++; е.setAttribute('data-люд', String(н));
      let підпис = (е.innerText || '').replace(/\s+/g, ' ').trim();
      const тег = е.tagName;
      let вид = 'кнопка';
      if (тег === 'INPUT'){
        вид = е.type === 'checkbox' ? 'галочка' + (е.checked ? ' ☑' : ' ☐') : е.type === 'radio' ? 'вибір' + (е.checked ? ' ◉' : ' ○')
          : е.type === 'file' ? 'додати фото/файл' : е.type === 'range' ? 'повзунок' : 'поле';
        const лб = е.labels && е.labels[0] ? е.labels[0].innerText.replace(/\s+/g, ' ').trim() : '';
        підпис = [лб, е.placeholder ? 'підказка: ' + е.placeholder : '', е.value && !/^(checkbox|radio|file)$/.test(е.type) ? 'зараз: ' + е.value : ''].filter(Boolean).join(' · ');
      } else if (тег === 'TEXTAREA'){ вид = 'поле для тексту'; підпис = [е.placeholder ? 'підказка: ' + е.placeholder : '', е.value ? 'зараз: ' + е.value : ''].filter(Boolean).join(' · '); }
      else if (тег === 'SELECT'){ вид = 'список'; підпис = 'зараз: ' + (е.options[е.selectedIndex] || {}).text + ' · варіанти: ' + Array.from(е.options).map(о => о.text).join(' / '); }
      else if (е.isContentEditable){ вид = 'поле для тексту'; }
      else if (тег === 'A') вид = 'посилання';
      if (!підпис) підпис = (е.getAttribute('aria-label') || е.getAttribute('title') || е.getAttribute('alt') || '').trim();
      if (!підпис){ const з = е.querySelector('img[alt],svg title'); if (з) підпис = (з.getAttribute('alt') || з.textContent || '').trim(); }
      if (!підпис) підпис = '(без підпису; див. знімок, місце: ' + Math.round(р.left) + ',' + Math.round(р.top) + ')';
      елем.push('[' + н + '] ' + вид + ': ' + підпис.slice(0, 140));
    }
    return {текст: рядки.join('\n').slice(0, 3500), елем, прокрутка: Math.round(scrollY)};
  });
}

async function головна(){
  const ж = (...а) => fs.appendFileSync(ХІД, а.join('') + '\n');
  if (!fs.existsSync(ХІД)) ж('# Хід проходу — що вона бачила й робила (', ПРОХІД, ')\n');
  const браузер = await chromium.launch({headless: true, executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium',
    proxy: process.env.HTTPS_PROXY ? {server: process.env.HTTPS_PROXY, bypass: 'localhost,127.0.0.1'} : undefined});
  const конт = await браузер.newContext({viewport: {width: 390, height: 844}, deviceScaleFactor: 1, isMobile: true, hasTouch: true,
    userAgent: 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36',
    locale: 'uk-UA', timezoneId: 'Europe/Kyiv', ignoreHTTPSErrors: true, acceptDownloads: true});
  await конт.grantPermissions(['clipboard-read', 'clipboard-write'], {origin: БАЗА}).catch(() => {});
  const стор = await конт.newPage();
  стор.setDefaultTimeout(30000);
  const консоль = fs.createWriteStream(path.join(СЛУЖБОВЕ, 'консоль.txt'));
  стор.on('console', м => { if (м.type() === 'error' || м.type() === 'warning') консоль.write(new Date().toISOString() + ' ' + м.type() + ': ' + м.text().slice(0, 400) + '\n'); });
  стор.on('pageerror', е => консоль.write(new Date().toISOString() + ' pageerror: ' + String(е).slice(0, 400) + '\n'));
  let галерея = 0;
  стор.on('filechooser', fc => { галерея++; консоль.write('filechooser відкрито — фото на телефоні нема\n'); });
  стор.on('download', async з => {
    const ім = з.suggestedFilename() || 'вердикти.json';
    await з.saveAs(path.join(ТЕКА, ім)).catch(е => консоль.write('download: ' + е + '\n'));
    ж('\n> файл збережено на телефоні: `', ім, '`\n');
  });
  const цеМіст = u => decodeURIComponent(u.pathname).endsWith('/міст');
  const обміни = fs.createWriteStream(path.join(СЛУЖБОВЕ, 'обміни.jsonl'));
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
  /* фото крамниць і шрифти — з мережі, як на її телефоні; кадр, що мовчить, — чесна помилка за 15 с */
  await стор.route(u => u.origin !== БАЗА && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href), async route => {
    try { await route.fulfill({response: await route.fetch({timeout: 15000})}); } catch (_) { try { await route.abort(); } catch (__) {} }
  });
  await стор.route(u => цеМіст(u), async route => {
    const тіло = route.request().postData() || '{}';
    const т0 = Date.now();
    try {
      const в = await fetch('http://127.0.0.1:' + ПОРТ + '/', {method: 'POST', body: тіло,
        headers: {'content-type': 'application/json', 'x-prohid': encodeURIComponent(ПРОХІД)}, signal: AbortSignal.timeout(960000)});
      const текст = await в.text(); const заг = {};
      for (const к of ['x-model', 'x-images-dropped']) if (в.headers.get(к)) заг[к] = в.headers.get(к);
      обміни.write(JSON.stringify({час: new Date(т0).toISOString(), с: (Date.now() - т0) / 1000, статус: в.status, запит: тіло, відповідь: текст}) + '\n');
      await route.fulfill({status: в.status, contentType: 'application/json', headers: заг, body: текст}).catch(() => {});
    } catch (е) {
      обміни.write(JSON.stringify({час: new Date(т0).toISOString(), помилка: String(е)}) + '\n');
      await route.fulfill({status: 502, contentType: 'application/json', body: JSON.stringify({error: {message: 'міст: ' + String(е).slice(0, 200)}})}).catch(() => {});
    }
  });
  await стор.goto(БАЗА + '/index.html#міст=' + БАЗА + '/міст&т=tok-lyudyna&модель=claude-sonnet-5-5&модель_мови=claude-sonnet-5-5',
    {waitUntil: 'load', timeout: 180000});
  await с(8000);

  let крок = 0, попЗнімок = null, помилокПоспіль = 0, поясн = '';
  const перше = 'Ти відкрила посилання на Люстерко на телефоні. Починай.';
  while (крок < КРОКІВ){
    крок++;
    const е = await екран(стор).catch(е => ({текст: '(сторінка не відповідає: ' + String(е).slice(0, 100) + ')', елем: [], прокрутка: 0}));
    const ім = String(крок).padStart(3, '0') + '.jpg';
    const кадр = await стор.screenshot({type: 'jpeg', quality: 72}).catch(() => null);
    if (кадр) fs.writeFileSync(path.join(ЗНІМКИ, ім), кадр);
    const блоки = [];
    if (кадр) блоки.push({type: 'image', source: {type: 'base64', media_type: 'image/jpeg', data: кадр.toString('base64')}});
    блоки.push({type: 'text', text: (крок === 1 ? перше + '\n\n' : '') + (поясн ? поясн + '\n\n' : '')
      + 'Крок ' + крок + '. Екран телефона (знімок вище).\nТекст, який зараз видно:\n' + (е.текст || '(порожньо)')
      + '\n\nМожна натиснути чи заповнити:\n' + (е.елем.join('\n') || '(нічого)') + '\n\nТвій JSON:'});
    поясн = '';
    let відп = await жінка(блоки), р = розібрати(відп);
    if (!р || !р.дія){
      відп = await жінка([{type: 'text', text: 'Відповідь має бути одним JSON-об\'єктом {"бачу": "...", "дія": {...}}. Повтори для того самого екрана.'}]);
      р = розібрати(відп);
    }
    if (!р || !р.дія){ if (++помилокПоспіль >= 3) { ж('\n> зупинено: жінка тричі не дала дії\n'); break; } continue; }
    помилокПоспіль = 0;
    const д = р.дія, мітка = н => { const рядок = е.елем.find(х => х.startsWith('[' + н + '] ')); return рядок ? рядок.replace(/^\[\d+\] /, '') : '№' + н; };
    let опис = '';
    try {
      if (д.готово){ ж('\n### ', крок, ' · ', new Date().toISOString().slice(11, 19), ' UTC · знімок `знімки/', ім, '`\n- бачу: ', р.бачу || '', '\n- дія: готово\n'); break; }
      if (д.тап != null){
        опис = 'натиснула «' + мітка(д.тап) + '»';
        const лок = стор.locator('[data-люд="' + д.тап + '"]');
        if (!(await лок.count())) { поясн = 'Елемента ' + д.тап + ' на цьому екрані нема.'; опис += ' (такого нема)'; }
        else {
          const тег = await лок.evaluate(х => х.tagName + ':' + (х.type || '')).catch(() => '');
          if (/INPUT:file/.test(тег)) { поясн = 'Відкрилась галерея телефона, але фото, яке тут потрібне, у тебе на телефоні нема. Ти закрила галерею.'; опис += ' — у галереї нема потрібного фото'; }
          else await лок.click({timeout: 10000}).catch(async () => { await лок.click({force: true, timeout: 5000}); });
        }
      } else if (д.ввести != null){
        опис = 'надрукувала в «' + мітка(д.ввести) + '»: «' + String(д.текст || '') + '»';
        const лок = стор.locator('[data-люд="' + д.ввести + '"]');
        if (!(await лок.count())) { поясн = 'Поля ' + д.ввести + ' на цьому екрані нема.'; опис += ' (такого нема)'; }
        else {
          await лок.click({timeout: 8000}).catch(() => {});
          try { await лок.fill(String(д.текст || ''), {timeout: 8000}); }
          catch (_) { await стор.keyboard.press('Control+A'); await стор.keyboard.type(String(д.текст || ''), {delay: 5}); }
        }
      } else if (д.гортати){
        опис = 'гортнула ' + (д.гортати === 'вгору' ? 'вгору' : 'вниз');
        await стор.mouse.move(195, 420); await стор.mouse.wheel(0, д.гортати === 'вгору' ? -600 : 600);
      } else if (д.чекати != null){
        const сек = Math.min(Math.max(Number(д.чекати) || 10, 3), 120); опис = 'чекала ' + сек + ' с';
        await с(сек * 1000);
      } else { опис = 'незрозуміла дія ' + JSON.stringify(д).slice(0, 100); поясн = 'Такої дії нема; обери з переліку дій.'; }
    } catch (е) { опис += ' — не вдалося: ' + String(е.message || е).split('\n')[0].slice(0, 120); поясн = 'Дія не вдалася: на екрані нічого не змінилося.'; }
    if (галерея) { галерея = 0; поясн = (поясн ? поясн + ' ' : '') + 'Відкрилась галерея телефона, але придатного фото там нема. Ти закрила галерею.'; опис += ' → відкрилась галерея, фото нема'; }
    ж('\n### ', крок, ' · ', new Date().toISOString().slice(11, 19), ' UTC · знімок `знімки/', ім, '`\n- бачу: ', String(р.бачу || '').replace(/\n/g, ' '), '\n- дія: ', опис);
    await с(д.чекати != null ? 500 : 2500);
  }
  /* підсумкове повідомлення — як від тестувальниці: поломки п'ятьма рядками і що ще хоче сказати */
  const фін = await жінка([{type: 'text', text: 'Ти закінчила. Напиши тепер повідомлення, яке надіслала б нам разом із файлом вердиктів, — так, як просить пам\'ятка: '
    + 'про кожну поломку окремо п\'ятьма рядками (що робила, що сталося, коли, на якому кроці/знімку, телефон і браузер — у тебе Android, Chrome), '
    + 'а далі вільно — що ще хочеш нам сказати про цей досвід. Не став оцінок «вдалий/невдалий» образам. Пиши звичайним текстом (markdown), не JSON.'}]);
  fs.writeFileSync(path.join(ТЕКА, 'повідомлення.md'), '# Повідомлення тестувальниці (' + ПРОХІД + ')\n\n' + (фін || '(не написала)') + '\n');
  fs.writeFileSync(path.join(СЛУЖБОВЕ, 'жінка.json'), JSON.stringify({модель: МОДЕЛЬ_ЖІНКИ, кроків: крок, викликів: викликівЖінки,
    usd: +доларівЖінки.toFixed(4), сесія}, null, 1));
  консоль.end(); обміни.end();
  await браузер.close();
  console.log(ПРОХІД + ' кроків ' + крок + ' жінка $' + доларівЖінки.toFixed(2));
}
головна().catch(е => { console.error(е); process.exit(1); });
