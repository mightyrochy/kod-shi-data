/* Вузький UI прогін A по спільному stockbuild; не збирає HTML й не запускає Pyodide. */
const fs = require('fs'), http = require('http'), path = require('path'), crypto = require('crypto');
const assert = require('assert/strict');
const { chromium } = require('playwright');
const файл = process.argv[2], вихід = path.resolve(process.argv[3]);
if (!файл || !вихід) throw Error('Потрібні зібраний HTML і тека результатів');
const html = fs.readFileSync(файл), sha = crypto.createHash('sha256').update(html).digest('hex');
const сервер = http.createServer((req, res) => {
  if (req.url === '/index.html') { res.setHeader('Content-Type', 'text/html; charset=utf-8'); res.end(html); }
  else { res.statusCode = 404; res.end(); }
});
(async () => {
  await new Promise(resolve => сервер.listen(0, '127.0.0.1', resolve));
  const адреса = 'http://127.0.0.1:' + сервер.address().port;
  const браузер = await chromium.launch({headless:true, executablePath:process.env.CHROMIUM,
    args:['--no-sandbox','--disable-dev-shm-usage']});
  const сторінка = await браузер.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
  const помилки = [], мережа = [];
  сторінка.on('pageerror', e => помилки.push(String(e)));
  await сторінка.route('**/*', route => {
    if (route.request().url().startsWith(адреса + '/')) return route.continue();
    мережа.push(new URL(route.request().url()).hostname); return route.abort();
  });
  try {
    await сторінка.goto(адреса+'/index.html', {waitUntil:'load'});
    await сторінка.waitForFunction(() => typeof ПЕРЕЛІКИ_П !== 'undefined'
      && !!АКТИВНИЙ && typeof document.getElementById('пф-вибір').onchange === 'function');
    const значення = await сторінка.evaluate(() => ({збірка:ЗБІРКА_ПОКАЗУ, переліки:ПЕРЕЛІКИ_П,
      main:typeof розмоваЯкMainП, великі:ВЕЛИКІ_СЛОТИ, зони:ЗОНИ_ВЕТО_П, гами:ГАМИ}));
    assert.deepEqual(значення.переліки, {
      великі_слоти:['сукня','верх','низ','верхній_шар'], гами:['приглушені','середні','насичені'],
      групи_вето:['типи','тканини','принти','кольори','зони'], драп:['метал','білий','нейтралі','барви'],
      зони_вето:['декольте','спина','руки','плечі','ноги','живіт'],
      основні_обхвати:['плечі','груди','талія','стегна'], текстові_групи_вето:['типи','тканини','принти','кольори']});
    assert.equal(значення.main,'function');
    assert.deepEqual(значення.великі,значення.переліки.великі_слоти);
    assert.deepEqual(значення.зони,значення.переліки.зони_вето);
    assert.deepEqual(значення.гами,значення.переліки.гами);
    await сторінка.evaluate(() => відкритиПрофіль('др-блок'));
    await сторінка.waitForFunction(() => document.querySelectorAll('#др-тіло .мітка').length === 4);
    const питання = await сторінка.locator('#др-тіло .мітка').allTextContents();
    assert.deepEqual(питання,['Золото чи срібло біля обличчя','Білий чи молочний','Теплі чи холодні нейтралі','Твої власні барви — очі, волосся, губи']);
    const відповіді = [['Золото','метал','золото'], ['Молочний','білий','вершковий'],
      ['Теплі','нейтралі','теплі'], ["Приглушені, м'які",'барви','приглушені']];
    for (const [текст,ключ,значення] of відповіді) {
      await сторінка.locator('#др-тіло .чип').filter({hasText:new RegExp('^'+текст+'$')}).click();
      await сторінка.waitForFunction(([к,в]) => ДРАП[к]===в && document.getElementById('др-стан').textContent.includes('Відповіла'), [ключ,значення]);
    }
    await сторінка.waitForFunction(() => document.getElementById('др-стан').textContent==='Відповіла на 4 з 4.');
    const факти = await сторінка.evaluate(() => {
      const збережено = JSON.parse(JSON.stringify(ДРАП));
      const очищуваний = {вето:{типи:['а'],тканини:['б'],принти:['в'],кольори:['г'],зони:['декольте']},
        вето_тверде:{типи:['а'],тканини:['б'],принти:['в'],кольори:['г'],зони:['декольте']}};
      for (const к of ПЕРЕЛІКИ_П.групи_вето) зняттяВетоП(к,очищуваний.вето[к][0],true);
      почиститиВетоП(очищуваний);
      const межі = межіПаспорта({вето_тверде:{типи:['а'],тканини:['б'],принти:['в'],кольори:['г'],зони:['декольте']}});
      ЗНЯТІ_ВЕТО_П = [];
      for (const [ід,к] of ПОЛЯ_ОБХВАТІВ) document.getElementById(ід).value=ПЕРЕЛІКИ_П.основні_обхвати.includes(к)?'90':'';
      const стан = станДляШі();
      return {драп:збережено, очищуваний, межі, стан, статус:document.getElementById('др-стан').textContent};
    });
    assert.deepEqual(факти.драп,{білий:'вершковий',метал:'золото',нейтралі:'теплі',барви:'приглушені'});
    for (const в of Object.values(факти.очищуваний)) assert.ok(Object.values(в).every(x=>x.length===0));
    assert.deepEqual(факти.межі,['а','б','в','г','не відкриваємо декольте']);
    assert.equal(факти.стан.профіль.що_до_лиця,4);
    assert.ok(значення.переліки.основні_обхвати.every(к=>!факти.стан.бракує.includes(к)));
    await сторінка.locator('#аркуш-тіло').evaluate(e=>e.scrollTop=0);
    await сторінка.screenshot({path:path.join(вихід,'драп-390x844.png')});
    await сторінка.locator('#др-стан').scrollIntoViewIfNeeded();
    await сторінка.screenshot({path:path.join(вихід,'драп-відповіді-390x844.png')});
    assert.deepEqual(помилки,[]);
    const результат = {html_sha256:sha,html:файл,збірка:значення.збірка,вікно:[390,844],
      експорт:значення.переліки,питання,факти,main:значення.main,помилки,
      зовнішня_мережа_заблокована:[...new Set(мережа)],моделі_не_викликались:true};
    fs.writeFileSync(path.join(вихід,'результат.json'),JSON.stringify(результат,null,2));
    console.log(JSON.stringify({збірка:значення.збірка,html_sha256:sha,експорт:'7 ключів тотожні',
      драп:'4 питання / 4 відповіді',вето:'5 груп очищаються в обох формах',обхвати:'4 виміри почуті',помилки:помилки.length}));
  } finally { await браузер.close(); await new Promise(resolve=>сервер.close(resolve)); }
})().catch(e=>{console.error(e.stack);сервер.close();process.exitCode=1;});
