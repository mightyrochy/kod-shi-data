/* Безплатний вимір набору фото жінок: (1) контроль маски «та сама людина» на кожному фото в повний зріст
   (кадр → кадр, той самий конвеєр, що в `примірка-openai-маска-на-фото/прогін.js`), (2) вимір кольорів з кожного портрета
   кодом сторінки (`вимірПортретаП` → `портрет_вимір`, Pyodide). Мережі моста нема: будь-який POST до моста обривається.
   Рамки зон — на око з самого кадру (місце моделі зору, яку тут не кличемо); мають форму `из.зони` (тисячні).
   Запуск: STOR=<корінь з index.html> PYODIDE=/tmp/pyodide node прогін.js <виміри.json> */
const fs = require('fs'), path = require('path');
const {chromium} = require('playwright');
const ТЕКА = __dirname, вих = path.resolve(process.argv[2] || path.join(ТЕКА, 'виміри.json'));
const база = 'https://mightyrochy.github.io';
const W = 760, H = 1024;
/* рамки в пікселях кадру 760×1024: [ліво, верх, право, низ] */
const ЗОНИ = {
  ж1: {щока_ліва:[245,430,335,540], щока_права:[470,430,560,540], лоб:[300,190,500,260], волосся:[125,400,195,700], око_ліве:[297,350,325,382], око_праве:[465,346,495,376]},
  ж2: {щока_ліва:[275,400,350,500], щока_права:[470,400,545,500], лоб:[310,200,490,270], волосся:[140,450,225,650], око_ліве:[321,322,347,348], око_праве:[465,324,491,350]},
  ж3: {щока_ліва:[240,440,330,560], щока_права:[470,440,555,560], лоб:[290,220,500,290], волосся:[118,300,185,540], око_ліве:[297,370,323,396], око_праве:[464,371,490,397]},
  ж4: {щока_ліва:[235,470,325,580], щока_права:[480,470,575,580], лоб:[300,235,510,300], волосся:[240,90,560,160], око_ліве:[296,389,324,417], око_праве:[481,388,509,416]},
  ж7: {щока_ліва:[235,450,330,560], щока_права:[475,450,565,560], лоб:[300,230,500,290], волосся:[250,70,520,150], око_ліве:[304,389,330,415], око_праве:[468,390,494,416]},
  ж8: {щока_ліва:[245,460,340,560], щока_права:[470,460,565,560], лоб:[300,250,500,320], волосся:[205,560,260,720], око_ліве:[308,392,336,418], око_праве:[467,393,495,419]},
};
const тисячні = ([л,в,п,н]) => ({ліво: Math.round(л/W*1000), верх: Math.round(в/H*1000), право: Math.round(п/W*1000), низ: Math.round(н/H*1000)});
(async () => {
  const б = await chromium.launch({headless:true, proxy: process.env.HTTPS_PROXY ? {server:process.env.HTTPS_PROXY, bypass:'localhost,127.0.0.1'} : undefined});
  const ctx = await б.newContext({viewport:{width:390,height:844}, ignoreHTTPSErrors:true, locale:'uk-UA'});
  const стор = await ctx.newPage(); стор.setDefaultTimeout(0);
  let постів = 0;
  await стор.route(u => u.origin === база, async r => {
    const ім = decodeURIComponent(new URL(r.request().url()).pathname).replace(/^\/kod-shi-data\//,'').replace(/^\//,'') || 'index.html';
    const ф = path.join(process.env.STOR, ім);
    await r.fulfill({status: fs.existsSync(ф)?200:404, contentType:'text/html; charset=utf-8', body: fs.existsSync(ф)?fs.readFileSync(ф):'нема'});
  });
  await стор.route('https://cdn.jsdelivr.net/pyodide/**', async r => {
    const ім = new URL(r.request().url()).pathname.split('/').pop(), ф = path.join(process.env.PYODIDE, ім);
    await r.fulfill({status: fs.existsSync(ф)?200:404, contentType: ім.endsWith('.wasm')?'application/wasm':/\.m?js$/.test(ім)?'application/javascript':ім.endsWith('.json')?'application/json':'application/octet-stream', body: fs.existsSync(ф)?fs.readFileSync(ф):''});
  });
  /* лише публічні безплатні вага й скрипт сегментера (mediapipe, `джерела/показ/повернення.js`); решта, зокрема міст, — обрив */
  await стор.route(u => u.origin !== база && !/cdn\.jsdelivr\.net\/pyodide/.test(u.href), async r => {
    if (r.request().method() === 'POST') постів++;
    if (r.request().method() === 'GET' && /^https:\/\/(cdn\.jsdelivr\.net\/npm\/@mediapipe\/|storage\.googleapis\.com\/mediapipe-models\/)/.test(r.request().url())) {
      try { return await r.fulfill({response: await r.fetch({timeout:120000})}); } catch(_) {}
    }
    await r.abort().catch(()=>{});
  });
  await стор.goto(база + '/kod-shi-data/index.html', {waitUntil:'load', timeout:180000});
  await стор.waitForTimeout(8000);
  const рез = {};
  for (const ж of Object.keys(ЗОНИ)) {
    const повний = fs.readFileSync(path.join(ТЕКА, ж + '-повний-зріст.jpg')).toString('base64');
    const портрет = fs.readFileSync(path.join(ТЕКА, ж + '-портрет.jpg')).toString('base64');
    const зони = {}; for (const к in ЗОНИ[ж]) зони[к] = тисячні(ЗОНИ[ж][к]);
    рез[ж] = await стор.evaluate(async ({повний, портрет, зони}) => {
      const о = {};
      const блоб = await (await fetch('data:image/jpeg;base64,' + повний)).blob();
      const її = await фотоДоСторониП(await блобВБазу(блоб), СТОРОНА_ФОТО_ЛЮДИНИ_П);
      о.кадр = {ширина: її.ширина, висота: її.висота};
      const підготовка = підготуватиПоверненняП(її);
      const кон = await повернутиЛюдинуП(підготовка, {media_type: її.тип, data: її.дані}, false);
      о.маска = {прийнято: !!кон.кадр, звіт: JSON.parse(JSON.stringify(кон.звіт))};
      const б2 = await (await fetch('data:image/jpeg;base64,' + портрет)).blob();
      const п = await блобВБазу(б2);
      const вим = await вимірПортретаП(п, зони);
      о.вимір = JSON.parse(JSON.stringify(вим));
      return о;
    }, {повний, портрет, зони});
  }
  fs.writeFileSync(вих, JSON.stringify({постів_до_моста_обірвано: постів, жінки: рез}, null, 1));
  console.log(JSON.stringify({постів, жінки: Object.fromEntries(Object.entries(рез).map(([ж, о]) => [ж, {маска: o_(о.маска), вимір: о.вимір && {стан: о.вимір.стан, причини: о.вимір.причини, шкіра: о.вимір.шкіра && о.вимір.шкіра.hex, волосся: о.вимір.волосся && о.вимір.волосся.hex, очі: о.вимір.очі && о.вимір.очі.hex}}]))}, null, 1));
  function o_(м){ return {прийнято: м.прийнято, звіт: м.звіт}; }
  await б.close();
})().catch(e => { console.error(e); process.exit(1); });
