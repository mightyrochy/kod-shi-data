/* Драйвер проходу «як тестувальниця» на ОПУБЛІКОВАНІЙ сторінці (наряд Прохід-через-міст-запланований).
   Запуск з кореня репозиторію (фоном, один процес):
     node аудит/проби/Прохід-через-міст-2026-11-21/скрипти/драйвер.js <тека-виходу> [ширина×висота]
   Сторінка — https://mightyrochy.github.io/kod-shi-data/index.html без підміни (index.html і Pyodide — з мережі).
   MIST=stub (типово) — виклики моста не йдуть далі браузера: відповідь 503 без провайдера (дослідження екранів, $0).
   MIST=real — сторінка кличе справжній міст; токен — заглушка tok-stub, справжній підставляє проксі.
   Команди — файли <тека>/черга/NNNN.json (одна дія): {"дія":"екран"|"тап"|"друк"|"файл"|"гортай"|"чекай"|"кадр"|"ключ"|"кінець", ...};
   відповідь — <тека>/черга/NNNN.відп.json, кадр — <тека>/знімки/NNNN.jpg. Кожен обмін із мостом — <тека>/обміни.jsonl. */
const fs = require('fs'), path = require('path');
const {chromium} = require('playwright');
const джерело = fs.readFileSync(path.resolve('аудит/проби/живий-як-людина-4/стенд/людина.js'), 'utf8');
const екран = eval('(' + джерело.slice(джерело.indexOf('async function екран('), джерело.indexOf('const {знімокРук')).trim() + ')');
const вихід = path.resolve(process.argv[2]); const [ш, в] = (process.argv[3] || '390x844').split(/[x×]/).map(Number);
const МІСТ_РЕЖИМ = process.env.MIST || 'stub';
const СТЕЛЯ = Number(process.env.STELYA || 0);   // >0 — після стількох справжніх викликів міст далі не кличеться (503 сторінці)
const черга = path.join(вихід, 'черга'), знімки = path.join(вихід, 'знімки');
for (const p of [черга, знімки]) fs.mkdirSync(p, {recursive: true});
const сон = n => new Promise(r => setTimeout(r, n));
const МІСТ = 'https://lyusterko-mist.mighty-rochy.workers.dev/';
const СТОРІНКА = 'https://mightyrochy.github.io/kod-shi-data/index.html';
let стор, активні = 0, останній = 0, справжніх = 0;
const журнал = т => fs.appendFileSync(path.join(вихід, 'журнал.txt'), new Date().toISOString() + ' ' + т + '\n');
async function спокій(межа_с = 900) {
  const т0 = Date.now();
  while (Date.now() - т0 < межа_с * 1000) {
    const думає = await стор.evaluate(() => {
      const т = document.getElementById('е-очікування'), п = document.getElementById('пал-стан');
      return !!((т && т.getBoundingClientRect().height > 0) ||
        (п && п.getBoundingClientRect().height > 0 && /^(Ще мить…|…)\s*$/.test(п.innerText)) ||
        Array.from(document.querySelectorAll('input,textarea')).some(x => x.disabled && x.getBoundingClientRect().height > 0) ||
        /Думаю…/.test(document.body.innerText));
    }).catch(() => true);
    if (!активні && !думає && Date.now() - останній >= 2500) return (Date.now() - т0) / 1000;
    await сон(1000);
  }
  return -1;
}
function оцінка(рядок, мітка) {
  const a = рядок.replace(/^\[\d+\] /, '').replace(/\s+/g, ' ').trim(), b = мітка.replace(/\s+/g, ' ').trim();
  if (a === b) return 3; if (a.startsWith(b)) return 2; if (a.includes(b)) return 1; return 0;
}
async function знайти(мітка) {
  for (let i = 0; i < 30; i++) {
    const ст = await екран(стор);
    const к = ст.елем.map(s => ({s, о: оцінка(s, мітка)})).filter(x => x.о).sort((a, b) => b.о - a.о);
    if (к.length) { const n = Number(к[0].s.match(/^\[(\d+)\]/)[1]); return {лок: стор.locator(`[data-люд="${n}"]`), мітка: к[0].s}; }
    const ключ = ст.прокрутка; await стор.mouse.move(ш / 2, в / 2); await стор.mouse.wheel(0, i < 15 ? 600 : -600); await сон(250);
    const ст2 = await екран(стор); if (ст2.прокрутка === ключ && i < 15) i = 14;
  }
  return null;
}
async function головна() {
  const браузер = await chromium.launch({headless: true, proxy: process.env.HTTPS_PROXY ? {server: process.env.HTTPS_PROXY, bypass: 'localhost,127.0.0.1'} : undefined});
  const телефон = ш < 600;
  const ctx = await браузер.newContext({viewport: {width: ш, height: в}, deviceScaleFactor: 1, isMobile: телефон, hasTouch: телефон, locale: 'uk-UA',
    timezoneId: 'Europe/Kyiv', ignoreHTTPSErrors: true, acceptDownloads: true,
    userAgent: телефон ? 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Mobile Safari/537.36' : undefined});
  стор = await ctx.newPage(); стор.setDefaultTimeout(15000);
  стор.on('console', m => { if (['warning', 'error'].includes(m.type())) fs.appendFileSync(path.join(вихід, 'консоль.txt'), new Date().toISOString() + ' ' + m.text().slice(0, 2000) + '\n'); });
  стор.on('pageerror', e => fs.appendFileSync(path.join(вихід, 'консоль.txt'), new Date().toISOString() + ' pageerror ' + String(e) + '\n'));
  стор.on('download', async d => { const ф = path.join(вихід, 'завантаження', d.suggestedFilename()); fs.mkdirSync(path.dirname(ф), {recursive: true}); await d.saveAs(ф); журнал('завантажено ' + ф); });
  стор.on('filechooser', () => {});
  стор.on('response', r => { if (r.request().resourceType() === 'document') журнал('документ ' + r.status() + ' ' + r.url() + ' last-modified=' + (r.headers()['last-modified'] || '')); });
  await стор.route(u => u.origin + '/' === МІСТ, async route => {
    if (route.request().method() !== 'POST') return route.fallback();
    const тіло = route.request().postData() || '{}', початок = new Date().toISOString(), т0 = Date.now();
    if (МІСТ_РЕЖИМ !== 'real' || (СТЕЛЯ && справжніх >= СТЕЛЯ)) {
      fs.appendFileSync(path.join(вихід, 'обміни.jsonl'), JSON.stringify({час: початок, заглушка: true, запит: тіло.slice(0, 4000)}) + '\n');
      return route.fulfill({status: 503, contentType: 'application/json', body: JSON.stringify({error: {type: 'заглушка', message: 'stub: міст не кликано'}})});
    }
    активні++; справжніх++; останній = Date.now();
    try {
      const r = await route.fetch({timeout: 960000}); const body = await r.text(); const h = r.headers(), x = {};
      for (const n in h) if (/^x-|^retry-after|^anthropic-ratelimit/.test(n)) x[n] = h[n];
      fs.appendFileSync(path.join(вихід, 'обміни.jsonl'), JSON.stringify({час: початок, с: (Date.now() - т0) / 1000, статус: r.status(), заголовки: x, запит: тіло, відповідь: body}) + '\n');
      if (x['x-runs-left'] && x['x-runs-left'] !== 'n/a') { журнал('СТОП: x-runs-left=' + x['x-runs-left']); fs.writeFileSync(path.join(вихід, 'СТОП.txt'), 'x-runs-left=' + x['x-runs-left']); }
      await route.fulfill({response: r, body});
    } catch (e) {
      fs.appendFileSync(path.join(вихід, 'обміни.jsonl'), JSON.stringify({час: початок, с: (Date.now() - т0) / 1000, запит: тіло, помилка: String(e)}) + '\n');
      await route.fulfill({status: 502, body: JSON.stringify({error: {message: String(e)}})}).catch(() => {});
    } finally { активні--; останній = Date.now(); }
  });
  const адреса = СТОРІНКА + '#міст=' + МІСТ + '&т=tok-stub' + (process.env.HESH ? "&" + process.env.HESH : '');
  журнал('відкриваю ' + адреса + ' міст=' + МІСТ_РЕЖИМ + ' ' + ш + '×' + в);
  await стор.goto(адреса, {waitUntil: 'load', timeout: 300000}); await сон(5000); await спокій();
  fs.writeFileSync(path.join(вихід, 'готово.txt'), new Date().toISOString());
  let n = 0;
  while (true) {
    const ім = String(n).padStart(4, '0'), ф = path.join(черга, ім + '.json');
    if (!fs.existsSync(ф)) { await сон(500); continue; }
    let к; try { к = JSON.parse(fs.readFileSync(ф, 'utf8')); } catch (e) { await сон(300); continue; }
    const відп = {n, к, початок: new Date().toISOString()};
    try {
      if (к.дія === 'тап' || к.дія === 'друк' || к.дія === 'файл') {
        const з = await знайти(к.мітка); if (!з) throw new Error('нема елемента: ' + к.мітка); відп.знайдено = з.мітка;
        if (к.дія === 'тап') await з.лок.click({timeout: 15000});
        if (к.дія === 'друк') await з.лок.fill(к.текст);
        if (к.дія === 'файл') { const тип = await з.лок.evaluate(x => x.tagName + ':' + (x.type || ''));
          if (/INPUT:file/.test(тип)) await з.лок.setInputFiles(к.шляхи); else { const [fc] = await Promise.all([стор.waitForEvent('filechooser', {timeout: 8000}), з.лок.click()]); await fc.setFiles(к.шляхи); } }
      } else if (к.дія === 'гортай') { await стор.mouse.move(ш / 2, в / 2); await стор.mouse.wheel(0, к.dy || 600); }
      else if (к.дія === 'ключ') { await стор.keyboard.press(к.ключ); }
      else if (к.дія === 'js') { відп.js = await стор.evaluate(к.код); }
      else if (к.дія === 'кінець') { fs.writeFileSync(path.join(черга, ім + '.відп.json'), JSON.stringify(відп)); break; }
      if (к.дія !== 'кадр' && к.дія !== 'екран') { await сон(к.пауза || 1200); }
      if (к.чекати !== false && к.дія !== 'екран') відп.чекав_с = await спокій(к.межа || 900);
    } catch (e) { відп.помилка = String(e).split('\n')[0]; }
    await стор.screenshot({path: path.join(знімки, ім + '.jpg'), type: 'jpeg', quality: 72, timeout: 0, fullPage: !!к.весь}).catch(() => {});
    const ст = await екран(стор); відп.кінець = new Date().toISOString(); відп.текст = ст.текст; відп.елем = ст.елем; відп.справжніх = справжніх;
    fs.writeFileSync(path.join(черга, ім + '.відп.json'), JSON.stringify(відп, null, 1));
    журнал(`${ім} ${к.дія} ${к.мітка || ''} ${відп.помилка || ''}`);
    n++;
  }
  await браузер.close();
}
головна().catch(e => { fs.writeFileSync(path.join(вихід, 'збій.txt'), String(e.stack)); console.error(e); process.exit(1); });
