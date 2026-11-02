/* Відтворення хибного зеленого результату: незмінені фрагменти показу й умови PR. */
const fs = require('fs'), path = require('path');
const {chromium} = require('playwright');
const [корінь, тека] = process.argv.slice(2);
const стенд = fs.readFileSync(path.join(корінь, 'аудит/проби/рв6_стенд.js'), 'utf8');
const показ = fs.readFileSync(path.join(корінь, 'джерела/показ/картки.js'), 'utf8');
const старе = стенд.split('\n').find(р => р.includes('к.фото + к.без_свого === к.речей')).trim().replace(/,$/, '');
const нове = стенд.split('\n').find(р => р.includes('фотоКарток[i].filter(ф_ => ф_.ok).length >= к.фото')).trim().replace(/,$/, '');
const обчислити = (умова, картки, фотоКарток) => new Function('с2', 'фотоКарток', 'return ' + умова)({картки}, фотоКарток);
const записи = JSON.parse(fs.readFileSync(path.join(тека, 'записи.json'), 'utf8'));
const числа = {записів: записи.length, стара_зелена: 0, нова_червона: 0};
for (const з of записи){
  const фото = з.картки.map(к => Array.from({length: к.img}, (_, і) => ({ok: і < к.прийшло})));
  числа.стара_зелена += Number(обчислити(старе, з.картки, фото));
  числа.нова_червона += Number(!обчислити(нове, з.картки, фото));
}
console.log(JSON.stringify(числа));
const ланцюг = показ.slice(показ.indexOf('function силуетКадру()'), показ.indexOf('const ЧИСЛА ='));
const колаж = показ.slice(показ.indexOf('  const зФото = речі.filter'), показ.indexOf('  /* СПИСОК РЕЧЕЙ:'));
const початок = показ.indexOf("      if (x.фото){ const і = ел('img', 'мініатюра');");
const мініатюра = показ.slice(початок, показ.indexOf('      /* річ, у якої кадрів нема зовсім', початок));
(async () => {
  const браузер = await chromium.launch({headless: true});
  try {
    const стор = await браузер.newPage({viewport: {width: 390, height: 844}});
    const помилки = [];
    стор.on('pageerror', п => помилки.push(String(п)));
    await стор.route('https://фото.invalid/**', р => р.fulfill({status: 404, body: ''}));
    await стор.setContent('<meta charset="utf-8"><style>body{font-family:serif;margin:15px}img,.арка{display:inline-block;width:95px;height:140px;object-fit:contain}.арка{background:#ddd;border-radius:45px 45px 0 0}.колаж-вн,.список{display:flex;gap:20px}.мініатюра{width:60px;height:80px}</style><h2>Проба звірки #2461</h2><p>Дві речі: одна з фото, друга — силует.</p><div id="картки"><div class="картка"></div></div>');
    await стор.addScriptTag({content: `
      const ел = (т, к) => {const е=document.createElement(т); if(к)е.className=к; return е;};
      const назваЖінціП = (е, т, н, поле) => е.setAttribute(поле, т);
      const елЖінціП = (т, к, текст) => {const е=ел(т,к); е.textContent=текст; return е;};
      const ВЕЛИКІ_СЛОТИ=[], НАПИСИ_БЕЗ_ШАРУ_П=new Set(), своїКартки={};
      ${ланцюг}
      const д=document.querySelector('.картка'), к={кадр_не_відкрився:'Фото не відкривається'};
      const фото='data:image/svg+xml,'+encodeURIComponent('<svg xmlns="http://www.w3.org/2000/svg" width="120" height="160"><rect width="120" height="160" fill="beige"/><path d="M30 25L10 50L25 70L35 60V145H85V60L95 70L110 50L90 25L75 20Q60 40 45 20Z" fill="navy"/></svg>');
      const речі=[{id:'1',назва:'Сукня',фото},{id:'2',назва:'Друга річ',фото:'https://фото.invalid/нема.png'}];
      ${колаж}
      const список=ел('div','список'); д.appendChild(список);
      for(const x of речі){const о=ел('div','річ'),н=ел('div','н'); список.appendChild(о); ${мініатюра} о.appendChild(н);}
      document.querySelectorAll('img').forEach(і=>і.loading='eager');
    `});
    await стор.waitForFunction(() => document.querySelectorAll('.арка').length === 2 &&
      [...document.querySelectorAll('img')].every(і => і.complete && і.naturalWidth > 0));
    const стан = await стор.evaluate(() => ({силуетів: document.querySelectorAll('.арка').length,
      фото: [...document.querySelectorAll('.картка img')].map(і => ({src: і.currentSrc || і.src,
        w: і.naturalWidth, h: і.naturalHeight, ok: !!(і.complete && і.naturalWidth > 0)}))}));
    const результат = {речей: 2, 'речей_із_видимим_фото': 1, силуетів: стан.силуетів,
      завантажених_img: стан.фото.filter(ф => ф.ok).length,
      нова_звірка_зелена: обчислити(нове, [{рука: '1', фото: 2}], [стан.фото]), помилки};
    console.log(JSON.stringify(результат));
    await стор.screenshot({path: path.join(тека, 'дублікати-390x844.png')});
    if (!результат.нова_звірка_зелена || результат.силуетів !== 2 || помилки.length) process.exitCode = 1;
  } finally {await браузер.close();}
})().catch(п => {console.error(п); process.exitCode = 1;});
