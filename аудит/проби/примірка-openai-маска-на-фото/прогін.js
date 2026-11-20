/* Одна жива примірка через справжній міст: вхід «вона» — ФОТО справжньої жінки на повний зріст (Wikimedia Commons, вільна ліцензія),
   яке лежить ПОЗА репозиторієм. Спершу безкоштовний контроль маски «та сама людина» на самому фото (не прийняла — платного виклику нема),
   потім (PAID=1) один платний виклик і вердикт маски на результаті.
   Запуск: STOR=<корінь з index.html> PYODIDE=/tmp/pyodide node прогін.js <тека-виходу-поза-репо> <фото.jpg> [PAID=1 у середовищі].
   У теці виходу лишаються кадр і результат; у репозиторій іде лише `виміри.json` (без зображень). Стеля: 2 POST до моста з gpt-image-*. */
const fs = require('fs'), path = require('path');
const {chromium} = require('playwright');
const вих = path.resolve(process.argv[2] || '.'); fs.mkdirSync(вих, {recursive:true});
const ФОТО = path.resolve(process.argv[3]); const PAID = process.env.PAID === '1';
const МІСТ = 'https://lyusterko-mist.mighty-rochy.workers.dev/', база = 'https://mightyrochy.github.io';
const РІЧ = path.resolve(__dirname, '../фото_сцен/ж-01851@onebyone.ua.jpg');
const обміни = []; let платних = 0;
(async () => {
  const б = await chromium.launch({headless:true, proxy: process.env.HTTPS_PROXY ? {server:process.env.HTTPS_PROXY, bypass:'localhost,127.0.0.1'} : undefined});
  const ctx = await б.newContext({viewport:{width:390,height:844}, ignoreHTTPSErrors:true, locale:'uk-UA'});
  const стор = await ctx.newPage(); стор.setDefaultTimeout(0);
  стор.on('console', m => { if (['error','warning'].includes(m.type())) fs.appendFileSync(path.join(вих,'консоль.txt'), m.text().slice(0,300)+'\n'); });
  await стор.route(u => u.origin === база, async r => {
    const ім = decodeURIComponent(new URL(r.request().url()).pathname).replace(/^\/kod-shi-data\//,'').replace(/^\//,'') || 'index.html';
    const ф = path.join(process.env.STOR, ім);
    await r.fulfill({status: fs.existsSync(ф)?200:404, contentType:'text/html; charset=utf-8', body: fs.existsSync(ф)?fs.readFileSync(ф):'нема'});
  });
  await стор.route('https://cdn.jsdelivr.net/pyodide/**', async r => {
    const ім = new URL(r.request().url()).pathname.split('/').pop(), ф = path.join(process.env.PYODIDE, ім);
    await r.fulfill({status: fs.existsSync(ф)?200:404, contentType: ім.endsWith('.wasm')?'application/wasm':/\.m?js$/.test(ім)?'application/javascript':ім.endsWith('.json')?'application/json':'application/octet-stream', body: fs.existsSync(ф)?fs.readFileSync(ф):''});
  });
  await стор.route(u => u.origin !== база && u.origin+'/' !== МІСТ && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href), async r => {
    try { await r.fulfill({response: await r.fetch({timeout:60000})}); } catch(_) { await r.abort().catch(()=>{}); }
  });
  await стор.route(u => u.origin+'/' === МІСТ, async route => {
    if (route.request().method() !== 'POST') return route.fallback();
    const тіло = route.request().postData() || '{}'; let мод = ''; try { мод = JSON.parse(тіло).model || ''; } catch(_) {}
    if (/^gpt-image-/.test(мод)) {
      if (!PAID || платних >= 2) { обміни.push({обірвано:true, платних}); return route.abort(); }
      платних++;
    }
    const т0 = Date.now();
    try {
      const r = await route.fetch({timeout:600000}); const t = await r.text(); const h = r.headers(); const x = {};
      for (const n in h) if (/^x-|^retry-after|^content-type|^cf-ray/.test(n)) x[n] = h[n];
      let ключі = null, usage = null; try { const j = JSON.parse(t); ключі = Object.keys(j); usage = j.usage || null; } catch(_) {}
      обміни.push({модель: мод, статус: r.status(), секунд: (Date.now()-т0)/1000, заголовки: x, usage, ключі_відповіді: ключі,
        тіло_запиту_байтів: Buffer.byteLength(тіло), тіло_відповіді_байтів: Buffer.byteLength(t),
        тіло_відмови: r.status() === 200 ? null : t.slice(0, 1500)});
      await route.fulfill({response: r, body: t});
    } catch(e) { обміни.push({модель: мод, помилка: String(e)}); await route.abort().catch(()=>{}); }
  });
  await стор.goto(база + '/kod-shi-data/index.html#міст=' + МІСТ + '&т=tok-stub', {waitUntil:'load', timeout:180000});
  await стор.waitForTimeout(8000);
  const річБ64 = fs.readFileSync(РІЧ).toString('base64');
  const р = await стор.evaluate(async ({річБ64, фотоБ64, PAID}) => {
    const звіт = {};
    // 1. фото жінки (байти з теки поза репо) → той самий конвеєр сторінки, що й для завантаженого фото
    const блоб = await (await fetch('data:image/jpeg;base64,' + фотоБ64)).blob();
    const їїБ = await блобВБазу(блоб); const її = await фотоДоСторониП(їїБ, СТОРОНА_ФОТО_ЛЮДИНИ_П);
    звіт.її = {ширина: її.ширина, висота: її.висота, символів: її.дані.length};
    звіт.її_дані = її.дані;
    // 2. маска (безкоштовно, поки генератор «малює»)
    const підготовка = підготуватиПоверненняП(її);
    // 3. промпт — з моста тим самим містП(...), що й сторінка; річ — власна (байти), як `свої` в приміряти()
    const річБл = блокФотоП({тип:'image/jpeg', дані: річБ64});
    const вхід = {з_фото:[{слот:'сукня', назва:'сукня', код_кольору:null, hex:null, крій:null, довжина_рівень:null, матеріал:null, деталі:null, власна:true, кадр_інший:false}],
                  без_фото:[], макіяж:null, як_носити:null};
    const пр = await містП('приміряння', вхід);
    звіт.промпт_довжина = (пр.промпт||'').length; звіт.промпт_ключі = Object.keys(JSON.parse(пр.промпт));
    const зміст = [{type:'image', source:{type:'base64', media_type:її.тип, data:її.дані}}, річБл, {type:'text', text: пр.промпт}];
    звіт.вхід_зображень_символів = [її.дані.length, річБ64.length];
    { const п = await підготовка; звіт.маска_підготовка = п.е ? 'збій: ' + String(п.е.message||п.е).slice(0,200) : 'готова';
      const кон = await повернутиЛюдинуП(підготовка, {media_type: її.тип, data: її.дані}, false);
      звіт.контроль_вхід = {прийнято: !!кон.кадр, звіт: JSON.parse(JSON.stringify(кон.звіт))};
      if (!кон.кадр) { звіт.зупинено = 'контроль на вході не прийнято — платного виклику нема'; return звіт; } }
    if (!PAID) { const п = await підготовка; звіт.маска_підготовка = п.е ? 'збій: ' + String(п.е.message||п.е).slice(0,200) : 'готова'; return звіт; }
    const зг = {}, вміщ = {};
    const т0 = performance.now(); let блоки;
    try { блоки = await модельЗадачіП(зміст, null, null, 'gpt-image-2.6-sunburst', зг, undefined, вміщ); }
    catch(e) { звіт.виклик_помилка = String(e && e.message || e).slice(0,600); return звіт; }
    звіт.секунд_на_сторінці = (performance.now()-т0)/1000;
    const кар = блоки.find(b => b.type === 'image');
    звіт.блоки = блоки.map(b => b.type + (b.type==='text' ? ':'+String(b.text).slice(0,200) : ''));
    звіт.журнал_викликів = JSON.parse(JSON.stringify(ЖУРНАЛ_ВИКЛИКІВ_П.slice(-3)));
    звіт.зведення = JSON.parse(JSON.stringify(зведенняВикликівП(0)));
    звіт.токени_п = JSON.parse(JSON.stringify(ТОКЕНИ_П));
    if (кар) {
      const вим = await розмір_картинки(кар.source.media_type, кар.source.data);
      звіт.результат = {тип: кар.source.media_type, ...вим, символів: кар.source.data.length};
      звіт.результат_дані = кар.source.data;
      const пов = await повернутиЛюдинуП(підготовка, кар.source, false);
      звіт.маска = {прийнято: !!пов.кадр, звіт: JSON.parse(JSON.stringify(пов.звіт))};
    }
    return звіт;
  }, {річБ64, фотоБ64: fs.readFileSync(ФОТО).toString('base64'), PAID});
  const її = р.її_дані, рез = р.результат_дані; delete р.її_дані; delete р.результат_дані;
  if (її) fs.writeFileSync(path.join(вих,'вона_кадр.jpg'), Buffer.from(її,'base64'));
  if (рез) fs.writeFileSync(path.join(вих,'результат.png'), Buffer.from(рез,'base64'));
  fs.writeFileSync(path.join(вих, PAID ? 'виміри.json' : 'суха_частина.json'), JSON.stringify({сторінка:р, обміни}, null, 1));
  console.log(JSON.stringify({сторінка:р, обміни}, null, 1).slice(0, 6000));
  await б.close();
})().catch(e => { console.error(e); process.exit(1); });
